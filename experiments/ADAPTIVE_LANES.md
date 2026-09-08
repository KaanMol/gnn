# Adaptive lane comparison

Graph-authored policy: graph-authoring/adaptive-lanes.mjs, emitted as curriculum/adaptive-lanes.json. Python experiment orchestration: experiments/adaptive_lanes.py. Existing scoring, fair-search transitions, retention and nested execution charging remain frozen.

The policy probes up to four compatible memories in independent frontiers, protects primitive execution initially, then allocates by recent example-agreement gain per charged execution step. All routing and duplicate work is charged. Memory stalls affect only task-local activation.

Validation commands:

```sh
python3 -B -m unittest test_adaptive_lanes test_adaptive_lane_contract test_compositional_transfer
python3 -B experiments/audit_adaptive_lanes.py --output experiments/adaptive-lanes-results
```

The completed run and manifest are in adaptive-lanes-results. Do not overwrite or resume it. The earlier static split sweep remains stopped. Read adaptive-lanes-results/FINDINGS.md for outcomes, the retrospective test chronology, and limitations. No policy retuning was performed after freezing.
