# 02 · Ideas: how to build a mini workflow you can trust

Complex ideas are explained with **4W1H**: What · Why · When · Where · How.

---

## 1. The core idea

| | |
|---|---|
| **What** | A *mini workflow* is a cheaper copy of your agent workflow. It is built to answer **one question**, e.g. "Is planner prompt B better than prompt A?" |
| **Why** | Full runs are slow and cost a lot. You want an inner loop that is 10–100× cheaper, so you can try many changes. |
| **When** | While you iterate: prompt edits, model swaps, tool-description edits. **Not** for the final sign-off. |
| **Where** | Around the part you are changing. We call it the **focus**. Keep the focus real. Shrink everything else. |
| **How** | Record a few full runs → apply reduction rules → check the mini on a small test set → iterate on the mini → confirm the winner on the full workflow. |

**Analogy: a wind tunnel.** Engineers test a small model of a plane, not the plane. The small model's
results are valid only if a few key ratios match the real plane. Engineers call this *similitude*.
We want the same thing for agents: a short list of things that must stay the same so the eval stays valid.

---

## 2. Rule zero: "valid for what?"

No mini is valid for everything. First pick the decision the eval must support.

| Decision | Example | What must match | Difficulty |
|---|---|---|---|
| **Compare two** | "Is B better than A?" | Same winner | Easiest |
| **Rank many** | "Which of 10 prompts is best?" | Same order | Medium |
| **Diagnose** | "Why does it fail?" | Same failure reasons from the judge | Medium |
| **Absolute score** | "What is our pass rate?" | Same number | Hardest. Needs a few full runs to correct it |

Tip: aim for the first three. Get the fourth with a correction step (see §6.2).

---

## 3. The reduction toolbox

Each tool ("operator") makes the workflow cheaper in one way. Grouped by how much validity you risk.

### Group A: free wins (no validity loss)

| # | Operator | What it does | Saves |
|---|---|---|---|
| A1 | **Prefix replay** | You changed step 5. Steps 1–4 did not change, so replay them from a recorded run. Only run from step 5 on. | All calls before the focus |
| A2 | **Tool cache** | Same tool input → return the recorded output. No real call. | Tool cost + latency |
| A3 | **Paired runs** | Variants A and B see the *same* tool outputs. Differences now come from the change, not from noise. | Fewer repeat runs needed |
| A4 | **Prompt caching** | Put the fixed part of each prompt first. The provider bills cached tokens cheaply. | LLM cost |

### Group B: small risk (usually safe)

| # | Operator | What it does | Watch out for |
|---|---|---|---|
| B1 | **Slice** | Drop branches whose output never reaches what the judge scores. | Hidden side effects (shared memory, state) |
| B2 | **Cap loops** | Max 2 retries instead of 10. | Variants that only win through retries |
| B3 | **Cheaper model off-focus** | Use a small model for parts you are not changing. | Small model gives different inputs to the focus |
| B4 | **Fewer test cases** | Pick a small, representative set of test inputs. | Combines with everything, but pick cases carefully |

### Group C: real risk (must be checked)

| # | Operator | What it does | Watch out for |
|---|---|---|---|
| C1 | **Simulated tools** *(your idea)* | An LLM pretends to be the tool and writes a believable output. | Too clean: no errors, no timeouts, no messy data |
| C2 | **Call fusion** *(your idea)* | Merge a chain of LLM calls into one call, with imagined tool results in between. | The model invents tool results that make its own plan work |
| C3 | **Prompt shrinking** | Compress long prompts; keep only the parts that matter for this eval. | Behavior quietly changes (one study saw outputs get ~56× longer) |
| C4 | **Sub-agent stub** | Replace a whole sub-agent with one call that copies its typical output (learned from recorded runs). | Misses rare outputs |
| C5 | **Early stop + judge** | After the focus, do not run the rest. A judge scores the middle output (e.g. the plan) and predicts the final result. | Plan looks good but fails when run |
| C6 | **Smaller inputs** | Shorter documents, fewer retrieved chunks. | Changes task difficulty |

### Your two ideas, in more detail

**C1 · Simulated tools (4W1H)**
- **What:** an LLM plays the tool. It gets the tool's description and the call, and returns an output.
- **Why:** real tools can be slow (web, code runs), paid, rate-limited, or have side effects (sending email).
- **When:** the tool is expensive or unsafe to call, and its output is easy to fake well.
- **Where:** off-focus tools first. A tool that the focus reads closely needs a high-quality simulator.
- **How:** three levels, from cheap to faithful:
  1. *Pure sim:* the LLM guesses from the tool description.
  2. *Grounded sim:* the LLM also sees real recorded outputs of that tool as examples.
  3. *Cache first, sim on miss:* replay the real output if we have it; simulate only new calls.
  Add **error injection**: make the simulator fail at the real tool's failure rate.
- **Evidence:** building the fake from recorded real calls beats faking from docs by a lot
  (success/failure agreement F1 53% → 94%, [MCP-Persona](https://arxiv.org/abs/2606.02470)). And getting
  the tool's *behavior* right matters far more than its exact wording: wrong behavior cost agents ~30%,
  noisy wording < 5% ([When Simulation Lies](https://arxiv.org/abs/2605.11928)).

**C2 · Call fusion (4W1H)**
- **What:** one LLM call writes the whole run: thought → tool call → imagined result → next step → answer.
- **Why:** 10 calls become 1. Huge latency and cost savings.
- **When:** you are testing **reasoning and planning** (does it pick the right tools, in a sensible order?).
- **Where:** a chain of steps with no real-world feedback you care about.
- **How:** give the model the full workflow as one prompt. Safer version: **split roles**. One model acts, a
  *different* model imagines the tool results. This stops the actor from writing results that suit itself.
- **Not valid for:** testing how the agent reacts to surprising or broken tool outputs.
- **Evidence:** for: one agent in one long chat can match a same-model multi-agent workflow
  ([OneFlow](https://arxiv.org/abs/2601.12307)). Against: a merged prompt tends to "fake" refine/review
  steps instead of doing them ([2406.00507](https://arxiv.org/abs/2406.00507)). So: merge freely
  between plain steps; keep review/critique steps as separate calls.

---

## 4. The rules: six dimensions that decide what to shrink

For each part of the workflow, ask six questions. They decide which operator to use.

| Dimension | Question | Rule |
|---|---|---|
| **1. Distance** | How far is it from the focus? | Far → shrink hard. Near → keep real. |
| **2. Cost share** | What % of cost/latency does it use? | Shrink the expensive parts first. |
| **3. Determinism** | Same input → same output? | Yes → replay it exactly (Group A). |
| **4. Influence** | Does its output reach what the judge scores? | No → cut it (B1). |
| **5. Fakeability** | How easy is it to fake well? | Calculator: easy. Web search: medium. Database with hidden state: hard → keep real or cache. LLM fakes break when several things change at once ([EnvSimBench](https://arxiv.org/abs/2605.07247)). |
| **6. Feedback** | Does the focus react to its output (e.g. reads errors)? | Yes → the simulator must copy errors and messiness too. Get the *behavior* right before the wording. |

**One-line rule:** *Keep real what you change. Replay what you didn't change. Simulate what you can't
replay. Check before you trust.*

---

## 5. How to know the mini is valid

Run a small **calibration set** on both mini and full. Measure:

| Metric | Plain meaning | Target (first guess) |
|---|---|---|
| **Decision agreement** | % of A-vs-B comparisons where mini and full pick the same winner | ≥ 90% |
| **Rank correlation** (Kendall τ) | Do mini and full order the variants the same way? 1 = same order | ≥ 0.8 |
| **MMRV** | Ranking mistakes, weighted by how big the real gap was. Mixing up two near-equal variants barely counts. (From robotics sim-vs-real work.) | Low |
| **Mutant detection** | We break the focus on purpose. Does the mini's score drop like the full's? | Catches ≥ 90% |
| **Reasoning agreement** | Does the judge name the same failure reasons on mini and full? (Scott's π: agreement corrected for luck.) | π ≥ 0.6 |
| **Fix transfer rate** | Fixes found on the mini, applied to the full: % that improve the full | Headline metric |

The last two are **new**: no paper we found measures them. Rankings usually transfer better than
absolute scores (prior work agrees), so decisions come first.
| **Cost / latency ratio** | Mini cost ÷ full cost | ≤ 0.1 |

**Mutant check (4W1H)**
- **What:** make deliberately worse versions of the focus ("mutants"). Delete a key instruction, swap in a weak model, break a tool description.
- **Why:** if the mini cannot see *planned* breakage, it will not see real changes either.
- **When:** every time you build a new mini, before trusting it.
- **Where:** only on the focus.
- **How:** run mutants on mini and full. Count how many the mini also catches. Borrowed from *mutation testing* in software. ([Chronicle](https://arxiv.org/abs/2609.20625) used mutants the same way for replayed agent tests; a "fake every step" baseline caught none.)

---

## 6. Bigger ideas (paper-worthy)

### 6.1 Multi-fidelity loop
Try 50 variants on the mini. Send the top 5 to a medium version. Send the top 1 to the full workflow.
Cheap filter first, expensive check last. (Same idea as *Hyperband* in hyperparameter tuning.)

### 6.2 Mini as a "correction partner" (control variate)
- **What:** a statistics trick. Run the mini on *all* test cases and the full on *a few*. Use the gap seen on the few to correct the mini's number.
- **Why:** you get an honest absolute score with far fewer full runs.
- **When:** you need the absolute number (decision type 4).
- **Where:** after a mini passes the validity checks.
- **How:** known methods: *control variates*, *prediction-powered inference*, *multi-fidelity Monte Carlo*.

### 6.3 Auto-reducer (like delta debugging)
- **What:** a program that builds the mini for you.
- **Why:** picking operators by hand is slow and error-prone.
- **When:** each time you pick a new focus.
- **Where:** runs on recorded full traces plus a small calibration set.
- **How:** borrow from *test-case reduction* (delta debugging, [Shrink Ray](https://github.com/DRMacIver/shrinkray)).
  Those tools shrink a failing input step by step, and keep each step only if "the bug still shows".
  We shrink the workflow step by step, and keep each step only if "the mini still passes the validity
  checks". Output: a "reduction recipe" per focus.

### 6.4 "Similitude numbers" for agents (most novel)
- **What:** a few measurable properties that, if they match between mini and full, predict that the mini is valid. Like the Reynolds number for wind tunnels.
- **Why:** then you can predict validity **without** running the full workflow.
- **Candidates:** context length when the focus runs · tool error rate seen by the focus · number of steps · how informative tool outputs are · how often the focus's choice changes the next step.
- **How:** measure them on many (mini, full) pairs. See which ones predict validity.

---

## 7. How a mini can lie (and the guards)

| Failure | Example | Guard |
|---|---|---|
| **Too clean** | Simulated tools never fail, so every prompt looks great | Error injection; grounded sim |
| **Self-serving imagination** | In a fused call, the model invents perfect search results | Split roles: separate simulator model |
| **Overfitting to the sim** | You tune prompts to the simulator's quirks | Regular full-run audits |
| **Simulator choice changes the answer** | A different simulator model reorders the rankings ([OccuBench](https://arxiv.org/abs/2604.10866)) | Same simulator for all variants; spot-check with a second simulator model |
| **Easy mode** | Fake users/tools are too cooperative, so everything looks better ([Sim2Real Gap](https://arxiv.org/abs/2603.11245)) | Trust differences between variants, not absolute scores |
| **Quiet behavior shift** | Shrunk prompt drops a rule the model needed | Mutant check |
| **Missing interactions** | Long real contexts, rate limits, latency effects | Keep context length similar (a similitude number) |
