# W1: do OpenAI's decisions carry over to Gemini?

Same tasks, prompts and tools; only the model family differs. Read the OpenAI run as a miniature of the Gemini run. (Judges differ: Opus for OpenAI runs, Sonnet for Gemini runs.)

| variant | Gemini acc | OpenAI acc |
|---|---|---|
| base | 0.74 | 0.68 |
| e-question-decomposition | 0.75 | 0.70 |
| e-query-rewriting | 0.78 | 0.70 |
| e-verify-before-answer | 0.74 | 0.70 |
| e-page-reading-strategy | 0.75 | 0.66 |
| e-entity-disambiguation | 0.74 | 0.69 |
| e-answer-normalisation | 0.76 | 0.74 |
| m-memory-first | 0.72 | 0.66 |
| m-one-page | 0.71 | 0.64 |
| m-first-entity | 0.69 | 0.71 |
| m-rush | 0.72 | 0.70 |
| m-3-steps | 0.56 | 0.54 |
| m-no-format | 0.71 | 0.70 |

| metric | value |
|---|---|
| kendall | 0.2735583347674307 |
| spearman | 0.3400680204068024 |
| decision_acc | 0.5555555555555556 |
| decision_acc_clear | 0.9285714285714286 |
| clear_pairs | 14 |
| mmrv | 0.04903846153846156 |
| top1_match | False |
| mutant_same_direction | 1.0 |
| reason_js | 0.5511210502777891 |
| top_reason_match | 0.15384615384615385 |
