"""Have a fresh Claude Code instance write "edit" variants: prompt changes a developer would
plausibly try to improve a workflow. Writes data/<workflow>/edits.json.

    uv run python scripts/write_edits.py            # W1: 6 edits of the agent prompt
    uv run python scripts/write_edits.py research   # W3: 3 edits each of the writer and planner
    uv run python scripts/write_edits.py tau        # W2: 4 preambles for the shop agent
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from similitude.claude_code import OPUS, ask_claude
from similitude.workflows import research, tau, wikiqa

ROOT = Path(__file__).resolve().parents[1]

SYSTEM = """\
You are an engineer improving an LLM agent. You will see the agent's system prompt, its tools, \
and example questions. Write 6 different revised system prompts that an engineer could \
plausibly try to make the agent answer more questions correctly.

Rules:
- Each revision changes ONE idea, so its effect can be measured. Make the six ideas clearly \
different (for example: question decomposition, query rewriting, verification, page reading \
strategy, entity disambiguation, answer normalisation).
- Keep the tool names and the "FINAL ANSWER: <answer>" output rule exactly as they are.
- Keep each prompt under 180 words.
- Some ideas may help and some may hurt; write each as a sincere attempt.

Reply with only JSON: {"edits": [{"name": "e-<short-kebab-name>", "description": "<one \
sentence>", "prompt": "<the full revised system prompt>"}]}"""


def main() -> None:
    tools = wikiqa.WikiQA().tools()
    dev = wikiqa.load_tasks("dev")[:5]
    user = "\n".join(
        [
            "Current system prompt:",
            wikiqa.BASE_PROMPT,
            "",
            "Tools:",
            *[f"- {t.name}: {t.description}" for t in tools.values()],
            "",
            "Example questions (multi-hop, from HotpotQA):",
            *[f"- {t['question']}" for t in dev],
        ]
    )
    answer = ask_claude(
        SYSTEM, user, model=OPUS, effort="high", keep_dir=ROOT / "runs" / "claude" / "edits",
        name="wikiqa-edits",
    )  # fmt: skip
    edits = answer["edits"]
    assert len(edits) == 6 and all("FINAL ANSWER" in e["prompt"] for e in edits)
    wikiqa.EDITS_FILE.write_text(
        json.dumps({"written_by": f"{OPUS} via Claude Code (high effort)", "edits": edits},
                   indent=1, ensure_ascii=False) + "\n"
    )  # fmt: skip
    for e in edits:
        print(f"{e['name']}: {e['description']}")


RESEARCH_SYSTEM = """\
You are an engineer improving a multi-agent research pipeline: a planner splits a hard question \
into sub-questions, researchers look each one up on Wikipedia, and a writer combines their notes \
into the final answer (then a reviewer may ask for one revision). You will see the current system \
prompts of the PLANNER and the WRITER, and example questions.

Write 3 revised PLANNER prompts and 3 revised WRITER prompts that an engineer could plausibly try \
to get more questions right.

Rules:
- Each revision changes ONE idea, so its effect can be measured. Make the ideas clearly different.
- Keep each role's output format exactly: the planner replies with only JSON \
{"subquestions": [...]}; the writer ends with "FINAL ANSWER: ..." and may never answer \
"cannot be determined".
- Keep each prompt under 150 words.
- Some ideas may help and some may hurt; write each as a sincere attempt.

Reply with only JSON: {"planner": [{"name": "p-e-<short-kebab-name>", "description": "<one \
sentence>", "prompt": "..."}], "writer": [{"name": "w-e-<short-kebab-name>", ...}]}"""


def research_edits() -> None:
    dev = research.load_tasks("dev")[:5]
    user = "\n".join(
        ["Current PLANNER prompt:", research.PLANNER, "", "Current WRITER prompt:", research.WRITER,
         "", "Example questions (from the FRAMES benchmark):", *[f"- {t['question']}" for t in dev]]
    )  # fmt: skip
    answer = ask_claude(
        RESEARCH_SYSTEM, user, model=OPUS, effort="high",
        keep_dir=ROOT / "runs" / "claude" / "edits", name="research-edits",
    )  # fmt: skip
    planner, writer = answer["planner"], answer["writer"]
    assert len(planner) == 3 and len(writer) == 3
    assert all("subquestions" in e["prompt"] for e in planner)
    assert all("FINAL ANSWER" in e["prompt"] for e in writer)
    research.EDITS_FILE.write_text(
        json.dumps({"written_by": f"{OPUS} via Claude Code (high effort)",
                    "edits": {"planner": planner, "writer": writer}}, indent=1,
                   ensure_ascii=False) + "\n"
    )  # fmt: skip
    for e in planner + writer:
        print(f"{e['name']}: {e['description']}")


TAU_SYSTEM = """\
You are an engineer improving a customer-service agent for an online shop. Its system prompt is \
the shop's policy (shown below). You may add a short PREAMBLE in front of the policy; the policy \
itself stays unchanged. Write 4 different preambles that an engineer could plausibly try so the \
agent completes more customer requests correctly (right changes to orders, policy followed).

Rules:
- Each preamble changes ONE idea, so its effect can be measured. Make the ideas clearly different \
(for example: a step-by-step procedure, double-checking item ids before any change, summarising \
the request before acting, how to handle several requests in one chat).
- Each preamble is under 120 words and does not contradict the policy.
- Some ideas may help and some may hurt; write each as a sincere attempt.

Reply with only JSON: {"edits": [{"name": "e-<short-kebab-name>", "description": "<one \
sentence>", "prompt": "<the preamble>"}]}"""


def tau_edits() -> None:
    dev = tau.load_tasks("dev")[:4]
    user = "\n".join(
        ["The shop's policy (the agent's current system prompt):", tau.POLICY, "",
         "Example customer goals (hidden from the agent):",
         *[f"- {t['instruction']}" for t in dev]]
    )  # fmt: skip
    answer = ask_claude(
        TAU_SYSTEM, user, model=OPUS, effort="high",
        keep_dir=ROOT / "runs" / "claude" / "edits", name="tau-edits",
    )  # fmt: skip
    edits = answer["edits"]
    assert len(edits) == 4
    tau.EDITS_FILE.parent.mkdir(parents=True, exist_ok=True)
    tau.EDITS_FILE.write_text(
        json.dumps({"written_by": f"{OPUS} via Claude Code (high effort)", "edits": edits},
                   indent=1, ensure_ascii=False) + "\n"
    )  # fmt: skip
    for e in edits:
        print(f"{e['name']}: {e['description']}")


if __name__ == "__main__":
    {"research": research_edits, "tau": tau_edits}.get(sys.argv[1] if sys.argv[1:] else "", main)()
