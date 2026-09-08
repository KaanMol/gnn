# Sleep consolidation results

One 120-task sequence, six fixed sleep phases. All sleep work is included.

| Arm | Solved | Wake steps | Sleep steps | Inherited steps | Lifetime steps | Cost / solve | Whole / mixed |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_memory | 60/120 | 31,942,672 | 0 | 0 | 31,942,672 | 532,378 | 0 / 0 |
| online | 41/120 | 37,122,519 | 0 | 83,127,730 | 120,250,249 | 2,932,933 | 0 / 0 |
| sleep | 60/120 | 28,588,501 | 10,528,129 | 0 | 39,116,630 | 651,944 | 17 / 0 |

| Arm | Wake CPU / wall | Sleep CPU / wall | Activations / helpful | Negative transfer | Lost primitive | Library | DB growth |
|---|---:|---:|---:|---:|---:|---:|---:|
| no_memory | 111.13 / 111.73 | 0.00 / 0.00 | 0 / 0 | 0 | 0 | 0 | 0 bytes |
| online | 135.12 / 136.08 | 0.00 / 0.00 | 0 / 0 | 0 | 19 | 2 | 2,392,064 bytes |
| sleep | 108.63 / 109.96 | 40.02 / 40.19 | 17 / 17 | 0 | 0 | 2 | 20,393,984 bytes |

First cumulative crossover: None. Final consolidation cost repaid: False.
Observed useful-memory false negatives: 4 / 34 replayed rejected pairs whose methods existed at wake. Remaining opportunities are unmeasured, not negative.
Rejected-wake primitive-prefix checks: 103. Lost primitive tasks after rejection: 0.
Stored audit: 4 methods on 64 cases. Final false positives: 0.

Historical acquisition and fitting cost is included for the inherited online router. Wake/sleep CPU columns describe this run; inherited historical CPU is reported separately in FINDINGS.md. Cold sleep learning receives no prior model or utility table.

No future-task data was passed to consolidation. Tables are frozen between sleep boundaries. Thresholds, streams and budgets were frozen before results. See audit.json for every wake decision, cumulative trajectory, usefulness replay and paired outcome.
