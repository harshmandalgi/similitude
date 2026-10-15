"""Paper figure: what each miniature costs vs how many clear decisions it keeps.

    uv run python scripts/figures.py   # reads results/summary.json -> paper/figures/

Small multiples, one panel per workflow, same axes: x is the miniature's cost per run as a share of
the full workflow's (log scale), y is the share of clear pairwise decisions it keeps. Colour is the
operator's risk group (docs/02-IDEAS.md); grey hollow markers are the noise ceiling (the full
workflow re-run). In W3, triangles are the planner group and diamonds the writer group. Palette:
dataviz reference categorical slots 1-3, validated all-pairs for light mode; every point carries a
text label, placed so labels do not overlap.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import matplotlib
import matplotlib.transforms

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
GROUP_COLOURS = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
GROUP_NAMES = {"A": "A: replay (lossless)", "B": "B: low risk", "C": "C: simulate / merge"}
CEILING = "#8a8986"
INK, MUTED = "#0b0b0b", "#52514e"
WORKFLOWS = {"wikiqa": ("W1", "o"), "tau": ("W2", "s"), "research": ("W3", "^")}
SHORT = {
    "full-rerun": "re-run", "W-rerun": "re-run (writer)", "P-rerun": "re-run (planner)",
    "C1-cache-sim": "sim tools, cache",
    "C1-pure": "sim tools, pure", "P-C1-pure": "sim tools (planner)", "C6-short-obs": "short outputs",
    "B4-quarter": "1/4 tasks", "C2-fused": "one call", "C2+B4": "one call + 1/4",
    "B3-cheap-user": "cheaper customer", "C2-all": "one call", "W-A-replay": "replay (writer)",
    "W-A+B1+C5": "replay + stop (writer)", "W-C4-stub": "stub (writer)",
    "P-C4-stub": "stub (planner)", "P-C4+B1+C5": "stub + stop (planner)",
    "P-C2-all": "one call (planner)",
}  # fmt: skip


def risk_group(recipe: str) -> str | None:
    """A recipe's riskiest operator group: 'W-A+B1+C5' -> 'C'. None for the re-run."""
    name = re.sub(r"^[WP]-", "", recipe)
    if "rerun" in name:
        return None
    groups = re.findall(r"(?:^|\+)([ABC])\d?", name)
    return max(groups) if groups else None


def points() -> list[dict]:
    """One point per (workflow section, miniature) from results/summary.json, the same numbers
    as the paper's main table."""
    data = json.loads((ROOT / "results" / "summary.json").read_text())
    out = []
    for section, results in data.items():
        if "self-agreement" in section:
            continue
        label, marker = next(v for k, v in WORKFLOWS.items() if k in section)
        if "writer" in section:
            marker = "D"
        for v in results:
            if not isinstance(v.get("cost_ratio"), float):
                continue
            out.append({**v, "workflow": label, "marker": marker, "group": section,
                        "risk": risk_group(v["recipe"])})  # fmt: skip
    return out


def place_labels(ax, items: list[tuple[float, float, str]], fig) -> None:
    """Label every point. Try right of it, then left, at growing heights above and below; skip
    spots that overlap a marker or an earlier label, or leave the panel. A label moved off its
    point gets a thin leader line. If nothing fits, the first spot is used anyway."""
    renderer = fig.canvas.get_renderer()
    panel = ax.get_window_extent(renderer)
    to_px = ax.transData.transform
    obstacles = []
    for x, y, _ in items:
        px, py = to_px((x, y))
        obstacles.append(matplotlib.transforms.Bbox([[px - 5, py - 5], [px + 5, py + 5]]))
    candidates = [(side, dy) for k in range(16) for dy in ({0} if k == 0 else (5 * k, -5 * k))
                  for side in (1, -1)]  # fmt: skip

    def label(x, y, text, side, dy, leader):
        line = {"arrowprops": {"arrowstyle": "-", "color": "#b8b7b0", "lw": 0.4, "shrinkA": 0,
                               "shrinkB": 3}} if leader else {}  # fmt: skip
        return ax.annotate(text, (x, y), xytext=(7 * side, dy), textcoords="offset points",
                           fontsize=5.2, color=MUTED, va="center",
                           ha="left" if side > 0 else "right", **line)  # fmt: skip

    for x, y, text in sorted(items, key=lambda t: -t[1]):
        own = matplotlib.transforms.Bbox.from_bounds(*to_px((x, y)) - 5, 10, 10)
        spot, box = (1, 0), None
        for side, dy in candidates:
            # Measure a plain label: with a leader line, the extent would include the line.
            probe = label(x, y, text, side, dy, leader=False)
            b = probe.get_window_extent(renderer).expanded(1.03, 1.2)
            probe.remove()
            fits = (panel.x0 <= b.x0 and b.x1 <= panel.x1 and panel.y0 <= b.y0
                    and b.y1 <= panel.y1)  # fmt: skip
            clash = any(b.overlaps(o) for o in obstacles if
                        not (abs(o.x0 - own.x0) < 1e-6 and abs(o.y0 - own.y0) < 1e-6))  # fmt: skip
            if fits and not clash:
                spot, box = (side, dy), b
                break
        if box is None:  # never drop a label: fall back to the plain spot on the right
            probe = label(x, y, text, 1, 0, leader=False)
            box = probe.get_window_extent(renderer).expanded(1.03, 1.2)
            probe.remove()
        label(x, y, text, *spot, leader=spot[1] != 0)
        obstacles.append(box)


def main() -> None:
    data = points()
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})  # fmt: skip
    fig, axes = plt.subplots(1, 3, figsize=(6.3, 2.6), sharey=True)
    titles = {"W1": "W1: one agent, Wikipedia", "W2": "W2: $\\tau$-bench retail",
              "W3": "W3: research pipeline"}  # fmt: skip
    labels = {}
    for ax, label in zip(axes, ["W1", "W2", "W3"], strict=True):
        items = []
        for p in [p for p in data if p["workflow"] == label]:
            y = p.get("decision_acc_clear")
            if not isinstance(y, float) or math.isnan(y) or p["cost_ratio"] <= 0:
                continue
            ceiling = p["risk"] is None
            colour = CEILING if ceiling else GROUP_COLOURS[p["risk"]]
            ax.scatter(p["cost_ratio"], y, s=26, marker=p["marker"], zorder=3,
                       facecolor="none" if ceiling else colour, edgecolor=colour,
                       linewidths=1.2 if ceiling else 0.6)  # fmt: skip
            items.append((p["cost_ratio"], y, SHORT.get(p["recipe"], p["recipe"])))
        ax.set_xscale("log")
        ax.set_xlim(0.04, 9)
        ax.set_ylim(-0.14, 1.18)
        ax.set_title(titles[label], fontsize=7.5, color=INK, loc="left")
        ax.grid(True, color="#e5e4df", linewidth=0.5, zorder=0)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        labels[label] = (ax, items)
    axes[0].set_ylabel("clear decisions kept")
    axes[1].set_xlabel("cost per run ÷ full workflow's (log scale)")
    handles = [plt.Line2D([], [], marker="o", linestyle="", color=c, label=GROUP_NAMES[g])
               for g, c in GROUP_COLOURS.items()]  # fmt: skip
    handles.append(plt.Line2D([], [], marker="o", linestyle="", markerfacecolor="none",
                              color=CEILING, label="full re-run (ceiling)"))  # fmt: skip
    fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.5, -0.02))  # fmt: skip
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.canvas.draw()  # labels go on last, once the layout is final
    for ax, items in labels.values():
        place_labels(ax, items, fig)
    out = ROOT / "paper" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "cost-vs-validity.pdf")
    fig.savefig(out / "cost-vs-validity.png", dpi=200)
    print(f"{len(data)} points -> {out / 'cost-vs-validity.pdf'}")


if __name__ == "__main__":
    main()
