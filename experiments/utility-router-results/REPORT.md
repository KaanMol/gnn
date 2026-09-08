# Learned utility routing

Four evaluation orders excluded from fitting; same planning generator. Model and policy frozen before evaluation.

| Arm | Solved | Steps | CPU / wall seconds | Cost / solved | Activations | Helpful | Lost primitive tasks | Mixed / whole |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| no_memory | 60/120 | 31,978,509 | 115.34 / 116.74 | 532,975 | 0 | 0 | 0 | 0 / 0 |
| fixed | 50/120 | 28,742,986 | 115.71 / 117.39 | 574,860 | 34 | 24 | 10 | 0 / 24 |
| router | 42/120 | 36,464,921 | 134.97 / 136.44 | 868,212 | 0 | 0 | 18 | 0 / 0 |

Per-order results:
- 210011 no_memory: 15/30, gained 0, lost 0.
- 210011 fixed: 10/30, gained 0, lost 5.
- 210011 router: 10/30, gained 0, lost 5.
- 220009 no_memory: 15/30, gained 0, lost 0.
- 220009 fixed: 15/30, gained 0, lost 0.
- 220009 router: 11/30, gained 0, lost 4.
- 230003 no_memory: 15/30, gained 0, lost 0.
- 230003 fixed: 15/30, gained 0, lost 0.
- 230003 router: 11/30, gained 0, lost 4.
- 240007 no_memory: 15/30, gained 0, lost 0.
- 240007 fixed: 10/30, gained 0, lost 5.
- 240007 router: 10/30, gained 0, lost 5.

Useful-memory false negatives: 24 / 34 probe-positive rejected methods tested in isolated snapshots. Unfinished probes are not labeled useful or useless.
Historical negative-transfer regression: frozen model suppresses 10 / 10 previously harmful contexts. This is fitting-set diagnostics, not held-out evidence.
Unactivated primitive trace prefix checks: 206. Retained audits: 12 methods, 192 cases.
Fitting overhead: 9,524,623 graph steps. Diagnostic counterfactual overhead: 6,923,668 graph steps. These are separate from the arm totals above.

See audit.json for activation precision, negative-transfer counts, exploration, model regression, paired outcomes and counterfactual details. Training history and frozen parameters are in training.json and model.json.

All 450k task caps include validation, audit, retention and router persistence. A common 100k finalization allowance reduces the search cap to 350k, so raw solved counts are not directly comparable with earlier search-only-budget experiments.

No evaluation outcomes updated the model. Activation credit is downstream task-level utility against the matched baseline; if multiple methods activate, this does not identify individual causal credit.
