# 03 · Plan: research + build

> Planning notes from 14 Oct 2026, kept as a record. The final setup and results are in
> [05-IMPLEMENTATION.md](05-IMPLEMENTATION.md), [06-RESULTS.md](06-RESULTS.md) and the paper.

## Goal in one line
Show that a cheap mini workflow can make the **same decisions** as the full workflow's eval, and give
people a tool + rules to build such minis.

---

## Research questions

| # | Question | Answer looks like |
|---|---|---|
| **RQ1** | Can a mini make the same decisions as the full eval? At what cost? | "Mini agreed on 92% of A-vs-B decisions at 8% of the cost" |
| **RQ2** | Which operators are safe, and which break validity? | A table: operator → effect on validity and cost |
| **RQ3** | Does the judge's *reasoning* transfer? Do fixes found on the mini help the full? | Fix transfer rate |
| **RQ4** | Can we predict validity cheaply, before trusting a mini? | Mutant check and "similitude numbers" vs real validity |
| **RQ5** | How many full runs does the correction trick save? | "Same confidence with 5× fewer full runs" |

---

## Experiment design

**Workflows to test (pick 2–3).** Each must have real tools and a clear score.

| Candidate | Why it is a good test | Cost to run full |
|---|---|---|
| A multi-hop QA agent with real web/Wikipedia search | Classic agent loop. Easy to score (exact answer). | Low |
| τ-bench (retail or airline) | Well known. Tools + a simulated user. Has a pass/fail score. Others have already studied sim-vs-real *users* on it, so we can compare. | Medium |
| A multi-agent research/report workflow (planner → searchers → writer → reviewer) | Long, expensive, judge-scored. This is where minis matter most. | High |

**Variants.** For each workflow, make ~20 versions: prompt edits, model swaps, tool-description edits,
plus mutants (deliberately broken versions). These are what the mini must rank correctly.

**Procedure.**
1. Run every variant on the **full** workflow. This is the ground truth. (Costs money once.)
2. Build minis with each operator alone, then in combinations.
3. Run every variant on every mini.
4. Compare with the metrics from [02-IDEAS.md §5](02-IDEAS.md): decision agreement, Kendall τ, mutant
   detection, reasoning agreement, fix transfer rate, cost ratio.

**Model.** The plan named DeepSeek; the study ran on Gemini on Vertex AI (see
[05-IMPLEMENTATION.md](05-IMPLEMENTATION.md)). A second model family for the judge, to avoid a model
grading itself.

**Budget.** First rough guess: the full ground-truth runs are the big cost. Start with the cheap
workflow, measure real cost per run, then size the rest.

---

## Build plan (the software)

A small Python library. Plain Python first; framework adapters (LangGraph, DSPy) later.

| Part | Job |
|---|---|
| `trace` | Record every LLM call and tool call in a run: inputs, outputs, cost, time. |
| `replay` | Prefix replay + tool cache (operators A1, A2). |
| `simulate` | LLM tool simulators: pure, grounded, cache-first; error injection (C1). |
| `fuse` | Merge a chain of calls into one, with split-role option (C2). |
| `reduce` | Apply a "reduction recipe" (a list of operators) to a workflow. |
| `validate` | Run variants + mutants on mini and full; compute the validity metrics. |
| `report` | One page: cost saved, validity scores, which decisions are safe to trust. |

---

## Milestones

| # | Milestone | Done when |
|---|---|---|
| **M0** | Research + docs (this folder) | Docs reviewed and the name chosen |
| **M1** | Build workflow 1 (full) + tracer | Full runs recorded with cost and time |
| **M2** | Free wins (Group A) | Cost saving measured, validity unchanged |
| **M3** | Risky operators (Groups B, C) | Each operator runs on workflow 1 |
| **M4** | Validity checker | Metrics computed for every (variant, mini) pair |
| **M5** | Workflows 2 and 3 + full experiments | RQ1–RQ4 answered with numbers |
| **M6** | Correction trick + auto-reducer | RQ5 answered |
| **M7** | Paper draft | See [04-PAPER-OUTLINE.md](04-PAPER-OUTLINE.md) |

Each milestone gets its own git branch; `main` holds finished work.

---

## Risks

| Risk | What we do |
|---|---|
| Someone publishes the same idea first (close papers came out Aug–Sep 2026) | Move fast. Re-run the prior-work search monthly and before submitting. |
| Full ground-truth runs cost a lot | Start with the cheapest workflow. Measure real cost before scaling. |
| Minis turn out **not** to be valid | Still a paper: "which shortcuts break agent evals, and why" is useful on its own. |
| Results only hold for one model | Repeat the key experiment with a second model family. |

---

## Decisions made (14 Oct 2026)

1. **Name:** Similitude.
2. **Workflows:** the three candidates above (W1 wikiqa, W2 τ-bench retail, W3 research).
3. **Budget:** a hard cap on API spend, raised to $75 as real costs became known.
4. **Target:** an arXiv preprint first.
