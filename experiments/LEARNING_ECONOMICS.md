# Sustained learning economics experiment

This experiment compares online composition retention against discarding each solution after a task. Both start with the same supplied graph library and no learned compositions. It does not migrate the live app or implement the proposed Rust/binary format.

## Frozen stream

Three seeds each generate 60 tasks, split into three 20-task phases. Each phase has eight presentations from newly introduced families, four opportunities to reuse earlier families, four irrelevant/control tasks, and four deliberately misleading tasks. Initial misleading examples make a selected-items rule agree with a plain aggregate; distinguishing validation examples break that agreement. Whether a learned method actually enters the trap is reported separately.

All inputs are generated before execution. Family, phase and role labels are reporting metadata, never retrieval inputs. The three schemas have supplied predicates/projectors. The family set is finite and engineered, with sum/count, optional selection, and scalar transformations. Maximum controls are not generally expressible. Every other target has an original-operation witness of length at most five.

## Graph-owned learner

`graph-authoring/learning-economics.mjs` emits five graph procedures:

- `economy_init` initializes a persistent catalog.
- `economy_prepare` retrieves the catalog, constructs prefix probes for the four most recent methods, and includes all methods in exhaustive search.
- `economy_validate` tests a discovered candidate against feedback examples.
- `economy_refine` adds that validation set as counterexamples for one retry.
- `economy_retain` stores validated multi-instruction solutions, rejecting single-call aliases and exact sequence duplicates.

Retention does not test semantic equivalence or whether a composition improves on a primitive. This is a known limitation to measure, not an optimization silently added after results are seen. A composition may call prior compositions. The search strategy and retention gates are supplied rules; the programs and catalog contents are learned.

## Accounting and audit

Each task gets 450,000 logical steps for retrieval, search and feedback refinement, shared across at most two search attempts. Validation and persistence have separately bounded executions; their full costs are included in totals rather than treated as free. Twenty final audit examples are evaluated after retention. They never influence learning, but their execution costs also appear in totals for both arms.

Graph steps are not a price for disk space or a complete proxy for CPU work. The report separately records inclusive CPU/wall time, SQLite row changes, database footprint and growth. Initial setup is included. Benchmark reporting and the independent post-run integrity/expressibility audit are not learning costs.

Report cumulative results and last-20-task steps per solved task at tasks 20, 40 and 60. A sustained crossover requires lower cumulative steps and at least as many audit-passing tasks through every remaining prefix of the finite stream. A few late fast tasks do not establish amortization.

## Reproduce

Run from the repository root with a fresh output directory:

```sh
node graph-authoring/learning-economics.mjs
python3 -B -m unittest test_learning_economics test_adaptive_reuse test_reuse_benchmark -q
python3 -B experiments/learning_economics.py --output /tmp/new-learning-economics
python3 -B experiments/audit_learning_economics.py --output /tmp/new-learning-economics
```

The output includes a hashed manifest and source hashes, six isolated databases, an incremental trial ledger, summaries, an integrity/expressibility audit and post-run behavioral-overlap diagnostics. A failed or existing run is not overwritten. The audit does not tune the learner or rerun searches.

The recorded run is in `learning-economics-results/`. Read `FINDINGS.md` and `REPORT.md` for results, `report.json` for detailed accounting and `audit.json` for expanded learned compositions and finite behavioral fingerprints.
