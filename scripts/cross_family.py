"""Does a different model family make the same decisions? (W1: OpenAI vs Gemini ground truth)

    uv run python scripts/cross_family.py     # -> results/w1-cross-family.md

Treats the OpenAI run (gpt-5.4-nano, workflow "wikiqa-openai") as if it were a miniature of the
Gemini run (gemini-3.5-flash-lite, "wikiqa"), on the variants both share: the base, the prompt
edits and the prompt mutants. Model-swap variants are left out (they name different models).
"""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

from similitude.report import rows_for
from similitude.validate import compare, mean_se, per_task
from similitude.workflows import wikiqa

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    runs = ROOT / "runs"
    gemini, _ = rows_for(runs, "wikiqa")
    openai, _ = rows_for(runs, "wikiqa-openai")
    gemini = [r for r in gemini if r.recipe == "full"]
    openai = [replace(r, recipe="openai-full") for r in openai if r.recipe == "full"]
    shared = [v.name for v in wikiqa.variants() if v.kind in ("base", "edit", "mutant")]
    shared = [
        v for v in shared if per_task(gemini, "full", v) and per_task(openai, "openai-full", v)
    ]
    rows = gemini + openai
    mutants = [v for v in shared if v.startswith("m-")]
    result = compare(rows, "openai-full", shared, base="base", mutants=mutants)

    lines = ["# W1: do OpenAI's decisions carry over to Gemini?\n",
             ("Same tasks, prompts and tools; only the model family differs. Read the OpenAI "
              "run as a miniature of the Gemini run. (Judges differ: Opus for OpenAI runs, "
              "Sonnet for Gemini runs.)\n"),
             "| variant | Gemini acc | OpenAI acc |", "|---|---|---|"]  # fmt: skip
    for v in shared:
        g = mean_se(list(per_task(rows, "full", v).values()))[0]
        o = mean_se(list(per_task(rows, "openai-full", v).values()))[0]
        lines.append(f"| {v} | {g:.2f} | {o:.2f} |")
    keys = ["kendall", "spearman", "decision_acc", "decision_acc_clear", "clear_pairs", "mmrv",
            "top1_match", "mutant_same_direction", "reason_js", "top_reason_match"]  # fmt: skip
    lines.append("\n| metric | value |\n|---|---|")
    lines += [f"| {k} | {result.get(k)} |" for k in keys]
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "w1-cross-family.md").write_text("\n".join(lines) + "\n")
    (out / "w1-cross-family.json").write_text(json.dumps(result, indent=1, default=str))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
