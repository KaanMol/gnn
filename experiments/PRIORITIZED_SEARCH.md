# Planning-only generic search allocation

This experiment changes search allocation only. It preserves the memory rules, supplied primitives, two existing planning streams, expanded length limit of five, and nested execution charging. It leaves text/tree and subgraph abstraction untouched.

Two arms start with empty learned libraries: prioritized search without retention, and the same search with the existing managed memory. Both use the same graph allocator. There is no separate complete-program probe phase. The frozen memory manager still selects at most four active recent methods; those methods join the ordinary callable vocabulary.

## Generic priority

The graph traverses each training target into scalar paths, then excludes paths whose target value already equals the original input value. For an executable partial program it measures the fraction of the remaining target leaves matched by its output. This is a heuristic focus on requested changes, not a rule about planning fields or actions. Exact full-output equality still determines success, including unchanged fields and empty containers.

The integer priority, lowest first, is:

`expanded length - 1,000,000 × fully matched training examples - floor(1,000 × summed per-example changed-leaf agreement)`

The allocator evaluates all children of the selected partial program, then selects the best queued partial program, regardless of call depth. The queue holds at most 100 entries. Ties preserve generation order. Failed executable prefixes are not expanded; identical expanded instruction sequences are deduplicated. Every scored candidate obeys the expanded length bound. Queue management, feature construction, scoring, canonicalization and execution are all graph operations charged to the search budget. No admissible-heuristic or completeness claim is made.

The generic allocator is authored in `graph-authoring/prioritized-search.mjs` and emitted to `curriculum/prioritized-search.json`. The Python runner supplies experimental scheduling, limits, metering and diagnostics. No engine or memory-rule edits are required.

## Reproduction

From the repository root, choose a fresh directory:

```sh
python3 -B -m unittest test_prioritized_search test_compositional_transfer
python3 -B experiments/prioritized_search.py --freeze --output experiments/priority-reproduction
python3 -B experiments/prioritized_search.py --output experiments/priority-reproduction
python3 -B experiments/audit_prioritized_search.py --output experiments/priority-reproduction
```

The manifest preserves exact parent task data and hashes all previously frozen dependencies plus the new allocator. The runner refuses to overwrite results. No policy tuning occurs after freezing. Independent final audits never feed learning.

Tests cover changed-leaf extraction and field renaming, generic callable search, choosing a deeper promising queue entry over shallower entries, expanded-length rejection, exact deduplication, hard search budgets, and the existing cached nested-cost checks. Test fixtures are not seeded into benchmark libraries.

Primary interpretation: compare audited paired task outcomes under the two new arms. A useful compositional gain must include a previously acquired learned method combined with other operations. Report subsequent complete-program reuse separately. These are two previously evaluated planning streams; even a gain is not fresh or cross-domain confirmation.
