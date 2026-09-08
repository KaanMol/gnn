# Next experiment: managed compositional memory

Status: proposed next version. The completed retention experiment remains unchanged.

## Motivation

The frozen three-stream experiment produced 37/60 solved tasks per stream without retention, versus 22, 23 and 24 with retention and recency-based prefix search. This is evidence against that specific accumulation policy. It is not a general impossibility result for compositional retention or cumulative intelligence.

The next version should manage a method's lifecycle, not merely retrieve more accurately:

1. Discover a candidate method.
2. Validate behavior using learning feedback, separate from final audit.
3. Simplify/canonicalize using explicit justified graph transformations.
4. Compare with existing methods and primitives.
5. Reject redundancy, merge appropriate evidence, or retain a distinct method.
6. Index by measured applicability evidence.
7. Retrieve a small candidate subset within a search budget.
8. Update utility from subsequent use, charging that measurement.
9. Retire consistently harmful methods from search eligibility.

Discovery, comparison, simplification, indexing and lifecycle rules should themselves be graph programs. The engine remains generic. The rules are supplied unless and until the system independently learns them.

## Distinctions to preserve

- Identical canonical forms can justify deduplication under the specified rules. Matching a few examples only establishes empirical overlap, not semantic equivalence.
- Simplification must preserve relevant types, preconditions, effects and error behavior. A value-level arithmetic identity does not automatically justify rewriting an arbitrary effectful or partial program.
- Retiring a method from retrieval is different from deleting its graph. Retained methods may still call it; preserve dependencies, evidence and active snapshots.
- Merge provenance and validation evidence without claiming unsupported applicability. A method's name is not evidence of understanding a domain.
- Counterfactual utility checks, exploration and indexing are not free. Count every additional execution and storage operation in the same economics report.
- Keep audit data isolated. No retirement, retention or routing update may use final audit answers.

## Acceptance criteria

Use the existing hashed streams as fixed regression tests. Beat the 37/60 discard result on each stream while improving total cost per solved task after charging all management work. Report cumulative costs, final-window costs, failures, library size, active retrieval-set size and storage growth; do not collapse them into one favorable metric.

Also require a sustained cumulative advantage with at least as many solved tasks, rather than a transient crossover. The baseline and managed version must have the same original primitives, search allowances and permitted feedback.

These streams are now known development data. Freeze additional unseen streams before evaluating the new manager, including useful, irrelevant and actually triggered misleading reuse. Passing the old streams alone is not evidence of generalization or resolution of large-library scaling.

Retain the unmodified discard and retention conditions as ablations. Separately measure canonicalization/deduplication, retrieval changes and utility-based retirement so any benefit can be attributed rather than bundled into an unexplained new system.
