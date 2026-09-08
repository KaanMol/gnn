# Frozen transfer experiment

This experiment tests the boundary of the existing memory manager across text transformations, tree zipper edits, and simulated stateful planning. It does not change the running application.

## Conditions

- `discard`: search using the environment primitives, with no retained programs.
- `exact_frozen`: the original manager, including its original host vocabulary binding. The original reduction primitives are unavailable. This deliberately exposes interface incompatibility; it is not a fair measure of an already ported manager's search quality.
- `rules_disabled`: the same scheduler body with the environment vocabulary bound explicitly, exact ordered sequence deduplication, and singleton retained-program probes. Two graph rules replace the reduction-specific canonicalizer and continuation policy.
- `disabled_no_memory`: the same adapted scheduler without retention, controlling for scheduler differences.

Each environment has two seeds, 30 tasks per seed, four training examples, six feedback validation examples, and 16 isolated final audit examples per task. All arms receive the same supplied environment primitives. The search budget is 450,000 logical graph steps with maximum sequence length five and at most two attempts. Validation, feedback, retention, utility updates, and final audit costs are separately recorded and included in totals. CPU time, wall time, and database growth are also recorded.

All task streams, policies, and source hashes are saved before evaluation in `transfer-results/manifest.json`. No post-result domain rescue is permitted in this run. Final audits do not feed learning. The independent reference implementation creates expected outputs; candidate execution uses graph-defined environment operations.

## Boundaries included by construction

Text digit deletion and planning gate unlocking require missing operations. Full variable-depth tree mirroring and variable-length goal-reaching exceed the available fixed-sequence representation. Other targets have supplied reference witnesses within the length bound, checked after the run on all example splits. Failure on those representable targets can expose search-budget limits.

The disabled condition retains and probes complete solutions. It does not search new compositions containing learned method names. Positive economics would therefore demonstrate bounded whole-program reuse under an explicit adapter, not unrestricted hierarchical abstraction discovery. All three environments still share sequential composition.

## Reproduction

From the repository root, use a fresh output directory:

```sh
python3 -B -m unittest test_transfer
python3 -B experiments/transfer_test.py --freeze --output experiments/transfer-reproduction
python3 -B experiments/transfer_test.py --output experiments/transfer-reproduction
python3 -B experiments/audit_transfer.py --output experiments/transfer-reproduction
```

The runner refuses to overwrite an existing stream. The auditor checks frozen hashes, manager definitions, accounting, retained methods, and representable target witnesses, then produces the boundary report. Post-run diagnostic audits are separate from the online learning costs.
