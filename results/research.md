# research / focus: writer: validity of each mini

Runs used: 3360; skipped: 0 with errors, 0 not yet judged.

## Accuracy per variant (share of tasks correct)

| variant | kind | full | W-A+B1+C5 | W-A-replay | W-A-replay-2 | W-C4-stub | W-rerun |
|---|---|---|---|---|---|---|---|
| base | base | 0.82±0.04 (n=80) | 0.84±0.04 (n=80) | 0.82±0.04 (n=80) | 0.82±0.04 (n=80) | 0.61±0.05 (n=80) | 0.80±0.05 (n=80) |
| w-e-restate-constraints | edit | 0.80±0.05 (n=80) | 0.84±0.04 (n=80) | 0.84±0.04 (n=80) | 0.84±0.04 (n=80) | 0.60±0.06 (n=80) | 0.76±0.05 (n=80) |
| w-e-prefer-own-knowledge-on-conflict | edit | 0.74±0.05 (n=80) | 0.84±0.04 (n=80) | 0.85±0.04 (n=80) | 0.82±0.04 (n=80) | 0.60±0.06 (n=80) | 0.78±0.05 (n=80) |
| w-e-explicit-counting | edit | 0.72±0.05 (n=80) | 0.85±0.04 (n=80) | 0.84±0.04 (n=80) | 0.82±0.04 (n=80) | 0.60±0.06 (n=80) | 0.79±0.05 (n=80) |
| w-m-memory | mutant | 0.81±0.04 (n=80) | 0.84±0.04 (n=80) | 0.84±0.04 (n=80) | 0.84±0.04 (n=80) | 0.61±0.05 (n=80) | 0.78±0.05 (n=80) |
| w-m-first-note | mutant | 0.79±0.05 (n=80) | 0.85±0.04 (n=80) | 0.82±0.04 (n=80) | 0.82±0.04 (n=80) | 0.62±0.05 (n=80) | 0.78±0.05 (n=80) |
| w-model-3.8 | model | 0.78±0.05 (n=80) | 0.85±0.04 (n=80) | 0.84±0.04 (n=80) | 0.84±0.04 (n=80) | 0.61±0.05 (n=80) | 0.79±0.05 (n=80) |

## Does each mini make the same decisions as the full workflow?

| recipe | cost × | latency × (median) | Kendall τ | Spearman ρ | pair acc | pair acc (clear) | clear pairs | MMRV | same best | MAE | mutants: same dir | mutants: caught | reason JS | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| W-A+B1+C5 | 0.13 | 0.05 | -0.50 | -0.58 | 0.10 | 0.20 | 5 | 0.08 | no | 0.06 | – | – | 0.35 | 0.86 | 0.23 |
| W-A-replay | 0.21 | 0.15 | -0.47 | -0.56 | 0.14 | 0.00 | 5 | 0.08 | no | 0.06 | – | – | 0.39 | 0.14 | 0.41 |
| W-A-replay-2 | 0.21 | 0.16 | 0.25 | 0.29 | 0.38 | 0.40 | 5 | 0.05 | no | 0.05 | – | – | 0.34 | 0.57 | 0.21 |
| W-C4-stub | 0.66 | 0.40 | 0.39 | 0.46 | 0.52 | 1.00 | 5 | 0.04 | no | 0.17 | – | – | 0.32 | 0.86 | 0.22 |
| W-rerun | 1.01 | 1.44 | -0.05 | 0.00 | 0.38 | 0.40 | 5 | 0.06 | yes | 0.03 | – | – | 0.34 | 0.29 | 0.38 |

## Recipes

- **W-A+B1+C5**: Replay upstream, drop the summary, stop after the writer.
- **W-A-replay**: Replay planner and research from the base's recordings.
- **W-A-replay-2**: W-A-replay again with fresh writer samples: the mini's own noise.
- **W-C4-stub**: Each researcher is one call that imagines its searches.
- **W-rerun**: The full workflow again, fresh samples: the noise ceiling.

# research / focus: planner: validity of each mini

Runs used: 3360; skipped: 0 with errors, 0 not yet judged.

## Accuracy per variant (share of tasks correct)

| variant | kind | full | P-C1-pure | P-C2-all | P-C4+B1+C5 | P-C4-stub | P-rerun |
|---|---|---|---|---|---|---|---|
| base | base | 0.82±0.04 (n=80) | 0.65±0.05 (n=80) | 0.62±0.05 (n=80) | 0.59±0.06 (n=80) | 0.59±0.06 (n=80) | 0.76±0.05 (n=80) |
| p-e-resolve-time-anchors | edit | 0.82±0.04 (n=80) | 0.65±0.05 (n=80) | 0.62±0.05 (n=80) | 0.59±0.06 (n=80) | 0.59±0.06 (n=80) | 0.79±0.05 (n=80) |
| p-e-list-then-filter | edit | 0.79±0.05 (n=80) | 0.64±0.05 (n=80) | 0.60±0.06 (n=80) | 0.60±0.06 (n=80) | 0.59±0.06 (n=80) | 0.78±0.05 (n=80) |
| p-e-name-wikipedia-page | edit | 0.79±0.05 (n=80) | 0.66±0.05 (n=80) | 0.57±0.06 (n=80) | 0.53±0.06 (n=80) | 0.60±0.06 (n=80) | 0.79±0.05 (n=80) |
| p-m-one | mutant | 0.72±0.05 (n=80) | 0.55±0.06 (n=80) | 0.60±0.06 (n=80) | 0.56±0.06 (n=80) | 0.60±0.06 (n=80) | 0.70±0.05 (n=80) |
| p-m-vague | mutant | 0.68±0.05 (n=80) | 0.59±0.06 (n=80) | 0.56±0.06 (n=80) | 0.57±0.06 (n=80) | 0.60±0.06 (n=80) | 0.74±0.05 (n=80) |
| p-model-3.8 | model | 0.74±0.05 (n=80) | 0.64±0.05 (n=80) | 0.71±0.05 (n=80) | 0.60±0.06 (n=80) | 0.60±0.06 (n=80) | 0.79±0.05 (n=80) |

## Does each mini make the same decisions as the full workflow?

| recipe | cost × | latency × (median) | Kendall τ | Spearman ρ | pair acc | pair acc (clear) | clear pairs | MMRV | same best | MAE | mutants: same dir | mutants: caught | reason JS | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P-C1-pure | 1.16 | 1.01 | 0.63 | 0.79 | 0.79 | 1.00 | 8 | 0.04 | no | 0.14 | 1.00 | 0.50 | 0.30 | 0.71 | 0.26 |
| P-C2-all | 0.50 | 0.14 | 0.42 | 0.49 | 0.68 | 0.75 | 8 | 0.06 | no | 0.15 | 1.00 | 0.00 | 0.37 | 0.57 | 0.09 |
| P-C4+B1+C5 | 0.51 | 0.41 | 0.11 | 0.25 | 0.53 | 0.62 | 8 | 0.08 | no | 0.19 | 1.00 | 0.00 | 0.31 | 0.71 | 0.14 |
| P-C4-stub | 0.60 | 0.41 | -0.73 | -0.81 | 0.00 | 0.00 | 8 | 0.11 | no | 0.17 | 0.00 | 0.00 | 0.24 | 0.71 | 0.24 |
| P-rerun | 0.99 | 0.95 | 0.32 | 0.51 | 0.58 | 0.75 | 8 | 0.05 | no | 0.04 | 1.00 | 0.00 | 0.29 | 0.71 | 0.30 |

## Recipes

- **P-C1-pure**: Researchers' tools all faked from their descriptions.
- **P-C2-all**: Planner, researchers and writer as ONE call (imagined research), with no review.
- **P-C4+B1+C5**: Stubbed researchers, no summary, stop after the writer.
- **P-C4-stub**: Each researcher is one call that imagines its searches.
- **P-rerun**: The full workflow again, fresh samples: the noise ceiling.
