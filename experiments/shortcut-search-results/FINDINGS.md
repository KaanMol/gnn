# Shortcut injection: outcome

The frozen experiment does not support the hypothesis that this form of shortcut activation avoids degrading the base learner. Primitive search solved 60/120; the same search with probed injection solved 50/120. Two orders tied 15/30 versus 15/30; two lost 10/30 versus 15/30. There were no paired gains and ten losses, all round-trip tasks. These are previously evaluated orders, not fresh-order generalization.

The important positive contract result is narrower: when no proposal is injected, primitive candidate order and per-candidate charging remain intact. The synthetic pre-freeze test matched the baseline exactly at the residual budget after actual probe cost. In evaluation, all 86 first-attempt traces without injection matched prefixes of their full-budget baseline traces, including 77 with actual probes. Evidence is in rejected-probe-trace-audit.json. There is no extra lane scheduler or permanent memory reservation.

Positive behavioral progress was insufficient to ensure helpful activation. All ten losses admitted a learned pickup method on a round-trip task. The accepted proposal and callable extension altered the normal queue. This is observed queue interference after positive activation; it is not a rejection-path budget leak. Isolating the relative effects of the queued proposal and appended callable would require an additional ablation, which was not run.

Memory produced 24 audited whole-program reuse successes and 110 mixed candidate evaluations, but zero mixed successes. No additional solved task is directly attributable to an injected method because there were no additional solved tasks at all. Unlike the preceding lane experiment, mixed candidates were actually evaluated here.

There were 152 probes, 56 probe timeouts and 34 injections. Retrieval plus probing cost 1,759,469 graph steps; injection cost 255,782. The bounded probe cap prevents unbounded interference from rejection but can reject useful expensive methods. No thresholds were changed after inspecting results.

Total online graph work, including setup and management, was 37,842,294 without memory versus 35,760,813 with memory. This lower total does not establish better economics: memory solved fewer tasks. Average total work per solved task increased from approximately 630,705 to 715,216 steps. CPU totals were 125.27 and 124.68 seconds respectively.

Nine pre-freeze tests passed, including inherited nested/cache accounting checks. The frozen source and task hashes passed audit; expanded executable programs remained capped at five; the global search cost including probes/injection stayed within 450k. Exact validation and final audit behavior was preserved. Six retained method instances passed 96 post-run held-out cases; final false positives were zero. Task-local rejection does not delete globally retained methods.

The graph-authored proposal mechanism, tests and auditor remain frozen. No post-result tuning, new sweep, or live application change was made. The result establishes rejection-path preservation and useful whole-program shortcuts, while showing that partial-progress-based positive activation can still hurt acquisition.
