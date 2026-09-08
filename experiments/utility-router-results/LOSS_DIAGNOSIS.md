# Per-task routing diagnosis

A failed activated task is called an activation loss only if primitive search still solves after paying the same measured consultation cost. Otherwise consultation cost alone is sufficient; an additional activation effect is not identified. Rejected-memory losses have both exact trace-prefix and residual-budget replay checks.

{'joint_failure': 60, 'no_memory_considered': 5, 'decision_cost_loss': 18, 'true_neutral_rejection': 37}

| Seed / task | Baseline solved | Decision | Probe | Features / inference / decision | Activated | Primitive depth | Final solved | Diagnosis |
|---|---|---|---:|---:|---|---:|---|---|
| 210011 / 0 | False | none | 0 | 0 / 0 / 0 | False | 4 | False | joint_failure |
| 210011 / 1 | True | none | 0 | 0 / 0 / 0 | False | 2 | True | no_memory_considered |
| 210011 / 2 | True | router_reject | 13,423 | 47,316 / 33,513 / 5,938 | False | 4 | False | decision_cost_loss |
| 210011 / 3 | False | probe_reject | 7,119 | 24,847 / 48,988 / 5,481 | False | 5 | False | joint_failure |
| 210011 / 4 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 210011 / 5 | True | probe_reject | 7,972 | 26,641 / 46,589 / 11,841 | False | 1 | True | true_neutral_rejection |
| 210011 / 6 | False | probe_reject | 7,108 | 24,847 / 48,988 / 7,981 | False | 5 | False | joint_failure |
| 210011 / 7 | True | router_reject | 13,731 | 47,331 / 33,513 / 7,996 | False | 4 | False | decision_cost_loss |
| 210011 / 8 | True | probe_reject | 8,718 | 26,655 / 46,589 / 8,280 | False | 1 | True | true_neutral_rejection |
| 210011 / 9 | False | probe_reject | 11,625 | 24,430 / 50,118 / 12,244 | False | 2 | False | joint_failure |
| 210011 / 10 | True | router_reject | 10,986 | 39,481 / 45,529 / 9,341 | False | 2 | True | true_neutral_rejection |
| 210011 / 11 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 210011 / 12 | True | router_reject | 13,492 | 47,331 / 33,513 / 14,021 | False | 4 | False | decision_cost_loss |
| 210011 / 13 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 210011 / 14 | True | router_reject | 10,282 | 39,464 / 45,529 / 6,636 | False | 2 | True | true_neutral_rejection |
| 210011 / 15 | True | probe_reject | 8,859 | 26,655 / 46,589 / 11,717 | False | 1 | True | true_neutral_rejection |
| 210011 / 16 | False | probe_reject | 8,227 | 24,847 / 48,988 / 10,575 | False | 5 | False | joint_failure |
| 210011 / 17 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 210011 / 18 | True | router_reject | 10,792 | 39,481 / 45,529 / 12,694 | False | 2 | True | true_neutral_rejection |
| 210011 / 19 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 210011 / 20 | True | router_reject | 13,492 | 47,331 / 33,513 / 11,381 | False | 4 | False | decision_cost_loss |
| 210011 / 21 | True | probe_reject | 8,220 | 26,641 / 46,589 / 10,273 | False | 1 | True | true_neutral_rejection |
| 210011 / 22 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 210011 / 23 | False | probe_reject | 6,913 | 24,847 / 48,988 / 9,596 | False | 5 | False | joint_failure |
| 210011 / 24 | True | probe_reject | 7,734 | 26,641 / 46,589 / 14,984 | False | 1 | True | true_neutral_rejection |
| 210011 / 25 | True | router_reject | 10,685 | 39,481 / 45,529 / 10,690 | False | 2 | True | true_neutral_rejection |
| 210011 / 26 | False | probe_reject | 11,387 | 58,918 / 46,816 / 12,040 | False | 2 | False | joint_failure |
| 210011 / 27 | True | router_reject | 13,303 | 47,331 / 33,513 / 4,721 | False | 4 | False | decision_cost_loss |
| 210011 / 28 | False | probe_reject | 7,452 | 24,847 / 48,988 / 7,485 | False | 5 | False | joint_failure |
| 210011 / 29 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 220009 / 0 | True | none | 0 | 0 / 0 / 0 | False | 5 | True | no_memory_considered |
| 220009 / 1 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 220009 / 2 | False | probe_reject | 9,020 | 24,847 / 48,988 / 5,938 | False | 5 | False | joint_failure |
| 220009 / 3 | True | probe_reject | 8,428 | 26,655 / 46,589 / 5,480 | False | 1 | True | true_neutral_rejection |
| 220009 / 4 | True | probe_timeout | 15,000 | 0 / 0 / 0 | False | 2 | True | true_neutral_rejection |
| 220009 / 5 | False | probe_timeout, probe_reject | 26,713 | 58,918 / 46,816 / 11,841 | False | 2 | False | joint_failure |
| 220009 / 6 | False | probe_reject | 7,287 | 24,847 / 48,988 / 7,981 | False | 5 | False | joint_failure |
| 220009 / 7 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 220009 / 8 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 220009 / 9 | True | router_reject | 10,001 | 43,050 / 37,292 / 7,877 | False | 4 | False | decision_cost_loss |
| 220009 / 10 | True | probe_reject | 9,967 | 26,641 / 46,589 / 8,280 | False | 1 | True | true_neutral_rejection |
| 220009 / 11 | True | probe_timeout, router_reject | 24,807 | 39,464 / 45,529 / 12,127 | False | 2 | True | true_neutral_rejection |
| 220009 / 12 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 220009 / 13 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 220009 / 14 | True | router_reject | 10,164 | 43,065 / 37,292 / 9,341 | False | 4 | False | decision_cost_loss |
| 220009 / 15 | True | probe_timeout, router_reject | 24,207 | 39,447 / 45,529 / 13,903 | False | 2 | True | true_neutral_rejection |
| 220009 / 16 | False | probe_reject | 9,557 | 24,847 / 48,988 / 6,754 | False | 5 | False | joint_failure |
| 220009 / 17 | True | probe_reject | 10,924 | 26,641 / 46,589 / 11,717 | False | 1 | True | true_neutral_rejection |
| 220009 / 18 | True | router_reject | 9,275 | 43,035 / 37,292 / 10,457 | False | 5 | False | decision_cost_loss |
| 220009 / 19 | True | probe_reject | 9,370 | 26,641 / 46,589 / 12,811 | False | 1 | True | true_neutral_rejection |
| 220009 / 20 | False | probe_reject | 8,731 | 24,847 / 48,988 / 11,382 | False | 5 | False | joint_failure |
| 220009 / 21 | False | probe_timeout, probe_reject | 27,235 | 24,430 / 50,118 / 10,274 | False | 2 | False | joint_failure |
| 220009 / 22 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 220009 / 23 | True | probe_timeout, router_reject | 25,461 | 39,481 / 45,529 / 9,478 | False | 2 | True | true_neutral_rejection |
| 220009 / 24 | True | router_reject | 11,206 | 43,065 / 37,292 / 14,867 | False | 4 | False | decision_cost_loss |
| 220009 / 25 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 220009 / 26 | True | probe_timeout, router_reject | 25,266 | 39,481 / 45,529 / 10,690 | False | 2 | True | true_neutral_rejection |
| 220009 / 27 | True | probe_reject | 9,637 | 26,641 / 46,589 / 12,040 | False | 1 | True | true_neutral_rejection |
| 220009 / 28 | False | probe_reject | 9,242 | 24,847 / 48,988 / 4,721 | False | 5 | False | joint_failure |
| 220009 / 29 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 230003 / 0 | True | none | 0 | 0 / 0 / 0 | False | 1 | True | no_memory_considered |
| 230003 / 1 | False | none | 0 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 230003 / 2 | True | none | 0 | 0 / 0 / 0 | False | 5 | True | no_memory_considered |
| 230003 / 3 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 4 | False | joint_failure |
| 230003 / 4 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 230003 / 5 | True | probe_timeout | 15,000 | 0 / 0 / 0 | False | 2 | True | true_neutral_rejection |
| 230003 / 6 | True | probe_reject | 9,554 | 26,627 / 46,589 / 5,937 | False | 1 | True | true_neutral_rejection |
| 230003 / 7 | True | probe_timeout, router_reject | 24,612 | 39,464 / 45,529 / 5,363 | False | 2 | True | true_neutral_rejection |
| 230003 / 8 | False | probe_reject | 9,036 | 24,847 / 48,988 / 11,842 | False | 5 | False | joint_failure |
| 230003 / 9 | False | probe_timeout, probe_reject | 26,689 | 24,430 / 50,118 / 7,980 | False | 2 | False | joint_failure |
| 230003 / 10 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 230003 / 11 | True | router_reject | 11,258 | 43,065 / 37,292 / 7,877 | False | 4 | False | decision_cost_loss |
| 230003 / 12 | True | probe_timeout, router_reject | 24,418 | 39,464 / 45,529 / 8,163 | False | 2 | True | true_neutral_rejection |
| 230003 / 13 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 230003 / 14 | False | probe_timeout, probe_reject | 26,666 | 58,918 / 46,816 / 12,244 | False | 2 | False | joint_failure |
| 230003 / 15 | True | router_reject | 9,612 | 43,050 / 37,292 / 9,341 | False | 5 | False | decision_cost_loss |
| 230003 / 16 | False | probe_reject | 8,439 | 24,847 / 48,988 / 14,020 | False | 5 | False | joint_failure |
| 230003 / 17 | True | probe_reject | 9,789 | 26,641 / 46,589 / 6,753 | False | 1 | True | true_neutral_rejection |
| 230003 / 18 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 230003 / 19 | True | router_reject | 10,610 | 43,050 / 37,292 / 11,599 | False | 4 | False | decision_cost_loss |
| 230003 / 20 | False | probe_timeout, probe_reject | 25,850 | 58,918 / 46,816 / 10,574 | False | 2 | False | joint_failure |
| 230003 / 21 | True | probe_timeout, router_reject | 25,153 | 39,481 / 45,529 / 12,694 | False | 2 | True | true_neutral_rejection |
| 230003 / 22 | False | probe_reject | 10,332 | 24,847 / 48,988 / 11,382 | False | 5 | False | joint_failure |
| 230003 / 23 | True | probe_reject | 9,637 | 26,641 / 46,589 / 10,273 | False | 1 | True | true_neutral_rejection |
| 230003 / 24 | False | probe_reject | 8,244 | 24,847 / 48,988 / 9,596 | False | 5 | False | joint_failure |
| 230003 / 25 | True | probe_reject | 10,188 | 26,655 / 46,589 / 14,984 | False | 1 | True | true_neutral_rejection |
| 230003 / 26 | True | router_reject | 11,207 | 43,050 / 37,292 / 10,690 | False | 4 | False | decision_cost_loss |
| 230003 / 27 | True | probe_timeout, router_reject | 23,974 | 39,464 / 45,529 / 11,923 | False | 2 | True | true_neutral_rejection |
| 230003 / 28 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 230003 / 29 | False | probe_timeout, probe_timeout | 30,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 240007 / 0 | True | none | 0 | 0 / 0 / 0 | False | 2 | True | no_memory_considered |
| 240007 / 1 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 240007 / 2 | False | probe_reject | 11,068 | 58,903 / 46,816 / 5,937 | False | 2 | False | joint_failure |
| 240007 / 3 | True | router_reject | 13,423 | 47,316 / 33,513 / 5,481 | False | 4 | False | decision_cost_loss |
| 240007 / 4 | False | probe_reject | 7,381 | 24,847 / 48,988 / 11,842 | False | 5 | False | joint_failure |
| 240007 / 5 | True | probe_reject | 8,595 | 26,655 / 46,589 / 7,980 | False | 1 | True | true_neutral_rejection |
| 240007 / 6 | True | router_reject | 14,019 | 47,331 / 33,513 / 7,996 | False | 4 | False | decision_cost_loss |
| 240007 / 7 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 240007 / 8 | False | probe_reject | 6,605 | 24,847 / 48,988 / 8,280 | False | 5 | False | joint_failure |
| 240007 / 9 | True | router_reject | 11,030 | 39,481 / 45,529 / 12,127 | False | 2 | True | true_neutral_rejection |
| 240007 / 10 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 240007 / 11 | True | probe_reject | 9,149 | 26,655 / 46,589 / 9,459 | False | 1 | True | true_neutral_rejection |
| 240007 / 12 | True | probe_reject | 8,746 | 26,655 / 46,589 / 14,020 | False | 1 | True | true_neutral_rejection |
| 240007 / 13 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 240007 / 14 | False | probe_reject | 7,108 | 24,847 / 48,988 / 6,754 | False | 5 | False | joint_failure |
| 240007 / 15 | True | router_reject | 12,437 | 47,316 / 33,513 / 11,718 | False | 4 | False | decision_cost_loss |
| 240007 / 16 | True | router_reject | 10,435 | 39,481 / 45,529 / 10,458 | False | 2 | True | true_neutral_rejection |
| 240007 / 17 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 240007 / 18 | True | probe_reject | 8,248 | 26,641 / 46,589 / 12,811 | False | 1 | True | true_neutral_rejection |
| 240007 / 19 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 3 | False | joint_failure |
| 240007 / 20 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 240007 / 21 | False | probe_reject | 6,288 | 24,847 / 48,988 / 11,382 | False | 5 | False | joint_failure |
| 240007 / 22 | True | router_reject | 13,365 | 47,316 / 33,513 / 10,274 | False | 4 | False | decision_cost_loss |
| 240007 / 23 | True | router_reject | 9,612 | 39,464 / 45,529 / 9,478 | False | 2 | True | true_neutral_rejection |
| 240007 / 24 | False | probe_timeout | 15,000 | 0 / 0 / 0 | False | 5 | False | joint_failure |
| 240007 / 25 | True | router_reject | 13,702 | 47,331 / 33,513 / 14,984 | False | 4 | False | decision_cost_loss |
| 240007 / 26 | False | probe_reject | 7,603 | 24,847 / 48,988 / 10,808 | False | 5 | False | joint_failure |
| 240007 / 27 | True | probe_reject | 8,250 | 26,655 / 46,589 / 12,040 | False | 1 | True | true_neutral_rejection |
| 240007 / 28 | True | router_reject | 11,030 | 39,481 / 45,529 / 4,603 | False | 2 | True | true_neutral_rejection |
| 240007 / 29 | False | probe_reject | 10,264 | 58,903 / 46,816 / 7,484 | False | 2 | False | joint_failure |

Primitive depth is the maximum expanded length among executable primitive-only candidate attempts; equal depth does not imply the same candidates or amount of search.

True neutral rejection means both arms audited-solved with no activation; it does not claim zero computational overhead.
