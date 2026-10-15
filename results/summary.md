# Main results: each miniature vs the full workflow

Ceiling rows (full-rerun, W-rerun, P-rerun) are the full workflow run again: no miniature can agree with the full workflow more than it agrees with itself.


## W1 wikiqa (10 core variants)

| recipe | cost × | latency × | Kendall τ | clear pairs kept | clear pairs | MMRV | mutants: same way | mutants: caught | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|
| full-rerun | 1.05 | 1.14 | 0.67 | 1.00 | 20 | 0.02 | 1.00 | 1.00 | 1.00 | 0.57 |
| C1-cache-sim | 1.23 | 0.74 | 0.61 | 0.95 | 20 | 0.03 | 1.00 | 1.00 | 1.00 | 0.41 |
| C1-pure | 1.05 | 1.49 | 0.54 | 0.90 | 20 | 0.03 | 1.00 | 1.00 | 1.00 | 0.27 |
| C6-short-obs | 0.89 | 1.45 | 0.48 | 1.00 | 20 | 0.02 | 1.00 | 1.00 | 0.90 | 0.54 |
| B4-quarter | 0.20 | 0.86 | 0.40 | 0.85 | 20 | 0.05 | 1.00 | 0.50 | 0.62 | 0.53 |
| C2-fused | 0.28 | 0.21 | 0.08 | 0.50 | 20 | 0.15 | 1.00 | 0.00 | 0.80 | 0.17 |
| C2+B4 | 0.06 | 0.20 | 0.25 | 0.45 | 20 | 0.14 | 0.50 | 0.00 | 0.44 | 0.13 |

## W2 tau (8 core variants)

| recipe | cost × | latency × | Kendall τ | clear pairs kept | clear pairs | MMRV | mutants: same way | mutants: caught | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|
| B3-cheap-user | 1.01 | 1.46 | 0.73 | 0.79 | 14 | 0.10 | 0.50 | 0.50 | 0.50 | 0.48 |
| C1-pure | 0.88 | 1.23 | – | 0.00 | 14 | 0.20 | 0.00 | 0.00 | 0.00 | -0.13 |
| C2-all | 0.23 | 0.13 | -0.56 | 0.07 | 14 | 0.54 | 0.00 | 0.00 | 0.12 | -0.09 |

## W3 research, focus writer

| recipe | cost × | latency × | Kendall τ | clear pairs kept | clear pairs | MMRV | mutants: same way | mutants: caught | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|
| W-rerun | 1.01 | 1.44 | -0.05 | 0.40 | 5 | 0.06 | – | – | 0.29 | 0.38 |
| W-A-replay | 0.21 | 0.15 | -0.47 | 0.00 | 5 | 0.08 | – | – | 0.14 | 0.41 |
| W-A+B1+C5 | 0.13 | 0.05 | -0.50 | 0.20 | 5 | 0.08 | – | – | 0.86 | 0.23 |
| W-C4-stub | 0.66 | 0.40 | 0.39 | 1.00 | 5 | 0.04 | – | – | 0.86 | 0.22 |

## W3 research, focus planner

| recipe | cost × | latency × | Kendall τ | clear pairs kept | clear pairs | MMRV | mutants: same way | mutants: caught | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|
| P-rerun | 0.99 | 0.95 | 0.32 | 0.75 | 8 | 0.05 | 1.00 | 0.00 | 0.71 | 0.30 |
| P-C1-pure | 1.16 | 1.01 | 0.63 | 1.00 | 8 | 0.04 | 1.00 | 0.50 | 0.71 | 0.26 |
| P-C4-stub | 0.60 | 0.41 | -0.73 | 0.00 | 8 | 0.11 | 0.00 | 0.00 | 0.71 | 0.24 |
| P-C4+B1+C5 | 0.51 | 0.41 | 0.11 | 0.62 | 8 | 0.08 | 1.00 | 0.00 | 0.71 | 0.14 |
| P-C2-all | 0.50 | 0.14 | 0.05 | 0.50 | 8 | 0.09 | 0.50 | 0.00 | 0.00 | 0.06 |

## W3 writer: replay vs replay (self-agreement)

| recipe | cost × | latency × | Kendall τ | clear pairs kept | clear pairs | MMRV | mutants: same way | mutants: caught | top reason same | reason π |
|---|---|---|---|---|---|---|---|---|---|---|
| W-A-replay-2 | 1.00 | 1.06 | 0.23 | – | 0 | 0.02 | – | – | 0.29 | 0.35 |
