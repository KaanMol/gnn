# Seed: toward an inspectable graph-computation system

The target is an inspectable graph-computation architecture. The prior prototype
was a fixed collection of fact-processing operations. The new foundation treats procedures as typed, executable graph data.

## What now exists

1. **Computation language.** JSON graphs have typed input and output ports. Nodes
   represent constants, inputs, arithmetic, comparisons, lists, procedure calls,
   conditional selection, preconditions, and while loops with explicit guard/body
   graphs. The validator rejects invalid types, unresolved edges, and graph cycles.
2. **Interpreter.** The core executes graph instructions; numerical operations
   resolve to taught exact-rational programs. It records execution evidence. Branches are lazy.
   Node-step, call-depth, numeric-size, and collection-size limits bound execution.
   Graphs cannot execute Python, access the network, or write files.
3. **Reusable procedural knowledge.** Definitions persist as graphs and can be
   called or composed. Matching output/input types are required for composition.
   Identity and associativity are tested on computed results. Explicit composition
   copies graphs; named call nodes resolve the current referenced definition.
4. **Teaching interfaces.** Gemma translates short arithmetic procedure definitions.
   The advanced graph editor accepts the full graph language, including loops.
   This avoids pretending a small model reliably translates every algorithm from
   prose. Numeric expressions and simple count requests bypass Gemma for speed.
5. **Authoritative graph memory.** `graph_store.py` stores typed nodes, ordered
   edges and named roots in SQLite. Facts, proofs, rules, programs, history, sensor
   evidence, world-learning state and identity use views of this one database.
   `/api/graph` exposes its actual IDs and edges, rather than projecting other
   stores. Container values, including instructions, are decomposed into graph
   nodes. Current roots select active knowledge; history is inert evidence.

`examples/factorial.graph.json` demonstrates an algorithm supplied entirely as graph
data. It uses list state `[remaining, accumulator]`, a non-negative integer
precondition, a guard, and a loop body. There is no factorial instruction in the
interpreter. Tests execute this graph on unseen inputs and verify its precondition.

## Mathematical scope

Graphs have typed composition and identities, providing the beginnings of a
categorical treatment of programs. Execution is partial and resource-bounded:
division by zero, invalid inputs, and exhausted budgets are explicit failures.
We have not proved a universal categorical semantics, equivalence decision
procedure, or general reliability theorem. The separate subtype preorder remains
available for concept inclusion. It is not the foundation of all computation yet.

## Unified reasoning and skills

All active methods share `knowledge.procedures`. The foundation curriculum supplies
structural pattern matching/substitution; finite Horn inference and proof traversal;
concept/symmetry interpretation; symbolic rewriting; toy-world hypothesis search,
experiment selection and revision; counting; calendar interpretation; goal search
and execution; and basic workspace, canvas and clock usage. Sudoku and algebra
are additional packages in the same library, executed by the same interpreter.

`SkillSystem` validates boundaries, resolves the current library and persists runs.
The *planning algorithm* is `plan_search`, an ordinary graph program. It searches
contracts over tags using `plan_policy` bounds, then `plan_execute` invokes selected
programs. An explicit Bool checker can verify a stated outcome. Contract claims
alone produce `executed_unverified`, never automatic verified success. The example
temperature package demonstrates a new domain taught entirely as graph data.

`workspace_*` programs expose read, write, keys and deletion through a local port.
Programs can read and revise other programs as data. Validation and attribution
remain host boundaries. This is an explicit capability, not autonomous discovery
of better algorithms. Each execution uses an immutable library snapshot; revisions
apply to later invocations. Partial external actions cannot be rolled back.

## Remaining limits

- This is a bounded research prototype, not AGI.
- The generic interpreter, symbol and collection primitives, graph storage,
  parsing/formatting, app routing and raw device drivers remain code. Domain
  methods and interface-use sequences are taught programs. Eliminating every
  line of execution code is neither implemented nor the meaning of this design.
- Natural-language teaching supports restricted translations. New algorithms can
  be supplied as graph data; arbitrary prose is not a reliable programming language.
- Perception is structured drawing data and simulator features, not raw images.
  There is no autonomous acquisition of new sensors or unrestricted device access.
- General program synthesis, autonomous self-improvement, causal discovery and
  formal correctness proofs remain future research. Goal contracts and taught
  checkers are fallible; successful execution is not proof of general intelligence.
- `meaning.py` and `adaptive.py` retain earlier standalone CLI demonstrations.
  Live preview inference uses `Knowledge` and the taught foundation programs.

## Reusable algebra curriculum

The general procedure library now also accepts the explicit 24-lesson algebra
package. Polynomial interpretation, expansion, collection, solving and factor
search are graph programs. A flat syntax adapter preserves operators and child
references without assigning polynomial meanings; a stored token interpreter
supplies those meanings. Exact arithmetic, floor and rational components now
resolve to taught numeric graphs. No polynomial-solving primitive or external CAS is called.

The former sixth-degree rewrite is retained in history as a worked example and
removed from live active rules. Tests independently expand polynomials with
new coefficients, roots and degrees, check roots by substitution, exercise
contradictions and identities, and remove each dependency. The notebook retains
that algebra was taught as routing history, so deleting all of its procedures
cannot silently reactivate the old rewrite solver. This is authored procedural
knowledge, not autonomous algorithm discovery. See README for the precise scope.

## Storage and restart semantics

`preview-memory.graph.sqlite3` is the live authority. The old JSON notebook is
imported once and preserved as a backup. On later starts, current graph roots
load directly; historical teaching and device actions are never replayed. Missing
lesson dependencies remain missing. The interpreter snapshots the current
procedure roots once per execution and preflights every required dependency.

Content-addressed immutable nodes share repeated subgraphs. Named roots identify
current values; editing a record updates its root in a transaction. Nested edits
check the previous root ID, so stale references cannot restore a deleted lesson.
Knowledge proposals are staged in an isolated graph and adopted into the same
live store, keeping sensor and history views attached. Derived fact proofs are
materialized in the graph and refreshed when assertion/rule roots change.

Driver objects and the live canvas remain environment code. Their saved state and
attributed observations are graph records. Runtime limits, mathematical syntax parsing,
numeric representation/formatting and syntax/routing adapters are implementation,
not learned graph knowledge. Database transactions cannot undo physical input;
evidence of actions is kept even when a later graph instruction fails.

## Numerical foundation and conversation policies

Number instructions bind to editable `number_*` programs, whose dependencies
implement symbol interpretation, digit tables, carries, borrowing, multiplication,
long division and rational operations using generic Data operations. The live
interpreter has no native numerical-operation fallback. Type validation, rational
transport and output formatting still use host code. Supplied tables and methods
are explicit teacher choices, not independently discovered mathematical axioms.

`curriculum/conversation.json` is an explicitly installed package of dialogue-use
and tutoring programs. The raw port only displays text and persists a requested
continuation plus data. The host dispatches the next input to that continuation;
`tutor_*` programs decide whether to explain, ask, wait, check, retry, stop or
advance. A generic `attempt` returns recoverable failures to the stored policy,
without undoing actions or resetting budgets. The included linear-algebra course
executes its current solver to obtain example and exercise answers. It does not
make all procedural knowledge automatically explainable, nor implement general
self-directed learning. Missing programs stay missing across restarts.

The graph notebook presents fact relations, procedure input dependencies,
recorded execution events and pending conversation state. Semantic diagrams
project the authoritative graph data; `/api/graph` exposes physical stored IDs.
Trace arrows denote recorded chronology, not unobserved internal reasoning.
