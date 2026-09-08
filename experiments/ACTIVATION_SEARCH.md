# Stored versus active memory

This isolated experiment compares no memory, all retained methods active, and top-1 retrieved memory with task-local eviction. It uses the exact four planning orders saved before the stopped ratio sweep. That sweep remains stopped. All arms use the same fair search/scorer and 450,000-step search budget, with expanded primitive length at most five and full nested execution charging.

Retained executable methods remain in the catalog. A separate index stores each method's input/output kinds, changed output leaf paths/values from its first validation example, and expanded length. The signature is computed once on retention in both memory arms. Activation scans this index and compares it with the first training example's changed target leaves. Ranking combines path/type/value overlap, output-kind agreement, expanded length, and existing global wins/misses. Input-incompatible or zero-overlap methods are excluded from top-1. Full training and separate validation/audit determine success; retrieval is only a heuristic.

The all-active control keeps every retained method active. Top-1 also evicts a method for the current task after eight attempted candidates containing it fail to improve its best example agreement. Evicted calls are excluded and pending branches containing them are removed. Catalog and index entries are not deleted; the method is eligible again on another task. This is a combined retrieval-and-eviction treatment, not a clean ablation of each component.

Both memory arms preserve 100,000 remaining search steps for primitive-only fallback initialization/search. Retrieval and memory search cannot consume that reserve. Unused memory-phase budget also passes to fallback. The two phases have separate frontiers, so repeated primitive work is charged. A valid solution can end search before fallback; the floor is available opportunity, not mandatory spending. No-memory runs use the full available budget for primitive search.

## Reproduction

```sh
python3 -B -m unittest test_activation_search test_compositional_transfer
python3 -B experiments/activation_search.py --freeze --output experiments/activation-reproduction
python3 -B experiments/activation_search.py --output experiments/activation-reproduction
python3 -B experiments/audit_activation_search.py --output experiments/activation-reproduction
```

Use a fresh output directory. Frozen hashes cover prior rules and new activation code. No post-freeze tuning occurs. Tests cover target-specific selection, all-active control, task-local eviction, blocking evicted calls, later reactivation, total accounting, primitive fallback, and cached nested work.

The graph rules are in `curriculum/activation-search.json`, authored by `graph-authoring/activation-search.mjs`. Python supplies experimental scheduling, limits and diagnostics. Context-conditioned statistics, semantic/LLM scores and large-library indexing are not implemented; the current filter is a linear metadata scan. This run does not change the running application, text/tree, memory capacity or subgraph abstraction.
