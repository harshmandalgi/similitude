"""Paper tables from results/summary.json (run scripts/summary.py first).

uv run python scripts/tables.py   # -> paper/tables/main.tex
"""

from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

NAMES = {
    "full-rerun": "Full workflow, re-run (ceiling)", "W-rerun": "Full workflow, re-run (ceiling)",
    "P-rerun": "Full workflow, re-run (ceiling)",
    "C1-cache-sim": "Simulated tools, cache first", "C1-pure": "Simulated tools, pure",
    "C6-short-obs": "Short tool outputs", "B4-quarter": "Fewer tasks (1/4)",
    "C2-fused": "Agent loop as one call", "C2+B4": "One call + fewer tasks",
    "B3-cheap-user": "Cheaper simulated customer", "C2-all": "Whole conversation as one call",
    "W-A-replay": "Replay planner and research", "W-A+B1+C5": "Replay + slice + stop early",
    "W-C4-stub": "Stubbed researchers", "P-C1-pure": "Simulated researcher tools",
    "P-C4-stub": "Stubbed researchers", "P-C4+B1+C5": "Stubbed + slice + stop early",
    "P-C2-all": "Whole pipeline as one call", "C3-shrink-policy": "Shrunk policy",
}  # fmt: skip
OPS = {
    "full-rerun": "--", "W-rerun": "--", "P-rerun": "--", "C1-cache-sim": "A1 A2 C1", "C1-pure": "C1",
    "C6-short-obs": "C6", "B4-quarter": "B4", "C2-fused": "C2", "C2+B4": "C2 B4",
    "B3-cheap-user": "B3", "C2-all": "C2", "W-A-replay": "A1 A2 A3", "W-A+B1+C5": "A B1 C5",
    "W-C4-stub": "C4", "P-C1-pure": "C1", "P-C4-stub": "C4", "P-C4+B1+C5": "C4 B1 C5",
    "P-C2-all": "C2", "C3-shrink-policy": "C3",
}  # fmt: skip
SECTIONS = [
    ("W1 wikiqa (10 core variants)", "W1 (single agent, live Wikipedia; 10 variants)"),
    ("W2 tau (8 core variants)", "W2 ($\\tau$-bench retail; 8 variants)"),
    ("W3 research, focus planner", "W3, focus: planner (7 variants)"),
    ("W3 research, focus writer", "W3, focus: writer (7 variants)"),
]


def num(x, digits: int = 2) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "--"
    return f"{x:.{digits}f}".replace("-", "$-$")  # a real minus sign, not a hyphen


def frac(r: dict) -> str:
    if r.get("clear_pairs") in (None, 0) or r.get("decision_acc_clear") is None:
        return "--"
    acc = r["decision_acc_clear"]
    if isinstance(acc, float) and math.isnan(acc):
        return "--"
    return f"{round(acc * r['clear_pairs'])}/{r['clear_pairs']}"


def main() -> None:
    data = json.loads((ROOT / "results" / "summary.json").read_text())
    rows = [
        "\\begin{table*}[t]", "\\centering\\small",
        "\\begin{tabular}{@{}llrrrrrr@{}}", "\\toprule",
        "Miniature & Ops & Cost & Time & Clear pairs kept & Kendall $\\tau$ & MMRV & Reason $\\pi$ \\\\",
        "\\midrule",
    ]  # fmt: skip
    for key, title in SECTIONS:
        results = data.get(key, [])
        if not results:
            continue
        rows.append(f"\\multicolumn{{8}}{{@{{}}l}}{{\\textit{{{title}}}}} \\\\")
        for r in results:
            name = NAMES.get(r["recipe"], r["recipe"])
            if "rerun" in r["recipe"]:
                name = f"\\textbf{{{name}}}"
            rows.append(
                f"\\quad {name} & {OPS.get(r['recipe'], '')} & {num(r.get('cost_ratio'))}"
                f"$\\times$ & {num(r.get('latency_ratio_median'))}$\\times$ & {frac(r)} & "
                f"{num(r.get('kendall'))} & {num(r.get('mmrv'))} & {num(r.get('reason_pi'))} \\\\"
            )
        rows.append("\\addlinespace")
    rows[-1] = "\\bottomrule"
    rows += [
        "\\end{tabular}",
        ("\\caption{Each miniature against the full workflow. Cost and time are per-run medians "
        "relative to the full workflow. \\emph{Clear pairs kept}: of the variant pairs whose "
        "full-workflow gap exceeds two paired standard errors, how many the miniature orders the "
        "same way. MMRV weights ranking errors by the real gap (lower is better). Reason $\\pi$: "
        "agreement of the judge's failure reasons on the same task (Scott's $\\pi$). Bold rows are "
        "the noise ceiling: the full workflow run again.}"),
        "\\label{tab:main}", "\\end{table*}",
    ]  # fmt: skip
    out = ROOT / "paper" / "tables"
    out.mkdir(parents=True, exist_ok=True)
    (out / "main.tex").write_text("\n".join(rows) + "\n")
    print(f"wrote {out / 'main.tex'}")


if __name__ == "__main__":
    main()
