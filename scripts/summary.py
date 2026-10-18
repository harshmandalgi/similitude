"""The paper's main table: every miniature against the full workflow, on a fixed variant set per
workflow and focus, next to the noise ceiling (the full workflow re-run).

    uv run python scripts/summary.py   # -> results/summary.md and results/summary.json

Variant sets: W1 uses its ten core variants (the set every W1 miniature ran on); W2 its eight
core variants (its full set for the one-call miniature); W3 each focus group's full set. For
W2, pass/fail is tau-bench's own check, recomputed from the traces.
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

from similitude.experiment import load_traces
from similitude.report import rows_for
from similitude.validate import Row, compare
from similitude.workflows import research, tau

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "runs"

W1_CORE = ["base", "e-question-decomposition", "e-answer-normalisation", "e-page-reading-strategy", "m-3-steps", "m-2-steps", "m-no-tools", "m-one-page", "model-gemini-3.8-flash", "model-gemini-3.1-flash-lite"]  # fmt: skip
W2_CORE = ["base", "e-step-procedure", "e-verify-item-ids", "m-no-auth", "m-no-confirm", "m-8-steps", "model-gemini-3.8-flash", "model-gemini-3.1-flash-lite"]  # fmt: skip

KEYS = [
    ("cost_ratio", "cost ×"), ("latency_ratio_median", "latency ×"), ("kendall", "Kendall τ"),
    ("decision_acc_clear", "clear pairs kept"), ("clear_pairs", "clear pairs"),
    ("mmrv", "MMRV"), ("mutant_same_direction", "mutants: same way"),
    ("mutant_caught_by_mini", "mutants: caught"), ("top_reason_match", "top reason same"),
    ("reason_pi", "reason π"),
]  # fmt: skip


def tau_rows() -> list[Row]:
    """W2 rows with pass/fail from tau-bench's check and reasons from the judge's verdicts."""
    tasks = {t["id"]: t for t in tau.load_tasks()}
    judged, _ = rows_for(RUNS, "tau")
    reasons = {(r.recipe, r.variant, r.task_id, r.rep): r.category for r in judged}
    rows = []
    for t in load_traces(RUNS, "tau", ""):
        if t.task_id not in tasks or t.error or t.recipe.startswith("dev-"):
            continue
        ok, _ = tau.check(t, tasks[t.task_id])
        category = (
            "correct" if ok else reasons.get((t.recipe, t.variant, t.task_id, t.replicate), "?")
        )
        rows.append(Row(t.recipe, t.variant, t.task_id, t.replicate, float(ok), category,
                        t.cost_usd, t.latency_s))  # fmt: skip
    return rows


def block(rows: list[Row], variants: list[str], recipes: list[str], base: str = "base",
          full: str = "full") -> list[dict]:  # fmt: skip
    mutants = [v for v in variants if "-m-" in f"-{v}" or v.startswith("m-")]
    present = {r.recipe for r in rows}
    return [
        compare(rows, r, variants, full=full, base=base, mutants=mutants)
        for r in recipes if r in present
    ]  # fmt: skip


def fmt(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    return f"{x:.2f}" if isinstance(x, float) else str(x)


def main() -> None:
    w1, _ = rows_for(RUNS, "wikiqa")
    w3, _ = rows_for(RUNS, "research")
    w2 = tau_rows()
    groups = research.groups(research.variants())
    sections = {
        "W1 wikiqa (10 core variants)": block(
            w1, W1_CORE,
            ["full-rerun", "C1-cache-sim", "C1-pure", "C6-short-obs", "B4-quarter", "C2-fused",
             "C2+B4"]),
        "W2 tau (8 core variants)": block(
            w2, W2_CORE, ["full-rerun", "B3-cheap-user", "C1-pure", "C3-shrink-policy", "C2-all"]),
        "W3 research, focus writer": block(
            w3, groups["writer"],
            ["W-rerun", "W-A-replay", "W-A+B1+C5", "W-C4-stub", "W-B3-cheap"]),
        "W3 research, focus planner": block(
            w3, groups["planner"],
            ["P-rerun", "P-B3-cheap", "P-C1-pure", "P-C4-stub", "P-C4+B1+C5", "P-C2-all"]),
        # The replay miniature against a second replay run: the miniature's own noise.
        "W3 writer: replay vs replay (self-agreement)": block(
            [replace(r, recipe="replay-1") if r.recipe == "W-A-replay" else r for r in w3],
            groups["writer"], ["W-A-replay-2"], full="replay-1"),
    }  # fmt: skip
    lines = ["# Main results: each miniature vs the full workflow\n",
             ("Ceiling rows (full-rerun, W-rerun, P-rerun) are the full workflow run again: a "
              "reference point, not a hard limit. A miniature that agrees as often is as reliable "
              "as a second full evaluation.\n")]  # fmt: skip
    for title, results in sections.items():
        lines.append(f"\n## {title}\n")
        lines.append("| recipe | " + " | ".join(k[1] for k in KEYS) + " |")
        lines.append("|---|" + "---|" * len(KEYS))
        for r in results:
            lines.append(f"| {r['recipe']} | " + " | ".join(fmt(r.get(k[0])) for k in KEYS) + " |")
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "summary.md").write_text("\n".join(lines) + "\n")
    (out / "summary.json").write_text(json.dumps(sections, indent=1, default=str))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
