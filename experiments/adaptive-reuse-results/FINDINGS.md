# Findings from the completed adaptive reuse experiment

All results below use the frozen run in report.json. The budgets and search policies were not changed after evaluation.

| Per-task graph budget | Originals only | Fixed A+B | Evidence selection | Evidence + prefix extension |
|---:|---:|---:|---:|---:|
| 150,000 | 3/21 | 7/21 | 7/21 | 5/21 |
| 450,000 | 9/21 | 12/21 | 12/21 | 12/21 |
| 1,350,000 | 12/21 | 15/21 | 15/21 | 18/21 |

The prefix condition discovered `bench_learned_doubled_selected_sum → bench_negate` on all three supplied schemas at the 450,000 budget. The doubled-sum macro itself calls the previously learned selected-sum macro. The expanded program is select → sum → double → negate. This target family was absent from macro training and evidence calibration. It was not discovered by the other three conditions at any tested budget.

This is recursive use of learned whole-solution compositions under a supplied prefix-search policy. It is not independent invention of the policy, extraction of arbitrary intermediate subgraphs, or discovery of a new primitive operation.

At the largest budget, prefix search consumed 10,909,236 graph steps per 21-task cohort versus the baseline's 15,484,794. Including macro learning and the full evidence calibration/validation cost, it consumed 18,864,312: more than the baseline. The total cost of fixed A+B was 13,332,096. The more capable search did not repay its calibration overhead in this batch.

Both macros had positive aggregate calibration utility, so the selection-only arm retained both and gained no additional solved tasks over fixed reuse. Negative-evidence rejection works in tests, but the main experiment does not demonstrate beneficial pruning or learned contextual routing.

All discovered solutions passed their 40 held-out cases. All 18 non-control tasks passed separate baseline witness checks (828 cases); their targets are expressible using at most four original operations. The three maximum controls were unsolved. Repeated search outcomes were identical. Families across supplied schemas are correlated, so these are not 21 independent domains.

Separately, the feedback-learning experiment inferred a boolean field predictor in each of two synthetic graph environments. It refused initially ambiguous evidence, chose one distinguishing probe from a supplied pool, and saved the surviving predictor. Both passed 40 held-out records. An unseen field rename returned unknown; learning from feedback in the renamed environment worked. This demonstrates bounded active hypothesis testing, not human semantic understanding.

All changes are isolated experiments. The live preview was not restarted or migrated. See ../ADAPTIVE_REUSE.md for reproduction and scope, REPORT.md for accounting and matched-task comparisons, and report.json for every trial and learned-method dependency.
