# Stored versus active memory

Same four frozen planning orders from the stopped ratio sweep; 120 task presentations per arm. All conditions share the fair scorer/search and 450k budget. Memory treatments preserve 100k for primitive-only fallback. Top-k is top-1 retrieval plus task-local eviction; all-active keeps all retained methods active.

| Arm | Solved | Graph steps | CPU seconds | Mixed successes | Task-local evictions |
|---|---:|---:|---:|---:|---:|
| no_memory | 60/120 | 38,005,254 | 124.74 | 0 | 0 |
| all_active | 50/120 | 36,453,503 | 137.65 | 0 | 0 |
| top_k | 49/120 | 37,155,741 | 133.81 | 0 | 2 |

## Per-order results

| Seed | Arm | Solved | Methods retained |
|---:|---|---:|---:|
| 15053 | no_memory | 15/30 | 0 |
| 15053 | all_active | 10/30 | 1 |
| 15053 | top_k | 10/30 | 1 |
| 16057 | no_memory | 15/30 | 0 |
| 16057 | all_active | 15/30 | 2 |
| 16057 | top_k | 14/30 | 2 |
| 17077 | no_memory | 15/30 | 0 |
| 17077 | all_active | 15/30 | 2 |
| 17077 | top_k | 15/30 | 2 |
| 18089 | no_memory | 15/30 | 0 |
| 18089 | all_active | 10/30 | 1 |
| 18089 | top_k | 10/30 | 1 |

## Paired differences

- Top-k versus no_memory: 0 extra tasks, 11 lost tasks.
- Top-k versus all_active: 0 extra tasks, 1 lost tasks.

## Audited mixed solutions

None.

## Integrity

Frozen hashes and retained definitions match. All 12 retained method instances passed post-run audit (192 examples). Final false positives: 0. Every indexed signature matches its retained validation example, and no retained method was removed from the index. Activation uses only previously acquired methods. Top-1 bounds, eviction exclusion, original-only fallback and budget accounting were checked.

Totals include retrieval, search, utility updates, retention, signature indexing and final online audit, plus setup. The index is scanned linearly; this does not establish cheap retrieval at large library sizes. Global utility is used, not context-conditioned or semantic relevance.

## Frozen policy

Three arms: no retention; all retained methods active without eviction; top-1 input-compatible method with positive stored-effect overlap plus task-local eviction after eight non-improving attempted uses. Rank uses changed-leaf path/type/value overlap, output-kind agreement, expanded length and global wins/misses. Effect signatures indexed once upon retention in both memory arms. First training example supplies the retrieval target signature; full training and independent validation/audit govern acceptance. Memory-guided phase and retrieval must preserve 100k remaining steps for original-only fallback initialization/search; unused memory budget falls through to fallback. No deletion from long-term catalog/index. Both memory arms share retention and primitive fallback.

## Limitations

- Same four partially evaluated orders from the stopped sweep, not fresh confirmatory data. That sweep remains stopped.
- Top-k plus eviction is a combined treatment; there is no separate ablation isolating either component.
- Index scan is linear in retained methods; no large-library scaling claim.
- Global wins/misses are used; context-conditioned utility and semantic/LLM routing are not implemented.
- Signatures use one stored validation example and one current training example, so retrieval can be misleading.
- Eight non-improving candidate attempts is a supplied policy, not learned.
- Memory phase and fallback use separate frontiers; repeated work is fully charged. A fallback floor is not a guarantee of solving every new target.
- No app migration, text/tree, abstraction extraction or adaptive borrowing experiment.
