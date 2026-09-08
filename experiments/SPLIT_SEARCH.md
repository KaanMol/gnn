# Discovery/reuse reservation sweep

This experiment adds fixed search-budget reservations while preserving the fair allocator, scorer, primitive vocabulary, expanded-length limit, nested execution charging and memory policy.

The three ratios are **discovery/reuse: 25/75, 50/50 and 75/25**. Discovery enumerates only supplied primitives. Reuse enumerates supplied primitives plus the unchanged manager's selected learned callables. The two frontiers evolve independently. At each completed transition, the graph scheduler chooses the active lane with the smaller consumed fraction of its cap. Both lanes retain the existing one-child fair allocation policy internally.

Caps are calculated from the total budget remaining after shared initialization. Scheduling itself also consumes the total 450,000-step search budget, so lane caps are ceilings, not promises of exact delivered work. A lane cannot borrow another lane's reservation. A graph transition that reaches its cap is charged and stops that lane; the engine does not resume inside a partially executed transition. Distinct lanes may repeat candidate work, and all such work, including cache hits, remains charged.

When no learned methods are available, both vocabularies are identical and collapse to one full-budget frontier. Therefore all three ratios have identical no-memory behavior; the benchmark uses one shared no-memory control rather than three repeated controls. Isolated tests verify this equivalence.

## Frozen comparisons

Four new order seeds—15053, 16057, 17077 and 18089—permute the two existing planning example banks. They are fixed before search evaluation and shared by all ratios. There are 120 task presentations per condition, 480 trials total. These are new orders, not new examples or new computational domains. Every stream begins with an empty learned library.

The primary outcomes are paired wins and losses against no memory, full computational cost, and actual mixed-program solutions. Post-run acquisition accounting additionally asks whether a multi-operation target's exact reference sequence was absent from the catalog before the task and was solved after other methods had already accumulated. This is a narrow behavioral accounting definition; target witnesses never enter search priority or scheduling.

## Reproduction

Use a fresh directory from the repository root:

```sh
python3 -B -m unittest test_split_search test_compositional_transfer
python3 -B experiments/split_search.py --freeze --output experiments/split-reproduction
python3 -B experiments/split_search.py --output experiments/split-reproduction
python3 -B experiments/audit_split_search.py --output experiments/split-reproduction
```

The graph rules live in `curriculum/split-search.json`, authored by `graph-authoring/split-search.mjs`. Python supplies experiment scheduling, budget enforcement and diagnostics. All previous source hashes and all new orders are frozen. No post-freeze tuning, memory features, text/tree changes or abstraction machinery are added.

Tests check graph-defined caps and weighted selection, collapse equivalence, per-lane limits, total accounting, original-only discovery and cached nested costs. Post-run audits check exact task permutations, immutable prior dependencies, saved methods, method chronology, per-lane cursor progression, caps and charging.
