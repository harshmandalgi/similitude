"""Drive W1 (wikiqa): run the full grid, run minis, judge, analyse.

    uv run python scripts/w1.py smoke                  # base variant, 3 tasks, full
    uv run python scripts/w1.py full                   # every variant, full workflow (ground truth)
    uv run python scripts/w1.py mini C1-pure C2-fused  # minis (needs the base's full runs)
    uv run python scripts/w1.py judge                  # judge every trace without a verdict
    uv run python scripts/w1.py analyse                # metrics -> results/w1.json + .md

The spending cap is SIMILITUDE_CAP_USD (default 5). It is checked before every API call and
persists across runs in runs/ledger.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from similitude.experiment import Lab, load_traces, records_for, run_grid
from similitude.judge import Verdicts, judge_traces
from similitude.reduce import FULL, GENERIC, Recipe
from similitude.report import analyse
from similitude.workflows import wikiqa

ROOT = Path(__file__).resolve().parents[1]

RECIPES = {r.name: r for r in GENERIC} | {
    "C2-fused": Recipe("C2-fused", "The whole agent loop as one call with imagined tool results.",
                       fuse=frozenset({"agent"})),
    "B4-quarter": Recipe("B4-quarter", "A fixed random quarter of the tasks.", task_fraction=0.25),
    "C1+C6": Recipe("C1+C6", "Cached real tools, faked misses, outputs cut to 1,200 characters.",
                    llm_replay=True, tool_cache=True, tool_sim="cache_sim", obs_chars=1200),
    "C2+B4": Recipe("C2+B4", "Fused loop on a quarter of the tasks.", fuse=frozenset({"agent"}),
                    task_fraction=0.25),
}  # fmt: skip


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["smoke", "full", "mini", "judge", "analyse"])
    parser.add_argument("recipes", nargs="*")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--variants", nargs="*", help="only these variants")
    args = parser.parse_args()

    lab = Lab.open(float(os.environ.get("SIMILITUDE_CAP_USD", "5")))
    wf = wikiqa.WikiQA()
    tasks = wikiqa.load_tasks("test")
    variants = wikiqa.variants()
    if args.variants:
        variants = [v for v in variants if v.name in args.variants]

    if args.command == "smoke":
        run_grid(lab, wf, tasks[:3], [wikiqa.BASE], FULL, workers=3)
        for t in load_traces(lab.runs, wf.name, "full", "base")[:3]:
            print(
                f"\n{t.task_id}: final={t.final!r} error={t.error!r} cost=${t.cost_usd:.4f} "
                f"latency={t.latency_s:.1f}s llm={t.count('llm')} tools={t.count('tool')}"
            )
            print(t.trajectory(120))
    elif args.command == "full":
        run_grid(lab, wf, tasks, variants, FULL, workers=args.workers)
    elif args.command == "mini":
        records = records_for(lab.runs, wf, wikiqa.BASE)
        if not records.llm:
            sys.exit("run `full` first: minis replay the base variant's recorded runs")
        for name in args.recipes:
            run_grid(lab, wf, tasks, variants, RECIPES[name], workers=args.workers, records=records)
    elif args.command == "judge":
        by_id = {t["id"]: t for t in tasks}
        traces = [t for t in load_traces(lab.runs, wf.name, "") if not t.error]
        verdicts = Verdicts(lab.runs / "verdicts" / "wikiqa.jsonl")
        n = judge_traces(
            traces,
            verdicts,
            system=wikiqa.JUDGE_SYSTEM,
            item_text=wikiqa.judge_item(by_id),
            rule=wikiqa.rule(by_id),
            categories=wikiqa.CATEGORIES,
            raw_dir=lab.runs / "claude" / "judge-wikiqa",
        )
        print(f"judged {n} traces with Claude; {len(verdicts.items)} verdicts in total")
    elif args.command == "analyse":
        result = analyse(
            lab.runs,
            wf.name,
            variants,
            base="base",
            mutants=[v.name for v in variants if v.kind == "mutant"],
            recipes=[r for r in RECIPES.values()],
        )
        out = ROOT / "results"
        out.mkdir(exist_ok=True)
        (out / "w1.json").write_text(json.dumps(result, indent=1, default=str))
        print(result["markdown"])
        (out / "w1.md").write_text(result["markdown"])
    print(f"spent so far: ${lab.ledger.spent_usd:.4f} of ${lab.ledger.cap_usd:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
