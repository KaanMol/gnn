# Planning allocation result

The same generic prioritized search solved **35/60 with managed memory versus 30/60 without memory**. The effect occurred in one of two frozen streams: seed 7109 improved from 15/30 to 20/30, while seed 8111 stayed at 15/30. This is a bounded positive mechanism result with task-order sensitivity, not replicated cross-domain transfer.

## What produced the gain

On seed 7109, zero-based task 2, the learner discovered:

`allocated_0 → plan_west → plan_drop`

Here `allocated_0` was the previously learned `plan_east → plan_pick` program. The solution therefore used three calls, expanded to four primitives, and combined acquired structure with supplied operations. Discovery consumed 289,831 search graph steps and evaluated 17 candidates. The no-memory arm exhausted its identical 450,000-step budget without solving the task.

The manager validated and retained this new delivery composition. Four later delivery tasks reused that complete learned program. Thus the five additional solved tasks comprise **one new mixed composition followed by four whole-program reuses**, not five independent abstraction discoveries.

## Full measured costs

Including setup, scoring, queue work, validation, utility updates, retention and final online audit:

| Metric | No memory | Managed memory |
|---|---:|---:|
| Audited tasks solved | 30/60 | 35/60 |
| Logical graph steps | 16,638,494 | 14,611,467 |
| CPU seconds | 55.52 | 53.34 |
| Wall seconds | 56.11 | 54.16 |

This run used 12.2% fewer graph steps, 3.9% less CPU and 3.5% less wall time with memory. Timing is a measurement from one interleaved run, not a statistically established speedup. Storage growth was higher with memory. No retirement occurred.

## Why the second stream tied

Before its first delivery task, seed 8111 had already acquired both pickup and round-trip. They tied on changed-target-leaf agreement and expanded cost. Stable generation order, inherited from recency selection, put round-trip first. The allocator spent work expanding that branch before the pickup branch. It later reached the useful pickup–west prefix, but exhausted its budget before reaching the completing drop call.

In seed 7109 only pickup was available at the first delivery task, so the allocator reached the useful composition earlier. This trace is evidence of an allocation/tie-order bottleneck. It is not a causal ablation of tie-breaking and does not justify silently changing the frozen policy.

## Verification and scope

All frozen task/source hashes and memory definitions matched. All five retained method instances passed post-run audits on 80 held-out examples. No final false positives occurred. Learned calls predated their use. Search budgets, expanded length and queue bounds passed the audit. Five isolated tests passed, including generic queue behavior, expansion rejection and cached nested-cost charging.

The memory system and runtime were unchanged. The newly supplied allocator contains no planning action or field names; it scores requested changes generically and still requires exact complete outputs for acceptance. Text/tree were not run or modified. The running application was not migrated or restarted. These are previously evaluated planning streams; fresh task orders and other computational structures remain untested by this allocator. No subgraph abstraction was added.

See REPORT.md and report.json for paired outcomes and detailed diagnostics; ../PRIORITIZED_SEARCH.md for the policy and reproduction commands.
