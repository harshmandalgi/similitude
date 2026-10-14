"""Is a mini valid? Compare its decisions with the full workflow's (docs/02-IDEAS.md §5).

All metrics compare per-variant results of one mini recipe against the full recipe. The full
recipe is scored on all tasks; a mini may use a subset (operator B4), because the question is
whether the mini's cheaper evidence leads to the same decision as the full evidence.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import numpy as np
from scipy import stats
from scipy.spatial.distance import jensenshannon


@dataclass
class Row:
    recipe: str
    variant: str
    task_id: str
    rep: int
    score: float  # 1 correct, 0 not
    category: str
    cost: float
    latency: float


def per_task(rows: list[Row], recipe: str, variant: str) -> dict[str, float]:
    by_task: dict[str, list[float]] = {}
    for r in rows:
        if r.recipe == recipe and r.variant == variant:
            by_task.setdefault(r.task_id, []).append(r.score)
    return {t: float(np.mean(s)) for t, s in by_task.items()}


def mean_se(values: list[float]) -> tuple[float, float]:
    if not values:
        return math.nan, math.nan
    if len(values) < 2:
        return float(values[0]), math.nan
    return float(np.mean(values)), float(np.std(values, ddof=1) / math.sqrt(len(values)))


def paired(rows: list[Row], recipe: str, a: str, b: str) -> tuple[float, float, int]:
    """Mean of (a - b) over tasks both variants ran, with its standard error."""
    sa, sb = per_task(rows, recipe, a), per_task(rows, recipe, b)
    common = sorted(set(sa) & set(sb))
    diff, se = mean_se([sa[t] - sb[t] for t in common])
    return diff, se, len(common)


def mmrv(real: dict[str, float], mini: dict[str, float]) -> float:
    """Mean maximum rank violation (SIMPLER, Li et al. 2024): for each variant, the largest real
    gap among the variants the mini orders the wrong way round; averaged. 0 is perfect."""
    names = list(real)
    total = 0.0
    for i in names:
        worst = 0.0
        for j in names:
            if (mini[i] < mini[j]) != (real[i] < real[j]):
                worst = max(worst, abs(real[i] - real[j]))
        total += worst
    return total / len(names)


def scotts_pi(a: list[str], b: list[str]) -> float:
    """Agreement of two labellers on the same items, corrected for chance."""
    if not a:
        return math.nan
    observed = sum(x == y for x, y in zip(a, b)) / len(a)
    pooled = Counter(a) + Counter(b)
    expected = sum((n / (2 * len(a))) ** 2 for n in pooled.values())
    return (observed - expected) / (1 - expected) if expected < 1 else math.nan


def compare(
    rows: list[Row],
    mini: str,
    variants: list[str],
    *,
    full: str = "full",
    base: str | None = None,
    mutants: list[str] | None = None,
    z: float = 2.0,
) -> dict[str, Any]:
    present = [v for v in variants if per_task(rows, full, v) and per_task(rows, mini, v)]
    real = {v: mean_se(list(per_task(rows, full, v).values()))[0] for v in present}
    cheap = {v: mean_se(list(per_task(rows, mini, v).values()))[0] for v in present}
    out: dict[str, Any] = {"recipe": mini, "variants": len(present)}
    if len(present) < 3:
        return out

    x, y = [real[v] for v in present], [cheap[v] for v in present]
    out["pearson"] = float(stats.pearsonr(x, y).statistic) if np.std(y) > 0 else math.nan
    out["spearman"] = float(stats.spearmanr(x, y).statistic)
    out["kendall"] = float(stats.kendalltau(x, y).statistic)
    out["mmrv"] = mmrv(real, cheap)
    out["mae"] = float(np.mean(np.abs(np.array(x) - np.array(y))))
    pick = max(present, key=lambda v: cheap[v])
    out["top1_match"] = pick == max(present, key=lambda v: real[v])
    out["regret"] = max(x) - real[pick]

    # Pairwise decisions: does the mini pick the same winner of each pair?
    agree_all, agree_clear, n_clear = [], [], 0
    for a, b in combinations(present, 2):
        d_full, se_full, _ = paired(rows, full, a, b)
        d_mini, _, _ = paired(rows, mini, a, b)
        if d_full == 0:
            continue
        same = (d_mini > 0) == (d_full > 0) and d_mini != 0
        agree_all.append(same)
        if not math.isnan(se_full) and abs(d_full) > z * se_full:
            n_clear += 1
            agree_clear.append(same)
    out["pairs"] = len(agree_all)
    out["decision_acc"] = float(np.mean(agree_all)) if agree_all else math.nan
    out["clear_pairs"] = n_clear
    out["decision_acc_clear"] = float(np.mean(agree_clear)) if agree_clear else math.nan

    # Mutants: of the broken variants the full eval catches, how many does the mini catch?
    if base and mutants:
        caught_full, same_dir, caught_mini = 0, 0, 0
        for m in [m for m in mutants if m in present]:
            d_full, se_full, _ = paired(rows, full, base, m)
            if math.isnan(se_full) or d_full <= z * se_full:
                continue
            caught_full += 1
            d_mini, se_mini, _ = paired(rows, mini, base, m)
            same_dir += d_mini > 0
            caught_mini += (not math.isnan(se_mini)) and d_mini > z * se_mini
        out["mutants_caught_by_full"] = caught_full
        out["mutant_same_direction"] = same_dir / caught_full if caught_full else math.nan
        out["mutant_caught_by_mini"] = caught_mini / caught_full if caught_full else math.nan

    out.update(reasoning_agreement(rows, mini, present, full=full))

    def spend(recipe: str, field: str) -> float:
        return sum(getattr(r, field) for r in rows if r.recipe == recipe and r.variant in present)

    out["cost_ratio"] = (
        spend(mini, "cost") / spend(full, "cost") if spend(full, "cost") else math.nan
    )
    out["latency_ratio"] = (
        spend(mini, "latency") / spend(full, "latency") if spend(full, "latency") else math.nan
    )

    def median_of(recipe: str, field: str) -> float:
        values = [getattr(r, field) for r in rows if r.recipe == recipe and r.variant in present]
        return float(np.median(values)) if values else math.nan

    # Medians per run resist the odd stalled call, which can dominate a total.
    full_lat = median_of(full, "latency")
    out["latency_ratio_median"] = median_of(mini, "latency") / full_lat if full_lat else math.nan
    out["cost_per_run"] = median_of(mini, "cost")
    return out


def reasoning_agreement(
    rows: list[Row], mini: str, variants: list[str], *, full: str = "full"
) -> dict[str, float]:
    """Does the judge give the same *reasons* for failure on the mini as on the full runs?

    - js: Jensen-Shannon distance between the failure-category mixes of each variant (0 = same).
    - top_reason_match: share of variants whose most common failure reason is the same.
    - pi: Scott's pi over (variant, task) pairs that failed in both, replicate 0.
    """
    distances, matches, a_labels, b_labels = [], [], [], []
    for v in variants:
        f = [r for r in rows if r.recipe == full and r.variant == v and r.score < 1]
        m = [r for r in rows if r.recipe == mini and r.variant == v and r.score < 1]
        if len(f) >= 3 and len(m) >= 3:
            cats = sorted({r.category for r in f + m})
            cf, cm = Counter(r.category for r in f), Counter(r.category for r in m)
            p = np.array([cf[c] for c in cats], float)
            q = np.array([cm[c] for c in cats], float)
            distances.append(float(jensenshannon(p / p.sum(), q / q.sum(), base=2)))
            matches.append(cf.most_common(1)[0][0] == cm.most_common(1)[0][0])
        full_fail = {r.task_id: r.category for r in f if r.rep == 0}
        for r in m:
            if r.rep == 0 and r.task_id in full_fail:
                a_labels.append(full_fail[r.task_id])
                b_labels.append(r.category)
    return {
        "reason_js": float(np.mean(distances)) if distances else math.nan,
        "top_reason_match": float(np.mean(matches)) if matches else math.nan,
        "reason_pi": scotts_pi(a_labels, b_labels),
        "reason_pairs": len(a_labels),
    }
