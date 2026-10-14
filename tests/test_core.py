"""Offline tests: a scripted fake LLM and fake tools. No network, no spend."""

from __future__ import annotations

import math

import pytest

from similitude.cache import Cache
from similitude.core import Tool, Trace, Variant, Workflow
from similitude.fuse import parse_fused
from similitude.llm import BudgetExceeded, Completion, Ledger, Usage
from similitude.reduce import FULL, Recipe
from similitude.runtime import Records, Runtime
from similitude.validate import Row, compare, mmrv, scotts_pi


class FakeClient:
    """Calls the tool once, then answers. Counts real calls."""

    def __init__(self, ledger: Ledger | None = None) -> None:
        self.calls = 0
        self.ledger = ledger or Ledger(100.0)

    def chat(self, model, messages, *, tools=None, max_tokens=2000, json_mode=False,
             tool_choice=None, tag=""):  # fmt: skip
        self.ledger.check()
        self.calls += 1
        self.ledger.charge(0.01, tag)
        if "simulating a software tool" in messages[0]["content"]:
            text, calls = "SIMULATED OUTPUT", []
        elif "TEST MODE" in messages[0]["content"]:
            text = (
                'ACTION: lookup {"q": "x"}\nOBSERVATION: imagined result\n'
                "FINAL REPLY: FINAL ANSWER: 42"
            )
            calls = []
        elif tools and tool_choice != "none" and not any(m["role"] == "tool" for m in messages):
            text, calls = "", [{"id": f"c{self.calls}", "name": "lookup", "arguments": {"q": "x"}}]
        else:
            seen = [m["content"] for m in messages if m["role"] == "tool"]
            text, calls = f"FINAL ANSWER: {seen[-1] if seen else 'none'}", []
        message = {"role": "assistant", "content": text}
        if calls:
            message["tool_calls"] = [
                {"id": c["id"], "type": "function",
                 "function": {"name": c["name"], "arguments": '{"q": "x"}'}}
                for c in calls
            ]  # fmt: skip
        return Completion(model, text, calls, message, Usage(10, 0, 5), 0.01, 0.5)


class TinyFlow(Workflow):
    name = "tiny"
    nodes = ("agent",)

    def __init__(self) -> None:
        self.real_calls = 0

    def tools(self):
        def lookup(args):
            self.real_calls += 1
            return "REAL OUTPUT"

        return {"lookup": Tool("lookup", "Look something up.",
                               {"type": "object", "properties": {"q": {"type": "string"}}},
                               lookup, lambda o: o.startswith("none"))}  # fmt: skip

    def base_config(self):
        return {"models": {"agent": "fake:model"}, "prompts": {"agent": "Be good."}}

    def run(self, task, rt, config):
        return rt.agent("agent", config["prompts"]["agent"], task["q"], ["lookup"], 5).final


def _run(flow, client, cache, recipe, records=None, variant="base", task_id="t1"):
    trace = Trace(flow.name, recipe.name, variant, task_id, 0)
    config = flow.base_config()
    rt = Runtime(workflow=flow, client=client, cache=cache, recipe=recipe, config=config,
                 focus="agent", trace=trace, records=records)  # fmt: skip
    trace.final = flow.run({"q": "question?"}, rt, config)
    return trace


def test_full_run_calls_real_tool_and_records_cost():
    flow, client = TinyFlow(), FakeClient()
    trace = _run(flow, client, Cache(":memory:"), FULL)
    assert trace.final == "FINAL ANSWER: REAL OUTPUT"
    assert flow.real_calls == 1 and client.calls == 2
    assert trace.cost_usd == pytest.approx(0.02)
    assert [e.source for e in trace.events] == ["real", "real", "real"]


def test_replay_reuses_recorded_calls_for_free():
    flow, client, cache = TinyFlow(), FakeClient(), Cache(":memory:")
    base = _run(flow, client, cache, FULL)
    records = Records.from_traces([base])
    replay = Recipe("A", llm_replay=True, tool_cache=True)
    mini = _run(flow, client, cache, replay, records)
    assert mini.final == base.final
    assert client.calls == 2 and flow.real_calls == 1  # nothing new was called
    assert mini.cost_usd == 0 and mini.latency_s == 0
    assert {e.source for e in mini.events} == {"record"}


def test_pure_simulation_never_touches_the_real_tool():
    flow, client = TinyFlow(), FakeClient()
    trace = _run(flow, client, Cache(":memory:"), Recipe("C1", tool_sim="pure"))
    assert flow.real_calls == 0
    assert trace.final == "FINAL ANSWER: SIMULATED OUTPUT"
    assert [e.source for e in trace.events if e.kind == "tool"] == ["sim"]


def test_simulated_outputs_are_shared_across_variants():
    flow, client, cache = TinyFlow(), FakeClient(), Cache(":memory:")
    recipe = Recipe("C1", tool_sim="pure")
    _run(flow, client, cache, recipe, variant="a")
    calls = client.calls
    second = _run(flow, client, cache, recipe, variant="b")
    assert [e.source for e in second.events if e.kind == "tool"] == ["pool"]
    assert client.calls == calls + 2  # two agent calls, no new simulator call


def test_fused_run_is_one_call_with_imagined_tools():
    flow, client = TinyFlow(), FakeClient()
    trace = _run(flow, client, Cache(":memory:"), Recipe("C2", fuse=frozenset({"agent"})))
    assert client.calls == 1 and flow.real_calls == 0
    assert trace.final == "FINAL ANSWER: 42"
    assert [e.source for e in trace.events] == ["imagined", "real"]
    assert trace.events[-1].output == "FINAL ANSWER: 42"  # the transcript stays in completion


def test_short_observations_are_cut():
    flow, client = TinyFlow(), FakeClient()
    trace = _run(flow, client, Cache(":memory:"), Recipe("C6", obs_chars=4))
    assert trace.events[1].output == "REAL …[cut]"


def test_budget_cap_stops_calls():
    ledger = Ledger(0.005)  # the first call spends 0.01, so the second is refused
    flow, client = TinyFlow(), FakeClient(ledger)
    with pytest.raises(BudgetExceeded):
        _run(flow, client, Cache(":memory:"), FULL)


def test_parse_fused_reads_steps_and_final():
    steps, final = parse_fused(
        'ACTION: search {"query": "a b"}\nOBSERVATION: 1. A\n2. B\n'
        'ACTION: read_page {"title": "A"}\nOBSERVATION: text\nFINAL REPLY: FINAL ANSWER: yes'
    )
    assert [s[0] for s in steps] == ["search", "read_page"]
    assert steps[0][1] == {"query": "a b"} and steps[0][2] == "1. A\n2. B"
    assert final == "FINAL ANSWER: yes"


def test_variant_config_merges_one_level():
    flow = TinyFlow()
    v = Variant("v", "edit", "agent", "", {"prompts": {"agent": "Be better."}})
    assert flow.config_for(v) == {"models": {"agent": "fake:model"},
                                  "prompts": {"agent": "Be better."}}  # fmt: skip


def test_mmrv_and_scotts_pi():
    real = {"a": 0.9, "b": 0.5, "c": 0.1}
    assert mmrv(real, {"a": 3, "b": 2, "c": 1}) == 0
    # b and c swapped: each of b, c has a worst violation of 0.4
    assert mmrv(real, {"a": 3, "b": 1, "c": 2}) == pytest.approx(0.8 / 3)
    assert scotts_pi(["x", "y", "x", "y"], ["x", "y", "x", "y"]) == 1
    assert math.isclose(scotts_pi(["x", "x"], ["y", "y"]), -1)


def test_compare_perfect_mini_agrees_everywhere():
    rows = []
    for recipe in ("full", "mini"):
        for v, p in {"base": 0.8, "good": 0.9, "bad": 0.2, "worse": 0.1}.items():
            for t in range(40):
                score = 1.0 if (t * 7919 % 100) / 100 < p else 0.0
                rows.append(Row(recipe, v, f"t{t}", 0, score, "correct" if score else "x",
                                1.0 if recipe == "full" else 0.1, 1.0))  # fmt: skip
    out = compare(rows, "mini", ["base", "good", "bad", "worse"], base="base",
                  mutants=["bad", "worse"])  # fmt: skip
    assert out["kendall"] == pytest.approx(1)
    assert out["decision_acc"] == 1 and out["mmrv"] == 0
    assert out["mutant_caught_by_mini"] == 1
    assert out["cost_ratio"] == pytest.approx(0.1)


def test_two_ledgers_on_one_file_add_up(tmp_path):
    a, b = Ledger(1.0, tmp_path / "l.json"), Ledger(1.0, tmp_path / "l.json")
    a.charge(0.3, "x")
    b.charge(0.4, "y")
    a.charge(0.2, "x")
    assert Ledger(1.0, tmp_path / "l.json").spent_usd == pytest.approx(0.9)
    b.charge(0.2, "y")
    with pytest.raises(BudgetExceeded):
        a.check()
