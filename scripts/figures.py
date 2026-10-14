"""Paper figure: what each miniature costs vs how well it keeps the full workflow's decisions.

    uv run python scripts/figures.py   # reads results/<workflow>.json -> paper/figures/

Two panels on the same x-axis (cost of the miniature as a share of the full workflow's, log
scale): Kendall's tau between variant rankings, and agreement on clear pairwise decisions. Colour
is the operator's risk group (A/B/C, docs/02-IDEAS.md); marker shape is the workflow; grey hollow
markers are the full workflow re-run, the noise ceiling. Palette: the dataviz reference
categorical slots 1-3, validated all-pairs for light mode; every point carries a text label.
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
GROUP_COLOURS = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}
CEILING = "#8a8986"
INK, MUTED = "#0b0b0b", "#52514e"
WORKFLOWS = {"wikiqa": ("W1", "o"), "tau": ("W2", "s"), "research": ("W3", "^")}


def risk_group(recipe: str) -> str | None:
    """A recipe's riskiest operator group: 'W-A+B1+C5' -> 'C'. None for the re-run."""
    name = re.sub(r"^[WP]-", "", recipe)
    if "rerun" in name:
        return None
    groups = re.findall(r"(?:^|\+)([ABC])\d?", name)
    return max(groups) if groups else None


def points() -> list[dict]:
    out = []
    for workflow, (label, marker) in WORKFLOWS.items():
        path = ROOT / "results" / f"{workflow}.json"
        if not path.exists():
            continue
        for group, result in json.loads(path.read_text()).items():
            for v in result["validity"]:
                if not isinstance(v.get("cost_ratio"), float):
                    continue
                out.append({**v, "workflow": label, "marker": marker, "group": group,
                            "risk": risk_group(v["recipe"])})  # fmt: skip
    return out


def main() -> None:
    data = points()
    plt.rcParams.update({"font.family": "serif", "font.size": 8, "axes.edgecolor": MUTED,
                         "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED})  # fmt: skip
    fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.7), sharex=True)
    panels = [("kendall", "Kendall $\\tau$ (rankings)"),
              ("decision_acc_clear", "Agreement on clear pairs")]  # fmt: skip
    for ax, (key, title) in zip(axes, panels, strict=True):
        for p in data:
            y = p.get(key)
            if not isinstance(y, float) or math.isnan(y) or p["cost_ratio"] <= 0:
                continue
            ceiling = p["risk"] is None
            colour = CEILING if ceiling else GROUP_COLOURS[p["risk"]]
            ax.scatter(p["cost_ratio"], y, s=30, marker=p["marker"], zorder=3,
                       facecolor="none" if ceiling else colour, edgecolor=colour,
                       linewidths=1.2 if ceiling else 0.6)  # fmt: skip
            name = re.sub(r"^[WP]-", "", p["recipe"])
            ax.annotate(f"{p['workflow']} {name}", (p["cost_ratio"], y), xytext=(3, 2),
                        textcoords="offset points", fontsize=4.6, color=MUTED)  # fmt: skip
        ax.set_xscale("log")
        ax.set_title(title, fontsize=8, color=INK, loc="left")
        ax.set_xlabel("cost of the miniature ÷ cost of the full workflow")
        ax.grid(True, color="#e5e4df", linewidth=0.5, zorder=0)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    handles = [plt.Line2D([], [], marker="o", linestyle="", color=c, label=f"group {g}")
               for g, c in GROUP_COLOURS.items()]  # fmt: skip
    handles.append(plt.Line2D([], [], marker="o", linestyle="", markerfacecolor="none",
                              color=CEILING, label="full re-run (ceiling)"))  # fmt: skip
    handles += [plt.Line2D([], [], marker=m, linestyle="", color=MUTED, label=lab)
                for lab, m in WORKFLOWS.values()]  # fmt: skip
    fig.legend(handles=handles, loc="lower center", ncol=7, frameon=False, fontsize=6.5,
               bbox_to_anchor=(0.5, -0.04))  # fmt: skip
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    out = ROOT / "paper" / "figures"
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "cost-vs-validity.pdf")
    fig.savefig(out / "cost-vs-validity.png", dpi=200)
    print(f"{len(data)} points -> {out / 'cost-vs-validity.pdf'}")


if __name__ == "__main__":
    main()
