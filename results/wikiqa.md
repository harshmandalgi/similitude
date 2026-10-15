# wikiqa / focus: agent: validity of each mini

Runs used: 6800; skipped: 0 with errors, 0 not yet judged.

## Accuracy per variant (share of tasks correct)

| variant | kind | full | B4-quarter | C1-cache-sim | C1-pure | C2+B4 | C2-fused | C6-short-obs | full-rerun |
|---|---|---|---|---|---|---|---|---|---|
| base | base | 0.74±0.05 (n=80) | 0.80±0.09 (n=20) | 0.76±0.05 (n=80) | 0.65±0.05 (n=80) | 0.75±0.10 (n=20) | 0.65±0.05 (n=80) | 0.74±0.05 (n=80) | 0.74±0.05 (n=80) |
| e-question-decomposition | edit | 0.75±0.05 (n=80) | 0.75±0.10 (n=20) | 0.70±0.05 (n=80) | 0.70±0.05 (n=80) | 0.75±0.10 (n=20) | 0.62±0.05 (n=80) | 0.74±0.05 (n=80) | 0.74±0.05 (n=80) |
| e-query-rewriting | edit | 0.78±0.05 (n=80) | 0.80±0.09 (n=20) | – | – | 0.80±0.09 (n=20) | 0.62±0.05 (n=80) | – | – |
| e-verify-before-answer | edit | 0.74±0.05 (n=80) | 0.90±0.07 (n=20) | – | – | 0.75±0.10 (n=20) | 0.65±0.05 (n=80) | – | – |
| e-page-reading-strategy | edit | 0.75±0.05 (n=80) | 0.90±0.07 (n=20) | 0.74±0.05 (n=80) | 0.62±0.05 (n=80) | 0.80±0.09 (n=20) | 0.65±0.05 (n=80) | 0.75±0.05 (n=80) | 0.76±0.05 (n=80) |
| e-entity-disambiguation | edit | 0.74±0.05 (n=80) | 0.80±0.09 (n=20) | – | – | 0.75±0.10 (n=20) | 0.66±0.05 (n=80) | – | – |
| e-answer-normalisation | edit | 0.76±0.05 (n=80) | 0.85±0.08 (n=20) | 0.74±0.05 (n=80) | 0.65±0.05 (n=80) | 0.70±0.11 (n=20) | 0.60±0.06 (n=80) | 0.70±0.05 (n=80) | 0.75±0.05 (n=80) |
| m-memory-first | mutant | 0.72±0.05 (n=80) | 0.90±0.07 (n=20) | – | – | 0.75±0.10 (n=20) | 0.61±0.05 (n=80) | – | – |
| m-one-page | mutant | 0.71±0.05 (n=80) | 0.90±0.07 (n=20) | 0.69±0.05 (n=80) | 0.64±0.05 (n=80) | 0.70±0.11 (n=20) | 0.60±0.06 (n=80) | 0.75±0.05 (n=80) | 0.72±0.05 (n=80) |
| m-first-entity | mutant | 0.69±0.05 (n=80) | 0.85±0.08 (n=20) | – | – | 0.85±0.08 (n=20) | 0.61±0.05 (n=80) | – | – |
| m-rush | mutant | 0.72±0.05 (n=80) | 0.80±0.09 (n=20) | – | – | 0.80±0.09 (n=20) | 0.68±0.05 (n=80) | – | – |
| m-3-steps | mutant | 0.56±0.06 (n=80) | 0.75±0.10 (n=20) | 0.59±0.06 (n=80) | 0.55±0.06 (n=80) | 0.70±0.11 (n=20) | 0.62±0.05 (n=80) | 0.56±0.06 (n=80) | 0.56±0.06 (n=80) |
| m-2-steps | mutant | 0.40±0.06 (n=80) | 0.50±0.11 (n=20) | 0.44±0.06 (n=80) | 0.50±0.06 (n=80) | 0.75±0.10 (n=20) | 0.62±0.05 (n=80) | 0.40±0.06 (n=80) | 0.39±0.05 (n=80) |
| m-no-tools | mutant | 0.72±0.05 (n=80) | 0.85±0.08 (n=20) | 0.72±0.05 (n=80) | 0.65±0.05 (n=80) | 0.75±0.10 (n=20) | 0.69±0.05 (n=80) | 0.74±0.05 (n=80) | 0.78±0.05 (n=80) |
| m-snippets-only | mutant | 0.72±0.05 (n=80) | 0.70±0.11 (n=20) | – | – | 0.60±0.11 (n=20) | 0.61±0.05 (n=80) | – | – |
| m-no-format | mutant | 0.71±0.05 (n=80) | 0.80±0.09 (n=20) | – | – | 0.75±0.10 (n=20) | 0.64±0.05 (n=80) | – | – |
| model-gemini-3.8-flash | model | 0.75±0.05 (n=80) | 0.80±0.09 (n=20) | 0.81±0.04 (n=80) | 0.74±0.05 (n=80) | 0.90±0.07 (n=20) | 0.71±0.05 (n=80) | 0.80±0.05 (n=80) | 0.81±0.04 (n=80) |
| model-gemini-3.1-flash-lite | model | 0.68±0.05 (n=80) | 0.75±0.10 (n=20) | 0.72±0.05 (n=80) | 0.65±0.05 (n=80) | 0.75±0.10 (n=20) | 0.65±0.05 (n=80) | 0.69±0.05 (n=80) | 0.70±0.05 (n=80) |

## Does each mini make the same decisions as the full workflow?

| recipe | cost × | latency × (median) | Kendall τ | Spearman ρ | pair acc | pair acc (clear) | clear pairs | MMRV | same best | MAE | mutants: same dir | mutants: caught | reason JS | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B4-quarter | 0.19 | 0.88 | 0.23 | 0.29 | 0.51 | 0.85 | 39 | 0.07 | no | 0.10 | 1.00 | 0.50 | 0.47 | 0.50 | 0.56 |
| C1-cache-sim | 1.23 | 0.74 | 0.61 | 0.73 | 0.79 | 0.95 | 20 | 0.03 | no | 0.03 | 1.00 | 1.00 | 0.27 | 1.00 | 0.41 |
| C1-pure | 1.05 | 1.49 | 0.54 | 0.64 | 0.69 | 0.90 | 20 | 0.03 | no | 0.07 | 1.00 | 1.00 | 0.30 | 1.00 | 0.27 |
| C2+B4 | 0.06 | 0.20 | 0.21 | 0.26 | 0.46 | 0.51 | 39 | 0.13 | no | 0.07 | 0.50 | 0.00 | 0.52 | 0.53 | 0.04 |
| C2-fused | 0.31 | 0.20 | 0.10 | 0.16 | 0.50 | 0.49 | 39 | 0.16 | no | 0.10 | 1.00 | 0.00 | 0.38 | 0.89 | 0.18 |
| C6-short-obs | 0.89 | 1.45 | 0.48 | 0.59 | 0.69 | 1.00 | 20 | 0.02 | no | 0.02 | 1.00 | 1.00 | 0.27 | 0.90 | 0.54 |
| full-rerun | 1.05 | 1.14 | 0.67 | 0.78 | 0.83 | 1.00 | 20 | 0.02 | no | 0.02 | 1.00 | 1.00 | 0.27 | 1.00 | 0.57 |

## Recipes

- **B4-quarter**: A fixed random quarter of the tasks.
- **C1-cache-sim**: Replay recorded tool outputs; fake only calls never seen.
- **C1-pure**: An LLM fakes every tool from its description only.
- **C2+B4**: Fused loop on a quarter of the tasks.
- **C2-fused**: The whole agent loop as one call with imagined tool results.
- **C6-short-obs**: Tool outputs cut to 1,200 characters.
- **full-rerun**: The full workflow again, fresh samples: the noise ceiling.
