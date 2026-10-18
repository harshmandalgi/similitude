# 06 · Results: which minis keep the evaluation valid?

Data from 14–18 Oct 2026. Gemini on Vertex; Claude Code (Sonnet 5.5) as the blind judge (Opus 5.5
for the OpenAI run).
Full tables: [results/summary.md](../results/summary.md). Estimated spend: $73.18 on Gemini
(cap $75), plus $2.30 on OpenAI (W1 cross-family run).

> **Corrected on 18 Oct 2026** after a code review: (1) the merged-call parser dropped answers
> written as "FINAL ANSWER:" without "FINAL REPLY:"; 779 saved runs were re-parsed and re-judged;
> (2) τ-bench runs went on after a hand-over to a human, which ends the episode in τ-bench; saved
> runs are now scored up to the first hand-over (19 pass/fail results changed); (3) the first
> simulated-tools fix test replayed the full run, so it was redone; (4) an answer line inside an
> imagined tool result no longer counts as the answer, and 12 W3 runs with stubbed researchers had
> used replies read by an older parser, so they were run again (304 W3 runs re-judged; "stubbed + no
> review + no summary" went from 62% to 50%). All numbers below are the corrected ones.

---

## Short answer

1. **Idea 1, simulated tools, works, if the simulator can know the answer.** It kept
   90–100% of the clear decisions in W1 and in W3's planner tests. It works best when grounded in
   recorded real outputs ("cache first"). On τ-bench it kept **none**: the tools read a private
   shop database, which the simulator cannot see.
2. **Idea 2, merging calls with imagined tool results, misses what matters most.** It kept
   60–75% of the clear decisions (W1 12/20, W3 6/8), but it missed **all 4 broken variants** the
   full workflow caught, and its scores barely follow the full ones (r = 0.31, 0.16). The model
   imagines the facts its plan needs. On τ-bench it breaks completely: the model invents customer
   and order IDs, so nothing it "does" can be checked against the real database.
3. **Replaying the unchanged part of the workflow is cheap (0.21× the evaluation cost in W3)**, and
   a replayed call is
   a real sample when its inputs are identical. Our one test of it (W3 writer) was inconclusive:
   the full evaluation was itself mostly noise.
4. **Fewer tasks keeps most clear decisions at 0.2× the evaluation cost** (85% in W1). It combines with any mini.
5. **Most prompt changes barely matter.** In every workflow, most variants sat within noise of the
   base. Only big breakages (step caps, skipping confirmation) were clear. So the honest test of a
   mini is: does it settle the *same few* decisions the full evaluation can settle?

---

## How to read the tables

**Noise ceiling (4W1H)**

| | |
|---|---|
| **What** | The full workflow run a second time, with fresh samples. |
| **Why** | Agents are random, and test sets are small. The full evaluation does not even agree with itself. It is a reference point, not a hard limit: a mini that agrees as often is as reliable as a second full run. |
| **When** | Read every mini against it, not against perfection. |
| **Where** | The `full-rerun` / `W-rerun` / `P-rerun` rows. |
| **How** | Compute the same agreement numbers between the full workflow and its own re-run. |

**Columns**
- **Cost**: the mini's whole evaluation cost, as a share of the full evaluation's. A mini on fewer
  tasks is cheaper per evaluation, not per run.
- **Speed**: the mini's median time per run, as a share of the full workflow's.
- **Clear decisions kept**: of the pairs of variants where the full workflow sees a clear
  winner (gap > 2 standard errors), the share where the mini picks the same winner.
- **Broken caught**: of the deliberately broken variants the full workflow catches, how many
  the mini also catches.
- **Ranking (τ)**: Kendall's τ between the two rankings of all variants. 1 means the same order.
- **Reasons (π)**: do the judge's failure reasons match, run by run? (Scott's π: 0 means chance.)

---

## W1 · one agent, live Wikipedia (10 core variants)

| Mini | Cost | Speed | Clear kept | Broken caught | Ranking τ | Reasons π |
|---|---|---|---|---|---|---|
| **Ceiling (full re-run)** | 1.05× | 1.14× | 100% | 2/2 | 0.67 | 0.57 |
| Simulated tools, cache first | 1.23× | 0.74× | 95% | 2/2 | 0.61 | 0.41 |
| Simulated tools, pure | 1.05× | 1.49× | 90% | 2/2 | 0.54 | 0.27 |
| Short tool outputs | 0.89× | 1.45× | 100% | 2/2 | 0.48 | 0.54 |
| Fewer tasks (¼) | 0.20× | 0.86× | 85% | 1/2 | 0.40 | 0.53 |
| **Merged calls** | 0.28× | 0.21× | 60% | 0/2 | 0.12 | 0.18 |
| Merged calls + fewer tasks | 0.06× | 0.20× | 55% | 0/2 | 0.47 | 0.09 |

- Under merged calls, every variant scores about the same. The 2-step limit drops the real agent
  to 40%, but the merged version scores 62%: the model simply *imagines* the facts it never had
  the steps to look up.
- Simulated tools cost a bit *more* here: faking free Wikipedia with an LLM costs money. With
  paid or slow tools, they would save.

## W3 · research pipeline (planner → researchers → writer → reviewer)

**Focus: the planner (7 variants)**

| Mini | Cost | Speed | Clear kept | Ranking τ | Reasons π |
|---|---|---|---|---|---|
| **Ceiling (full re-run)** | 0.99× | 0.95× | 75% (6/8) | 0.32 | 0.30 |
| Simulated researcher tools | 1.16× | 1.01× | **100%** (8/8) | 0.63 | 0.26 |
| Stubbed researchers (one imagined call each) | 0.60× | 0.41× | 0% | −0.59 | 0.19 |
| Stubbed + no review + no summary | 0.51× | 0.41× | 50% | 0.05 | 0.22 |
| Pipeline as one call (no review) | 0.50× | 0.14× | 75% | 0.42 | 0.09 |

The planner's effect acts through what gets searched. Faking the *tools* keeps it. Faking the
*researchers* erases it. Simulated tools even matched the full workflow better than its own
re-run did, but with only 8 clear pairs that gap is noise: read it as "as good as the ceiling".

**Focus: the writer (7 variants)**

| Mini | Cost | Speed | Clear kept | Ranking τ |
|---|---|---|---|---|
| **Ceiling (full re-run)** | 1.01× | 1.44× | **40%** | **−0.05** |
| Replay planner + research | 0.21× | 0.15× | 0% | −0.47 |
| Replay + stop before review | 0.13× | 0.05× | 20% | −0.50 |

Here the full workflow cannot reproduce *its own* writer ranking. Its 5 "clear" pairs are mostly
noise (2 of 5 survive a re-run). The writer variants truly differ very little: even "ignore the
notes" scores 0.81 against the base's 0.82. Replay gives every variant the same research, so it
shows that (all variants 0.82–0.85). **Lesson: without a noise ceiling, you would reject the mini.
With it, the test is inconclusive: the full evaluation cannot settle these decisions.**

## W2 · τ-bench customer service (8 core variants)

| Mini | Cost | Speed | Clear kept | Broken caught | Ranking τ |
|---|---|---|---|---|---|
| Cheaper simulated customer | 1.01× | 1.46× | **100%** (13/13) | 1/2 | 0.79 |
| **Simulated shop tools (pure)** | 0.88× | 1.23× | 0% | 0/2 | – (all tied) |
| **Whole conversation as one call** | 0.23× | 0.13× | 8% | 0/2 | −0.55 |

As one call, the model invents IDs (`yusuf_rossi_123`, `item_kb_02`). Its "actions" fail on the real
database, so every variant scores 7.5–10%: just the tasks that need no changes.

Simulated shop tools fail the same way, for a different reason. The simulator cannot see the
database: it returned a real customer ID in only 22 of 320 runs (real tools: 308 of 320). It says
customers are "not found", or invents IDs. 260 of 320 runs end with a hand-over to a human, against
63 of 320 in the full workflow. Every variant scores 7.5%. A grounded simulator (recordings, or read access to the database) may fix this;
the budget did not allow that test.

## Fix transfer (W1)

Claude wrote 3 fixes from each source's failures (20 dev questions), without knowing the source.
All fixes were scored on the full workflow (80 test questions).

| Fixes written from | Mean change on the full workflow | Helped |
|---|---|---|
| Full workflow's failures | +2.9 points | 2 of 3 |
| Full workflow's failures, second set* | +1.3 points | 2 of 3 |
| Simulated-tools mini's failures | +0.4 points | 2 of 3 |
| Merged-call mini's failures | −0.8 points | 0 of 3 |

\* The first "simulated tools" arm replayed the full run for the unchanged base variant, so its
fixes came from full-workflow evidence. It was redone with fresh agent calls (the third row).

Two fix sets from the *same* evidence differ by 1.6 points, so this test cannot rank the sources.
No single fix moved the score by more than two standard errors.

## Cross-family check (W1: OpenAI run read as a mini of the Gemini run)

Same prompts, tools and tasks, different model family: 93% of clear decisions kept (13 of 14),
ranking τ 0.27. The failure *reasons* differ a lot (top reason matched for 15% of variants):
different models fail differently.

---

## Rules that held up

| Rule | Evidence |
|---|---|
| Replay what didn't change | Identical inputs → identical outputs. Cheapest valid mini. |
| Fake tools, not the agent's thinking | Simulated tools kept decisions; merged calls missed all 4 broken variants; stubs lost the planner. |
| Ground fakes in recordings | In W1, cache-first kept more decisions (95% vs 90%) and closer reasons (π 0.41 vs 0.27) than pure, at a higher cost (1.23× vs 1.05×). |
| Don't fake hidden state from scratch | τ-bench: one-call mini invented IDs; pure simulated tools rarely found real customers. Both: every variant 7.5–10%. |
| Always measure the noise ceiling | W3 writer: the full eval could not settle its own decisions, so the "invalid" verdict on replay could not be trusted. |

## Caveats

- Small test sets (40–80 tasks). Most variant differences are within noise.
- Most clear decisions involve a broken variant (W1 17/20, W2 13/13, W3 planner 6/8).
- One model family per workflow (W1 also on OpenAI).
- The judge is Claude, not people. Its reasons come from a fixed list per workflow.
- No noise ceiling for τ-bench, and no grounded tool simulator there (budget).
- Tools here are free, which understates the savings of simulation.
