"""Rebuild the imagined tool calls of saved fused runs from their stored transcripts.

    uv run python scripts/reparse_fused.py

Needed three times. 2026-10-14: the first parser missed ACTION lines with a speaker prefix
("AGENT: ACTION: ..."). 2026-10-18: it also dropped final answers written in the workflow's own
format ("FINAL ANSWER: ...") without a "FINAL REPLY:" line, and missed indented lines; later the
same day, an answer line inside an imagined observation stopped counting.

Two kinds of recipe:
- every LLM call is fused (FUSED): the imagined tool calls, the final reply and the run's final
  output are rebuilt;
- stubbed researchers (STUBS): later calls read each stub's reply. If a reply changes, the run is
  deleted, so `scripts/run.py research mini <recipe>` runs it again; if only the imagined tool
  calls change, they are rebuilt.
Verdicts of changed runs are removed, so the next judge pass sees the new log.
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
STUBS = [("research", "W-C4-stub"), ("research", "P-C4-stub"), ("research", "P-C4+B1+C5")]


def rebuild(trace: Trace, fused_nodes: set[str] | None = None) -> str:
    """Returns "same", "rebuilt" (saved again) or "rerun" (a stub's reply changed).
    `fused_nodes` None means every LLM call is fused."""
    events, changed, rerun = [], False, False
    old_steps = [(e.name, e.args, e.output) for e in trace.events if e.source == "imagined"]
    new_steps: list = []
    for e in trace.events:
        if e.source == "imagined":
            continue
        if e.kind == "llm" and e.completion and (fused_nodes is None or e.node in fused_nodes):
            steps, final = parse_fused(e.completion["text"])
            for name, args, imagined in steps:
                events.append(
                    Event("tool", e.node, name, "imagined", key_of({"tool": name, "args": args}),
                          imagined, args=args)
                )  # fmt: skip
            new_steps += [(name, args, imagined) for name, args, imagined in steps]
            if fused_nodes is not None:
                rerun = rerun or e.output != final
            else:
                # The workflow returns the fused reply as its output (W2 wraps it as JSON).
                out = json.dumps({"responses": [final]}) if trace.workflow == "tau" else final
                if e.output != final or trace.final != out:
                    e.output, trace.final, changed = final, out, True
        events.append(e)
    if rerun:
        return "rerun"
    if not changed and new_steps == old_steps:
        return "same"
    trace.events = events
    return "rebuilt"


def main() -> None:
    runs = ROOT / "runs"
    removed: set[str] = set()
    jobs = [(w, r, None) for w, r in FUSED] + [(w, r, {"researcher"}) for w, r in STUBS]
    for workflow, recipe, nodes in jobs:
        counts = {"same": 0, "rebuilt": 0, "rerun": 0}
        for t in load_traces(runs, workflow, recipe):
            status = rebuild(t, nodes)
            counts[status] += 1
            path = trace_path(runs, t.workflow, t.recipe, t.variant, t.task_id, t.replicate)
            if status == "rebuilt":
                t.save(path)
            elif status == "rerun":
                path.unlink()
            if status != "same":
                removed.add(t.run_id)
        print(f"{workflow}/{recipe}: {counts}")
    for workflow in {w for w, _, _ in jobs}:
        path = runs / "verdicts" / f"{workflow}.jsonl"
        if not path.exists():
            continue
        lines = [ln for ln in path.read_text().splitlines() if ln.strip()]
        kept = [ln for ln in lines if json.loads(ln)["run_id"] not in removed]
        path.write_text("".join(ln + "\n" for ln in kept))
        print(f"{workflow}: removed {len(lines) - len(kept)} verdicts")


if __name__ == "__main__":
    main()
