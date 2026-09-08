# Long-run findings

These are the results of the frozen policy, including unsuccessful searches and all validation/audit costs. No tuning was done after inspecting the stream.

| Arm | Solved / 180 | Total graph steps | Total CPU s | Validation rejections | Audit false positives |
|---|---:|---:|---:|---:|---:|
| discard | 111 | 52,932,262 | 174.51 | 0 | 0 |
| retain | 69 | 66,174,608 | 192.36 | 5 | 0 |

Final library sizes: seed 1907: 12, seed 2909: 14, seed 3911: 9.

Post-run original-operation witnesses passed 93 complete task samples / 3162 cases. The manifest and source hashes are unchanged.
There are 36 constructed misleading fixtures: a selected-items method fits all initial examples but disagrees with validation. Actual learned candidates reaching that trap: 5. Constructing a trap does not guarantee the learner acquires and selects the tempting method.

The audit.json file expands every retained composition and groups methods with matching outputs on seven numeric probes. These groups identify possible redundancy, not proven semantic equivalence. The learner never received these post-run diagnostics.

See REPORT.md for cumulative and last-window costs at tasks 20, 40 and 60, task-role breakdowns and sustained crossover checks. Every search attempt, storage footprint and retained method is recorded in report.json and trials.jsonl.
