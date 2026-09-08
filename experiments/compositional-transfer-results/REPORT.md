# Generic compositional reuse: frozen follow-up

Same previously evaluated text/tree/planning tasks; 450,000 search graph steps, expanded length at most five, empty initial learned libraries. All three conditions use the same expanded-length guard. This is an architectural follow-up, not a fresh held-out confirmation.

| Environment | No memory | Whole-program | Compositional | Successful mixed programs | Composition steps / no memory | Composition CPU / no memory |
|---|---:|---:|---:|---:|---:|---:|
| planning | 30/60 | 30/60 | 30/60 | 0 | 1.003 | 1.092 |
| text | 10/60 | 10/60 | 10/60 | 0 | 1.005 | 1.020 |
| tree | 20/60 | 20/60 | 20/60 | 0 | 1.006 | 1.027 |

## Per-stream diagnostics

| Environment | Seed | Arm | Solved | Methods | Mixed candidates evaluated | Over-length rejected |
|---|---:|---|---:|---:|---:|---:|
| planning | 7109 | no_memory | 15/30 | 0 | 0 | 0 |
| planning | 7109 | whole_program | 15/30 | 2 | 0 | 0 |
| planning | 7109 | compositional | 15/30 | 2 | 269 | 0 |
| planning | 8111 | no_memory | 15/30 | 0 | 0 | 0 |
| planning | 8111 | whole_program | 15/30 | 2 | 0 | 0 |
| planning | 8111 | compositional | 15/30 | 2 | 291 | 0 |
| text | 7109 | no_memory | 5/30 | 0 | 0 | 0 |
| text | 7109 | whole_program | 5/30 | 0 | 0 | 0 |
| text | 7109 | compositional | 5/30 | 0 | 0 | 0 |
| text | 8111 | no_memory | 5/30 | 0 | 0 | 0 |
| text | 8111 | whole_program | 5/30 | 0 | 0 | 0 |
| text | 8111 | compositional | 5/30 | 0 | 0 | 0 |
| tree | 7109 | no_memory | 10/30 | 0 | 0 | 0 |
| tree | 7109 | whole_program | 10/30 | 0 | 0 | 0 |
| tree | 7109 | compositional | 10/30 | 0 | 0 | 0 |
| tree | 8111 | no_memory | 10/30 | 0 | 0 | 0 |
| tree | 8111 | whole_program | 10/30 | 0 | 0 | 0 |
| tree | 8111 | compositional | 10/30 | 0 | 0 | 0 |

## Successful compositions

None. Generic composability was implemented and exercised, but this run did not produce an audited mixed-program solution.

## Integrity and interpretation

Frozen source and task hashes match. All 8 stored-method audits passed (128 examples). Final false positives: 0.

If text/tree acquire no multi-operation methods, their outcomes remain acquisition/search failures, not evidence against compositional transfer. A tie in planning shows this particular generic composition/search policy was insufficient at this budget; it does not establish impossibility, necessity, or a unique cause. Generic composition mechanics were tested with isolated fixtures, never seeded into benchmark libraries.

The previous study used a different candidate evaluator without the new expanded-length guard. Its historical 30/60 planning result is context; the primary causal comparisons are the freshly rerun matched controls here.

## Limitations

- Same previously evaluated tasks: this is a controlled architectural follow-up, not held-out confirmatory evidence.
- Text/tree may not acquire multi-operation methods within this budget, preventing an informative reuse test.
- Shared fixed-sequence Data-to-Data interface and supplied environment primitives.
- Generic callable composition is newly supplied search machinery, not invented by the learner.
- Expanded length checks and management are charged. CPU/wall and storage reported separately.
- No seeded methods in the benchmark; test fixtures are isolated.
- Two seeds per environment; no post-run rescue.
