"""C2: run a whole agent loop as one LLM call, with imagined tool results (docs/02-IDEAS.md §3).

The model writes its full run as a transcript (ACTION / OBSERVATION pairs) and then its final
reply. It is told to imagine honest, imperfect tool outputs; the known risk is that it imagines
outputs that suit its own plan.
"""

from __future__ import annotations

import json
import re
from typing import Any

from similitude.core import Tool

FUSION_SUFFIX = """

--- TEST MODE ---
In this run the tools are switched off. Do the task in ONE reply by writing out your whole \
working session as a transcript, step by step, as if the tools were real:

ACTION: <tool_name> <JSON arguments>
OBSERVATION: <what the real tool would most likely return; be honest: real tools often return \
partial, irrelevant or empty results, and you may need several tries>

Use at most {max_steps} ACTION steps. Tools available:
{tools}

When you are done, write a line "FINAL REPLY:" followed by your final reply, exactly as you \
would normally give it to the user (same format rules as above)."""

# Lines may be indented and may carry a speaker prefix ("AGENT: ACTION: ..."), as in fused
# conversations. A marker is never a speaker: "OBSERVATION: FINAL ANSWER: x" is part of an imagined
# observation, not the agent's answer.
_MARK = r"(?:ACTION|OBSERVATION|FINAL REPLY|FINAL ANSWER)[ \t]*:"
_WHO = rf"[ \t]*(?:(?![ \t]*{_MARK})[A-Za-z_ ]{{1,30}}:\s*)?"
_ACTION = re.compile(rf"^{_WHO}ACTION:\s*(\w+)\s*(.*)$", re.MULTILINE)
_END = rf"^{_WHO}(?:ACTION:|FINAL REPLY:|FINAL ANSWER:)"
_OBS = re.compile(rf"^{_WHO}OBSERVATION:\s*(.*?)(?={_END}|\Z)", re.MULTILINE | re.DOTALL)
_REPLY = re.compile(rf"^{_WHO}FINAL REPLY:[ \t]*", re.MULTILINE)
# The workflows' own answer line. Models often end with it and leave out "FINAL REPLY:".
_ANSWER = re.compile(rf"^{_WHO}(?=FINAL ANSWER:)", re.MULTILINE | re.IGNORECASE)


def fused_system(system: str, tools: list[Tool], max_steps: int) -> str:
    listed = "\n".join(
        f"- {t.name} {json.dumps(t.parameters.get('properties', {}))}: {t.description}"
        for t in tools
    )
    return system + FUSION_SUFFIX.format(max_steps=max_steps, tools=listed)


def parse_fused(text: str) -> tuple[list[tuple[str, Any, str]], str]:
    """Returns ([(tool, args, imagined output)], final reply)."""
    # The final reply follows the last tool step; a marker before that step is part of the
    # transcript. A "FINAL REPLY:" beats an answer line, and the last one wins. The answer line is
    # kept, so the workflow's own parser can read it. With no marker after the last step, the last
    # marker anywhere is used.
    last_step = max((m.start() for m in _ACTION.finditer(text)), default=-1)
    replies, answers = list(_REPLY.finditer(text)), list(_ANSWER.finditer(text))
    late = [[m for m in ms if m.start() > last_step] for ms in (replies, answers)]
    pick = late[0] or late[1] or replies or answers
    final = text[pick[-1].end() :].strip() if pick else ""
    actions = _ACTION.findall(text)
    observations = [o.strip() for o in _OBS.findall(text)]
    steps = []
    for i, (name, raw_args) in enumerate(actions):
        try:
            args = json.loads(raw_args) if raw_args.strip() else {}
        except json.JSONDecodeError:
            args = {"_raw": raw_args.strip()}
        steps.append((name, args, observations[i] if i < len(observations) else ""))
    return steps, final
