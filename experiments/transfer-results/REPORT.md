# Transfer boundary map

The exact condition preserves the original manager and its original host vocabulary. The disabled condition changes two graph rules and binds the new vocabulary; it is explicitly not unchanged transfer. All environments and budgets were frozen before search evaluation. No rescue rules were added.

| Environment | Original discard | Exact frozen | Rules disabled | Disabled, no memory | Disabled steps / discard | Disabled CPU / discard |
|---|---:|---:|---:|---:|---:|---:|
| planning | 30/60 | 0/60 | 30/60 | 30/60 | 0.990 | 1.049 |
| text | 10/60 | 0/60 | 10/60 | 10/60 | 1.002 | 1.023 |
| tree | 20/60 | 0/60 | 20/60 | 20/60 | 1.003 | 1.020 |

## Economic crossover

| Environment | Seed | Comparator | First advantage lasting to task 30 |
|---|---:|---|---:|
| planning | 7109 | discard | 16 |
| planning | 7109 | disabled_no_memory | 16 |
| planning | 8111 | discard | 15 |
| planning | 8111 | disabled_no_memory | 15 |
| text | 7109 | discard | none |
| text | 7109 | disabled_no_memory | none |
| text | 8111 | discard | none |
| text | 8111 | disabled_no_memory | none |
| tree | 7109 | discard | none |
| tree | 7109 | disabled_no_memory | none |
| tree | 8111 | discard | none |
| tree | 8111 | disabled_no_memory | none |

## Boundaries

- planning, exact: fails interface/representation: old vocabulary absent; new sequences rejected by old canonicalizer.
- planning, disabled: cumulative compute crossover within supported subset. Boundary tasks: reach_goal, unlock.
- text, exact: fails interface/representation: old vocabulary absent; new sequences rejected by old canonicalizer.
- text, disabled: no replicated cumulative crossover. Boundary tasks: remove_digits.
- tree, exact: fails interface/representation: old vocabulary absent; new sequences rejected by old canonicalizer.
- tree, disabled: no replicated cumulative crossover. Boundary tasks: mirror_all.

Stored-program audits: 4/4 passed (64 cases).

Missing-operation controls preserve an invariant no available primitive can change (digits in text, or the planning gate). Variable-shape controls require recursion/variable-length action plans that the bounded fixed-sequence search cannot express. Representable positive witnesses were verified independently after the run.

Fresh computational structures still share a sequential-composition interface. Disabled mode reuses complete previously discovered programs; it does not search new hierarchical compositions through learned names. Any positive result is a transfer of bounded whole-program memory management under an explicit adapter, not a domain-agnostic engine or arbitrary-program canonicalizer.

## Limitations

- Fixed sequential composition grammar still shared across environments.
- Rules-disabled condition is not exact unchanged transfer.
- Environment primitives are supplied; the learner does not invent primitives or understand natural-language goals.
- Text, tree zipper and simulated stateful action data are structured environments, not real-world side effects.
- Retained whole solutions are probed directly; there are no continuation probes or recursive new-composition search through macro names in disabled mode.
- Two seeds and 30 tasks per environment/seed; finite-stream crossover only.
- Final audit never informs retention. Physical storage bytes and CPU/wall are separate from logical steps.
