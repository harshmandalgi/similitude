# wikiqa-openai / focus: agent: validity of each mini

Runs used: 1276; skipped: 0 with errors, 4 not yet judged.

## Accuracy per variant (share of tasks correct)

| variant | kind | full |
|---|---|---|
| base | base | 0.68±0.05 (n=80) |
| e-question-decomposition | edit | 0.70±0.05 (n=80) |
| e-query-rewriting | edit | 0.70±0.05 (n=80) |
| e-verify-before-answer | edit | 0.70±0.05 (n=80) |
| e-page-reading-strategy | edit | 0.66±0.05 (n=80) |
| e-entity-disambiguation | edit | 0.69±0.05 (n=80) |
| e-answer-normalisation | edit | 0.74±0.05 (n=80) |
| m-memory-first | mutant | 0.66±0.05 (n=80) |
| m-one-page | mutant | 0.64±0.05 (n=80) |
| m-first-entity | mutant | 0.71±0.05 (n=79) |
| m-rush | mutant | 0.70±0.05 (n=79) |
| m-3-steps | mutant | 0.54±0.06 (n=80) |
| m-no-format | mutant | 0.70±0.05 (n=80) |
| model-gpt-5.4-mini | model | 0.72±0.05 (n=80) |
| model-gpt-4.1-mini | model | 0.75±0.05 (n=79) |
| model-gpt-4.1-nano | model | 0.51±0.06 (n=79) |

## Does each mini make the same decisions as the full workflow?

| recipe | cost × | latency × (median) | Kendall τ | Spearman ρ | pair acc | pair acc (clear) | clear pairs | MMRV | same best | MAE | mutants: same dir | mutants: caught | reason JS | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|

## Recipes

