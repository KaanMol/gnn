# Probed shortcut injection

Previously evaluated four planning orders; 120 tasks per arm. Same frozen fair expansion, 450k search budget, exact validation and final audit.

| Arm | Solved | Total graph steps | CPU seconds | Mixed | Whole reuse |
|---|---:|---:|---:|---:|---:|
| no_memory | 60/120 | 37,842,294 | 125.27 | 0 | 0 |
| memory | 50/120 | 35,760,813 | 124.68 | 0 | 24 |

Per-order results:
- 15053 no_memory: 15/30; 0 probes, 0 injections, 0 probe timeouts.
- 15053 memory: 10/30; 27 probes, 9 injections, 7 probe timeouts.
- 16057 no_memory: 15/30; 0 probes, 0 injections, 0 probe timeouts.
- 16057 memory: 15/30; 50 probes, 8 injections, 22 probe timeouts.
- 17077 no_memory: 15/30; 0 probes, 0 injections, 0 probe timeouts.
- 17077 memory: 15/30; 49 probes, 8 injections, 21 probe timeouts.
- 18089 no_memory: 15/30; 0 probes, 0 injections, 0 probe timeouts.
- 18089 memory: 10/30; 26 probes, 9 injections, 6 probe timeouts.

Paired gains: 0; losses: 10.
Additional tasks whose successful program directly uses an injected call: 0.
Final false positives: 0. Retained methods: 6 audited on 96 cases.

Attribution is a trace plus matched-arm comparison, not a separate ablation of memory history. Pure primitive wins, if any, are not counted as directly caused by injected calls.

Policy:
Unchanged fair_step with exact primitive state. Retrieve last three active retained entries, probe all current examples with generic changed-leaf agreement or exact matches above identity. Retrieval/probes together capped at 45000 steps; each probe capped at 15000. Inject only positive executable proposals into the ordinary queue and append callable vocabulary. Expanded cap five, full nested/cache charging. Rejected probes leave search state unchanged. No lanes or budget reservations.

Limitations:
- Previously evaluated task orders, not fresh-order generalization.
- Initialization constructs the exact empty-memory fair state directly; fair_step is unchanged.
- Probe ceiling and recent-three retrieval fixed before results; no post-run tuning.
- 450k covers initialization, retrieval, probes, injection, search and feedback; validation/retention/audit charged separately in total online cost.
- Successful activation can change queue ordering and reduce primitive exploration; this is measured, not assumed harmless.
