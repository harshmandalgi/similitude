"""C1: an LLM plays a tool (docs/02-IDEAS.md §3, "Simulated tools").

Three levels, from cheap to faithful:
  pure       - the LLM sees only the tool's description.
  grounded   - it also sees real recorded outputs of this tool, from *other* tasks (format/style).
  cache_sim  - exact recorded calls are replayed (by the Runtime); for new calls the LLM also sees
               the real outputs this tool gave earlier *in the same task* (content grounding).

The simulator never sees the user's question: a real tool does not know it either, and knowing it
would make the fake too helpful ("easy mode").
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass
from typing import Any

from similitude.core import Tool

SIM_SYSTEM = """\
You are simulating a software tool for a test harness. Given the tool's description and one call, \
write exactly what the real tool would return: same format, same length, same level of detail.
Be realistic, not helpful. Real tools return partial matches, irrelevant results, odd formatting, \
and sometimes nothing at all. Do not invent a cleaner world than the real one.
Write only the tool's raw output. No commentary, no code fences."""


@dataclass
class Recorded:
    task_id: str
    args: dict[str, Any]
    output: str


def failure_rate(tool: Tool, recorded: list[Recorded]) -> float:
    if not recorded:
        return 0.0
    return sum(tool.is_failure(r.output) for r in recorded) / len(recorded)


def injected_failure(tool: Tool, recorded: list[Recorded], task_id: str, args: Any) -> str | None:
    """Deterministic error injection: the same call always fails or always succeeds, at the real
    tool's measured failure rate. Returns a real recorded failure output, or None."""
    failures = [r.output for r in recorded if tool.is_failure(r.output)]
    rate = failure_rate(tool, recorded)
    if not failures or rate == 0:
        return None
    digest = hashlib.sha256(json.dumps([task_id, tool.name, args], sort_keys=True).encode())
    if int(digest.hexdigest()[:8], 16) / 0xFFFFFFFF >= rate:
        return None
    return failures[int(digest.hexdigest()[8:16], 16) % len(failures)]


def sim_prompt(
    tool: Tool,
    args: dict[str, Any],
    mode: str,
    task_id: str,
    recorded: list[Recorded],
    *,
    k_other: int = 3,
    k_same: int = 4,
    example_chars: int = 1200,
) -> list[dict[str, str]]:
    parts = [
        f"Tool: {tool.name}",
        f"Description: {tool.description}",
        f"Arguments schema: {json.dumps(tool.parameters)}",
    ]
    if mode in ("grounded", "cache_sim"):
        others = [r for r in recorded if r.task_id != task_id]
        rng = random.Random(f"{tool.name}:{task_id}")  # stable examples per task
        for i, r in enumerate(rng.sample(others, min(k_other, len(others))), start=1):
            parts.append(
                f"\nReal example {i} (another session):\nCall: {json.dumps(r.args)}\n"
                f"Output:\n{r.output[:example_chars]}"
            )
    if mode == "cache_sim":
        same = [r for r in recorded if r.task_id == task_id][:k_same]
        for i, r in enumerate(same, start=1):
            parts.append(
                f"\nEarlier real call in this same session {i}:\nCall: {json.dumps(r.args)}\n"
                f"Output:\n{r.output[:example_chars]}"
            )
    parts.append(f"\nNow simulate this call.\nCall: {json.dumps(args, ensure_ascii=False)}")
    return [
        {"role": "system", "content": SIM_SYSTEM},
        {"role": "user", "content": "\n".join(parts)},
    ]
