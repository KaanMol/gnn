# Fair near-tie search allocation

This follow-up changes only the allocator. The previous priority scorer and memory graph rules remain frozen. It compares the same new search without retention and with managed memory at 450,000 search graph steps per task, expanded primitive length at most five, and full nested-call charging including cached calls.

After the unchanged root singleton layer, each selected partial program receives one child attempt and returns to the queue if more children remain. Among programs within five integer priority units of the current best, the allocator selects the one with the fewest child attempts so far. FIFO breaks equal service counts; reinserted parents go to the tail. Programs with clearly better scores still take precedence. A beam of 100 limits the queue, and exact expanded-program deduplication remains in place.

This provides quota fairness in child attempts for a fixed near-tied cohort. It does not equalize CPU/graph cost per parent, guarantee every candidate survives beam truncation, or make finite-budget search fully permutation-invariant. Newly discovered candidates and changing scores can change cohort membership. Initial callable ordering still comes from the unchanged manager.

Six new order seeds are fixed before evaluation: 9209, 10211, 11213, 12227, 13229 and 14243. They alternate between the two existing planning example banks. Each six-task block is shuffled, preserving the task mix and all training/validation/audit examples exactly. This is an order-only robustness test with 180 task presentations per arm, not fresh-example or cross-domain evidence. Both arms start each stream with empty learned libraries. The old allocator is not rerun on these permutations, so this experiment estimates the memory benefit under fair allocation, not an isolated causal effect of replacing the allocator.

All queue selection and scoring logic is executable graph data. Python supplies only the experiment schedule, budgets, metering and diagnostics. No domain-specific action preferences are introduced. Text/tree, memory capacity, subgraph extraction and consolidation are outside this run.

## Reproduction

Use a fresh output directory from the repository root:

```sh
python3 -B -m unittest test_fair_search test_compositional_transfer
python3 -B experiments/fair_search.py --freeze --output experiments/fair-reproduction
python3 -B experiments/fair_search.py --output experiments/fair-reproduction
python3 -B experiments/audit_fair_search.py --output experiments/fair-reproduction
```

The manifest checks every dependency frozen in the previous experiment, hashes the new rules and runner, and saves all task orders before search. No post-freeze tuning or seeded benchmark methods are permitted. Tests cover quota balance under permutations and near ties, one-child rotation, preference for clearly better scores, unchanged scorer/memory definitions, preserved task instances, expanded cost and cached nested work. Post-run audits check source hashes, exact task permutations, saved methods, prior acquisition of used methods, search budgets, beam bounds and monotonically advancing child cursors.
