# Isolated online utility router

This experiment uses only experiment databases. It does not read or modify the live application database, replace existing retained methods, or rewrite previous experiment outputs.

The reliable search remains the frozen `fair_step`/`fair_choose`, with `shortcut_init` creating the same primitive state. The fixed comparator uses the previous shortcut retrieval/probe/injection graphs. The learned arm places a graph-authored linear utility predictor between a behavioral probe and injection. There are no memory lanes. When no method activates, the primitive trace is unchanged except for the exact measured overhead reducing its available budget.

## Fitting and freezing

A single chronological pass uses the earlier shortcut experiment's 34 single-activation outcomes. Features are reconstructed using current training examples, saved pre-activation probe observations, and the previous task's retained catalog. No final validation/audit result, task-family label, method identifier, operation name, or future utility statistic is a model input. Existing activation outcomes provide supervision after each logged task. This is incremental fitting from logged interventions, not an on-policy training run or a consolidation phase.

The six fixed-point features are bias, exact-example agreement fraction, changed-leaf agreement fraction, expanded primitive length divided by five, mean changed target leaves divided by 32, and historical wins divided by wins plus misses plus one. Features are clipped to [0,1000]. This small feature set intentionally omits semantics and method identity.

The model is linear. Each observed utility updates all weights with deterministic SGD, learning rate 1/5, clipped error [-2000,2000], and clipped weights [-4000,4000]. Utility is +1000 for gaining an audited solve, -2000 for losing a baseline solve, and normalized charged-work savings on jointly solved tasks. When both fail, only excess work receives negative utility. Tiny positive savings are kept positive. Logged activation cost includes its original probes/injection/validation/management and fitting-time feature/inference overhead. Update/persistence costs are reported in fitting totals; they do not retroactively change the recorded task outcome.

The policy is frozen before fitting. After that single pass, parameters and the model hash are frozen before any evaluation. Evaluation outcomes never update the model. Router state persists the frozen model and proposal ordinal; model snapshots are also recorded per task. Training snapshots record every weight transition.

## Activation

Only probe-positive, executable methods are eligible. Predicted utility must exceed 100, with at least five supervised updates. Scores in [-100,100] may explore at most one proposal per twenty considered, using a deterministic ordinal quota. Otherwise uncertainty defers to primitive search. Exploration receives the same charged injection and search execution as other activation. Rejections never remove long-term memory.

## Evaluation and costs

Four new seeds (210011, 220009, 230003, 240007), with 30 tasks each, come from the existing planning generator. Their order sequences differ from the fitting orders. This tests held-out orders within the same generator family, not general computational transfer or guaranteed disjoint individual examples.

All arms have a strict 450k total task cap. A common 100k finalization allowance leaves at most 350k for search, retrieval, probes, router inference and injection. Finalization charges exact validation, feedback, unchanged retention/utility/indexing, final audit, and router persistence. This differs from earlier experiments' 450k search-only caps; compare the three arms within this experiment. Nested execution and cache hits remain charged, and executable expanded length is capped at five. The old host CPU timeout is not an additional stopping criterion in this harness; graph budgets determine stopping.

Setup and fitting costs are reported separately from task costs. Graph persistence is logically metered; physical database and JSON logging overhead is represented by measured wall/CPU time rather than an invented byte-to-graph-step conversion. The full evaluation harness timing also includes cloning and diagnostic work.

For each rejected probe-positive method, an isolated copy of the pre-task state runs the forced activation as a diagnostic. These interventions cannot update the production evaluation history or router. Their budgets and costs are reported separately. A useful false negative requires a successful forced run that gains a solve or reduces total charged work versus the matched primitive arm. Incomplete probes are unmeasured opportunities, not confirmed negatives. Activation precision uses the same downstream definition; multiple activations on one task would receive shared task-level credit and must not be described as individually causal.

## Checks and outputs

Before freezing, 18 tests passed across router, shortcut and compositional modules. They cover deterministic learning, feature invariance to method/action renaming, uncertainty quota, signed downstream utility, rejection-path trace/cost equality, strict total budget, parameter immutability, learned composition, expanded-length caps and nested/cache charging.

Reproduce:

```sh
python3 -B -m unittest test_utility_router test_shortcut_search test_compositional_transfer
python3 -B experiments/audit_utility_router.py --output experiments/utility-router-results
```

The experiment directory contains the frozen manifest, fitted model and hash, incremental training history, task traces, counterfactual traces, and the final audit/report. No policy tuning is permitted after fitting or evaluation results are inspected.
