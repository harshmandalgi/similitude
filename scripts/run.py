"""Drive any workflow: ground truth, minis, judging, analysis.

    uv run python scripts/run.py wikiqa smoke            # base variant, 3 tasks, full
    uv run python scripts/run.py wikiqa full             # every variant, full workflow
    uv run python scripts/run.py wikiqa mini [RECIPE..]  # minis (default: all for the workflow)
    uv run python scripts/run.py wikiqa judge            # judge traces that have no verdict
    uv run python scripts/run.py wikiqa analyse          # -> results/<workflow>.md and .json

The spending cap is SIMILITUDE_CAP_USD (default 5), checked before every API call and kept
across runs in runs/ledger.json.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from similitude.claude_code import SONNET
from similitude.experiment import Lab, load_traces, records_for, run_grid
from similitude.judge import Verdicts, judge_traces
from similitude.reduce import FULL
from similitude.report import analyse
from similitude.specs import SPECS

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("workflow", choices=sorted(SPECS))
    parser.add_argument("command", choices=["smoke", "full", "mini", "judge", "analyse"])
    parser.add_argument("recipes", nargs="*")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--variants", nargs="*", help="only these variants")
    parser.add_argument("--judge-workers", type=int, default=4)
    parser.add_argument("--judge-model", default=SONNET, help="one judge per workflow, always")
    parser.add_argument("--judge-effort", default="medium")
    parser.add_argument("--judge-batch", type=int, default=25)
    args = parser.parse_args()

    spec = SPECS[args.workflow]
    wf = spec.workflow
    lab = Lab.open(float(os.environ.get("SIMILITUDE_CAP_USD", "5")))
    tasks = spec.load_tasks("test")
    variants = spec.variants()
    if args.variants:
        variants = [v for v in variants if v.name in args.variants]
    by_name = {v.name: v for v in spec.variants()}
    base = next(v for v in spec.variants() if v.kind == "base")
    groups = spec.groups(spec.variants())

    if args.command == "smoke":
        run_grid(lab, wf, tasks[:3], [base], FULL, workers=3)
        for t in load_traces(lab.runs, wf.name, "full", base.name)[:3]:
            print(f"\n{t.task_id}: final={t.final[-200:]!r} error={t.error!r} "
                  f"cost=${t.cost_usd:.4f} latency={t.latency_s:.1f}s "
                  f"llm={t.count('llm')} tools={t.count('tool')}")  # fmt: skip
            print(t.trajectory(120))
    elif args.command == "full":
        run_grid(lab, wf, tasks, variants, FULL, workers=args.workers)
    elif args.command == "mini":
        records = records_for(lab.runs, wf, base)
        if not records.llm:
            sys.exit("run `full` first: minis replay the base variant's recorded runs")
        for group, recipes in spec.recipes.items():
            members = [by_name[n] for n in groups[group] if n in {v.name for v in variants}]
            for recipe in recipes:
                if args.recipes and recipe.name not in args.recipes:
                    continue
                print(f"{group} / {recipe.name}: {len(members)} variants", file=sys.stderr)
                run_grid(lab, wf, tasks, members, recipe, workers=args.workers, records=records)
    elif args.command == "judge":
        by_id = {t["id"]: t for t in tasks}
        traces = [t for t in load_traces(lab.runs, wf.name, "") if not t.error]
        verdicts = Verdicts(lab.runs / "verdicts" / f"{wf.name}.jsonl")
        n = judge_traces(
            traces, verdicts, system=spec.judge_system, item_text=spec.judge_item(by_id),
            rule=spec.rule(by_id), categories=spec.categories,
            raw_dir=lab.runs / "claude" / f"judge-{wf.name}", workers=args.judge_workers,
            truth=spec.truth(by_id) if spec.truth else None, model=args.judge_model,
            effort=args.judge_effort, batch=args.judge_batch,
        )  # fmt: skip
        print(f"sent {n} traces to Claude; {len(verdicts.items)} verdicts in total")
    elif args.command == "analyse":
        out = ROOT / "results"
        out.mkdir(exist_ok=True)
        report, markdown = {}, []
        for group, recipes in spec.recipes.items():
            members = [by_name[n] for n in groups[group]]
            result = analyse(
                lab.runs, wf.name, members, base=base.name,
                mutants=[v.name for v in members if v.kind == "mutant"],
                recipes=recipes, only_recipes={"full", *(r.name for r in recipes)},
                title=f"{wf.name} / focus: {group}",
            )  # fmt: skip
            report[group] = {k: v for k, v in result.items() if k != "markdown"}
            markdown.append(result["markdown"])
        (out / f"{wf.name}.json").write_text(json.dumps(report, indent=1, default=str))
        (out / f"{wf.name}.md").write_text("\n".join(markdown))
        print("\n".join(markdown))
    print(f"spent so far: ${lab.ledger.spent_usd:.4f} of ${lab.ledger.cap_usd:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
