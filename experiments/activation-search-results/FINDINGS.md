# Stored/active separation is implemented; this policy did not fix interference

Across four frozen planning orders, no memory solved **60/120**, all retained methods active solved **50/120**, and top-1 retrieval with task-local eviction solved **49/120**. Top-1 gained no tasks over either control. There were no successful mixed compositions and no final audit false positives.

Long-term storage is now separate from task-local activation. Effect signatures are indexed once when methods are retained. Selection uses generic shape/effect overlap, expanded cost and existing global utility; eviction removes calls and pending branches only from the current task. Retained methods remain indexed and callable in later tasks.

## Observed failures

- In orders 15053 and 18089, both memory conditions retained pickup but missed all five round-trip tasks that no-memory search solved. On inspected failures, memory search consumed its allocation and left only the protected 100k primitive fallback. That was insufficient to recover those tasks.
- In order 16057, task 23, top-1 excluded the already learned round-trip method. Two methods tied on structural overlap, and a one-point historical utility difference selected the other method. All-active search solved the task by calling the retained round-trip method. This is a concrete retrieval false negative.
- Task-local eviction actually triggered twice, on delivery tasks in orders 16057 and 17077. Neither task was solved. Thus eviction mechanics were exercised, but no benefit from eviction was demonstrated.

## Cost and validation

| Condition | Total graph steps | CPU seconds | Solved |
|---|---:|---:|---:|
| No memory | 38,005,254 | 124.74 | 60 |
| All active | 36,453,503 | 137.65 | 50 |
| Top-1 plus eviction | 37,155,741 | 133.81 | 49 |

Lower total logical steps do not establish better economics when fewer tasks are solved. Totals include retrieval, indexing, utility updates, retention, online validation/audit and setup. The full audit verified frozen sources and task streams, all 12 retained method instances on 192 held-out examples, index preservation, method chronology, top-1 limits, eviction exclusion and budget accounting. Eight isolated tests passed.

This rejects the claim that this particular small-active-set policy fixes interference at the current budget. It does not reject stored/active separation generally. The filter scans metadata linearly, uses only one stored/current example for relevance, and uses global rather than context-conditioned utility. The experiment tests retrieval plus eviction together, not either mechanism in isolation. The examples/orders were previously exposed, so this is an architectural comparison rather than fresh confirmation.

The stopped ratio sweep remains incomplete. No adaptive borrowing experiment, application migration, text/tree change or abstraction extraction was started. See REPORT.md and report.json for the complete comparison and ../ACTIVATION_SEARCH.md for reproduction.
