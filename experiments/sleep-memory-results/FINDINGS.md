# Sleep consolidation: coverage preserved, lifetime economics negative

The frozen 120-task experiment supports the narrower wake-path result but not the primary lifetime-economics hypothesis. Sleep-assisted search matched no-memory coverage at 60/120, with no primitive solves lost. Cheap routing and learned reuse reduced wake work by 10.5%. However, consolidation added 10,528,129 steps, so lifetime work was 39,116,630 versus 31,942,672 for no memory: 22.5% more for the same audited coverage. There was no cumulative crossover anywhere in the measured sequence, and the final cost was not repaid.

## Matched outcomes

| Arm | Audited solves | Current wake steps | Sleep steps | Lifetime steps | Steps per solve |
|---|---:|---:|---:|---:|---:|
| No memory | 60/120 | 31,942,672 | 0 | 31,942,672 | 532,378 |
| Online router | 41/120 | 37,122,519 | 0 | 120,250,249 | 2,932,933 |
| Sleep system | 60/120 | 28,588,501 | 10,528,129 | 39,116,630 | 651,944 |

The online-router lifetime column includes 83,127,730 steps of inherited trace acquisition and fitting, reported explicitly rather than treated as free. Its current-run wake cost is shown separately so that historical-cost accounting cannot obscure the comparison. The sleep arm started without a trained utility table. The decisive primary comparison is sleep versus no memory, both without inherited training cost.

Current-run no-memory CPU/wall was 111.13/111.73 seconds. Sleep wake CPU/wall was 108.63/109.96 seconds; consolidation added 40.02/40.19, giving 148.65/150.15 seconds in total. Online-router current-run CPU/wall was 135.12/136.08, with another 267.13/271.08 seconds of measured inherited fitting and trace-generation work. These measurements include each arm's setup; the report also preserves full harness timing.

## Wake routing worked as a cheap decision mechanism

The frozen key lookup cost 27–39 steps per task, median 33, totaling 4,086 across all 120 tasks. It used already-enriched current-example structure, with no method execution, utility fitting or numeric model inference to make the decision. Execution happened only after a method was admitted.

All 103 wake tasks with no admitted method matched a prefix of the primitive baseline's candidate trace, including identical per-transition charging. No primitive solve was lost after rejection or activation. The inherited online router lost 19 baseline solves while making zero activations; its consultation cost remained on the task path.

Sleep published no routes after tasks 20 or 40, one after 60, and two after 80, 100 and 120. Seventeen later activations produced seventeen useful audited whole-program reuses: 100% observed activation precision, zero negative-transfer activations. This is a small finite sample, not a guarantee for other contexts. There were no mixed compositional successes and no additional solved tasks beyond the primitive baseline.

The bounded replay diagnostics identified four useful-memory false negatives among 34 replayed rejected pairs whose methods already existed at the original wake task. Other opportunities were not exhaustively replayed and remain unknown. The false-negative count must not be presented as a complete census of every missed opportunity.

## Where consolidation cost went

| Work | Charged steps |
|---|---:|
| Forced completed-task replays | 8,683,002 |
| Downstream utility calculation | 1,683,487 |
| Model updates | 74,738 |
| Metadata consolidation, indexing and publication | 70,298 |
| Replay selection | 16,604 |
| Total sleep | 10,528,129 |

Six fixed sleeps performed 36 bounded interventions. Most replay interventions did not provide positive utility; the model learned from these outcomes as well as successes. The final sleep cost is included even though no future wake task could repay it. It alone does not explain the negative result: no earlier cumulative crossover occurred either.

Persistent storage is separate from graph compute. Final databases were 12,500,992 bytes for no memory, 14,913,536 for the online router, and 32,915,456 for sleep. Growth above setup was 0, 2,392,064 and 20,393,984 bytes respectively. The sleep database persists task experiences and traces as well as its model/index. Both memory arms ended with two globally retained methods; consolidation did not delete or edit those methods.

## Integrity and scope

Eleven tests passed before freezing. The source/stream hashes passed the final audit. Every sleep received only an explicitly completed experience prefix; all replay tasks and learned methods predated that boundary. Each wake read a table published at the preceding boundary, and every used method existed before use. No future audit answer or evaluation outcome entered an earlier routing decision.

All wake tasks stayed within the same inclusive 450k cap, with the shared 350k search ceiling and 100k finalization allowance. All sleep phases stayed within the frozen 6M cap. Replay costs exactly equal the sum of their fully charged wake-style runs, and all fitting, utility, indexing and publication work appears in the cumulative ledger. Nested learned execution and cache charging were preserved, and executable expanded length stayed at or below five. Successful programs were revalidated against exact held-out validation and final audits; the four retained method instances across memory arms passed 64 additional held-out cases. Audit false positives were zero.

The sequence uses new generated planning tasks/orders from the same supplied generator family. Structural context keys, tabular sufficient statistics and the confidence threshold are supplied generic mechanisms. The result does not show general semantic routing, arbitrary program learning, or cross-domain consolidation. The replay quota also limits the usefulness diagnostics.

The primary conclusion remains negative: this consolidation policy did not make experience pay for itself over the measured lifetime. The secondary controlled result is useful: moving learning off the wake path and using a cheap frozen lookup avoided the earlier rejection-overhead failure while permitting beneficial whole-program reuse. No policy, threshold, feature or schedule was tuned after evaluation began. No new sweep or live application change was made.

REPORT.md contains the main tables; audit.json contains every wake decision, observed usefulness signal, paired outcome and cumulative point. sleeps.jsonl preserves all model/table snapshots and charged replay histories. All previous experiment outputs remain preserved.
