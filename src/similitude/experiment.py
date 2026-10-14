"""Run the grid: variants × tasks × replicates, under one recipe. Resumable: a run whose trace
file exists is skipped. Stops cleanly at the budget cap."""

from __future__ import annotations

import os
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from similitude.cache import Cache
from similitude.core import Trace, Variant, Workflow
from similitude.llm import BudgetExceeded, Ledger, LLMClient
from similitude.reduce import Recipe
from similitude.runtime import Records, Runtime

ROOT = Path(__file__).resolve().parents[2]


@dataclass
class Lab:
    runs: Path
    client: LLMClient
    cache: Cache
    ledger: Ledger

    @classmethod
    def open(cls, cap_usd: float, runs: Path | None = None) -> Lab:
        runs = runs or ROOT / "runs"
        ledger = Ledger(cap_usd, runs / os.environ.get("SIMILITUDE_LEDGER", "ledger.json"))
        return cls(runs, LLMClient(ledger), Cache(runs / "cache.sqlite"), ledger)


def _safe(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)


def trace_path(
    runs: Path, workflow: str, recipe: str, variant: str, task_id: str, rep: int
) -> Path:
    return runs / "traces" / workflow / recipe / _safe(variant) / f"{_safe(task_id)}.r{rep}.json"


def select_tasks(workflow: str, tasks: list[dict[str, Any]], recipe: Recipe) -> list[dict]:
    """B4: a fixed random subset, the same for every variant."""
    if recipe.task_fraction >= 1:
        return tasks
    n = max(1, round(len(tasks) * recipe.task_fraction))
    return random.Random(f"{workflow}:subset").sample(tasks, n)


def run_one(
    lab: Lab, wf: Workflow, task: dict, variant: Variant, recipe: Recipe, rep: int,
    records: Records | None,
) -> Trace:  # fmt: skip
    trace = Trace(wf.name, recipe.name, variant.name, task["id"], rep)
    rt = Runtime(
        workflow=wf, client=lab.client, cache=lab.cache, recipe=recipe,
        config=wf.config_for(variant), focus=recipe.focus or variant.focus, trace=trace,
        records=records,
    )  # fmt: skip
    try:
        trace.final = wf.run(task, rt, wf.config_for(variant))
    except BudgetExceeded:
        raise
    except Exception as exc:  # noqa: BLE001 - a failed run is recorded, not fatal
        trace.error = f"{type(exc).__name__}: {exc}"
    trace.save(trace_path(lab.runs, wf.name, recipe.name, variant.name, task["id"], rep))
    return trace


def run_grid(
    lab: Lab,
    wf: Workflow,
    tasks: list[dict[str, Any]],
    variants: list[Variant],
    recipe: Recipe,
    *,
    replicates: int = 1,
    workers: int = 8,
    records: Records | None = None,
) -> int:
    """Returns the number of new traces. Base variants run first, so later ones can reuse them."""
    chosen = select_tasks(wf.name, tasks, recipe)
    ordered = sorted(variants, key=lambda v: v.kind != "base")
    jobs = [
        (task, v, rep)
        for v in ordered
        for task in chosen
        for rep in range(replicates)
        if not trace_path(lab.runs, wf.name, recipe.name, v.name, task["id"], rep).exists()
    ]
    if not jobs:
        return 0
    done, errors, stop = 0, 0, threading.Event()
    start = time.time()

    def job(task, v, rep):
        if stop.is_set():
            return None
        return run_one(lab, wf, task, v, recipe, rep, records)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(job, *j) for j in jobs]
        for future in as_completed(futures):
            try:
                trace = future.result()
            except BudgetExceeded as exc:
                stop.set()
                print(f"  stopped: {exc}", file=sys.stderr)
                continue
            if trace is None:
                continue
            done += 1
            errors += bool(trace.error)
            if done % 25 == 0 or done == len(jobs):
                print(
                    f"  {recipe.name}: {done}/{len(jobs)} runs, {errors} errors, "
                    f"${lab.ledger.spent_usd:.3f} spent, {time.time() - start:.0f}s",
                    file=sys.stderr,
                )
    return done


def load_traces(runs: Path, workflow: str, recipe: str, variant: str | None = None) -> list[Trace]:
    folder = runs / "traces" / workflow / recipe
    if variant is not None:
        folder = folder / _safe(variant)
    return [Trace.load(p) for p in sorted(folder.rglob("*.json"))]


def records_for(runs: Path, wf: Workflow, base: Variant) -> Records:
    """What a team would already have: the full runs of the current (base) workflow."""
    return Records.from_traces(load_traces(runs, wf.name, "full", base.name))
