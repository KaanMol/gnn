# Frozen wake/sleep memory consolidation

This is an isolated experiment. Existing application code, live databases and prior experiment outputs remain untouched. The implementation is graph-authored in `graph-authoring/sleep-memory.mjs`, emitted to `curriculum/sleep-memory.json`, with experiment orchestration in `experiments/sleep_memory.py`.

## Frozen schedule and controls

One sequence of 120 tasks is generated from four new planning seeds and concatenated before evaluation. All three arms see that exact sequence: unchanged primitive search, the inherited frozen online utility router, and cold-start sleep-trained memory. `fair_step` and `fair_choose` remain unchanged. The common inclusive wake cap is 450k logical steps, with a 350k search ceiling and 100k finalization headroom, as in the preceding router experiment.

Sleep occurs after every 20 tasks, including the final task. Each sleep has a 6M cap and at most six forced task/method replay interventions. Candidate pairs come from the latest six completed tasks and up to three retained methods, after exact expanded-sequence metadata deduplication. Least-observed context/method pairs are prioritized. The model retains sufficient statistics from all prior sleep cycles. This is bounded replay, not exhaustive re-evaluation of the history.

## Cheap wake decisions

The primitive initializer already enriches current training examples with changed scalar leaves. Wake routing adds only the input/output root kinds and the ordered kinds of those leaves in the first example, joined into a table key. It reads a frozen index and chooses at most one method. No scalar values, field paths, operation names or task-family labels appear in the key. There is no task-time fitting, numeric utility-model inference, or execution of a method to decide whether it should be admitted.

After admission, the selected method executes on current examples and may enter the normal candidate queue. This is charged activation work, not a probe used for routing. Its expansions still pass the existing length <=5 guard and exact nested/cache charging. Rejecting a key leaves the primitive state unchanged. The pre-freeze contract fixture measured fewer than 128 routing steps and exact residual-budget primitive trace equality.

Task outcomes and traces are persisted after completion. Newly validated retained methods enter long-term storage under the unchanged retention rules. They cannot appear in the active routing index until a later sleep publication.

## Sleep learning

Sleep receives only a completed prefix of experience, including completed audits. It cannot access the future task stream through its API. Current retained methods may be replayed on those older tasks. Each replay runs in an isolated graph-store copy, includes all wake/activation/search/finalization work, and is compared with that completed task's matched primitive baseline.

Supervision is downstream utility: +1000 for gaining an audited solve, -2000 for losing a baseline solve, normalized charged-work saving for jointly solved tasks, and nonpositive overhead when both fail. Local progress is not the learning target. The tabular model tracks count, summed utility, positive outcomes, lost solves and zero-utility outcomes for each structural context/method pair.

A routing entry requires at least two positive outcomes, mean utility above 50 milli-utility, and no observed lost baseline solve. The highest eligible mean wins per context. The whole table is replaced at sleep boundaries and stays frozen between them. These are supplied generic confidence heuristics, not calibrated statistical bounds. Coarse structural keys may alias distinct behaviors.

Consolidation deduplicates indexed metadata only by exact expanded instruction sequence. It does not delete or edit globally retained methods, introduce equivalence rules, or generate domain-specific routing hints.

## Costs and diagnostics

All replay, utility calculation, model updates, metadata deduplication, selection and table publication are charged to sleep. Wake charges routing, activation, nested/cached calls, unsuccessful search, validation, retention, audit and experience persistence. Each graph-store copy's physical work is reflected in sleep CPU/wall; graph operations are charged by the unchanged logical meter. Persistent database growth is reported separately.

Cumulative totals add sleep work at its actual boundary, including the last sleep. Crossover requires at least baseline audited coverage and lower cumulative cost after any scheduled sleep at that boundary; a temporary crossover is not a final economic win.

The inherited online-router arm is shown both with current-run wake cost and with its historical trace-acquisition/fitting cost. The sleep arm receives no pretrained table. Post-run verification audits are diagnostics, not sleep-learning inputs; all final task audits and counterfactual replay audits are already included in lifetime cost.

Useful-memory false negatives are measured among the bounded sleep replays whose methods already existed and were rejected at the original wake task. Other rejected opportunities remain unmeasured. This limitation must accompany the metric. Activation precision and negative transfer use matched task outcomes; whole-program reuse is separated from mixed compositions.

## Reproduction and checks

Before freezing, 11 tests passed across sleep and nested-composition modules, covering rejection trace/cost equality, cheap lookup without method execution, exclusion of semantic names/extra audit fields from context, downstream confidence updates, rejection of future experiences, replay quota, exact metadata deduplication, global retention, end-to-end charged consolidation, expanded-length guards and cache/nested charging.

```sh
python3 -B -m unittest test_sleep_memory test_compositional_transfer
python3 -B experiments/audit_sleep_memory.py --output experiments/sleep-memory-results
```

The frozen manifest, task traces, sleep histories, routing tables, cumulative ledger and findings live in `sleep-memory-results`. No thresholds, features, intervals, budgets or utility rules may be tuned after evaluation begins.
