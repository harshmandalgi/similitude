"""Turn traces + verdicts into the validity tables (JSON and Markdown)."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from similitude.core import Variant
from similitude.experiment import load_traces
from similitude.judge import Verdicts
from similitude.reduce import Recipe
from similitude.validate import Row, compare, mean_se, per_task


def rows_for(runs: Path, workflow: str) -> tuple[list[Row], dict[str, int]]:
    verdicts = Verdicts(runs / "verdicts" / f"{workflow}.jsonl").items
    rows, missing = [], {"errors": 0, "unjudged": 0}
    for t in load_traces(runs, workflow, ""):
        if t.error:
            missing["errors"] += 1
            continue
        v = verdicts.get(t.run_id)
        if v is None:
            missing["unjudged"] += 1
            continue
        rows.append(
            Row(t.recipe, t.variant, t.task_id, t.replicate, float(v.correct), v.category,
                t.cost_usd, t.latency_s)
        )  # fmt: skip
    return rows, missing


def _f(x: Any, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return f"{x:.{digits}f}"
    return str(x)


def analyse(
    runs: Path,
    workflow: str,
    variants: list[Variant],
    *,
    base: str,
    mutants: list[str],
    recipes: list[Recipe],
    only_recipes: set[str] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    rows, missing = rows_for(runs, workflow)
    names = [v.name for v in variants]
    rows = [r for r in rows if r.variant in names]
    if only_recipes is not None:
        rows = [r for r in rows if r.recipe in only_recipes]
    present = sorted({r.recipe for r in rows}, key=lambda r: (r != "full", r))

    scores = {}
    for recipe in present:
        for v in names:
            values = list(per_task(rows, recipe, v).values())
            if values:
                scores.setdefault(v, {})[recipe] = mean_se(values) + (len(values),)

    validity = [compare(rows, r, names, base=base, mutants=mutants) for r in present if r != "full"]

    lines = [f"# {title or workflow}: validity of each mini\n"]
    lines.append(
        f"Runs used: {len(rows)}; skipped: {missing['errors']} with errors, "
        f"{missing['unjudged']} not yet judged.\n"
    )
    lines.append("## Accuracy per variant (share of tasks correct)\n")
    lines.append("| variant | kind | " + " | ".join(present) + " |")
    lines.append("|---|---|" + "---|" * len(present))
    kinds = {v.name: v.kind for v in variants}
    for v in names:
        if v not in scores:
            continue
        cells = []
        for r in present:
            if r in scores[v]:
                m, se, n = scores[v][r]
                cells.append(f"{m:.2f}±{_f(se)} (n={n})")
            else:
                cells.append("–")
        lines.append(f"| {v} | {kinds[v]} | " + " | ".join(cells) + " |")

    lines.append("\n## Does each mini make the same decisions as the full workflow?\n")
    cols = [
        ("cost_ratio", "cost ×"), ("latency_ratio", "latency ×"), ("kendall", "Kendall τ"),
        ("spearman", "Spearman ρ"), ("decision_acc", "pair acc"),
        ("decision_acc_clear", "pair acc (clear)"), ("clear_pairs", "clear pairs"),
        ("mmrv", "MMRV"), ("top1_match", "same best"), ("mae", "MAE"),
        ("mutant_same_direction", "mutants: same dir"),
        ("mutant_caught_by_mini", "mutants: caught"), ("reason_js", "reason JS"),
        ("top_reason_match", "top reason same"), ("reason_pi", "reason π"),
    ]  # fmt: skip
    lines.append("| recipe | " + " | ".join(c[1] for c in cols) + " |")
    lines.append("|---|" + "---|" * len(cols))
    for v in validity:
        lines.append(f"| {v['recipe']} | " + " | ".join(_f(v.get(c[0])) for c in cols) + " |")

    described = {r.name: r.description for r in recipes}
    lines.append("\n## Recipes\n")
    for r in present:
        if r != "full":
            lines.append(f"- **{r}**: {described.get(r, '')}")
    return {
        "scores": scores,
        "validity": validity,
        "missing": missing,
        "markdown": "\n".join(lines) + "\n",
    }
