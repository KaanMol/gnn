# Controlled graph reuse benchmark

21 tasks across three supplied input schemas; two repetitions per condition. No model calls.

| Condition | Step budget per task | Tasks passed / 21 | Median CPU s | Search steps, 21 tasks | Steps including learning |
|---|---:|---:|---:|---:|---:|
| baseline | 150,000 | 6/21 | 0.5649 | 2,616,494 | 2,616,494 |
| reuse_a | 150,000 | 9/21 | 0.5408 | 2,383,921 | 2,680,087 |
| reuse_ab | 150,000 | 9/21 | 0.4667 | 2,412,557 | 3,387,499 |
| baseline | 450,000 | 12/21 | 1.0561 | 6,249,386 | 6,249,386 |
| reuse_a | 450,000 | 12/21 | 1.2405 | 5,713,430 | 6,009,596 |
| reuse_ab | 450,000 | 12/21 | 0.5728 | 5,231,109 | 6,206,051 |
| baseline | 1,350,000 | 12/21 | 1.0720 | 14,349,386 | 14,349,386 |
| reuse_a | 1,350,000 | 15/21 | 1.2306 | 11,880,648 | 12,176,814 |
| reuse_ab | 1,350,000 | 15/21 | 0.5823 | 11,223,090 | 12,198,032 |

Learned on separate training tasks:
- `bench_learned_selected_sum` = synth_select → synth_sum; discovery cost 293,995 graph steps.
- `bench_learned_doubled_selected_sum` = bench_learned_selected_sum → bench_double; discovery cost 676,605 graph steps.

The frozen library hash is `b546d35025ed16d7722e656329d555bb3b03af6117b6402fa4ce9dd57f005ff2`. The baseline has the same supplied operations and adapters; only reuse conditions may select learned macros. Calls inside macros remain metered. All conditions allow depth five.

| Budget | Task family | Original only | Reuse A | Reuse A+B |
|---:|---|---:|---:|---:|
| 150,000 | selected_sum | 0/3 | 3/3 | 3/3 |
| 150,000 | selected_double_sum | 0/3 | 0/3 | 3/3 |
| 150,000 | selected_negative_double_sum | 0/3 | 0/3 | 0/3 |
| 150,000 | plain_sum | 3/3 | 3/3 | 3/3 |
| 150,000 | selected_count | 0/3 | 0/3 | 0/3 |
| 150,000 | plain_double_sum | 3/3 | 3/3 | 0/3 |
| 150,000 | maximum_control | 0/3 | 0/3 | 0/3 |
| 450,000 | selected_sum | 3/3 | 3/3 | 3/3 |
| 450,000 | selected_double_sum | 0/3 | 0/3 | 3/3 |
| 450,000 | selected_negative_double_sum | 0/3 | 0/3 | 0/3 |
| 450,000 | plain_sum | 3/3 | 3/3 | 3/3 |
| 450,000 | selected_count | 3/3 | 3/3 | 0/3 |
| 450,000 | plain_double_sum | 3/3 | 3/3 | 3/3 |
| 450,000 | maximum_control | 0/3 | 0/3 | 0/3 |
| 1,350,000 | selected_sum | 3/3 | 3/3 | 3/3 |
| 1,350,000 | selected_double_sum | 0/3 | 3/3 | 3/3 |
| 1,350,000 | selected_negative_double_sum | 0/3 | 0/3 | 0/3 |
| 1,350,000 | plain_sum | 3/3 | 3/3 | 3/3 |
| 1,350,000 | selected_count | 3/3 | 3/3 | 3/3 |
| 1,350,000 | plain_double_sum | 3/3 | 3/3 | 3/3 |
| 1,350,000 | maximum_control | 0/3 | 0/3 | 0/3 |

Steps and candidates below are conditional on finding a solution; conditions may solve different task subsets. The JSON report also includes paired comparisons on jointly solved tasks.

| Condition | Budget | Median steps to solution | Median candidates to solution | Direct learned-method use |
|---|---:|---:|---:|---|
| baseline | 150,000 | 60854.0 | 6.0 | {'bench_learned_selected_sum': 0, 'bench_learned_doubled_selected_sum': 0} |
| reuse_a | 150,000 | 58846.0 | 7.0 | {'bench_learned_selected_sum': 3, 'bench_learned_doubled_selected_sum': 0} |
| reuse_ab | 150,000 | 87678.0 | 7.0 | {'bench_learned_selected_sum': 3, 'bench_learned_doubled_selected_sum': 3} |
| baseline | 450,000 | 205319.5 | 18.0 | {'bench_learned_selected_sum': 0, 'bench_learned_doubled_selected_sum': 0} |
| reuse_a | 450,000 | 92698.5 | 9.5 | {'bench_learned_selected_sum': 3, 'bench_learned_doubled_selected_sum': 0} |
| reuse_ab | 450,000 | 97588.5 | 7.5 | {'bench_learned_selected_sum': 3, 'bench_learned_doubled_selected_sum': 3} |
| baseline | 1,350,000 | 205319.5 | 18.0 | {'bench_learned_selected_sum': 0, 'bench_learned_doubled_selected_sum': 0} |
| reuse_a | 1,350,000 | 125592.0 | 12.0 | {'bench_learned_selected_sum': 6, 'bench_learned_doubled_selected_sum': 0} |
| reuse_ab | 1,350,000 | 106195.0 | 8.0 | {'bench_learned_selected_sum': 3, 'bench_learned_doubled_selected_sum': 3} |

Paired comparisons below use only tasks solved by both conditions. Ratios above 1 mean reuse cost more graph steps.

| Reuse condition | Budget | Jointly solved tasks | Median step ratio to baseline |
|---|---:|---:|---:|
| reuse_a | 150,000 | 6 | 1.057 |
| reuse_ab | 150,000 | 3 | 1.015 |
| reuse_a | 450,000 | 12 | 1.057 |
| reuse_ab | 450,000 | 9 | 1.015 |
| reuse_a | 1,350,000 | 12 | 1.057 |
| reuse_ab | 1,350,000 | 12 | 1.343 |

Learned-method use including nested calls (unique solved tasks):

| Condition | Budget | A including nested use | B including nested use |
|---|---:|---:|---:|
| baseline | 150,000 | 0 | 0 |
| reuse_a | 150,000 | 3 | 0 |
| reuse_ab | 150,000 | 6 | 3 |
| baseline | 450,000 | 0 | 0 |
| reuse_a | 450,000 | 3 | 0 |
| reuse_ab | 450,000 | 6 | 3 |
| baseline | 1,350,000 | 0 | 0 |
| reuse_a | 1,350,000 | 6 | 0 |
| reuse_ab | 1,350,000 | 6 | 3 |

Post-search baseline witness checks passed for all 18 non-control tasks (828 training/held-out cases). Witnesses use at most four original operations and were never supplied to the learner. See expressibility.json.

Average the two evaluation repetitions; add learning/promotion cost once to each 21-task evaluation cohort, not once across both repetitions.

Limitations:
- Fixed six supplied primitives and two learned whole-solution macros.
- Predicates/projections are supplied to all arms; domain labels do not demonstrate semantic understanding.
- Graph-step budgets include candidate generation, errors and nested macro calls; validation and Python overhead appear in CPU/wall measurements.
- Two repetitions estimate timing noise; correlated task families are not independent evidence of broad generality.
- Macro vocabulary order is fixed and appended; ordering affects search.
- Maximum-control tasks have no general solution in this candidate language.
- This is a finite, hand-designed benchmark, not open-ended capability discovery.
- Learning cost is included once per independent 21-task cohort; repetitions do not double amortization opportunities.
