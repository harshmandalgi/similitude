# Similitude

**Cheap mini versions of agent workflows that keep your evals valid.**

Status (14 Oct 2026): library + 3 workflows built; experiments running on Gemini (Vertex), $40 cap.
Paper draft started in [paper/](paper/). Private repo: github.com/harshmandalgi/similitude.

---

## The project in 4W1H

| | |
|---|---|
| **What** | A method + Python library that shrinks an agent workflow into a cheap **mini workflow**. Evals on the mini lead to the **same decisions** as evals on the full workflow. Plus a research paper that tests this. |
| **Why** | Running a full agent workflow for every eval is slow and costly. So teams test few changes. A mini that is 10–100× cheaper lets you test many. |
| **When** | In the inner loop: trying prompt edits, model swaps, tool changes. The full workflow is still used for the final check. |
| **Where** | Any multi-step LLM workflow with tools: agents, multi-agent systems, pipelines. |
| **How** | Record full runs → shrink with a set of operators (replay, simulated tools, merged calls, …) → check the mini on a small test set → iterate on the mini → confirm on the full. |

## Why the name

In engineering, **similitude** is the theory of when a small model (e.g. a plane in a wind tunnel) gives
results that are valid for the real thing. That is exactly our question, for agent workflows.
The name is free: no LLM tool or paper uses it.
Other options if you prefer: *ScaleModel*, *AgentTwin*.

## Is this already out there? (short answer)

- **No one does the full idea.** Pieces exist: smaller test sets, LLM-faked tools, cheap-model prompt
  search, replaying recorded steps.
- **Our gap:** shrink a whole existing workflow, then check that rankings, the judge's reasons, and
  fixes carry back. No paper measures the last two.
- **But the field is moving fast.** Close papers came out in Aug–Sep 2026. Speed matters.

Details: [docs/01-PRIOR-WORK.md](docs/01-PRIOR-WORK.md).

## Read in this order

| Doc | What's in it | Time |
|---|---|---|
| [01-PRIOR-WORK.md](docs/01-PRIOR-WORK.md) | What exists, the 5 closest papers, our gap | 8 min |
| [02-IDEAS.md](docs/02-IDEAS.md) | How to build a mini: operators, 6 rules, validity checks, risks | 12 min |
| [03-PLAN.md](docs/03-PLAN.md) | Research questions, experiments, milestones, **decisions I need from you** | 5 min |
| [04-PAPER-OUTLINE.md](docs/04-PAPER-OUTLINE.md) | Title, draft abstract, contributions, sections | 3 min |
| [05-IMPLEMENTATION.md](docs/05-IMPLEMENTATION.md) | How the code works, the 3 workflows, models, money, how to run | 6 min |
| results/ | Tables per workflow, written by `scripts/run.py <workflow> analyse` | when ready |

## Words used in these docs

| Word | Meaning |
|---|---|
| **Workflow** | Your agent system: LLM calls + tool calls, in some order. |
| **Full** | The real workflow, unchanged. |
| **Mini** | The cheap, shrunk copy. |
| **Focus** | The part you are changing and testing. Stays real in the mini. |
| **Operator** | One way to shrink (e.g. "replace this tool with an LLM fake"). |
| **Variant** | One version of the focus (e.g. prompt A vs prompt B). |
| **Valid** | The mini leads to the same decision as the full workflow would. |
| **Judge** | An LLM (or rule) that scores a run and explains why. |
