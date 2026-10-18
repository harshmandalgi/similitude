# 04 · Paper outline (draft)

> Planning notes from 14 Oct 2026, kept as a record. The final setup and results are in
> [05-IMPLEMENTATION.md](05-IMPLEMENTATION.md), [06-RESULTS.md](06-RESULTS.md) and the paper.

## Working title
**Similitude: Cheap Miniature Workflows that Keep Agent Evaluations Valid**

## Abstract (draft, ~120 words)
Evaluating an agentic workflow end-to-end is slow and expensive, so teams test few changes and trust
noisy results. We ask whether a workflow can be *reduced* into a cheap miniature whose evaluation leads
to the same decisions as the full workflow. We define validity by decisions, not raw scores: same
winner, same ranking, same failure reasons, and fixes that transfer back. We propose a set of reduction
operators (replaying unchanged steps, simulating tools, fusing calls, slicing branches, early judging)
and six rules for choosing them. A mutant-based check estimates a miniature's validity before it is
trusted. On [N] workflows, miniatures cost [x]% of a full run and agree with full-run decisions [y]% of
the time. We release the library.

## Positioning (one sentence vs prior work)
Prior work fakes **one part** (tools, users, environments), swaps in a **cheaper model**, or shrinks the
**test set**. We shrink a **whole existing workflow** with several operators, and we are the first to
test whether **decisions, judge reasons and fixes** carry back to the full workflow.
(Details: [01-PRIOR-WORK.md](01-PRIOR-WORK.md).)

## Contributions (what is new)
1. **Problem:** "evaluation-preserving workflow reduction", with decision-based validity definitions.
2. **Toolbox:** reduction operators, sorted by validity risk, and six rules for picking them.
3. **Check:** a cheap mutant-based test that predicts whether a mini can be trusted.
4. **Study:** which operators keep validity, across several workflows and many variants.
5. **Library:** open-source code to trace, reduce, and validate workflows.

## Sections
1. **Introduction:** the cost problem; the wind-tunnel analogy; contributions.
2. **Related work:** cheap eval by smaller datasets; simulated tools and environments; compound-AI
   optimizers; multi-fidelity optimization; similitude and surrogate models. (Filled from
   [01-PRIOR-WORK.md](01-PRIOR-WORK.md).)
3. **Problem setup:** workflow as a graph; focus; decisions; validity metrics.
4. **Method:** operators; the six rules; mutant check; correction trick.
5. **Experiments:** workflows, variants, metrics, results per RQ.
6. **Analysis:** when minis lie; "similitude numbers".
7. **Limits and ethics:** sim-to-real gap; overfitting to simulators.
8. **Conclusion.**

## Key figures to plan for
- Cost vs validity scatter: each dot is a mini; the good ones sit top-left.
- Operator ablation table: validity and cost per operator.
- Full-vs-mini rank plot for the variants of one workflow.
