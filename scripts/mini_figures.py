"""Figures for the short paper (paper/figures/).

    uv run python scripts/mini_figures.py

1. decisions.pdf: for each miniature, the share of the full workflow's clear decisions it keeps,
   grouped by workflow, with the noise ceiling (the full workflow re-run) as a dashed line. Colour
   is the kind of shortcut. Numbers come from results/summary.json, the same as every table.
2. tracking.pdf: each variant's score on the miniature against its score on the full workflow.
   A miniature that keeps decisions puts the dots near the diagonal; one that loses them gives a
   flat row. Hollow dots are mutants (variants broken on purpose).
"""

from __future__ import annotations

import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import matplotlib
import matplotlib.transforms

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from summary import RUNS, W1_CORE, W2_CORE, tau_rows

from similitude.report import rows_for
from similitude.workflows import research

OUT = ROOT / "paper" / "figures"
SIM, REDUCE, MERGE = "#1baf7a", "#2a78d6", "#eb6834"
CEILING, INK, MUTED, GRID = "#8a8986", "#0b0b0b", "#52514e", "#e4e3df"
KIND = {"sim": (SIM, "Simulated tools"), "reduce": (REDUCE, "Replay or reduce"),
        "merge": (MERGE, "Merged calls or stubs")}  # fmt: skip

# (section in summary.json, panel title, [(recipe, label, kind)]); the ceiling row is the re-run.
GROUPS = [
    (
        "W1 wikiqa (10 core variants)",
        "W1: Wikipedia agent",
        "full-rerun",
        [
            ("C6-short-obs", "Short tool outputs", "reduce"),
            ("C1-cache-sim", "Simulated tools, grounded", "sim"),
            ("C1-pure", "Simulated tools, pure", "sim"),
            ("B4-quarter", "A quarter of the tasks", "reduce"),
            ("C2-fused", "Agent loop as one call", "merge"),
            ("C2+B4", "One call + a quarter", "merge"),
        ],
    ),
    (
        "W3 research, focus planner",
        "W3: research pipeline (planner)",
        "P-rerun",
        [
            ("P-C1-pure", "Simulated researcher tools", "sim"),
            ("P-C4+B1+C5", "Stubs + slice + early stop", "merge"),
            ("P-C2-all", "Whole pipeline as one call", "merge"),
            ("P-C4-stub", "Stubbed researchers", "merge"),
        ],
    ),
    (
        "W2 tau (8 core variants)",
        "W2: shop agent (private database)",
        None,
        [
            ("B3-cheap-user", "Cheaper simulated customer", "reduce"),
            ("C2-all", "Conversation as one call", "merge"),
            ("C1-pure", "Simulated shop tools", "sim"),
        ],
    ),
]


def style() -> None:
    plt.rcParams.update({"font.family": "serif", "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
                         "font.size": 7.5, "mathtext.fontset": "stix", "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
                         "axes.spines.top": False, "axes.spines.right": False})  # fmt: skip


def decisions() -> None:
    data = json.loads((ROOT / "results" / "summary.json").read_text())
    rows = []  # (label, kept, n, cost, kind) or ("group", title, ceiling)
    for section, title, ceiling, minis in GROUPS:
        by = {r["recipe"]: r for r in data[section]}
        rows.append(("group", title, by[ceiling]["decision_acc_clear"] if ceiling else None))
        for recipe, label, kind in minis:
            r = by[recipe]
            rows.append((label, r["decision_acc_clear"], r["clear_pairs"], r["cost_ratio"], kind))
    fig, ax = plt.subplots(figsize=(3.15, 3.6))
    fig.subplots_adjust(left=0.455, right=0.995, top=0.985, bottom=0.135)
    to_left = matplotlib.transforms.blended_transform_factory(fig.transFigure, ax.transData)
    y, ticks, labels, spans = 0.0, [], [], []
    for row in rows:
        if row[0] == "group":
            y -= 0.35
            ax.text(0.015, y - 0.05, row[1], transform=to_left, ha="left", va="center",
                    fontsize=7, fontweight="bold", color=INK)  # fmt: skip
            spans.append([y, y, row[2]])
            y -= 0.75
            continue
        label, kept, n, cost, kind = row
        ax.barh(y, kept, height=0.62, color=KIND[kind][0], edgecolor="none")
        ax.text(kept + 0.025, y, f"{round(kept * n)}/{n} · {cost:.2f}×", va="center",
                fontsize=6, color=MUTED, zorder=4,
                bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.4})  # fmt: skip
        ticks.append(y)
        labels.append(label)
        spans[-1][1] = y
        y -= 0.9
    for top, bottom, ceiling in spans:
        if ceiling is not None:
            ax.plot([ceiling, ceiling], [top - 0.3, bottom - 0.45], ls=(0, (3, 2)), lw=0.9,
                    color=CEILING)  # fmt: skip
            ax.text(ceiling, top - 0.05, "full re-run", ha="center", va="center", fontsize=5.6,
                    color=CEILING)  # fmt: skip
    ax.set_yticks(ticks, labels, fontsize=6.4)
    ax.tick_params(axis="y", length=0, pad=3)
    ax.set_xlim(0, 1.6)
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0%", "25%", "50%", "75%", "100%"], fontsize=6.3)
    ax.spines["bottom"].set_bounds(0, 1)
    ax.set_xlabel("clear decisions kept", fontsize=6.8, x=0.35)
    ax.set_ylim(y + 0.4, 0.1)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color=GRID, lw=0.5)
    ax.set_axisbelow(True)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c, _ in KIND.values()]
    fig.legend(handles, [n for _, n in KIND.values()], loc="lower center", ncol=3, frameon=False,
               fontsize=6.1, handlelength=1.0, columnspacing=0.9, borderaxespad=0.2)  # fmt: skip
    fig.savefig(OUT / "decisions.pdf")
    fig.savefig(OUT / "decisions.png", dpi=200)
    plt.close(fig)


def means(rows, recipe: str, variants: list[str]) -> dict[str, float]:
    scores = defaultdict(list)
    for r in rows:
        if r.recipe == recipe and r.variant in variants:
            scores[r.variant].append(r.score)
    return {v: statistics.mean(s) for v, s in scores.items()}


def tracking() -> None:
    w1, _ = rows_for(RUNS, "wikiqa")
    w3, _ = rows_for(RUNS, "research")
    w2 = tau_rows()
    planner = research.groups(research.variants())["planner"]
    panels = [
        ("(a) W1: simulated tools,\ngrounded", w1, W1_CORE, "C1-cache-sim", SIM),
        ("(b) W3 planner: simulated\nresearcher tools", w3, planner, "P-C1-pure", SIM),
        ("(c) W1: agent loop\nas one call", w1, W1_CORE, "C2-fused", MERGE),
        ("(d) W2: simulated shop\ntools (private database)", w2, W2_CORE, "C1-pure", SIM),
    ]
    fig, axes = plt.subplots(1, 4, figsize=(6.3, 1.95))
    for ax, (title, rows, variants, recipe, colour) in zip(axes, panels, strict=True):
        full, mini = means(rows, "full", variants), means(rows, recipe, variants)
        xs = [full[v] for v in variants]
        ys = [mini[v] for v in variants]
        broken = ["-m-" in f"-{v}" or v.startswith("m-") for v in variants]
        ax.plot([0, 1], [0, 1], ls=(0, (3, 2)), lw=0.7, color=CEILING, zorder=1)
        for x, yv, b in zip(xs, ys, broken, strict=True):
            ax.scatter(x, yv, s=16, zorder=2, linewidths=0.9, edgecolors=colour,
                       facecolors="white" if b else colour)  # fmt: skip
        r = _pearson(xs, ys)
        note = f"r = {r:.2f}" if r is not None else "all variants\nscore the same"
        ax.text(0.04, 0.96, note, transform=ax.transAxes, va="top", fontsize=6.3, color=MUTED)
        ax.set_title(title, fontsize=7, color=INK, pad=4)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.set_xticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.set_yticks([0, 0.5, 1], ["0", "0.5", "1"])
        ax.grid(color=GRID, lw=0.4)
        ax.set_axisbelow(True)
        ax.set_xlabel("full workflow score", fontsize=6.5)
    axes[0].set_ylabel("miniature score", fontsize=6.5)
    fig.tight_layout(w_pad=1.2)
    fig.savefig(OUT / "tracking.pdf")
    fig.savefig(OUT / "tracking.png", dpi=200)
    plt.close(fig)


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    if statistics.pstdev(ys) < 1e-9 or statistics.pstdev(xs) < 1e-9:
        return None
    r = statistics.correlation(xs, ys)
    return None if math.isnan(r) else r


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    style()
    decisions()
    tracking()
    print(f"wrote decisions.pdf and tracking.pdf to {OUT}")


if __name__ == "__main__":
    main()
