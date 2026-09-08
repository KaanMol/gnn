# Frozen trace-assisted consolidation

The experiment compares no memory, the unchanged full-replay sleep policy, and trace-assisted sleep on the preserved 120-task sequence. This is an architectural comparison on previously evaluated tasks, not fresh-order generalization. Existing wake search, routing signatures, publication threshold, retained methods, validation/audit code and cache/nested charges are unchanged.

## Wake evidence and its cost

A meter wrapper records fair-step evaluation summaries and frontier fields already returned by normal execution: operations, expanded program, executable/accepted/progress summaries, parent and next parent, next child index, and duplicate status. Existing task records already contain candidate costs, routing context and final audited outcomes. A charged metadata read records method availability before the task; a charged persistence call stores the additional evidence. No new method evaluation or semantic probe is introduced to collect it.

The wrapper binds only the meter in the exact frozen `wake_trial` function body. Its extra read occurs before initialization and is therefore deducted from the same task budget; recording is charged during finalization. Physical serialization and storage overhead appear in measured CPU/wall and persistent database growth. The preserved full-replay control receives no recorder.

This version does not claim to have saved unavailable per-example intermediate program outputs. It reuses actual evaluation/frontier records and completed intervention outcomes. Arbitrary cached-state continuation is not inferred from a matching prefix. Any executed learned call or cache hit still pays the existing logical cost.

## Frozen sleep evidence rule

Sleep retains the previous 20-task schedule, six investigated pairs per boundary, utility function, structural routing key, model threshold and 6M sleep cap. Each considered pair follows this deterministic sequence:

1. If the completed task had exactly one attempt and the exact same method name and expanded definition was its admitted memory, and its outcome was certified, use the recorded downstream outcome/cost as factual intervention evidence. This can support positive or negative utility. It does not estimate the cost of a different hypothetical run.
2. Otherwise, if the trace contains that exact expanded program evaluated as executable, allow a bounded 75k-total-step replay in an isolated store. A completed audited solve with no budget exhaustion provides downstream utility. A failure or incomplete execution remains UNKNOWN, never a negative label and never positive evidence.
3. At most one unresolved pair per sleep, the first encountered, receives a full wake-style fallback replay. All others remain UNKNOWN.

Actual replay uses the same recorder and wake function, including its cost. A successful bounded run follows the same paths as full execution because its limit was never reached; a pre-freeze test verifies exact trace and cost equality. Replays do not receive a free cached-execution allowance.

UNKNOWN advances a separate investigation-count index only. It never updates the utility model, positive count, lost-solve count, confidence threshold or routing score. Supplying these investigation counts to the same pair selector prevents unresolved contexts from repeatedly crowding out other investigations. This index is charged separately.

## Audits and ablation

Twelve pre-freeze tests passed across trace and nested-composition modules, including charged recording equivalence, exact factual intervention identity, bounded replay censoring, successful partial/full equality, UNKNOWN isolation, future-prefix rejection, one-full-fallback quota and exact nested/cache charging.

The unchanged full arm must reproduce the original 8,683,002 forced-replay steps. The audit matches individual replay pairs by boundary/task/method and reports the exact prior full cost of skipped pairs, any cost difference for retained fallbacks, added partial execution, added trace/index analysis and added wake recording. Other changed consolidation costs and the net lifetime difference are reported separately. A lower replay component alone does not establish economic success.

Wake rejection traces, method availability, completed-prefix boundaries, expanded-length caps, strict task/sleep totals and exact held-out audits are checked. Useful-memory false negatives are measured only where factual or completed replay evidence resolves the outcome; UNKNOWN and unsampled opportunities remain unmeasured.

```sh
python3 -B -m unittest test_trace_sleep test_compositional_transfer
python3 -B experiments/audit_trace_sleep.py --output experiments/trace-sleep-results
```

The manifest hashes the policy, tests and auditor before evaluation. Previous outputs remain preserved; no threshold, feature, routing or budget tuning is permitted after the run begins.
