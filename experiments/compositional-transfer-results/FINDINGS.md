# What the compositional follow-up established

Generic learned callables are implemented in graph rules and tested across all three environments. The benchmark did not demonstrate a transfer benefit from this search policy at the frozen budget.

All three matched conditions tied: planning 30/60, text 10/60, and tree 20/60. Planning evaluated 560 mixed candidates containing learned calls, but found no audited mixed solution. It used about 0.3% more total graph steps and 9.2% more CPU than no memory, including setup costs. Text and tree acquired no multi-operation methods, so they remain acquisition/search failures rather than informative negative tests of compositional memory.

In planning, all ten delivery tasks exhausted their search budget at call depth two. The learned pickup method could be composed with west and drop to express delivery in three calls, expanding to four primitives. The isolated implementation test verifies that this composition executes correctly. The actual benchmark never reached that candidate depth. This is a specific enumeration bottleneck; it does not establish that no other domain-independent search policy could benefit from the learned methods.

The next useful change would target acquisition and candidate allocation rather than simply adding more seeds or more callable names. It should remain generic across environments, retain expanded-length and nested-execution charging, and be tested separately against these preserved results. No such follow-up search improvement is claimed here.

The audit confirmed frozen sources and identical task streams, checked that learned calls predated their use, and validated all eight stored-method instances on 128 held-out cases. There were zero final audit false positives and no retirements. Over-length rejection and cached nested-cost charging passed isolated tests, but this benchmark never searched deep enough to exercise an over-length rejection.

See REPORT.md and report.json for the full comparison. These are experimental rules and runners; the running application was not migrated or restarted.
