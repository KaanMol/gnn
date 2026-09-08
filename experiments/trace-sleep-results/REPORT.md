# Trace-assisted consolidation

Preserved 120-task sequence; architectural comparison, not fresh evaluation.

| Arm | Solved | Wake | Sleep | Lifetime | Cost / solve | CPU / wall |
|---|---:|---:|---:|---:|---:|---:|
| no_memory | 60/120 | 31,942,672 | 0 | 31,942,672 | 532,378 | 112.76 / 113.31 |
| full | 60/120 | 28,588,501 | 10,528,129 | 39,116,630 | 651,944 | 150.81 / 152.53 |
| trace | 60/120 | 28,589,401 | 3,710,599 | 32,300,000 | 538,333 | 127.93 / 129.37 |

First crossover: None; final cost repaid: False.
Old full-replay control reproduced 8,683,002 steps. New full-replay component: 2,114,882; partial replay: 775,952.
Trace analysis/attempt indexing introduced 73,029 steps; extra wake recording introduced 1,080.
Evidence counts: {'full': 6, 'UNKNOWN': 24, 'partial': 4, 'trace': 2}. Full replays avoided: 30/36; matched replay pairs: 36/36.
Activations/helpful: 17/17; negative transfer: 0; lost primitive solves: 0; whole/mixed: 17/0; audit false positives: 0.

See audit.json for the exact matched ablation, wake decisions, measured false negatives, storage, cumulative ledger and evidence provenance. UNKNOWN and unsampled opportunities are not labeled useless. All prior outputs and frozen wake/validation rules are preserved.
