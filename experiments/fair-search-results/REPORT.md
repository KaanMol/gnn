# Fair search allocation: fresh planning orders

Six freshly frozen permutations of two existing example banks: 180 task presentations per arm. Vocabulary, scoring, expanded length five, 450,000-step search budget and memory rules are unchanged. Both arms use the same fair allocator and start each stream with empty learned libraries. These are fresh orders, not fresh examples.

| Seed | Arm | Solved | Total graph steps | CPU seconds | Stored methods | Mixed successes |
|---:|---|---:|---:|---:|---:|---:|
| 9209 | no_memory | 15/30 | 9,475,791 | 27.62 | 0 | 0 |
| 9209 | managed_memory | 15/30 | 8,250,939 | 26.11 | 2 | 0 |
| 10211 | no_memory | 15/30 | 9,446,244 | 28.83 | 0 | 0 |
| 10211 | managed_memory | 10/30 | 9,804,052 | 31.84 | 1 | 0 |
| 11213 | no_memory | 15/30 | 9,475,791 | 29.26 | 0 | 0 |
| 11213 | managed_memory | 10/30 | 9,806,996 | 32.59 | 1 | 0 |
| 12227 | no_memory | 15/30 | 9,446,244 | 30.68 | 0 | 0 |
| 12227 | managed_memory | 15/30 | 8,232,544 | 29.25 | 2 | 0 |
| 13229 | no_memory | 15/30 | 9,475,791 | 31.09 | 0 | 0 |
| 13229 | managed_memory | 15/30 | 8,236,562 | 29.39 | 2 | 0 |
| 14243 | no_memory | 15/30 | 9,446,244 | 31.97 | 0 | 0 |
| 14243 | managed_memory | 15/30 | 8,209,841 | 29.98 | 2 | 0 |

## Direct paired differences

- Seed 10211, task 3 (round_trip): no memory wins; memory calls: None.
- Seed 10211, task 10 (round_trip): no memory wins; memory calls: None.
- Seed 10211, task 13 (round_trip): no memory wins; memory calls: None.
- Seed 10211, task 20 (round_trip): no memory wins; memory calls: None.
- Seed 10211, task 29 (round_trip): no memory wins; memory calls: None.
- Seed 11213, task 5 (round_trip): no memory wins; memory calls: None.
- Seed 11213, task 6 (round_trip): no memory wins; memory calls: None.
- Seed 11213, task 14 (round_trip): no memory wins; memory calls: None.
- Seed 11213, task 23 (round_trip): no memory wins; memory calls: None.
- Seed 11213, task 29 (round_trip): no memory wins; memory calls: None.

## Audited mixed programs

No successful solution combined a learned callable with other operations.

## Family diagnostics

| Seed | Arm | Family | Solved / 5 | Maximum evaluated call depth |
|---:|---|---|---:|---:|
| 9209 | no_memory | charge | 5/5 | 1 |
| 9209 | no_memory | deliver | 0/5 | 5 |
| 9209 | no_memory | pickup | 5/5 | 2 |
| 9209 | no_memory | reach_goal | 0/5 | 4 |
| 9209 | no_memory | round_trip | 5/5 | 5 |
| 9209 | no_memory | unlock | 0/5 | 5 |
| 9209 | managed_memory | charge | 5/5 | 1 |
| 9209 | managed_memory | deliver | 0/5 | 4 |
| 9209 | managed_memory | pickup | 5/5 | 2 |
| 9209 | managed_memory | reach_goal | 0/5 | 3 |
| 9209 | managed_memory | round_trip | 5/5 | 5 |
| 9209 | managed_memory | unlock | 0/5 | 4 |
| 10211 | no_memory | charge | 5/5 | 1 |
| 10211 | no_memory | deliver | 0/5 | 5 |
| 10211 | no_memory | pickup | 5/5 | 2 |
| 10211 | no_memory | reach_goal | 0/5 | 4 |
| 10211 | no_memory | round_trip | 5/5 | 5 |
| 10211 | no_memory | unlock | 0/5 | 5 |
| 10211 | managed_memory | charge | 5/5 | 1 |
| 10211 | managed_memory | deliver | 0/5 | 4 |
| 10211 | managed_memory | pickup | 5/5 | 2 |
| 10211 | managed_memory | reach_goal | 0/5 | 3 |
| 10211 | managed_memory | round_trip | 0/5 | 4 |
| 10211 | managed_memory | unlock | 0/5 | 5 |
| 11213 | no_memory | charge | 5/5 | 1 |
| 11213 | no_memory | deliver | 0/5 | 5 |
| 11213 | no_memory | pickup | 5/5 | 2 |
| 11213 | no_memory | reach_goal | 0/5 | 4 |
| 11213 | no_memory | round_trip | 5/5 | 5 |
| 11213 | no_memory | unlock | 0/5 | 5 |
| 11213 | managed_memory | charge | 5/5 | 1 |
| 11213 | managed_memory | deliver | 0/5 | 4 |
| 11213 | managed_memory | pickup | 5/5 | 2 |
| 11213 | managed_memory | reach_goal | 0/5 | 4 |
| 11213 | managed_memory | round_trip | 0/5 | 4 |
| 11213 | managed_memory | unlock | 0/5 | 5 |
| 12227 | no_memory | charge | 5/5 | 1 |
| 12227 | no_memory | deliver | 0/5 | 5 |
| 12227 | no_memory | pickup | 5/5 | 2 |
| 12227 | no_memory | reach_goal | 0/5 | 4 |
| 12227 | no_memory | round_trip | 5/5 | 5 |
| 12227 | no_memory | unlock | 0/5 | 5 |
| 12227 | managed_memory | charge | 5/5 | 1 |
| 12227 | managed_memory | deliver | 0/5 | 4 |
| 12227 | managed_memory | pickup | 5/5 | 2 |
| 12227 | managed_memory | reach_goal | 0/5 | 3 |
| 12227 | managed_memory | round_trip | 5/5 | 5 |
| 12227 | managed_memory | unlock | 0/5 | 4 |
| 13229 | no_memory | charge | 5/5 | 1 |
| 13229 | no_memory | deliver | 0/5 | 5 |
| 13229 | no_memory | pickup | 5/5 | 2 |
| 13229 | no_memory | reach_goal | 0/5 | 4 |
| 13229 | no_memory | round_trip | 5/5 | 5 |
| 13229 | no_memory | unlock | 0/5 | 5 |
| 13229 | managed_memory | charge | 5/5 | 1 |
| 13229 | managed_memory | deliver | 0/5 | 4 |
| 13229 | managed_memory | pickup | 5/5 | 2 |
| 13229 | managed_memory | reach_goal | 0/5 | 3 |
| 13229 | managed_memory | round_trip | 5/5 | 5 |
| 13229 | managed_memory | unlock | 0/5 | 4 |
| 14243 | no_memory | charge | 5/5 | 1 |
| 14243 | no_memory | deliver | 0/5 | 5 |
| 14243 | no_memory | pickup | 5/5 | 2 |
| 14243 | no_memory | reach_goal | 0/5 | 4 |
| 14243 | no_memory | round_trip | 5/5 | 5 |
| 14243 | no_memory | unlock | 0/5 | 5 |
| 14243 | managed_memory | charge | 5/5 | 1 |
| 14243 | managed_memory | deliver | 0/5 | 5 |
| 14243 | managed_memory | pickup | 5/5 | 2 |
| 14243 | managed_memory | reach_goal | 0/5 | 3 |
| 14243 | managed_memory | round_trip | 5/5 | 5 |
| 14243 | managed_memory | unlock | 0/5 | 5 |

## Integrity

Task/source hashes and frozen memory definitions match. All 10 stored methods passed post-run audit (160 cases). Final audit false positives: 0. Every used method predates its task. Evaluated expansions satisfy the length limit; search budgets and queue bounds were checked.

Logical totals include search scoring, queue work, validation, utility, retention and final audit. CPU/wall include host/storage overhead and setup; post-run diagnostic audits are separate.

## Frozen policy

Frozen previous score and memory rules. Root singleton layer completes as before. Thereafter each parent receives one child attempt before returning to the queue. Among parents within five integer priority units of the best, choose the least-served (smallest next_i); FIFO breaks equal service counts. Returned parents go to the tail. Better scores outside that band retain priority. Beam 100; exact expanded-sequence dedup; expanded length <=5; all nested execution and allocation work charged. Fairness is by child attempts, not equal CPU or graph work per parent.

## Limits

- Six fresh task orders from two previously evaluated example banks; not fresh examples or cross-domain transfer.
- Same improved allocator in both arms; prior allocator is not rerun on these orders, so no isolated causal estimate of allocator improvement.
- Near-tie band five and one-child quota fixed before evaluation. No post-freeze tuning.
- Initial callable ordering remains inherited from the frozen memory manager; finite-budget results need not be invariant to every permutation.
- Scoring, memory selection, canonicalization, retention and utilities unchanged. No seeded learned methods.
- No text/tree, subgraph extraction, parameterization or consolidation changes.
