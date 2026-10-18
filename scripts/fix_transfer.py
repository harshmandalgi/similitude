"""RQ3: do fixes found by looking at a mini's failures improve the full workflow? (W1, wikiqa)

    uv run python scripts/fix_transfer.py evidence C1-cache-sim C2-fused   # base on dev, judged
    uv run python scripts/fix_transfer.py write C1-cache-sim C2-fused      # Claude writes fixes
    uv run python scripts/fix_transfer.py run C1-cache-sim C2-fused        # fixes on test
    uv run python scripts/fix_transfer.py analyse C1-cache-sim C2-fused    # -> results/

1. Evidence: the base variant runs on the 20 dev questions under the full workflow and under each
   named mini (recipe names prefixed "dev-", so dev runs never mix with test results). A blind
   Claude judge gives every failure a reason.
2. Write: for each evidence source, a fresh Claude Code instance sees only the failures (question,
   reference, answer, judge's reason, short log), never which source they came from, and writes 3
   revised prompts, each fixing one pattern it sees.
3. Run: every fix runs on the 80 test questions, under full (ground truth) and under each mini.
4. Analyse: per source, how much the fixes help on full; and per mini, whether it predicts the
   sign of each fix's effect on full.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys
from pathlib import Path

from similitude.claude_code import OPUS, SONNET, ask_claude
from similitude.core import Variant
from similitude.experiment import Lab, load_traces, run_grid
from similitude.judge import Verdicts, judge_traces
from similitude.reduce import FULL
from similitude.report import rows_for
from similitude.runtime import Records
from similitude.specs import SPECS, W1_RECIPES
from similitude.validate import paired
from similitude.workflows import wikiqa

ROOT = Path(__file__).resolve().parents[1]
FIXES = ROOT / "data" / "wikiqa" / "fixes.json"
RECIPES = {r.name: r for r in W1_RECIPES}
# Evidence from simulated tools must not replay the agent: the base variant's calls are identical
# to the recorded ones, so C1-cache-sim would just replay the full run (as the first run of this
# test did, 2026-10-15; its "C1-cache-sim" fixes are in effect a second set written from full
# evidence). C1-sim samples the agent afresh; tools answer from the recording first, else simulated.
RECIPES["C1-sim"] = RECIPES["C1-cache-sim"].but(
    "C1-sim", llm_replay=False,
    description="Fresh agent calls; recorded tool outputs first, simulated outputs for the rest.",
)  # fmt: skip

WRITE_SYSTEM = """\
You are an engineer improving an LLM agent that answers multi-hop questions with Wikipedia tools. \
You will see its current system prompt and the failures from a recent evaluation run: for each, \
the question, the reference answer, the agent's answer, a grader's one-line reason, and a short \
log of the agent's tool calls.

Write 3 revised system prompts. Each one targets ONE failure pattern you see in this evidence, so \
its effect can be measured; make the three clearly different.
- Keep the tool names and the "FINAL ANSWER: <answer>" output rule exactly as they are.
- Keep each prompt under 180 words.

Reply with only JSON: {"fixes": [{"name": "<short-kebab-name>", "pattern": "<the failure \
pattern it targets, one sentence>", "prompt": "<the full revised system prompt>"}]}"""


def _lab() -> Lab:
    return Lab.open(float(os.environ.get("SIMILITUDE_CAP_USD", "5")))


def _dev(name: str):
    return (FULL if name == "full" else RECIPES[name]).but("dev-" + name)


def evidence(minis: list[str]) -> None:
    lab, spec = _lab(), SPECS["wikiqa"]
    dev = wikiqa.load_tasks("dev")
    run_grid(lab, spec.workflow, dev, [wikiqa.BASE], _dev("full"), workers=6)
    records = Records.from_traces(load_traces(lab.runs, "wikiqa", "dev-full", "base"))
    for name in minis:
        run_grid(lab, spec.workflow, dev, [wikiqa.BASE], _dev(name), workers=6, records=records)
    by_id = {t["id"]: t for t in dev}
    traces = [
        t for r in ["full", *minis] for t in load_traces(lab.runs, "wikiqa", "dev-" + r)
        if not t.error
    ]  # fmt: skip
    judge_traces(
        traces, Verdicts(lab.runs / "verdicts" / "wikiqa.jsonl"), system=spec.judge_system,
        item_text=spec.judge_item(by_id), rule=spec.rule(by_id), categories=spec.categories,
        raw_dir=lab.runs / "claude" / "judge-wikiqa", model=SONNET, effort="medium", batch=25,
    )  # fmt: skip


def _failures(source: str) -> str:
    lab = _lab()
    dev = {t["id"]: t for t in wikiqa.load_tasks("dev")}
    verdicts = Verdicts(lab.runs / "verdicts" / "wikiqa.jsonl").items
    blocks = []
    for t in load_traces(lab.runs, "wikiqa", "dev-" + source, "base"):
        v = verdicts.get(t.run_id)
        if v is None or v.correct:
            continue
        log = t.trajectory(obs_chars=160).splitlines()[:12]
        blocks.append(
            "\n".join([f"Question: {dev[t.task_id]['question']}",
                       f"Reference answer: {dev[t.task_id]['answer']}",
                       f"Agent's answer: {wikiqa.final_answer(t.final) or '(none)'}",
                       f"Grader's reason: {v.reason}", "Log:", *log])
        )  # fmt: skip
    random.Random(source).shuffle(blocks)
    return "\n\n---\n\n".join(blocks)


def write(minis: list[str]) -> None:
    lab = _lab()
    out = json.loads(FIXES.read_text()) if FIXES.exists() else {}
    for source in ["full", *minis]:
        if source in out:
            continue
        evidence_text = _failures(source)
        user = f"Current system prompt:\n{wikiqa.BASE_PROMPT}\n\nFailures:\n\n{evidence_text}"
        answer = ask_claude(
            WRITE_SYSTEM, user, model=OPUS, effort="high",
            keep_dir=lab.runs / "claude" / "fixes", name=f"fixes-{source}",
        )  # fmt: skip
        fixes = answer["fixes"]
        assert len(fixes) == 3 and all("FINAL ANSWER" in f["prompt"] for f in fixes)
        out[source] = fixes
        FIXES.write_text(json.dumps(out, indent=1, ensure_ascii=False) + "\n")
        print(f"{source}: " + "; ".join(f["name"] for f in fixes))


def fix_variants() -> list[Variant]:
    out = []
    for source, fixes in json.loads(FIXES.read_text()).items():
        for f in fixes:
            out.append(
                Variant(f"fix-{source}-{f['name']}", "fix", "agent", f["pattern"],
                        {"prompts": {"agent": f["prompt"]}})
            )  # fmt: skip
    return out


def run(minis: list[str]) -> None:
    lab, spec = _lab(), SPECS["wikiqa"]
    tasks = wikiqa.load_tasks("test")
    variants = fix_variants()
    run_grid(lab, spec.workflow, tasks, variants, FULL, workers=8)
    records = Records.from_traces(load_traces(lab.runs, "wikiqa", "full", "base"))
    for name in minis:
        run_grid(lab, spec.workflow, tasks, variants, RECIPES[name], workers=8, records=records)
    by_id = {t["id"]: t for t in tasks}
    names = {v.name for v in variants}
    traces = [
        t for r in ["full", *minis] for t in load_traces(lab.runs, "wikiqa", r)
        if t.variant in names and not t.error
    ]  # fmt: skip
    judge_traces(
        traces, Verdicts(lab.runs / "verdicts" / "wikiqa.jsonl"), system=spec.judge_system,
        item_text=spec.judge_item(by_id), rule=spec.rule(by_id), categories=spec.categories,
        raw_dir=lab.runs / "claude" / "judge-wikiqa", model=SONNET, effort="medium", batch=25,
    )  # fmt: skip


def analyse(minis: list[str]) -> None:
    lab = _lab()
    rows, _ = rows_for(lab.runs, "wikiqa")
    variants = fix_variants()
    lines = ["# Fix transfer (W1, wikiqa)\n",
             ("Each fix was written by a blind Claude Code instance from one evidence source's "
              "failures on the 20 dev questions, then scored on the 80 test questions.\n"),
             "| fix | written from | gain on full (± SE) | " + " | ".join(f"gain on {m}" for m in minis)
             + " |", "|---|---|---|" + "---|" * len(minis)]  # fmt: skip
    summary: dict[str, dict] = {}
    sources = list(json.loads(FIXES.read_text()))  # every evidence source, run under a mini or not
    for v in variants:
        source = next(s for s in sources if v.name.startswith(f"fix-{s}-"))
        d_full, se_full, _ = paired(rows, "full", v.name, "base")
        cells = []
        for m in minis:
            d_mini, _, _ = paired(rows, m, v.name, "base")
            cells.append(f"{d_mini:+.3f}")
            agree = summary.setdefault(m, {"agree": 0, "n": 0})
            # Same sign, strictly: a zero gain on the mini does not agree with a loss on full.
            if not math.isnan(d_full) and d_full != 0 and not math.isnan(d_mini):
                agree["n"] += 1
                agree["agree"] += (
                    math.copysign(1, d_full) == math.copysign(1, d_mini) and d_mini != 0
                )
        s = summary.setdefault(f"from:{source}", {"gains": []})
        s["gains"].append(d_full)
        lines.append(f"| {v.name} | {source} | {d_full:+.3f} ± {se_full:.3f} | " + " | ".join(cells)
                     + " |")  # fmt: skip
    lines.append("\n## Do fixes found on a mini help the full workflow?\n")
    for key, s in summary.items():
        if key.startswith("from:"):
            gains = [g for g in s["gains"] if not math.isnan(g)]
            helped = sum(g > 0 for g in gains)
            label = {"C1-cache-sim": "C1-cache-sim (in effect full: it replayed the full run)"}
            lines.append(f"- Fixes written from **{label.get(key[5:], key[5:])}** evidence: mean gain on full "
                         f"{sum(gains) / len(gains):+.3f}; {helped}/{len(gains)} helped.")  # fmt: skip
    lines.append("\n## Does each mini predict whether a fix helps?\n")
    for m in minis:
        s = summary[m]
        lines.append(f"- **{m}**: same sign as full for {s['agree']}/{s['n']} fixes.")
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / "w1-fix-transfer.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["evidence", "write", "run", "analyse"])
    parser.add_argument("minis", nargs="+")
    args = parser.parse_args()
    {"evidence": evidence, "write": write, "run": run, "analyse": analyse}[args.command](args.minis)
    return 0


if __name__ == "__main__":
    sys.exit(main())
