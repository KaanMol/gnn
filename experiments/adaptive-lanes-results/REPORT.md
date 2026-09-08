# Adaptive probes and borrowing

Same four frozen planning orders; 120 task presentations per arm, 450k total search steps. Same scorer, memory manager, task examples, validation and nested charging. Up to four retrieved methods receive independent fair-search lanes alongside the primitive lane.

| Arm | Solved | Total graph steps | CPU seconds | Mixed successes |
|---|---:|---:|---:|---:|
| no_memory | 40/120 | 43,164,952 | 151.82 | 0 |
| memory | 40/120 | 43,592,382 | 157.19 | 0 |

## Per-order outcomes

| Seed | Arm | Solved | Methods | Memory transitions beyond probe | Primitive transitions beyond floor |
|---:|---|---:|---:|---:|---:|
| 15053 | no_memory | 10/30 | 0 | 0 | 75 |
| 15053 | memory | 10/30 | 1 | 10 | 39 |
| 16057 | no_memory | 10/30 | 0 | 0 | 81 |
| 16057 | memory | 10/30 | 1 | 9 | 41 |
| 17077 | no_memory | 10/30 | 0 | 0 | 75 |
| 17077 | memory | 10/30 | 1 | 8 | 44 |
| 18089 | no_memory | 10/30 | 0 | 0 | 81 |
| 18089 | memory | 10/30 | 1 | 10 | 40 |

These counts require that a lane already exceeded its initial allowance before receiving another transition. They do not mistake one-transition probe overshoot for adaptive borrowing.

## Paired task differences

Memory gained 0 tasks and lost 0 against the same adaptive allocator without memory.

## Audited mixed programs

None.

## Integrity

Frozen source/task hashes match. All 4 retained method instances passed audit (64 held-out examples). Final false positives: 0. The lane scheduler was independently replayed from event records. Selected methods predate use, primitive-floor precedence and lane vocabularies match policy, and execution/routing/total costs were checked.

Total costs include retrieval, routing, duplicated lane work, retention, indexing, utility and online validation/audit. Post-run diagnostic audits are separate. No permanent memory deletion or new task teaching occurred.

## Frozen policy

Same relevance scores, widen to top four compatible positive-overlap memories. Independent fair-search lane per memory (that callable plus primitives), and a primitive-only lane. Primitive lane receives 100k execution steps first unless it solves/exhausts sooner. Then each live lane gets a 20k probe target, checked at completed-transition boundaries; these are opportunities, not caps. Remaining work goes to the highest recent positive agreement gain / execution cost, measured over four transitions; least total execution spent breaks ties. Drop memory lanes after eight non-improving transitions once probe target is reached; never stall-drop the primitive lane. No fixed lane caps or permanent partitions. Retrieval, routing, duplicated work and nested cached work all count toward total 450k.

## Limitations

- Same four previously evaluated planning orders; not held-out confirmation or cross-domain evidence.
- Independent lanes may repeat primitive work; all repetitions charged.
- Initial floor is execution work, so shared retrieval/routing add overhead. A solution can end the task before other probes occur.
- Probe target can overshoot by one completed transition. No promise of useful learning from a fixed probe allowance.
- Recent gain is heuristic and can favor misleading intermediate agreement. No semantic/action-specific routing.
- Only two arms: effect of this whole adaptive policy with memory, not separate ablations of probes, borrowing or stall thresholds.
- Memory manager, signature index, scorer, validation and task data unchanged. No further heuristic tuning after freezing.
