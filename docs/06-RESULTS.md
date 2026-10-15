# 06 · Results: which minis keep the evaluation valid?

Data from 14–15 Oct 2026. Gemini on Vertex; Claude Code (Sonnet 5.5) as the blind judge.
Full tables: [results/summary.md](../results/summary.md). Spend: $72.13 of the $75 Gemini cap,
plus $2.30 on OpenAI (W1 cross-family run).

---

## Short answer

1. **Your idea 1, simulated tools, works, if the simulator can know the answer.** It kept
   90–100% of the clear decisions in W1 and in W3's planner tests. It works best when grounded in
   recorded real outputs ("cache first"). On τ-bench it kept **none**: the tools read a private
   shop database, which the simulator cannot see.
2. **Your idea 2, merging calls with imagined tool results, fails** whenever the change you test
   acts *through* the tools: step limits, search strategy, planning. It kept ~50% of clear
   decisions, which is a coin flip. On τ-bench it breaks completely: the model invents customer and
   order IDs, so nothing it "does" can be checked against the real database.
3. **Replaying the unchanged part of the workflow is cheap (0.2× cost) and safe**, because the
   replayed calls have identical inputs. It can still disagree with a full evaluation that is
   itself mostly noise (W3 writer).
4. **Fewer tasks keeps most clear decisions at 0.2× cost** (85% in W1). It combines with any mini.
5. **Most prompt changes barely matter.** In every workflow, most variants sat within noise of the
   base. Only big breakages (step caps, skipping confirmation) were clear. So the honest test of a
   mini is: does it settle the *same few* decisions the full evaluation can settle?

---

## How to read the tables

**Noise ceiling (4W1H)**

| | |
|---|---|
| **What** | The full workflow run a second time, with fresh samples. |
| **Why** | Agents are random, and test sets are small. The full evaluation does not even agree with itself. No mini can beat that. |
| **When** | Read every mini against it, not against perfection. |
| **Where** | The `full-rerun` / `W-rerun` / `P-rerun` rows. |
| **How** | Compute the same agreement numbers between the full workflow and its own re-run. |

**Columns**
- **Cost / speed**: the mini's cost or median time per run, as a share of the full workflow's.
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
| **Merged calls** | 0.28× | 0.21× | 50% | 0/2 | 0.08 | 0.17 |
| Merged calls + fewer tasks | 0.06× | 0.20× | 45% | 0/2 | 0.25 | 0.13 |

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
| Stubbed researchers (one imagined call each) | 0.60× | 0.41× | 0% | −0.73 | 0.24 |
| Stubbed + no review + no summary | 0.51× | 0.41× | 62% | 0.11 | 0.14 |
| Whole pipeline as one call | 0.50× | 0.14× | 50% | 0.05 | 0.06 |

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
shows that (all variants 0.82–0.85). **Lesson: without a noise ceiling, you would wrongly blame
the mini.**

## W2 · τ-bench customer service (8 core variants)

| Mini | Cost | Speed | Clear kept | Broken caught | Ranking τ |
|---|---|---|---|---|---|
| Cheaper simulated customer | 1.01× | 1.46× | 79% | 1/2 | 0.73 |
| **Simulated shop tools (pure)** | 0.88× | 1.23× | 0% | 0/2 | – (all tied) |
| **Whole conversation as one call** | 0.23× | 0.13× | 7% | 0/2 | −0.56 |

As one call, the model invents IDs (`yusuf_rossi_123`, `item_kb_02`). Its "actions" fail on the real
database, so every variant scores 7%: just the tasks that need no changes.

Simulated shop tools fail the same way, for a different reason. The simulator cannot see the
database, so it says real customers are "not found". The agent cannot verify the customer and
hands over to a human: 260 of 320 runs, against 63 of 320 in the full workflow. Every variant
again scores 7%. A grounded simulator (recordings, or read access to the database) may fix this;
the budget did not allow that test.

## Fix transfer (W1)

Claude wrote 3 fixes from each source's failures (20 dev questions), without knowing the source.
All 9 were scored on the full workflow (80 test questions).

| Fixes written from | Mean change on the full workflow | Helped |
|---|---|---|
| Full workflow's failures | +2.9 points | 2 of 3 |
| Simulated-tools mini's failures (cache first) | +1.3 points | 2 of 3 |
| Merged-call mini's failures | −0.8 points | 0 of 3 |

Same direction as everything else, but small and within noise. Treat it as a hint.

## Cross-family check (W1: OpenAI run read as a mini of the Gemini run)

Same prompts, tools and tasks, different model family: 93% of clear decisions kept (13 of 14),
ranking τ 0.29. The failure *reasons* differ a lot (top reason matched for 15% of variants):
different models fail differently.

---

## Rules that held up

| Rule | Evidence |
|---|---|
| Replay what didn't change | Identical inputs → identical outputs. Cheapest valid mini. |
| Fake tools, not the agent's thinking | Simulated tools kept decisions; merged/stubbed calls didn't. |
| Ground fakes in recordings | Cache-first beat pure on every column in W1. |
| Don't fake stateful worlds from scratch | τ-bench: one-call mini invented IDs; pure simulated tools could not find real customers. Both: every variant 7%. |
| Always measure the noise ceiling | W3 writer: the "invalid" mini was really a noisy full eval. |

## Caveats

- Small test sets (40–80 tasks). Most variant differences are within noise.
- One model family per workflow (W1 also on OpenAI).
- The judge is Claude, not people. Its reasons come from a fixed list per workflow.
- No noise ceiling for τ-bench, and no grounded tool simulator there (budget).
- Tools here are free, which understates the savings of simulation.
