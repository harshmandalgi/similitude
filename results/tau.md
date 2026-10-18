# tau / focus: agent: validity of each mini

Runs used: 1520; skipped: 0 with errors, 0 not yet judged.

## Accuracy per variant (share of tasks correct)

| variant | kind | full | B3-cheap-user | C1-pure | C2-all |
|---|---|---|---|---|---|
| base | base | 0.65±0.08 (n=40) | 0.50±0.08 (n=40) | 0.07±0.04 (n=40) | 0.07±0.04 (n=40) |
| e-step-procedure | edit | 0.60±0.08 (n=40) | 0.55±0.08 (n=40) | 0.07±0.04 (n=40) | 0.07±0.04 (n=40) |
| e-verify-item-ids | edit | 0.62±0.08 (n=40) | 0.53±0.08 (n=40) | 0.07±0.04 (n=40) | 0.07±0.04 (n=40) |
| e-summarize-first | edit | 0.72±0.07 (n=40) | – | – | 0.07±0.04 (n=40) |
| e-multi-request-handling | edit | 0.62±0.08 (n=40) | – | – | 0.07±0.04 (n=40) |
| m-no-auth | mutant | 0.57±0.08 (n=40) | 0.42±0.08 (n=40) | 0.07±0.04 (n=40) | 0.10±0.05 (n=40) |
| m-no-confirm | mutant | 0.33±0.07 (n=40) | 0.40±0.08 (n=40) | 0.07±0.04 (n=40) | 0.07±0.04 (n=40) |
| m-half-policy | mutant | 0.47±0.08 (n=40) | – | – | 0.07±0.04 (n=40) |
| m-8-steps | mutant | 0.07±0.04 (n=40) | 0.10±0.05 (n=40) | 0.07±0.04 (n=40) | 0.10±0.05 (n=40) |
| model-gemini-3.8-flash | model | 0.72±0.07 (n=40) | 0.62±0.08 (n=40) | 0.07±0.04 (n=40) | 0.07±0.04 (n=40) |
| model-gemini-3.1-flash-lite | model | 0.70±0.07 (n=40) | 0.60±0.08 (n=40) | 0.07±0.04 (n=40) | 0.07±0.04 (n=40) |

## Does each mini make the same decisions as the full workflow?

| recipe | cost × | latency × (median) | Kendall τ | Spearman ρ | pair acc | pair acc (clear) | clear pairs | MMRV | same best | MAE | mutants: same dir | mutants: caught | reason JS | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B3-cheap-user | 1.01 | 1.46 | 0.79 | 0.90 | 0.89 | 1.00 | 13 | 0.02 | yes | 0.09 | 1.00 | 0.50 | 0.33 | 0.50 | 0.50 |
| C1-pure | 0.88 | 1.23 | – | – | 0.00 | 0.00 | 13 | 0.19 | no | 0.46 | 0.00 | 0.00 | 0.79 | 0.00 | -0.15 |
| C2-all | 0.23 | 0.13 | -0.45 | -0.52 | 0.04 | 0.05 | 21 | 0.52 | no | 0.48 | 0.00 | 0.00 | 0.63 | 0.09 | -0.10 |

## Recipes

- **B3-cheap-user**: The simulated customer on gemini-3.1-flash-lite.
- **C1-pure**: An LLM fakes the shop's tools (database included).
- **C2-all**: The whole conversation as ONE call: agent, customer and tools imagined.
