# Generic prioritized search: planning only

Frozen same 60 planning tasks, vocabulary, expanded length five and 450,000-step search budget. Memory rules unchanged. Both arms use the same new allocator, starting with no learned methods.

| Seed | Arm | Solved | Total graph steps | CPU seconds | Stored methods | Mixed successes |
|---:|---|---:|---:|---:|---:|---:|
| 7109 | no_memory | 15/30 | 8,323,023 | 27.78 | 0 | 0 |
| 7109 | managed_memory | 20/30 | 6,650,257 | 25.25 | 3 | 1 |
| 8111 | no_memory | 15/30 | 8,315,471 | 27.74 | 0 | 0 |
| 8111 | managed_memory | 15/30 | 7,961,210 | 28.09 | 2 | 0 |

## Direct paired differences

- Seed 7109, task 2 (deliver): memory wins; memory calls: ['allocated_0', 'plan_west', 'plan_drop'].
- Seed 7109, task 6 (deliver): memory wins; memory calls: ['allocated_2'].
- Seed 7109, task 14 (deliver): memory wins; memory calls: ['allocated_2'].
- Seed 7109, task 23 (deliver): memory wins; memory calls: ['allocated_2'].
- Seed 7109, task 26 (deliver): memory wins; memory calls: ['allocated_2'].

## Audited mixed programs

- Seed 7109, task 2 (deliver): ['allocated_0', 'plan_west', 'plan_drop'] → ['plan_east', 'plan_pick', 'plan_west', 'plan_drop'].

## Family diagnostics

| Seed | Arm | Family | Solved / 5 | Maximum evaluated call depth |
|---:|---|---|---:|---:|
| 7109 | no_memory | charge | 5/5 | 1 |
| 7109 | no_memory | deliver | 0/5 | 3 |
| 7109 | no_memory | pickup | 5/5 | 2 |
| 7109 | no_memory | reach_goal | 0/5 | 4 |
| 7109 | no_memory | round_trip | 5/5 | 2 |
| 7109 | no_memory | unlock | 0/5 | 3 |
| 7109 | managed_memory | charge | 5/5 | 1 |
| 7109 | managed_memory | deliver | 5/5 | 3 |
| 7109 | managed_memory | pickup | 5/5 | 2 |
| 7109 | managed_memory | reach_goal | 0/5 | 3 |
| 7109 | managed_memory | round_trip | 5/5 | 2 |
| 7109 | managed_memory | unlock | 0/5 | 3 |
| 8111 | no_memory | charge | 5/5 | 1 |
| 8111 | no_memory | deliver | 0/5 | 3 |
| 8111 | no_memory | pickup | 5/5 | 2 |
| 8111 | no_memory | reach_goal | 0/5 | 4 |
| 8111 | no_memory | round_trip | 5/5 | 2 |
| 8111 | no_memory | unlock | 0/5 | 4 |
| 8111 | managed_memory | charge | 5/5 | 1 |
| 8111 | managed_memory | deliver | 0/5 | 3 |
| 8111 | managed_memory | pickup | 5/5 | 2 |
| 8111 | managed_memory | reach_goal | 0/5 | 3 |
| 8111 | managed_memory | round_trip | 5/5 | 2 |
| 8111 | managed_memory | unlock | 0/5 | 3 |

## Integrity

Task/source hashes and frozen memory definitions match. All 5 stored methods passed post-run audit (80 cases). Final audit false positives: 0. Every used method predates its task. Evaluated expansions satisfy the length limit; search budgets and queue bounds were checked.

Logical totals include search scoring, queue work, validation, utility, retention and final audit. CPU/wall include host/storage overhead and setup; post-run diagnostic audits are separate.

## Frozen policy

Best-first queue capped at 100 partial programs. Complete all children of the selected parent, then choose lowest priority. Integer priority = expanded primitive length - 1000000 * full training-example matches - floor(1000 * sum of per-example fractions of changed target scalar leaves already matched). Scalar target leaves equal to input at the same path are excluded from heuristic only. Full output equality remains acceptance. Exact expanded-sequence dedup; failed executable prefixes pruned; successful prefixes below expanded length five queued. All callables use the same expansion rule. Up to four recent active methods selected by unchanged memory manager. No whole-program probe phase.

## Limits

- Planning only, two previously evaluated streams: architectural diagnostic, not fresh confirmation or cross-domain transfer evidence.
- Heuristic is newly supplied generic search machinery. No planning action or field names occur in allocator rules.
- Partial scoring ignores unchanged target leaves and empty containers; full equality still validates solutions.
- Priority is heuristic, not an admissible remaining-cost estimate. Beam truncation may discard useful candidates.
- All scoring, canonicalization, queue and execution graph work is charged; host CPU, wall time and storage are separately reported.
- Memory canonicalization, retention, routing and utility rules unchanged. No seeded learned methods.
- No post-freeze tuning; text/tree untouched.
