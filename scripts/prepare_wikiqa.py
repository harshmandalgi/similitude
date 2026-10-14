"""Sample W1's tasks from HotpotQA (distractor config, validation split; CC BY-SA 4.0).

    uv run python scripts/prepare_wikiqa.py

Writes data/wikiqa/tasks.jsonl: 80 test tasks + 20 dev tasks (dev is used only to write fixes,
never to score them). The natural mix of question types is kept (~80% bridge, ~20% comparison).
"""

from __future__ import annotations

import json
import random
import time
import urllib.request
from pathlib import Path

URL = (
    "https://datasets-server.huggingface.co/rows?dataset=hotpotqa/hotpot_qa"
    "&config=distractor&split=validation&offset={offset}&length=100"
)
OUT = Path(__file__).resolve().parents[1] / "data" / "wikiqa" / "tasks.jsonl"
TOTAL = 7405


def main() -> None:
    rng = random.Random("similitude-wikiqa-v1")
    offsets = rng.sample(range(0, TOTAL - 100, 100), 6)
    rows = []
    for offset in offsets:
        with urllib.request.urlopen(URL.format(offset=offset), timeout=60) as r:
            rows += [x["row"] for x in json.load(r)["rows"]]
        time.sleep(1)
    rng.shuffle(rows)
    picked = rows[:100]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w") as f:
        for i, row in enumerate(picked):
            task = {
                "id": row["id"],
                "split": "test" if i < 80 else "dev",
                "question": row["question"],
                "answer": row["answer"],
                "type": row["type"],
                "supporting_titles": sorted(set(row["supporting_facts"]["title"])),
            }
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    kinds = [t["type"] for t in picked[:80]]
    print(
        f"wrote {len(picked)} tasks to {OUT}: test types { {k: kinds.count(k) for k in set(kinds)} }"
    )


if __name__ == "__main__":
    main()
