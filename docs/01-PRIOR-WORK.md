# 01 · Prior work: is this idea already out there?

Searched 14 Oct 2026. Every link was opened and checked. The closest papers were re-checked by hand.

## Short answer

**No one does the full idea. Many pieces exist.**

| Already done by others | Not done yet (our gap) |
|---|---|
| Make the **test set** smaller and still rank models correctly | Take an **existing workflow** and shrink the **system** with several operators |
| Let an LLM **fake tools, users, or whole environments** | Check that **rankings / A-vs-B decisions** on the mini match the full workflow (for simulated tools) |
| Search prompts on a **cheap model**, then move the prompt to a strong one | Check that the **judge's reasons** for failure match |
| **Replay** recorded steps in regression tests | Check that **fixes** found on the mini improve the full workflow |
| **Stop runs early** and predict the outcome | **Rules** for deciding which parts to shrink, and how |
| **Merge** a multi-agent workflow into one agent, as a permanent replacement | Use a merged version as a **test stand-in**, then carry changes back |
| **Predict** a workflow's score with a trained model (no run) | A cheap version you can **run and debug**, with traces and reasons |

**Warning:** this area is moving fast. Several close papers came out in Aug–Sep 2026. We should
move quickly and search again before we submit.

---

## The five closest works

| Work | What it does | How we differ |
|---|---|---|
| [Optimize Cheap, Deploy Strong](https://arxiv.org/abs/2608.10694) (Aug 2026) | Runs prompt search on the cheapest model, then moves the prompt to a strong model. 5.6–14× cheaper, same or better result. | Only swaps the **model**. Tools, calls and prompts stay the same. Measures gain transfer, not rankings or reasons. |
| [ToolEmu](https://arxiv.org/abs/2309.15817) (2023) | An LLM fakes the tools; a judge flags risky actions. 68.8% of flagged failures were real. | Only fakes tools. Never checks that scores or rankings match real tools. |
| [OccuBench](https://arxiv.org/abs/2604.10866) (Apr 2026) | A benchmark run fully on LLM-faked environments. | Builds a **new benchmark**; does not shrink an existing workflow. Shows the choice of simulator model **reorders rankings**. A risk for us. |
| [Chronicle](https://arxiv.org/abs/2609.20625) (Sep 2026) | Records an agent run; replays some steps, runs the rest live, for regression tests. | Very close to our "prefix replay". But its goal is catching bugs, not predicting scores. No live-vs-replay agreement reported. |
| [Screen Before You Serve](https://arxiv.org/abs/2609.30137) (Nubank, Sep 2026) | Simulated customers + simulated tool outputs screen agent versions before release. | Real-world proof that it can work: sim and production scores "highly correlated". But only 4 versions, no number given, no method for building the mini. |

---

## Map of related work

### 1. Smaller test sets (shrink the dataset, not the system)
Pick a few test cases that predict the full score.

- [tinyBenchmarks](https://arxiv.org/abs/2402.14992), [Anchor Points](https://arxiv.org/abs/2309.08638), [metabench](https://arxiv.org/abs/2407.12844) (Spearman 0.94), [Flash-HELM](https://arxiv.org/abs/2308.11696) (~100× cheaper)
- For agents: [Efficient Benchmarking of AI Agents](https://arxiv.org/abs/2603.23749) (keep tasks with 30–70% pass rate; Spearman 0.93), [PACE](https://arxiv.org/abs/2607.02032), [DualViewEval](https://arxiv.org/abs/2609.18909), [She & Lin 2026](https://arxiv.org/abs/2609.21267)

**For us:** a different axis. It **combines** with our idea: smaller system × fewer cases.

### 2. LLM-faked tools, users and environments
- Tools: [ToolEmu](https://arxiv.org/abs/2309.15817), [StableToolBench](https://arxiv.org/abs/2403.07714), [MirrorAPI](https://arxiv.org/abs/2503.20527), [MCP-Persona](https://arxiv.org/abs/2606.02470), [Proxy State-Based Eval](https://arxiv.org/abs/2602.16246)
- Users: [τ-bench](https://arxiv.org/abs/2406.12045), [τ²-bench](https://arxiv.org/abs/2506.07982), [SimulatorArena](https://arxiv.org/abs/2510.05444) (sim vs human rating: Spearman ≈ 0.7)
- Training environments (not eval): [Simia](https://arxiv.org/abs/2511.01824), [UI-Simulator](https://arxiv.org/abs/2510.14969), [DreamGym](https://arxiv.org/abs/2511.03773), [WebDreamer](https://arxiv.org/abs/2411.06559)

**Most useful finding:** faking a tool from its docs alone is weak. Building the fake from **recorded
real calls** is much better: success/failure agreement rose from F1 53% to 94% (MCP-Persona).

### 3. Warnings: when fakes lie
| Paper | Finding |
|---|---|
| [Lost in Simulation](https://arxiv.org/abs/2601.17087) | Swapping which LLM plays the user moves agent success by up to 9 points. |
| [Mind the Sim2Real Gap](https://arxiv.org/abs/2603.11245) | Simulated users are an "easy mode". They make agents look better than with real humans. |
| [When Simulation Lies](https://arxiv.org/abs/2605.11928) | Noise in what the agent sees costs < 5%. Changing how tools *behave* costs ~30%. |
| [EnvSimBench](https://arxiv.org/abs/2605.07247) | LLM simulators fail when several things change at once. |
| [OccuBench](https://arxiv.org/abs/2604.10866) | A strong agent is not always a strong simulator. |

These give us a ready-made **risk map**: what is safe to fake and what is not.

### 4. Cheap version of the system, results carried back
- [Optimize Cheap, Deploy Strong](https://arxiv.org/abs/2608.10694): cheap model for search, strong model for use.
- [DataDecide](https://arxiv.org/abs/2504.11393): small models pick the right pretraining data ~80% of the time.
- [RegMix](https://arxiv.org/abs/2407.01492): tiny proxy models rank data mixtures.
- [SIMPLER](https://simpler-env.github.io/): robot policies in simulation vs real robots. Introduces the **MMRV** metric (see below).
- [AgentSquare](https://arxiv.org/abs/2410.06153): an LLM predicts an agent design's score to skip weak designs.

### 5. Replay and early stopping
- [Chronicle](https://arxiv.org/abs/2609.20625): cut-point replay (see above).
- [EarlyEval](https://arxiv.org/abs/2609.02783): stops agent runs early and predicts the result. 89–97% accurate; saves up to 44% of input tokens.
- [LangSmith pytest cache](https://docs.langchain.com/langsmith/pytest): records and replays LLM/API calls in tests.

### 6. Compound-AI optimizers
Tools that tune prompts and structure of multi-step workflows. They all pay for many full runs.

| Work | What it does | Relevance to us |
|---|---|---|
| [DSPy](https://arxiv.org/abs/2310.03714) + [MIPROv2](https://arxiv.org/abs/2406.11695), [TextGrad](https://arxiv.org/abs/2406.07496), [Trace](https://arxiv.org/abs/2406.16218) | Tune prompts in multi-step programs from scores or text feedback | They run the **full** pipeline on smaller batches. A mini workflow could make each of their steps cheaper. |
| [GEPA](https://arxiv.org/abs/2507.19457), [AFlow](https://arxiv.org/abs/2410.10762), [ADAS](https://arxiv.org/abs/2408.08435) | Search for better prompts/workflows on a cheap model, then run on a strong one | Only "cheap model → strong model" transfer numbers in the field. It **usually** works, but sometimes fails (an AFlow workflow searched with one model dropped on another). |
| [Optimas](https://arxiv.org/abs/2507.03041) (2025) | Gives each component a local reward that stays in line with the end-to-end score | Closest in spirit: a cheap local signal that must agree with the full one. But its stand-in is a learned reward model, not a runnable mini workflow. |
| [FLORA-Bench](https://arxiv.org/abs/2503.11301), [Agentic Predictor](https://arxiv.org/abs/2505.19764), [GLOW](https://arxiv.org/abs/2512.15751), [AgentSquare](https://arxiv.org/abs/2410.06153) | Trained models guess a workflow's score without running it | Very cheap, but give **no traces and no reasons**. A mini workflow gives both. |

**Evidence for and against merging calls (our operator C2):**
- **For:** [OneFlow](https://arxiv.org/abs/2601.12307) (Jan 2026). A single agent in one long chat matches multi-agent workflows on 7 benchmarks, when all agents use the same model. Breaks when agents use different models.
- **Against:** [Prompt chaining vs one prompt](https://arxiv.org/abs/2406.00507) (2024). A merged prompt "fakes" the refine step, so the multi-call chain wins.

**Evidence on shrinking prompts (C3):** [LLMLingua-2](https://arxiv.org/abs/2403.12968) keeps task scores but never checks
behavior. [A 2026 study](https://arxiv.org/abs/2603.23527) found compressed prompts made DeepSeek's outputs up to ~56× longer. Behavior is **not** preserved by default.

**A useful hint:** [Prompt Optimization Is a Coin Flip](https://arxiv.org/abs/2604.14585) (2026) found that prompts of different agents in a workflow barely interact. If that holds, we can shrink around one component at a time.

### 7. Ideas from engineering we can borrow
| Idea | What it is | How it maps to us |
|---|---|---|
| **Similitude** ([Buckingham 1914](https://doi.org/10.1103/PhysRev.4.345)) | A wind-tunnel model is valid if a few key ratios match the real plane. | Find the few workflow properties that must match for the eval to stay valid. |
| **Multi-fidelity methods** ([Peherstorfer et al. 2018](https://arxiv.org/abs/1806.10761), [Hyperband](https://jmlr.org/papers/v18/16-558.html)) | Use many cheap runs plus a few expensive ones. | Mini = cheap run; full = expensive check. |
| **Test-case reduction** ([delta debugging](https://www.st.cs.uni-saarland.de/papers/tse2002/), [Shrink Ray](https://github.com/DRMacIver/shrinkray)) | Shrink a failing input while a check still passes. | Shrink the workflow while "the eval still transfers" passes. **Closest analogy.** |
| **Program slicing** | Keep only code that affects one output. | Keep only steps that affect what the judge scores. |
| **Mocks + contract tests** | Fake a dependency; check the fake against the real thing. | Simulated tools, checked against recorded real outputs. |
| **Mutation testing** | Break code on purpose; check tests notice. | Break the focus on purpose; check the mini notices. |
| **Goodhart's law** ([Manheim & Garrabrant](https://arxiv.org/abs/1803.04585)) | Optimizing a proxy can break it. | Tuning on the mini can overfit to the mini. |

---

## Validity metrics we can borrow

| Metric | Plain meaning | Used by |
|---|---|---|
| **Pairwise decision accuracy** | % of A-vs-B pairs where cheap and full pick the same winner | DataDecide, PACE |
| **Spearman ρ / Kendall τ** | Do cheap and full rank things in the same order? (1 = same) | metabench, agent benchmarking papers |
| **MMRV** | Ranking mistakes, weighted by how big the real gap was. Small mistakes between near-ties count little. | SIMPLER |
| **MAE (points)** | Average gap between cheap and full scores | metabench, PACE |
| **Transfer gap** | Gain on full minus gain on cheap | Optimize Cheap, Deploy Strong |
| **Scott's π / Cohen's κ** | Agreement between two labelers, corrected for luck | [Judge agreement paper](https://arxiv.org/abs/2406.12624) |

**New metrics we would add:** *reasoning agreement* (same failure reasons) and *fix transfer rate*.
No paper we found measures either.

---

## Name check
| Name | Status |
|---|---|
| **Similitude** | **Free.** No LLM/agent tool or paper uses it. |
| ScaleModel, AgentTwin | Free |
| Wind Tunnel | Partly taken (two tiny 0-star repos for agent testing) |
| MiniFlow | Taken (a no-code AI workflow product) |
| Bonsai, Shrinkray, Proxy Agent | Taken |
