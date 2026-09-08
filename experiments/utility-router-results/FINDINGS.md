# Learned utility router: audited result

The isolated experiment did not fix negative transfer. The learned router solved 42/120 tasks, compared with 60/120 for unchanged primitive expansion and 50/120 for the old fixed injection policy. It made zero activations. All four evaluation orders were excluded from fitting; they still come from the same planning generator. No live application state or previous experiment output was changed.

## What caused the losses

All 18 baseline-solvable tasks lost by the router were decision-cost losses after rejection. There were zero activation losses. For every loss, primitive-only replay with exactly the measured consultation charge imposed reproduced the router's primitive trace and failure. This is stronger than inferring cost erosion from zero activations alone.

There were 37 true neutral rejections: the router rejected and primitive search still audited-solved as the baseline did. Five other jointly solved tasks considered no memory. The remaining 60 tasks failed in both arms. Neutral here refers to final success, not zero overhead.

Consultation on lost tasks cost 98,231–109,538 steps, with median 102,406: about 23% of the entire 450k task budget and 29% of the 350k search allowance. Median component costs were 12,870 probing, 47,316 feature extraction, 33,513 inference, and 9,807 decision logic. Those component medians need not sum to the median total. The existing graph arithmetic and feature representation make even this six-feature linear model expensive to consult.

Read LOSS_DIAGNOSIS.md for the requested per-task table: baseline solve, decisions, probe/features/inference/decision costs, activation, primitive depth, and final result. loss-diagnosis.json includes the residual-budget counterfactual traces. These diagnostics were added at the user's request during evaluation; policy and parameters remained frozen.

## Routing quality remains unresolved by the loss explanation

The model suppressed all ten historically harmful fitting contexts, but it also rejected every completed evaluation proposal. Scores ranged from -1572 to -231, below both the +100 activation threshold and the [-100,100] uncertainty band. Therefore the deterministic uncertainty exploration quota never fired. Activation precision is undefined, not 100%.

The isolated forced-activation diagnostics found 24 useful-memory false negatives among 34 probe-positive rejections. These methods would have reduced fully charged work on an audited solve despite the consultation cost. The other ten did not meet that utility criterion. There were also incomplete probes; their usefulness is unmeasured, not assumed negative. Thus avoiding harmful activation did not demonstrate selective or well-calibrated routing.

The fixed policy activated 34 times: 24 helped (70.6% activation precision), while ten lost a primitive-solved task. Its 24 helpful successes were whole-program reuse, not additional solved tasks. No arm gained a task over baseline or produced a mixed compositional success. The learned router produced no whole-program reuse.

## Economics and accounting

| Arm | Audited solves | Total graph steps | CPU / wall seconds | Steps per solve |
|---|---:|---:|---:|---:|
| Primitive | 60/120 | 31,978,509 | 115.34 / 116.74 | 532,975 |
| Fixed injection | 50/120 | 28,742,986 | 115.71 / 117.39 | 574,860 |
| Learned router | 42/120 | 36,464,921 | 134.97 / 136.44 | 868,212 |

These arm totals include setup. Every task stayed within its strict 450k inclusive cap; exact validation, final audit, retention, indexing, memory utility and router persistence are charged. All arms share 100k finalization headroom. This is not the earlier experiment's 450k search-only allowance, so raw counts should be compared within this experiment.

The single chronological fitting pass cost an additional 9,524,623 graph steps and 17.17 CPU / 17.48 wall seconds. Historical trace generation had already cost 73,603,011 task-level steps and was not rerun; it must not be treated as free experience in an end-to-end economics claim. Forced-method diagnostics cost 6,923,668 extra steps, while the paid-consultation replay diagnostics executed another 4,454,551. Diagnostic work is separate from online arm costs and never feeds the router. The full evaluation harness, including isolated diagnostic execution and snapshot overhead, took 391.17 CPU / 395.88 wall seconds.

## Integrity and limits

Eighteen tests passed before freezing. The source, training trace, model and parameter-history hashes passed audit. Every one of the 34 deterministic model updates also matched an independent integer-arithmetic replay. Evaluation snapshots preserve the same weights and threshold. Executable expanded programs stayed at length <=5; nested/cache charging remained intact. Exact validation and final audit were rerun for successful programs. Twelve retained method instances passed 192 held-out audit cases; final false positives were zero.

The model learned from earlier logged interventions, not from an on-policy deployment. Training traces used the old search-only budget, while evaluation used the stricter inclusive budget. That distribution shift and the single-pass optimization are limitations. This experiment does not demonstrate that a linear model cannot represent a useful router, nor justify a neural replacement.

## Next architecture boundary

Cheaper consultation is the immediate requirement because it explains every lost solve. A separate metadata-only router could remove task-time method probes and expensive agreement-feature extraction. But inference itself is costly here: removing probes alone does not make a 33k-step dot-product/score path negligible. Its generic numeric representation and cost must also be measured. Physical cache speedups alone would not reduce the fully charged logical budget used by this experiment.

A metadata-only version needs its own pre-execution features and training; the present weights cannot simply be reused because they depend on behavioral probe agreement. It must still measure useful false negatives so rejection of everything cannot count as success. No such new policy or tuning sweep was started, and the current experiment remains frozen.
