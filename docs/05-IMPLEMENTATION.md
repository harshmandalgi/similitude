# 05 · Implementation: how the code works

Status 14 Oct 2026: library + 3 workflows built; ground truth running on Gemini.

---

## The one idea behind the code (4W1H)

| | |
|---|---|
| **What** | Every LLM call and tool call of a workflow goes through one object, the **Runtime**. |
| **Why** | A shortcut (replay, fake tool, merged calls…) can then be switched on without touching the workflow's code. |
| **When** | On every call, in every run. |
| **Where** | [runtime.py](../src/similitude/runtime.py). A **Recipe** ([reduce.py](../src/similitude/reduce.py)) says which shortcuts are on. |
| **How** | The workflow calls `rt.llm(...)`, `rt.tool(...)` or `rt.agent(...)`. The Runtime checks the recipe: replay from a recording, fake with an LLM, merge into one call, or run for real. Then it writes what happened into a **Trace**. |

---

## Map: idea → code

| Idea (docs/02-IDEAS.md) | Code |
|---|---|
| A1 prefix replay, A3 paired runs | `Recipe(llm_replay=True)`: identical LLM calls are answered from the base's recordings or from a pool shared by all variants |
| A2 tool cache | `Recipe(tool_cache=True)` |
| B1 slice | `Recipe(skip={...})` + `rt.skipped(node)` in the workflow |
| B2 cap loops | `Recipe(max_steps=...)` |
| B3 cheaper model off-focus | `Recipe(off_focus_model=..., focus=...)` |
| B4 fewer tasks | `Recipe(task_fraction=...)` |
| C1 simulated tools (pure / grounded / cache-first) | `Recipe(tool_sim=...)`, [simulate.py](../src/similitude/simulate.py) |
| C1 guard: error injection | `Recipe(error_injection=True)` |
| C2 call fusion (one agent loop → one call) | `Recipe(fuse={node})`, [fuse.py](../src/similitude/fuse.py) |
| C2 at workflow level (whole pipeline → one call) | `Recipe(fuse_all=True)` |
| C3 prompt shrinking | `Recipe(shrink={node})` + `rt.system_prompt(node, text)` |
| C4 sub-agent stub | `Recipe(fuse={"researcher"})` |
| C5 early stop | `Recipe(stop_after=node)` |
| C6 short tool outputs | `Recipe(obs_chars=...)` |
| Validity metrics | [validate.py](../src/similitude/validate.py): decision accuracy, Kendall τ, MMRV, mutants caught, reason agreement |
| Blind judge (score + reason) | [judge.py](../src/similitude/judge.py), Claude Code via [claude_code.py](../src/similitude/claude_code.py) |

---

## The three workflows

| | W1 `wikiqa` | W2 `tau` | W3 `research` |
|---|---|---|---|
| **Shape** | One tool-calling agent | Agent + simulated customer | 5-role pipeline |
| **Tools** | Live Wikipedia (search, read) | 16 shop tools over a database | Live Wikipedia |
| **Tasks** | 80 HotpotQA questions | 40 τ-bench retail tasks | 80 FRAMES questions (2–3 pages) |
| **Score** | Correct answer (rule, else Claude judge) | τ-bench's own check (database + facts told) | Correct answer (rule, else Claude judge) |
| **Variants** | 18: base, 6 edits, 9 mutants, 2 models | 11: base, 4 edits, 4 mutants, 2 models | 13: base + writer group + planner group |
| **Focus** | the agent | the agent | the writer, or the planner |

Edits were written by Claude Code (synthetic variants). Mutants are hand-written breakages.

---

## Models and money

- **Models** (Gemini on Vertex AI): `gemini-3.5-flash-lite` everywhere by default;
  `gemini-3.1-flash-lite` as the cheap model and the tool simulator; `gemini-3.8-flash` for the
  "stronger model" variants.
- **Judge, variant writer, fix writer:** Claude Code, blind and with no tools: Sonnet 5.5
  judges, Opus 5.5 writes the variants and fixes.
- **Spending cap:** set with `SIMILITUDE_CAP_USD` (the study used $75), enforced before every call by a ledger shared across processes
  ([llm.py](../src/similitude/llm.py)). OpenAI spend before the switch: $2.30, kept separately.
- **Bonus data:** the first W1 ground truth ran on OpenAI (gpt-5.4-nano). Kept as `wikiqa-openai`,
  a second model family for robustness checks.

### Two things worth knowing (found while building)

1. **Faking a free tool can cost more than calling it.** Wikipedia is free and fast. An LLM that
   fakes a Wikipedia page writes ~750 output tokens. So for W1, simulated tools *raise* the bill.
   Tool simulation pays off only when real tools are slow, paid, or unsafe.
2. **τ-bench scores the database, which fake tools never change.** Fix: score every run by
   replaying the agent's *write* calls on a fresh real database. Same result as τ-bench for real
   runs; also works for minis.

---

## How to run

```bash
cd similitude
export SIMILITUDE_CAP_USD=5
uv run python scripts/run.py <wikiqa|research|tau> full      # ground truth
uv run python scripts/run.py <workflow> mini                 # all minis for that workflow
uv run python scripts/run.py <workflow> judge                # Claude judges new runs
uv run python scripts/run.py <workflow> analyse              # -> results/<workflow>.md
uv run python scripts/fix_transfer.py evidence|write|run|analyse <mini> ...
uv run pytest                                                # offline tests, no spend
# the paper's numbers, figures and tables (offline, from runs/):
uv run python scripts/summary.py && uv run python scripts/tables.py && uv run python scripts/mini_figures.py
```

Runs are resumable: a run whose trace exists is skipped.
