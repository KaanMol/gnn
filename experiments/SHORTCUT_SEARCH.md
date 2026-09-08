# Behavioral shortcut injection

This experiment keeps `fair_step` and `fair_choose` unchanged. There is one ordinary queue, no memory lanes and no reservation of search budget. `shortcut_init` constructs the exact primitive-only fair-search state without asking the memory manager to populate its vocabulary. A contract test compares that state to the original `fair_init` with an empty library. Both arms use this initializer; its charged initialization cost is explicit.

Memory is an optional pre-search proposal stage. A graph retrieves the last three active retained entries. Each is executed against all current training examples, with a 15k logical-step probe ceiling and a shared 45k ceiling for retrieval and probes. These are ceilings on actual work, not amounts reserved from primitive search. A timeout or failed probe makes no search-state change. The probe accepts only executable methods that improve exact example matches over identity or produce positive agreement on changed target leaves. This uses the existing domain-independent scorer, not action names. Whole-program exact matches still pass ordinary held-out validation and final audit.

Accepted entries become queued partial programs, with the same expanded-cost/progress priority as other candidates. They also become callable extensions appended after the supplied primitives. Thus a queued learned method can compose with primitives or another accepted method, and primitive prefixes can call accepted methods. The existing beam, tie allocation, canonicalization and expanded-length limit of five remain unchanged. Accepted expanded programs enter the existing seen set; duplicate primitive expansions may therefore be skipped after successful activation. Successful activation is allowed to affect search order; whether that helps is the experiment.

All lookup, probes, injection, initialization and search work share the 450k cap. Nested learned execution, including cache hits, retains the existing logical charge. Feedback deducts from the remaining search allowance. Existing validation, retention, indexing, utility and final-audit operations remain unchanged and are included in reported total online work, outside the search cap. Post-run audits are separate diagnostic work.

Task-local rejection never deletes or retires a globally stored method. Existing retention and utility rules are unchanged. The same previously evaluated four planning orders are used; this is not fresh-order or cross-domain generalization.

Before freezing, nine tests passed across the shortcut and compositional test modules. Explicit checks cover identical rejected-probe primitive traces at the residual budget, equal per-transition charges, full-budget prefix agreement, retained catalog integrity, exact primitive initialization, mixed learned/primitive and learned/learned execution, expanded-length rejection, whole reuse, budget accounting and nested cache charges. No policy tuning is permitted after evaluation begins.

Reproduce checks:

```sh
python3 -B -m unittest test_shortcut_search test_compositional_transfer
python3 -B experiments/audit_shortcut_search.py --output experiments/shortcut-search-results
```

The frozen manifest hashes the implementation, graph source, generated curriculum, tests and auditor. Results are written to `shortcut-search-results`; do not overwrite a completed run. Report mixed compositions separately from whole-program reuse. Attribute an additional solved task directly to injection only when the audited successful program contains a method injected on that task and the paired baseline failed. That trace criterion is narrower than a separate causal ablation of memory history.
