"""The eval's judge: a score *and* a reason for every run.

Clear-cut runs are scored by a workflow's rule (e.g. exact match). The rest go to a blind
Claude Code judge in batches. The judge sees only the task, the reference, the final reply and a
short trajectory, under a random code: never the recipe, the variant, or whether it was a mini.
"""

from __future__ import annotations

import json
import random
import secrets
import sys
import threading
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from pathlib import Path

from similitude.claude_code import OPUS, ask_claude
from similitude.core import Trace


@dataclass
class Verdict:
    run_id: str
    correct: bool
    category: str  # "correct" or a failure category from the workflow's taxonomy
    reason: str
    by: str  # "rule" or "claude:<model>/<effort>"


class Verdicts:
    """An append-only JSONL file of verdicts, keyed by run_id."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = threading.Lock()
        self.items: dict[str, Verdict] = {}
        if path.exists():
            for line in path.read_text().splitlines():
                if line.strip():
                    v = Verdict(**json.loads(line))
                    self.items[v.run_id] = v

    def add(self, verdicts: list[Verdict]) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a") as f:
                for v in verdicts:
                    self.items[v.run_id] = v
                    f.write(json.dumps(asdict(v), ensure_ascii=False) + "\n")


def judge_traces(
    traces: list[Trace],
    verdicts: Verdicts,
    *,
    system: str,
    item_text: Callable[[str, Trace], str],
    rule: Callable[[Trace], Verdict | None],
    categories: list[str],
    raw_dir: Path,
    batch: int = 20,
    workers: int = 3,
    model: str = OPUS,
    effort: str = "high",
    truth: Callable[[Trace], bool] | None = None,
) -> int:
    """`truth`, when given, decides pass/fail (e.g. a benchmark's own check); the judge then
    supplies only the reason."""
    """Judge every trace that has no verdict yet. Returns how many Claude judged."""
    todo = [t for t in traces if t.run_id not in verdicts.items]
    by_rule = [v for t in todo if (v := rule(t)) is not None]
    verdicts.add(by_rule)
    ruled = {v.run_id for v in by_rule}
    todo = [t for t in todo if t.run_id not in ruled]
    random.Random(len(todo)).shuffle(todo)  # mix recipes and variants inside every batch
    batches = [todo[i : i + batch] for i in range(0, len(todo), batch)]

    def one(number: int, chunk: list[Trace]) -> None:
        codes = {secrets.token_hex(3): t for t in chunk}
        user = "\n\n".join(item_text(code, t) for code, t in codes.items())
        answer = ask_claude(
            system, user, model=model, effort=effort, keep_dir=raw_dir, name=f"batch{number}"
        )
        got = {str(a["item"]): a for a in answer["items"]}
        out = []
        for code, t in codes.items():
            a = got.get(code)
            if a is None:
                continue  # left for the next pass
            category = str(a.get("category", "")).strip()
            correct = truth(t) if truth else bool(a.get("correct"))
            if correct:
                category = "correct"
            elif category not in categories:
                category = "other"
            out.append(
                Verdict(t.run_id, correct, category, str(a.get("reason", ""))[:400],
                        f"claude:{model}/{effort}")
            )  # fmt: skip
        verdicts.add(out)

    def safe(number: int, chunk: list[Trace]) -> None:
        try:
            one(number, chunk)
        except Exception as exc:  # noqa: BLE001 - the batch stays unjudged; the next pass retries it
            print(f"  judge batch {number} failed: {exc}", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=workers) as pool:
        list(pool.map(lambda nc: safe(*nc), enumerate(batches, start=1)))
    return len(todo)
