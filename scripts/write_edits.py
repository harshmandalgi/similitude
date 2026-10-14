"""Have a fresh Claude Code instance write W1's "edit" variants: prompt changes a developer
would plausibly try to improve the agent. Writes data/wikiqa/edits.json.

    uv run python scripts/write_edits.py
"""

from __future__ import annotations

import json
from pathlib import Path

from similitude.claude_code import OPUS, ask_claude
from similitude.workflows import wikiqa

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


if __name__ == "__main__":
    main()
