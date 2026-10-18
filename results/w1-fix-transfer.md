# Fix transfer (W1, wikiqa)

Each fix was written by a blind Claude Code instance from one evidence source's failures on the 20 dev questions, then scored on the 80 test questions.

| fix | written from | gain on full (± SE) | gain on C2-fused |
|---|---|---|---|
| fix-full-read-before-answering | full | +0.050 ± 0.035 | +0.037 |
| fix-full-disambiguate-entities | full | +0.000 ± 0.031 | +0.000 |
| fix-full-exact-page-wording | full | +0.037 ± 0.033 | +0.050 |
| fix-C2-fused-read-before-answering | C2-fused | -0.013 ± 0.033 | +0.000 |
| fix-C2-fused-verify-bridge-entity | C2-fused | -0.013 ± 0.033 | +0.013 |
| fix-C2-fused-match-question-scope | C2-fused | +0.000 ± 0.036 | +0.000 |
| fix-C1-cache-sim-read-entity-pages-not-snippets | C1-cache-sim | +0.000 ± 0.031 | +0.000 |
| fix-C1-cache-sim-follow-surfaced-leads-disambiguate | C1-cache-sim | +0.013 ± 0.042 | +0.013 |
| fix-C1-cache-sim-answer-exact-attribute-asked | C1-cache-sim | +0.025 ± 0.025 | +0.013 |
| fix-C1-sim-shared-wording-for-common-questions | C1-sim | +0.013 ± 0.033 | -0.013 |
| fix-C1-sim-verify-every-qualifier | C1-sim | -0.013 ± 0.028 | -0.025 |
| fix-C1-sim-grounded-answer-and-finish | C1-sim | +0.013 ± 0.033 | +0.025 |

## Do fixes found on a mini help the full workflow?

- Fixes written from **full** evidence: mean gain on full +0.029; 2/3 helped.
- Fixes written from **C2-fused** evidence: mean gain on full -0.008; 0/3 helped.
- Fixes written from **C1-cache-sim (in effect full: it replayed the full run)** evidence: mean gain on full +0.013; 2/3 helped.
- Fixes written from **C1-sim** evidence: mean gain on full +0.004; 2/3 helped.

## Does each mini predict whether a fix helps?

- **C2-fused**: same sign as full for 6/9 fixes.
