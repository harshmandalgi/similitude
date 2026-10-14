"""The Runtime: every LLM and tool call of a workflow goes through here, so a Recipe can swap in
its shortcuts (replay, simulated tools, fused loops, ...) without touching the workflow's code.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from similitude.cache import Cache, key_of
from similitude.core import Event, Tool, Trace, Workflow
from similitude.fuse import fused_system, parse_fused
from similitude.llm import Completion, LLMClient
from similitude.reduce import Recipe
from similitude.simulate import Recorded, injected_failure, sim_prompt

MEMO = "memo/tools"  # real tool outputs, kept so re-runs need not hit the real service again

SHRINK_SYSTEM = """\
Rewrite the system prompt you are given to about one third of its length. Keep every instruction \
that changes behaviour (format rules, steps, constraints). Drop politeness, repetition and \
examples. Reply with only the rewritten prompt."""


@dataclass
class Records:
    """What the base variant's full runs recorded. Minis may replay these (operators A1, A2)."""

    llm: dict[str, dict[str, Any]] = field(default_factory=dict)  # key -> completion json
    tool: dict[str, str] = field(default_factory=dict)  # key -> output
    by_tool: dict[str, list[Recorded]] = field(default_factory=dict)

    @classmethod
    def from_traces(cls, traces: list[Trace]) -> Records:
        records = cls()
        for trace in traces:
            for e in trace.events:
                if e.kind == "llm" and e.completion and e.source != "imagined":
                    records.llm[e.key] = e.completion
                elif e.kind == "tool" and e.source in ("real", "memo"):
                    records.tool[e.key] = e.output
                    records.by_tool.setdefault(e.name, []).append(
                        Recorded(trace.task_id, e.args, e.output)
                    )
        return records


@dataclass
class AgentResult:
    final: str
    steps: int
    exhausted: bool = False


class Runtime:
    def __init__(
        self,
        *,
        workflow: Workflow,
        client: LLMClient,
        cache: Cache,
        recipe: Recipe,
        config: dict[str, Any],
        focus: str,
        trace: Trace,
        records: Records | None = None,
    ) -> None:
        self.workflow = workflow
        self.client = client
        self.cache = cache
        self.recipe = recipe
        self.config = config
        self.focus = focus
        self.trace = trace
        self.records = records or Records()
        self.tools: dict[str, Tool] = workflow.tools()
        self.pool = f"pool/{workflow.name}/{recipe.name}"

    # ── what the workflow asks ────────────────────────────────────────────────

    def model_for(self, node: str) -> str:
        if self.recipe.off_focus_model and node != self.focus:
            return self.recipe.off_focus_model
        return self.config["models"][node]

    def skipped(self, node: str) -> bool:
        return node in self.recipe.skip

    def stop_after(self, node: str) -> bool:
        return self.recipe.stop_after == node

    def system_prompt(self, node: str, text: str) -> str:
        """C3: a node's system prompt, compressed when the recipe says so."""
        if node not in self.recipe.shrink:
            return text
        key = "shrink:" + key_of(text)
        hit = self.cache.get(self.pool, key)
        if hit is not None:
            return hit
        c = self.client.chat(
            self.recipe.sim_model,
            [{"role": "system", "content": SHRINK_SYSTEM}, {"role": "user", "content": text}],
            max_tokens=2000,
            tag=f"{self.recipe.name}/shrink",
        )
        self.trace.events.append(
            Event("llm", node, c.model, "sim", key, c.text, cost_usd=c.cost_usd,
                  latency_s=c.latency_s, usage=c.usage.__dict__)
        )  # fmt: skip
        self.cache.put(self.pool, key, "shrink", c.text)
        return c.text

    # ── LLM calls ────────────────────────────────────────────────────────────

    def llm(
        self,
        node: str,
        messages: list[dict[str, Any]],
        *,
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 2000,
        json_mode: bool = False,
        tool_choice: str | None = None,
    ) -> Completion:
        model = self.model_for(node)
        key = key_of(
            {"model": model, "messages": messages, "tools": tools, "max_tokens": max_tokens,
             "json_mode": json_mode, "tool_choice": tool_choice,
             "replicate": self.trace.replicate}
        )  # fmt: skip
        source, hit = "real", None
        if self.recipe.llm_replay:
            hit = self.records.llm.get(key)
            source = "record"
            if hit is None:
                hit = self.cache.get(self.pool, "llm:" + key)
                source = "pool"
        if hit is not None:
            c = Completion.from_json(hit)
            self.trace.events.append(Event("llm", node, model, source, key, c.text, completion=hit))
            return c
        c = self.client.chat(
            model, messages, tools=tools, max_tokens=max_tokens, json_mode=json_mode,
            tool_choice=tool_choice, tag=f"{self.recipe.name}/{node}",
        )  # fmt: skip
        if self.recipe.llm_replay:
            self.cache.put(self.pool, "llm:" + key, "llm", c.to_json())
        self.trace.events.append(
            Event("llm", node, model, "real", key, c.text, cost_usd=c.cost_usd,
                  latency_s=c.latency_s, usage=c.usage.__dict__, completion=c.to_json())
        )  # fmt: skip
        return c

    # ── tool calls ───────────────────────────────────────────────────────────

    def tool(self, node: str, name: str, args: dict[str, Any]) -> str:
        tool = self.tools.get(name)
        key = key_of({"tool": name, "args": args})
        if tool is None:
            output = f"Error: there is no tool named {name!r}."
            self.trace.events.append(Event("tool", node, name, "real", key, output, args=args))
            return output

        output, source, cost, latency = None, "", 0.0, 0.0
        if self.recipe.tool_cache:
            output, source = self.records.tool.get(key), "record"
            if output is None:
                output, source = self.cache.get(self.pool, "tool:" + key), "pool"
        if output is None and self.recipe.tool_sim:
            output, source, cost, latency = self._simulate(tool, args, key)
        if output is None:
            output, source, latency = self._real(tool, args, key)
            if self.recipe.tool_cache:
                self.cache.put(self.pool, "tool:" + key, "tool", output)

        if self.recipe.obs_chars is not None and len(output) > self.recipe.obs_chars:
            output = output[: self.recipe.obs_chars] + " …[cut]"
        self.trace.events.append(
            Event("tool", node, name, source, key, output, args=args, cost_usd=cost,
                  latency_s=latency)
        )  # fmt: skip
        return output

    def _real(self, tool: Tool, args: dict[str, Any], key: str) -> tuple[str, str, float]:
        memo = self.cache.get(MEMO, key)
        if memo is not None:
            return memo["output"], "memo", memo["latency_s"]
        start = time.perf_counter()
        try:
            output = tool.fn(args)
        except Exception as exc:  # noqa: BLE001 - a real tool error is what the agent sees
            output = f"Error: {type(exc).__name__}: {exc}"
            return output, "real", time.perf_counter() - start  # errors are not memoised
        latency = time.perf_counter() - start
        self.cache.put(MEMO, key, "tool", {"output": output, "latency_s": latency})
        return output, "real", latency

    def _simulate(self, tool: Tool, args: dict[str, Any], key: str):
        mode = self.recipe.tool_sim
        recorded = self.records.by_tool.get(tool.name, [])
        if self.recipe.error_injection:
            failure = injected_failure(tool, recorded, self.trace.task_id, args)
            if failure is not None:
                return failure, "sim", 0.0, 0.0
        sim_key = f"sim:{mode}:{self.recipe.sim_model}:{self.trace.task_id}:{key}"
        hit = self.cache.get(self.pool, sim_key)
        if hit is not None:
            return hit, "pool", 0.0, 0.0
        messages = sim_prompt(tool, args, mode, self.trace.task_id, recorded)
        c = self.client.chat(
            self.recipe.sim_model, messages, max_tokens=1500, tag=f"{self.recipe.name}/sim"
        )
        self.cache.put(self.pool, sim_key, "sim", c.text)
        return c.text, "sim", c.cost_usd, c.latency_s

    # ── agent loops ──────────────────────────────────────────────────────────

    def agent(
        self, node: str, system: str, user: str, tool_names: list[str], max_steps: int
    ) -> AgentResult:
        """A standard tool-calling loop. The recipe may fuse it into one call (C2/C4) or cap
        its steps (B2)."""
        tools = [self.tools[n] for n in tool_names]
        if self.recipe.max_steps is not None:
            max_steps = min(max_steps, self.recipe.max_steps)
        system = self.system_prompt(node, system)
        if node in self.recipe.fuse:
            return self._fused(node, system, user, tools, max_steps)

        specs = [t.spec() for t in tools]
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        for step in range(1, max_steps + 1):
            c = self.llm(node, messages, tools=specs)
            messages.append(c.message)
            if not c.tool_calls:
                return AgentResult(c.text, step)
            for call in c.tool_calls:
                output = self.tool(node, call["name"], call["arguments"])
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": output})
        messages.append(
            {"role": "user", "content": "You have used all your steps. Give your final reply now."}
        )
        c = self.llm(node, messages, tools=specs, tool_choice="none")
        return AgentResult(c.text, max_steps, exhausted=True)

    def _fused(
        self, node: str, system: str, user: str, tools: list[Tool], max_steps: int
    ) -> AgentResult:
        messages = [
            {"role": "system", "content": fused_system(system, tools, max_steps)},
            {"role": "user", "content": user},
        ]
        c = self.llm(node, messages, max_tokens=6000)
        steps, final = parse_fused(c.text)
        # Keep the trace in the same shape as a real run: the imagined tool calls first, then a
        # final reply. The full transcript stays in the event's completion, for replay.
        call = self.trace.events.pop()
        call.output = final
        for name, args, imagined in steps:
            self.trace.events.append(
                Event("tool", node, name, "imagined", key_of({"tool": name, "args": args}),
                      imagined, args=args)
            )  # fmt: skip
        self.trace.events.append(call)
        return AgentResult(final, len(steps), exhausted=not final)
