# Trace-assisted consolidation: near parity, not a lifetime win

The frozen architectural comparison preserved coverage and safe wake behavior while reducing consolidation cost substantially. All three arms solved 60/120. Both memory arms achieved 17 useful whole-program activations, zero negative transfer, zero lost primitive solves, and zero audit false positives. Trace-assisted lifetime cost was 32,300,000 steps, versus 31,942,672 for no memory: still 357,328 steps (1.12%) above parity. No cumulative crossover survived the scheduled sleep charges at any measured task boundary.

This reused the preserved 120-task sequence. It is not evidence of fresh-order generalization, and no policy was tuned after evaluation began.

## Full lifetime comparison

| Arm | Wake steps | Sleep steps | Lifetime steps | Audited solves | Cost per solve | CPU / wall seconds |
|---|---:|---:|---:|---:|---:|---:|
| No memory | 31,942,672 | 0 | 31,942,672 | 60/120 | 532,378 | 112.76 / 113.31 |
| Full-replay sleep | 28,588,501 | 10,528,129 | 39,116,630 | 60/120 | 651,944 | 150.81 / 152.53 |
| Trace-assisted sleep | 28,589,401 | 3,710,599 | 32,300,000 | 60/120 | 538,333 | 127.93 / 129.37 |

Trace assistance cut sleep work by 64.8% and lifetime work by 6,816,630 steps relative to the old sleep system. Physical CPU/wall also improved relative to full replay, but remained above no memory in this run. Lower sleep cost did not quite yield the required final economic win.

## Exact replay-cost ablation

The unchanged full control reproduced the original forced-replay cost exactly: **8,683,002 steps**. All 36 boundary/task/method pairs matched between policies, making the following ablation direct rather than extrapolated.

| Change from full replay | Step effect |
|---|---:|
| Skip 30 matched full replays | -6,568,156 |
| Additional recording cost within six retained full fallbacks | +36 |
| Introduce bounded partial replay | +775,952 |
| Introduce trace analysis and attempt indexing/persistence | +73,029 |
| Reduce other consolidation work | -1,098,391 |
| Net sleep reduction | -6,817,530 |
| Net wake cost increase | +900 |
| Net lifetime reduction | -6,816,630 |

The full-replay component fell to 2,114,882 steps, a net reduction of 6,568,120 (75.6%). Partial replay plus remaining full replay consumed 2,890,834 steps. Other consolidation savings came from fewer utility calculations and model updates, with smaller publication work; pair selection retained exactly the same 16,604-step cost.

Added wake indexing and recording were explicitly charged at 1,080 steps. The net wake increase was 900 because 180 of those index steps displaced work inside already-exhausted fixed search budgets. They were not uncharged: all appear in the ledger. The 103 rejected-wake traces remained exact primitive-baseline prefixes, with identical per-candidate costs.

## What the evidence actually established

The 36 sleep investigations ended as:

- **2 trace-derived utility decisions:** the exact same single admitted method already had a completed factual wake outcome.
- **4 certified partial-replay decisions:** the 75k-bounded run finished an audited solve without exhausting any budget.
- **6 full-fallback decisions:** one unresolved pair per sleep received full wake-style replay.
- **24 UNKNOWN decisions:** no utility label, no positive count, and no routing-confidence update.

There were 12 partial attempts in total; eight did not establish utility. Their entire work remained charged. The separate attempt-count index advanced for UNKNOWN so that it would not repeatedly monopolize investigation priority, but UNKNOWN was never treated as zero utility or a successful observation.

Most full replays were avoided by leaving unresolved outcomes UNKNOWN, not by reconstructing all their downstream results from traces. The result supports a narrower mechanism: sparse sufficient evidence plus bounded investigation preserved the useful routes here. It does not demonstrate arbitrary counterfactual reconstruction or free cached execution.

The recorder preserved already-computed evaluation/frontier summaries, candidate transitions and costs, method availability, routing context and completed outcomes. It did not fabricate unavailable per-example intermediate program outputs. All actual partial/full executions retained the original nested and cache-hit charging. A pre-freeze test verified that a completed partial run exactly matched its full counterpart's candidate trace and costs.

## Wake and reliability diagnostics

Wake routing itself remained at **4,086 steps total**, unchanged from the old sleep system. Seventeen activations were helpful (100% observed precision); all were whole-program reuse. There were zero mixed compositional successes, zero negative-transfer activations, and zero primitive-solvable tasks lost. There were no additional solved tasks over no memory.

Trace-assisted evidence identified four useful-memory false negatives among ten resolved rejected pairs whose methods existed at the original wake task. The full-replay arm measured four among 34. These denominators differ because trace assistance deliberately leaves cases UNKNOWN; neither UNKNOWN nor unsampled opportunities can be counted as useless. The counts are not evidence that unresolved contexts are safe.

Final persistent database sizes were 12,623,872 bytes for no memory, 32,989,184 for full sleep, and 34,623,488 for trace assistance. Growth above setup was 0, 20,398,080 and 22,003,712 bytes respectively. Extra evidence therefore increased storage even while reducing logical compute. Both memory arms retained their two learned methods globally.

## Integrity and interpretation

Twelve tests passed before freezing, including factual identity checks, charged recording equivalence, partial/full execution equality, UNKNOWN isolation, one-fallback quota, future-prefix rejection, and nested/cache accounting. Source and prior-output hashes passed the final audit. The recorder and partial runner use the exact frozen wake function body with only the meter binding changed. Routing signatures, activation threshold, primitive queue policy, retained-method semantics and validation/audit behavior were not edited.

All sleep inputs were completed prefixes; used methods existed before their use. Executable expanded programs remained within five primitives. Every wake task and sleep phase remained inside its frozen budget, and all extra recording, partial/full replay, trace analysis, indexing, validation, retention and audit work was included. Successful solutions and four retained method instances passed exact held-out revalidation; the retained-method audit covered 64 cases. Final audit false positives were zero.

The primary economic result remains a near miss: trace assistance preserved reliability and moved lifetime cost from 22.5% above baseline to 1.12% above it, but did not cross final parity. The result, all UNKNOWN records and the exact matched ablation remain preserved. No fresh evaluation or follow-up tuning sweep was started, and the live application was not changed.

REPORT.md provides the summary. audit.json contains the per-pair ablation, decisions, usefulness counts, cumulative ledger and storage metrics. sleeps.jsonl and trials.jsonl retain the complete evidence and execution histories.
