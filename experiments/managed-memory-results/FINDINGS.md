# Managed-memory findings

All six streams and all three arms are retained. No post-run policy changes or favorable-seed selection.

The manager solved 125/180 regression tasks versus 111/180 for discard, using 18.6% fewer total graph steps. On fresh streams it solved 138/180 versus 111/180, using 24.7% fewer steps and 12.5% less CPU time. Management, failed searches, validation, persistence operations and final audit are included. Persistent storage growth is higher than discard and is reported separately; this is a compute saving, not a reduction in every resource.

| Split | Seed | Original discard | Manager disabled | Managed | Managed steps / original | Learned / active |
|---|---:|---:|---:|---:|---:|---:|
| regression | 1907 | 37/60 | 37/60 | 40/60 | 0.815 | 8/8 |
| regression | 2909 | 37/60 | 37/60 | 46/60 | 0.769 | 9/9 |
| regression | 3911 | 37/60 | 37/60 | 39/60 | 0.859 | 7/7 |
| fresh | 4903 | 37/60 | 37/60 | 47/60 | 0.742 | 10/10 |
| fresh | 5903 | 37/60 | 37/60 | 46/60 | 0.781 | 9/9 |
| fresh | 6907 | 37/60 | 37/60 | 45/60 | 0.735 | 9/9 |

The ratio includes canonicalization, validation, utility updates, storage graph calls, unsuccessful probes/searches and final audit. CPU/wall and physical database growth are separately reported.

## Cumulative crossover

| Seed | Comparator | First advantage maintained to end |
|---:|---|---:|
| 1907 | discard | 42 |
| 1907 | manager_disabled | 42 |
| 2909 | discard | 8 |
| 2909 | manager_disabled | 8 |
| 3911 | discard | 47 |
| 3911 | manager_disabled | 47 |
| 4903 | discard | 27 |
| 4903 | manager_disabled | 27 |
| 5903 | discard | 11 |
| 5903 | manager_disabled | 11 |
| 6907 | discard | 4 |
| 6907 | manager_disabled | 4 |

Stored canonical graphs: 52/52 passed independent post-run audit (1040 cases).

No retained method reached the retirement threshold in these streams. Retirement is unit-tested but cannot be credited with the observed improvement. The memory-disabled scheduler matched discard coverage on every stream; component-level ablations would still be needed to isolate canonicalization, screening and bounded probing from one another.

These tests address the fixed reduction-language memory failure. Canonicalization and scalar continuation templates are supplied domain rules; they do not generalize automatically to effects or arbitrary programming. Fresh streams change examples and order within the same generator, not the domain family.

REPORT.md contains the learning windows; report.json contains all trials, cost categories, CPU/wall, storage growth, retirement state and comparison summaries.
