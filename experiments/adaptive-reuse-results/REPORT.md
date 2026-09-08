# Evidence-guided graph reuse

Fresh evaluation inputs; 21 tasks, four conditions, two repetitions. Search policies, evidence decisions and candidate execution are graph procedures. Python schedules and meters trials and supplies independent fixtures. No model calls.

| Budget | Condition | Solved / 21 | Median steps to solution | Median candidates | Steps including learning and calibration |
|---:|---|---:|---:|---:|---:|
| 150,000 | baseline | 3 | 21659.0 | 1.0 | 2,758,851 |
| 150,000 | fixed_ab | 7 | 100605.0 | 7.0 | 3,620,902 |
| 150,000 | evidence | 7 | 104980.0 | 7.0 | 10,632,042 |
| 150,000 | evidence_prefix | 5 | 22284.0 | 1.0 | 10,628,732 |
| 450,000 | baseline | 9 | 218392.0 | 11.0 | 7,316,537 |
| 450,000 | fixed_ab | 12 | 133015.0 | 7.5 | 6,814,925 |
| 450,000 | evidence | 12 | 138740.5 | 7.5 | 13,854,973 |
| 450,000 | evidence_prefix | 12 | 166406.5 | 10.0 | 13,848,344 |
| 1,350,000 | baseline | 12 | 297122.0 | 18.0 | 15,484,794 |
| 1,350,000 | fixed_ab | 15 | 150656.0 | 8.0 | 13,332,096 |
| 1,350,000 | evidence | 15 | 156449.0 | 8.0 | 20,397,119 |
| 1,350,000 | evidence_prefix | 18 | 229288.0 | 14.5 | 18,864,312 |

Macro learning/promotion: 974,942 graph steps. Evidence calibration: 6,980,134, including 3,832,226 for validation that influenced retention. Setup is charged once per 21-task cohort. Solution medians are conditional on success and compare different subsets.

## Matched-task comparison

Ratios greater than one indicate more work for reuse on tasks both conditions solved.

| Budget | Condition | Jointly solved | Median graph-step ratio |
|---:|---|---:|---:|
| 150,000 | baseline | 3 | 1.000 |
| 150,000 | fixed_ab | 3 | 1.011 |
| 150,000 | evidence | 3 | 1.162 |
| 150,000 | evidence_prefix | 0 | n/a |
| 450,000 | baseline | 9 | 1.000 |
| 450,000 | fixed_ab | 7 | 1.015 |
| 450,000 | evidence | 7 | 1.228 |
| 450,000 | evidence_prefix | 4 | 11.372 |
| 1,350,000 | baseline | 12 | 1.000 |
| 1,350,000 | fixed_ab | 12 | 1.176 |
| 1,350,000 | evidence | 12 | 1.295 |
| 1,350,000 | evidence_prefix | 12 | 2.595 |

## Harder composition

The selected-negative-double-sum family is absent from macro training and evidence calibration.

| Budget | Condition | Solved / 3 |
|---:|---|---:|
| 150,000 | baseline | 0 |
| 150,000 | fixed_ab | 0 |
| 150,000 | evidence | 0 |
| 150,000 | evidence_prefix | 0 |
| 450,000 | baseline | 0 |
| 450,000 | fixed_ab | 0 |
| 450,000 | evidence | 0 |
| 450,000 | evidence_prefix | 3 |
| 1,350,000 | baseline | 0 |
| 1,350,000 | fixed_ab | 0 |
| 1,350,000 | evidence | 0 |
| 1,350,000 | evidence_prefix | 3 |

## Scope and checks

- Baseline witnesses passed 18 non-control tasks / 828 cases using at most four original operations. Witnesses were never search inputs.
- Held-out false positives: 0. Repeat search outcomes identical: True.
- The evidence policy is supplied, global and based on budget-censored utility; it does not learn task-specific semantic routing.
- Prefix search is also supplied: try retained whole-solution macros alone and with one base operation, then exhaustive fallback. It does not invent its own search algorithm or extract partial subgraphs.
- Each arm has maximum length five. Candidate construction, preparation and nested calls are charged. Calibration validation costs are included; final held-out evaluation is outside all search budgets.
- The three input schemas use supplied adapters; correlated task families are not independent demonstrations of domain understanding.
- Fixed ordering and a finite candidate language. Maximum controls are intentionally not generally expressible.
- Timing was measured on a shared machine and is secondary to deterministic graph-step counts.
- This is an isolated experiment, not a live app deployment.

Every candidate count, successful program, timing, family result and direct/nested macro use is in report.json.
