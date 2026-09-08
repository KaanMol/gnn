# Adaptive allocation: audited negative result

The frozen adaptive allocator solved 40/120 tasks with memory and 40/120 without memory, exactly 10/30 in each of four orders. Memory gained no tasks and lost none. Neither arm discovered a mixed learned-callable composition. These are the same previously evaluated orders, not fresh confirmation.

Memory used 43,592,382 total graph steps versus 43,164,952 without memory (about 1.0% more), and 157.19 versus 151.82 CPU seconds (about 3.5% more). All online management, validation and audit work is included in these totals. The shared 450k cap applies to search and allocation, with feedback deducted before a retry; validation, retention and final audits are reported separately rather than hidden inside that cap.

## Contract checks and limits

- Both directions of borrowing occurred in the run: memory received 37 transitions after already spending its 20k probe; primitive search in the memory arm received 164 transitions after already spending its 100k floor. This excludes mere one-transition overshoot.
- Controlled graph tests seed a positive-progress winner beyond its allowance, select it, execute its next search transition and verify increased charged spend, for both lane types.
- Two equally relevant synthetic methods are both selected and actually explored. Duplicate expanded programs in different lanes each incur positive execution charges.
- A controlled stall-boundary test verifies a memory lane becomes inactive, is skipped by subsequent selection, and remains in the global catalog and index. No memory lane reached that boundary in the benchmark itself, so this run does not demonstrate a benefit from stall eviction.
- Event replay checks routing decisions, independent lane spend, primitive precedence, and the shared search cap. Expanded length six is rejected at the actual search boundary; existing compositional tests verify nested and cached execution costs.
- All frozen source/task hashes match. Four retained method instances passed 64 held-out audit cases; final false positives were zero.

The initial supplemental fixture expected primitive borrowing and stall termination in the same 450k run. It exhausted the global budget first: 272,235 routing steps, 169,553 execution steps, and 8,212 initialization steps. The failed assertion was not evidence that borrowing is capped. Tests were separated into actual borrowing fixtures and explicit stall-boundary coverage; the frozen implementation was not changed. The original run began before these additional contract checks, so this was a retrospective acceptance audit, not a claim that all requested checks preceded freezing.

## Main failure

Routing alone consumed 23,181,316 steps without memory and 22,812,735 with memory, more than half the reported online total in each arm. The prior no-memory comparison solved 60/120 on these task orders; the new no-memory allocator solved 40/120. This is a regression under the logical compute budget. It is consistent with expensive control work crowding out acquisition, although isolating causality would require an ablation.

Only one retained method instance per order accumulated, and there were no mixed candidate evaluations in the benchmark. Consequently this run does not adequately test whether multiple useful memories can support the desired mixed composition. It demonstrates neither improved plasticity nor an economic benefit from memory. It also does not disprove compositional learning generally.

The policy remains frozen. No new heuristic sweep or text/tree run was started. The next architecture decision should address the cost and representation of search control before another allocator variation is justified.

See REPORT.md for per-order results and report.json/trials.jsonl for raw events.
