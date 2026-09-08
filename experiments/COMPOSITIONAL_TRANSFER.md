# Generic callable composition follow-up

The original transfer run is preserved in `transfer-results`. This follow-up changes one architectural feature: retained methods can join the search alphabet in arbitrary positions alongside original operations. It uses the exact same task streams, so it is a controlled follow-up informed by previous results, not a held-out confirmation.

Three matched arms start with empty learned libraries: no memory, complete-program reuse, and compositional reuse. All use the same new expanded-length evaluator. The third arm prepends at most four active recent learned methods to the original alphabet after the shared singleton search and complete-program probes. It enumerates candidates by call count. Every candidate is expanded through the stored canonical primitive sequences and rejected if its expanded length exceeds five. Nested execution remains ordinary metered graph calls, including cache hits. Rejected candidates still pay enumeration and expansion costs.

The domain-independent graph rules are authored in `graph-authoring/compositional-transfer.mjs` and stored in `curriculum/compositional-transfer.json`. There are no environment-specific continuation templates. Python supplies the experimental schedule, budgets, metering and result records; graph rules generate, check, evaluate, validate, canonicalize and retain candidates. Learned definitions are stored as flattened primitive sequences after validation, but remain callable units in subsequent searches. This permits repeated composition while avoiding hidden uncharged macro length.

All three arms use the same candidate guard to avoid attributing its overhead to retention alone. Compare the newly rerun controls for causal claims. The historical planning baseline of 30/60 is a reference point only.

## Verification and reproduction

Isolated tests cover learned-call composition in text, tree and planning; generation of mixed candidates through the rank enumerator; retention of composed programs; further expansion through those methods; over-length rejection; and charging cached nested work. Test methods are never loaded into benchmark stores.

```sh
python3 -B -m unittest test_compositional_transfer
python3 -B experiments/compositional_transfer.py --freeze --output experiments/compositional-reproduction
python3 -B experiments/compositional_transfer.py --output experiments/compositional-reproduction
python3 -B experiments/audit_compositional_transfer.py --output experiments/compositional-reproduction
```

The run freezes task and source hashes and refuses to overwrite existing output. No rescue rules or task changes are made after freezing. Audit examples never feed learning. Reports distinguish mixed candidate attempts, audited mixed solutions, library acquisition, expanded-length rejections, logical costs, CPU/wall time, and storage growth.

No multi-operation acquisition in text/tree means those environments still cannot test useful compositional memory. A planning tie means this particular search policy is insufficient at this budget; it does not prove generic composition cannot help. A win must be traced to successful mixed programs and weighed against full learning and management costs.
