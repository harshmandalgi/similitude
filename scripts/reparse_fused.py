"""Rebuild the imagined tool calls of saved fused runs from their stored transcripts.

    uv run python scripts/reparse_fused.py

Needed once (2026-10-14): the first parser missed ACTION lines with a speaker prefix
("AGENT: ACTION: ..."). Applies to recipes whose every LLM call is a fused call. Verdicts of
rebuilt runs are removed, so the next judge pass sees the full log.
"""

from __future__ import annotations

import json
from pathlib import Path

from similitude.cache import key_of
from similitude.core import Event, Trace
from similitude.experiment import load_traces, trace_path
from similitude.fuse import parse_fused

ROOT = Path(__file__).resolve().parents[1]
FUSED = [("wikiqa", "C2-fused"), ("wikiqa", "C2+B4"), ("tau", "C2-all"), ("research", "P-C2-all")]


def rebuild(trace: Trace) -> bool:
    events, changed = [], False
    for e in trace.events:
        if e.source == "imagined":
            continue
        if e.kind == "llm" and e.completion:
            steps, _ = parse_fused(e.completion["text"])
            old = sum(1 for x in trace.events if x.source == "imagined")
            for name, args, imagined in steps:
                events.append(
                    Event(
                        "tool",
                        e.node,
                        name,
                        "imagined",
                        key_of({"tool": name, "args": args}),
                        imagined,
                        args=args,
                    )
                )
            changed = changed or len(steps) != old
        events.append(e)
    trace.events = events
    return changed


def main() -> None:
    runs = ROOT / "runs"
    rebuilt: set[str] = set()
    for workflow, recipe in FUSED:
        for t in load_traces(runs, workflow, recipe):
            if rebuild(t):
                t.save(trace_path(runs, t.workflow, t.recipe, t.variant, t.task_id, t.replicate))
                rebuilt.add(t.run_id)
    for workflow in {w for w, _ in FUSED}:
        path = runs / "verdicts" / f"{workflow}.jsonl"
        if not path.exists():
            continue
        lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
        kept = [ln for ln in lines if json.loads(ln)["run_id"] not in rebuilt]
        path.write_text("".join(ln + "\n" for ln in kept))
        print(f"{workflow}: removed {len(lines) - len(kept)} verdicts")
    print(f"rebuilt {len(rebuilt)} traces")


if __name__ == "__main__":
    main()
