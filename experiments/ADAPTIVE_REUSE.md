# Evidence, composition extension and feedback learning

These are isolated research experiments. They do not modify the live preview database or establish an alternative to an LLM.

## What executes in the graph

- `adaptive_record` accumulates paired, budget-censored utility from calibration trials. Two failures give zero evidence of benefit; a lost solution is penalized; successful search receives the difference in consumed steps.
- `adaptive_save_evidence` persists those observations through the generic workspace port in `knowledge.reuse_evidence`.
- `adaptive_prepare` retains methods with positive aggregate utility. It is a global rule, not learned contextual routing.
- `adaptive_search_step` optionally tests retained macros alone and extended by each original operation, then resumes the original exhaustive search. It extends whole learned solutions; it does not extract intermediate subgraphs or invent a search algorithm.
- `grounded_observe` invokes a synthetic graph environment and collects outcome observations.
- `grounded_hypotheses` discovers which observed fields predict those outcomes.
- `grounded_choose_probe` selects a supplied candidate probe on which the surviving hypotheses disagree.
- `grounded_learn` refuses ambiguity and materializes/persists an unambiguous predictor as an executable graph.
- `grounded_predict` returns unknown when a learned field is absent.

The JavaScript authoring files emit graph data. They do not execute the learning process. Python supplies fixtures, schedules trials, meters generic graph execution, checks results and writes reports. No new domain operation was added to the Python runtime.

## Reproduce

Run from the repository root. Use **fresh database paths**: learned procedure names are protected against overwrite.

```sh
node graph-authoring/adaptive-reuse.mjs
node graph-authoring/grounded-adapter.mjs
python3 -B -m unittest test_adaptive_reuse test_grounded_adapter test_reuse_benchmark test_program_synthesis test_execution_cache test_prepared_ir -q
python3 -B experiments/adaptive_reuse.py --database /tmp/new-adaptive.graph.sqlite3 --output /tmp/new-adaptive-results
python3 -B experiments/audit_adaptive_reuse.py --database /tmp/new-adaptive.graph.sqlite3 --output /tmp/new-adaptive-results
python3 -B experiments/grounded_adapter.py --database /tmp/new-grounded.graph.sqlite3 --output /tmp/new-grounded-results
```

The audit checks baseline expressibility, includes calibration validation in learning cost, and reports paired comparisons and nested macro use. It does not change budgets, candidates or search results. Final held-out evaluation does not feed back into the search.

## Recorded runs

- Adaptive search: `adaptive-reuse-v2.graph.sqlite3`, `adaptive-reuse-results/REPORT.md` and `report.json`.
- Feedback learning with graph-selected probes: `grounded-adapter-v2.graph.sqlite3`, `grounded-adapter-results/REPORT.md` and `report.json`.
- `adaptive-reuse.graph.sqlite3` is an aborted setup run: evidence persistence used an unsupported workspace namespace. This was fixed before evaluation, without changing budgets or the search policy.
- `grounded-adapter.graph.sqlite3` is the initial feedback experiment with teacher-selected interventions; the v2 run adds graph-selected probes.

The search benchmark freezes calibration evidence and the library before evaluating new inputs. Both retained macros scored positively in calibration; this experiment therefore does not show actual vocabulary pruning, although the negative-evidence rejection path is tested. Input schemas have supplied adapters and related task families remain correlated.

The grounding experiment is deliberately small: boolean field predictors, a supplied finite probe pool, and synthetic graph worlds. Missing-field abstention does not detect every possible distribution shift. Neither experiment demonstrates human-like semantics or fundamentally new primitive operations.
