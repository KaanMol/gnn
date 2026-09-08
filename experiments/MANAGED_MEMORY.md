# Managed memory implementation and evaluation

This is a separate graph-policy version. The original negative economics run is unchanged, and the live preview is not migrated.

## Implemented lifecycle

- Canonicalize discovered methods by expanding stored canonical definitions. For the fixed pure reduction language, retain optional selection and the reducer, collect exact doubling operations, and normalize negation parity. Reject unsupported operation sequences rather than rewriting arbitrary programs.
- Reject primitive aliases and duplicate canonical sequences. A successful transformed method is revalidated before storage; finite behavioral overlap is never used as an equivalence proof.
- Execute the original one-instruction search layer first, protecting simple tasks from unnecessary memory probes.
- Retrieve at most four active methods. Try each alone and with the supplied scalar continuation templates (double and negate), screening on two examples before full training evaluation.
- Cap the probe phase at one quarter of the task search allowance. Resume original-only exhaustive search at its saved position, without adding the entire learned library to its branching factor.
- Record actual probe outcomes. A validated use resets consecutive misses; 24 consecutively probed tasks without a validated use retire a method from retrieval. Its definition remains stored and executable.

These are supplied rules expressed in graph data. Applicability is tested behaviorally during probing; there is no learned semantic retrieval index. The retirement threshold is an experimental policy choice, not a discovered constant. Canonicalization is specific to the supplied pure reducer contracts, not a general optimizer for JavaScript, effects or partial operations.

## Evaluation

The three original 60-task streams are regression data. Three additional streams (seeds 4903, 5903 and 6907) were saved before implementation in `managed-memory-fresh-streams.json`, SHA256 `8c4b5050191e14619a91b7c1062a39248ecb86ab5f81c6b9f95341a34e4b4a30`.

All six streams compare:

1. Original discard baseline.
2. Managed retention.
3. The same managed scheduler with an empty, non-retaining catalog.

The third condition separates memory benefits from scheduler changes. It does not ablate every individual management component; separate canonicalization, screening and retirement ablations remain future work.

All arms use the same 450,000-step search allowance and at most one feedback retry. Management, failed probes/searches, validation, retention and final audit are charged. CPU/wall include SQLite operations; storage growth is recorded in bytes. Final audit occurs after retention and never updates the learner.

The post-run audit verifies every stored canonical method on the audit cases of its discovery task, in addition to the per-task audit of the selected candidate. This independent analysis is not learning feedback and is not counted as learning cost.

## Reproduce

From the repository root, use a new output directory:

```sh
node graph-authoring/managed-memory.mjs
python3 -B -m unittest test_managed_memory -q
python3 -B experiments/managed_memory.py --output /tmp/new-managed-memory
python3 -B experiments/audit_managed_memory.py --output /tmp/new-managed-memory
```

The recorded run is `managed-memory-results/`. The output includes the hashed manifest, source hashes, incremental trial ledger, isolated databases, learning windows and the final audit. It refuses to overwrite an existing run.

Beating the regression baseline alone does not establish a general fix. Report held-out-seed coverage, cumulative and final-window costs, baseline comparisons, false positives, active/total library size and physical growth. The fresh streams still use the same finite task generator and supplied input adapters; they do not test genuinely new domains or large libraries.
