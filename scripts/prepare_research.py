"""Sample W3's tasks from FRAMES (google/frames-benchmark, test split; Apache 2.0).

    uv run python scripts/prepare_research.py

Writes data/research/tasks.jsonl: 80 test + 10 dev tasks, needing 2-3 pages and no tables.
Dev is used only to write variants.
"""

from __future__ import annotations

import ast
import json
import random
import time
import urllib.request
from pathlib import Path

URL = (
    "https://datasets-server.huggingface.co/rows?dataset=google/frames-benchmark"
    "&config=default&split=test&offset={offset}&length=100"
)
OUT = Path(__file__).resolve().parents[1] / "data" / "research" / "tasks.jsonl"
TOTAL = 824


def main() -> None:
    rows = []
    for offset in range(0, TOTAL, 100):
        with urllib.request.urlopen(URL.format(offset=offset), timeout=60) as r:
            rows += [x["row"] for x in json.load(r)["rows"]]
        time.sleep(1)
    # Keep questions that need 2-3 pages and no table reading (tables come through badly as
    # plain text): hard enough for a pipeline, not so hard that every variant scores zero.
    rows = [
        r
        for r in rows
        if len(ast.literal_eval(r["wiki_links"])) <= 3 and "Tabular" not in r["reasoning_types"]
    ]
    rng = random.Random("similitude-research-v1")
    rng.shuffle(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for i, row in enumerate(rows[:90]):
            task = {
                "id": f"frames-{row['Unnamed: 0']}",
                "split": "test" if i < 80 else "dev",
                "question": row["Prompt"],
                "answer": row["Answer"],
                "reasoning_types": row["reasoning_types"],
                "wiki_links": ast.literal_eval(row["wiki_links"]),
            }
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    print(f"wrote 90 tasks to {OUT}")


if __name__ == "__main__":
    main()
