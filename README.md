# A symbolic concept learner

The prototype now includes a **typed graph-computation core**, not just fact and
relationship handlers. See [ARCHITECTURE.md](ARCHITECTURE.md) for the implemented
foundation, mathematical scope, and the substantial work still needed toward a
general graph-computation research architecture.

## Calculate, teach procedures, and inspect computation

In the preview, try:

```text
Count to 10
What is (12 + 3) * 4?
What is twelve times seven?
Doubling a number means multiplying it by two.
Double 21
Show me the double procedure
Define increment as x + 1.
Create double_then_increment by running double then increment.
Run double_then_increment on 10
```

Numerical answers come from taught exact-arithmetic programs in the graph. Gemma
translates teaching into graph definitions; it does not supply the answer. Explicit
numeric expressions, counts, and learned calls such as `double(21)` bypass the LLM.
Errors such as division by zero produce no new facts. Counting can enumerate up to
200 consecutive numbers, count listed items, or count known concept members.

Procedure graphs persist in the notebook and appear under **Executable procedures**.
They can be composed, inspected, and explicitly redefined. The advanced graph
editor accepts the full runtime language, including branching and loops. Load the
factorial example, inspect it, and click **Learn this procedure** to install its
graph; then ask `factorial(6)`. The factorial algorithm is graph data, not a special
instruction in the interpreter. Natural-language teaching currently covers simple
one-input arithmetic procedures; arbitrary algorithm prose is not understood.

`/api/graph` exposes actual stored nodes, edges and current roots in the unified
SQLite graph database. Facts, dependencies, procedures, history and observations
use that database as their authoritative store. The Sudoku and algebra
curricula are executable graph programs using generic primitives. Goal planning and explicit memory/program revision now use taught graph programs too.
Autonomous procedure synthesis remains unimplemented.

## Open the teaching preview

```sh
python3 preview.py
```

Open [Seed on this Mac](http://127.0.0.1:8765). The launcher reuses the Gemma
runtime already installed by the Goud/Relevate desktop app. It checks the app's
ports 18766, 18765, and 18767 for a served Gemma model. If none is running, it reads
`~/Library/Application Support/com.relevate.desktop/llama.cpp/install.json` and
starts the installed binary with the installed Gemma 4 E2B GGUF on port 18769.
It does not download models or change the desktop app. Its own subprocess stops
when the preview exits; a reused desktop process is left running.

The preview saves learning to `preview-memory.graph.sqlite3` (the older JSON name
resolves to this database). Use `--memory` to choose a
separate notebook. The preview accepts structured teaching through natural language:
multiword entities, arbitrary relationships and properties, explicit negatives,
up to eight operations per message, and definitions with up to six conditions.
Try “My name is Kaan,” “I live in Amsterdam,” “Mira likes green tea,” or a correction
such as “Actually Mira is 31, not 30” after teaching her old age.
Property questions and yes/no questions read from memory. The
experiment buttons collect observations from the toy world. Raw images, audio,
and continuous autonomous learning are future work.

Gemma stays loaded between requests. There is no per-message model startup.
The structured adapter is in `semantics.py` and `knowledge.py`; it does not use the
legacy English sentence parser. Corrections retract exact assertions and recompute
derived facts. Negative and positive evidence can coexist as a reported conflict.
A message is applied atomically, so invalid corrections cannot partly change memory.
The notebook's original statements and prior interpretations remain in its history.

The local translator sees the speaker's name, recent messages, and a bounded
summary of memory. Common English question forms are additionally restricted to
read-only operations. Ambiguous or invalid semantic operations become clarification
messages with no fact changes. These checks do not prove translation accuracy:
Gemma can still omit or misinterpret meaning, so inspect “Understood as.”
Concept definitions remain a restricted rule language. Typed executable procedures
are supported as described above; temporal reasoning and general logical rules
are not implemented.

You can also teach symmetric relationships: after “Julia and Kaan are dating,”
teach “If A is dating B, B is also dating A.” The core stores an explicit symmetry
rule and derives the reverse fact with a proof. No dating-specific reasoning is
hardcoded. Removing a supporting assertion or symmetry rule recomputes the graph.
The language interface does not yet translate arbitrary implication rules. The taught
`horn_closure` program accepts general finite positive rules as structured data;
`relation_closure` supplies subtype identity and transitivity. Vague collective claims require
clarification rather than creating an entity named after a plural group.

Gemma is pretrained and handles language interpretation. The separate symbolic
learner is limited to explicit definitions and bounded feature-based induction.
This is a teachable prototype, not a simulation of a child's mind.

A small, dependency-free research prototype for learning explicit concepts from
statements and experiments. The symbolic core uses no LLM, embeddings, external
service, or pretraining corpus. An optional llama.cpp/Gemma language interface
translates everyday language into its limited semantic operations. User statements
and labeled examples are learning data acquired
during use. The supplied syntax adapters and teacher-authored hypothesis family are inductive
biases. Live hypothesis search and revision execute stored graph programs. Requires Python 3.9 or newer.

```sh
python3 meaning.py --demo
python3 meaning.py
python3 -m unittest -v
```

The interactive session saves accepted statements in `memory.json` and replays
them on startup. Use `--memory path.json` to select a different memory file.
Enter `/quit` to exit. Questions must end in `?`.

## Teach a concept

```text
A gardener is a person who grows a plant.
A rose is a plant.
Mira is a person.
Fern is a rose.
Mira grows Fern.
Is Mira a gardener?
Why is Mira a gardener?
What is a gardener?
What is Mira?
```

The learner compiles the definition into:

`gardener(x) := person(x) AND EXISTS y. grows(x,y) AND plant(y)`

It recognizes Mira as a gardener using the definition, the relation, and Fern's
inherited plant type. New concept and relation names require no code changes.
Try teaching `A mentor is a person who teaches a person`, then supply matching
facts. Explicit definition learning is complemented by the separate adaptive
learner described below.

## Learning concepts from examples

Start with a fresh memory (`python3 meaning.py --memory experiment.json`) and enter:

```text
Fern is a plant.
Mira is a person.
Theo is a person.
Alex is a person.
Rin is a person.
Mira grows Fern.
Theo grows Fern.
Rin grows Fern.
/example gardener Mira yes
/example gardener Theo yes
/example gardener Alex no
/hypotheses gardener
/predict gardener Rin
```

Without a gardener definition, the learner proposes `grows a plant` as a
provisional distinguishing rule. Labeling Rin negative withdraws this rule.
Adding features that distinguish the positive examples can produce a revised
rule; correcting Rin's label to positive restores the previous hypothesis.
Labels persist across restarts. Predictions remain separate from proven facts.

This is supervised online symbolic induction, not autonomous learning without
data. It searches minimal conjunctions of up to three observed type or outgoing
relation/type features, with at most 40 common features. At least two positive
and one negative examples are required. The threshold is an engineering choice,
not statistical assurance. Multiple consistent hypotheses are preserved and
disagreement causes abstention. It assumes consistent labels and treats absent
features as absent for hypothesis fitting; incomplete graph descriptions can
therefore mislead it. It is not probabilistic, noise-tolerant, or causally grounded.
Use a fresh concept name for induction experiments: explicit definitions mixed
with labels can introduce indirect target leakage through derived graph features.

## Implementation and mathematical scope

- The parser maps sentence constructions to typed semantic operation tuples.
- A relational graph stores entity membership and binary relation facts.
- Definitions compile into conjunction and existential-witness matching rules.
- The concept taxonomy generates a preorder category: concepts are objects;
  subtype reachability supplies morphisms; identity and composition are explicit.
  Instance propagation follows the category's generating subtype edges.
- Finite monotonic inference records a derivation for each fact. Missing evidence
  yields `Unknown`, rather than false.

The category layer is deliberately narrow. This is not yet a categorical model
of all sentence meanings or an implemented syntax-to-semantics functor. Its first
role is consistent composition of subtype inclusions. A later formalization can
interpret concepts as sets of entities and subtype arrows as inclusion maps.

Definitions provide sufficient classification rules and necessary base types.
If someone directly asserts `Mira is a gardener`, the engine derives `person(Mira)`
but does not generate an anonymous plant or relation witness. Consequently it is
not a complete reasoner for the full biconditional definition above.

## Language boundaries

This section describes the legacy `meaning.py` CLI. The connected preview uses
the structured operations described above, including negation and correction.

Use single-word, capitalized entity names (`Mira`, `Fern`), singular concept names
(`plant`), and the same verb spelling in definitions and assertions (`grows`).
Articles and grammatical forms follow the examples. Vocabulary is extensible,
but grammar is fixed. This is not unrestricted natural-language understanding.

No pronouns, tense, plural normalization, negation, belief contexts, probabilities,
revision of asserted facts, unrestricted concept induction, or perceptual grounding
are implemented. Provisional induced concepts can be revised by new evidence.
Recognized sentence forms assign meaning by that grammar; ambiguous words are not
disambiguated. Unsupported sentence forms raise an error. Different definitions
for the same concept are rejected. Inference is intended for small knowledge bases.

## Next research steps

1. Extend structured semantics with scope, richer ambiguity handling, and relation queries.
2. Distinguish necessary from sufficient rules and support richer definition logic.
3. Extend the bounded example learner with richer hypotheses, noisy feedback,
   active example selection, and evaluation on held-out examples.
4. Extend toy-world grounding to richer environments and additional sensors.
5. Formalize composition beyond the taxonomy and test semantic preservation.

Useful foundations: [Ologs and categorical databases](https://categoricaldata.net/papers.html)
and [categorical compositional semantics](https://arxiv.org/abs/1003.4394).

## Exploration and adaptation

```sh
python3 playground.py --demo
python3 playground.py
```

Eight objects expose shape, material, and color. The learner chooses roll/float
experiments where its candidate rules disagree and receives outcomes from the
simulator. It discovers the simulator's simplified rules in ten experiments in
the default demonstration, then predicts six untested object/action pairs.
This is a deterministic toy result, not a benchmark of general intelligence.

The taught `world_hypothesis_space` searches conjunctions of up to two feature
equalities. Shape and material labels come from the simulator. The hypothesis
family, selection method and revision method are editable supplied lessons.
They are not independently discovered algorithms. Contradictory evidence
starts a fresh learning context for that action while retaining episode history.
This crude adaptation cannot distinguish environmental change from sensor noise.
Once predictions agree, exploration stops; detecting later change requires a new
observation or explicit retest. There is no background monitoring.

## Local language interface and sensor adapters

Start your existing `llama-server` with your Gemma GGUF, then run:

```sh
python3 interface.py
```

The default provider is llama.cpp. It discovers a single served model from
`/v1/models`. If your server exposes several, select the Gemma model explicitly:

```sh
python3 interface.py --model YOUR_SERVED_MODEL_ID
```

The default server is `http://127.0.0.1:8080`; use `--base-url` to change it.
The client follows the [llama.cpp server API](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)
and requests schema-constrained output on `/v1/chat/completions`.
No cloud key is required. No model is downloaded automatically.
Ollama is available as an alternative via `--provider ollama`, defaulting to
port 11434 and its [structured output API](https://docs.ollama.com/capabilities/structured-outputs).
An optional OpenAI adapter is also available with `--provider openai --model MODEL`
and `OPENAI_API_KEY` in the process environment; it uses the documented
[structured response format](https://developers.openai.com/api/docs/guides/structured-outputs).

Use `/explore` to run one experiment, `/beliefs` to inspect learned rules, and
`/quit` to exit. Teach a word such as “Call things that roll a roller,” then ask
“Is Amber a roller?” The LLM translates language; answers come from the core.
The original wording, interpretation, and answer are retained in
`interface-memory.json`. The three most recent messages and a bounded vocabulary
and fact summary help resolve references; unresolved pronouns should produce a clarification.

`python3 interface.py --demo` runs offline with explicitly fixed translation
examples. It tests sensor integration without calling or evaluating an LLM.

`sensors.py` defines the first adapter contract: action, object, boolean outcome.
Registered adapters attach source, timestamp, and event ID to each outcome.
The toy-world adapter is implemented. Cameras, microphones, and numeric sensors
still need modality-specific observations, calibration, time handling, and feature
extraction; they are not supported merely by plugging in a device.

Language operations cannot submit sensor events. Translated assertions are stored
as user assertions and may be used for deduction, but they are not independently
verified. Schema validation does not guarantee faithful translation: a model can
still invent a syntactically valid assertion. Inspect the displayed interpretation.
The sensor registry is a software boundary, not a security sandbox or guarantee
of measurement truth. Learned world hypotheses remain separate from asserted facts.

The full system now contains a pretrained language model when that optional
interface is enabled. Its learned symbolic knowledge remains separately stored;
we cannot claim that its language interpretations are free of pretrained knowledge.

### Live date capability and taught age logic

“Today's date” maps to the read-only `current_date` tool. It reads the Mac's local
clock each time and returns the calendar date, timezone and observation timestamp.
It does not use dates asserted in conversation. This is an explicit language-to-tool
binding supplied to Gemma, with a deterministic shortcut for common date questions.

`examples/age_years.graph.json` is a teacher-authored lesson, not built-in age
arithmetic or an independently discovered rule. Teach it through the graph editor
under the name `age_years`. Its graph calls `current_date`, subtracts the birth year,
and subtracts one more while the birthday is ahead. Birth inputs come from memory.
Without this stored procedure, the system asks to be taught; editing its graph
changes the result. February 29 birthdays advance on March 1 in non-leap years
under this particular lesson.

Try “I was born on 24 February 2000”, “What's today's date?” and “How old am I?”
after identifying yourself. Full dates are required; ambiguous numeric dates and
conflicting birth dates request clarification. Answers keep tool observations,
procedure snapshots and execution traces in their history, without storing age
as a timeless fact. This is instruction through a supplied graph; arbitrary
spoken multi-step lessons are not yet automatically compiled into these graphs.

### Teaching reusable algebra

`Teach algebra` explicitly teaches 24 editable graph procedures from
`curriculum/algebra.json`. After that, `Solve:` and `Simplify` execute those
procedures through the same interpreter used by Sudoku. No LLM or external
computer algebra system calculates these results.

Try:

- `Solve: 3(2x-5)=4x+7` → `x = 11`
- `Simplify (x+3)(x-2)` → `x^2 + x - 6`
- `Solve: x^2-5x+6=0` → roots 2 and 3
- `Solve: x^2-2=0` → exact symbolic radical roots
- `Solve: 0*x=5` → no real solutions
- `Solve: 2(x+3)=2x+6` → every real value satisfies the equation

The taught representation is a list of rational coefficients, in ascending
power order. The curriculum teaches collecting equal powers, distribution,
scalar division with a nonzero check, and nonnegative integer powers. Another
stored program walks the parsed syntax and interprets each operator using those
lessons. The Python adapter only parses notation and formats results.

The solving curriculum teaches linear isolation, the quadratic formula, exact
rational square-root detection (including a taught integer binary search),
Horner evaluation, rational-root candidates and synthetic division. Every
extracted linear factor must have an exact zero remainder. Multiplicity comes
from repeated extraction and repeated quadratic roots. Trace entries are emitted
by the stored programs that performed these operations.

The original sixth-degree equation now gives 22 six times without a stored
factorization identity. The candidate `-a[n-1]/(n*a[n])` is derived from coefficients
and checked exactly; this handles repeated linear powers with different roots,
coefficients and degrees. Otherwise the graph searches signed rational-root
candidates within its taught bounds, then solves a linear or quadratic remainder.
An unresolved higher-degree factor is reported as incomplete, never as proof that
there are no roots. This is a general method within its scope, not all of algebra.

Current scope: **one unknown, rational coefficients, polynomial operations, real
solutions**, subject to parser and execution budgets. The stored policy limits
powers to 12 and trial divisor checks to 20,000. Variable denominators, negative
or variable exponents, systems, inequalities, and general roots of unresolved
higher-degree factors need further lessons. Negative quadratic discriminants
produce no *real* roots; complex roots have not been taught.

These are teacher-authored executable lessons, not independently discovered
axioms or a theorem-proved algebra engine. Ordinary arithmetic, rational
numerator/denominator access and floor now resolve to taught number programs.
The interpreter supplies symbol/collection operations, conditionals, loops and
calls. There is no built-in polynomial or algebra solver.
Forgetting any required procedure blocks execution; deleting every algebra
procedure also blocks it after a restart, without falling back to old shortcuts.
Re-teaching `Teach algebra` explicitly restores the curriculum.

### Explicit math rewrite rules and worked examples

`Teach math: u + 0 => u` stores a pattern rewrite. Letters are expression
placeholders, and repeated letters must match the same expression.
`Rewrite (q + 0)` explicitly uses those rules. `Show math rules` and
`Forget math: u + 0 => u` inspect and remove them. These trusted rules can be
wrong; the matcher does not prove them.

The old expanded-polynomial → `(x-22)^6` rule was one worked factorization, not a
method of finding factorizations. It has been retired from the live active rule
list and remains in historical messages. After the algebra curriculum is taught,
`Solve:` and `Simplify` use the graph algorithms, while explicit `Rewrite` keeps
the pattern-rule workflow available. A new empty notebook retains the legacy
rewrite workflow until an algebra curriculum is explicitly taught.

### Taught Sudoku and a freely editable canvas

Every cell accepts any digit from 1–9, including duplicates and edits to starting
clues. Backspace clears a cell. **Empty board** lets you enter your own puzzle.
There are no automatic candidate hints, conflict blockers, corrections, or wins.
Board state persists across restarts. Randomization supplies an environment
puzzle by shuffling a completed pattern; it never invokes a solver and does not
establish uniqueness.

**Check board** explicitly runs `sudoku_observe_check`: observe the drawing,
interpret its marks, construct the taught groups, check their distinctness,
and distinguish correct, incorrect, and incomplete. It leaves all entries in
place. A partial board without duplicates is not a proof of solvability.
**Run taught solver** executes `sudoku_observe_solve`, then checks the resulting
board. No language model participates in these runs.

The **Teach full Sudoku curriculum** button explicitly installs 20 normal,
editable procedure graphs from `curriculum/sudoku.json`. This is teacher-supplied
knowledge, not autonomously discovered knowledge:

- `sudoku_symbol`, `sudoku_read`: symbol meanings and spatial reading order;
- `sudoku_rules`, `sudoku_problem`: alphabet, blank marker, rows/columns/boxes;
- `finite_valid`, `finite_candidates`, `finite_options`: validity and candidates;
- `finite_naked_single`, `finite_hidden_single`, `finite_decision`: deductions
  and selecting a branch;
- `finite_search`: explicit stack, candidate expansion, rejection and backtracking;
- `sudoku_solver`, `sudoku_check`: solving and separate result checking;
- `sudoku_input`, `sudoku_do`: move, click, type, observe feedback;
- `sudoku_observe_check`, `sudoku_observe_solve`: the outer sensory workflows;
- `sudoku_observe_read`, `sudoku_query_candidates`: taught reading and candidate queries;
- `sudoku_goal_check`: a separate board observation and Bool checker for goals.

The runtime supplies small generic operations: list/record access, lookup,
structural comparison, conditionals, map/filter, loops, procedure calls and
scoped device I/O. It has no `csp_solve` instruction. The canvas has no candidate,
constraint-construction or validity helper. Search, candidate logic, group data,
and input sequencing are executable graph data. Runs remain resource-bounded;
a sufficiently difficult puzzle can exhaust the step budget. The curriculum
includes singles and search, not every named advanced human Sudoku technique.

Inspect and revise any lesson in **Stored sensory procedures**. Forgetting a
required dependency stops a run before any device effects and identifies the
missing lesson. Loading, solving or unrelated teaching never rebuilds a deleted
lesson. Explicitly teaching the whole curriculum again replaces its definitions.
`build_sudoku_curriculum.py` is an authoring script; the application never imports
or executes it. Legacy prose strategy records are historical descriptions and
cannot activate a built-in solver.

The graphs share the ordinary procedure library in the authoritative graph
database. General concept inference, pattern rewriting and toy-world hypothesis
search also execute taught graph methods. This does not make the system AGI.

### Reusable senses and taught actions

The **Senses & learned actions** panel adds a separate, basic `canvas` device:

- `observe`: text marks, geometry, line positions, pointer and input feedback;
- `move`: normalized x/y coordinates from zero to less than one;
- `click`: click at the current pointer position;
- `key`: type a digit or use Backspace/Delete.

These controls affect the local canvas only. The scene is supplied by the drawing
adapter, not recognized from raw pixels. It contains no candidate lists, cell
values, Sudoku constraints or answers. Input feedback reports device acceptance, not Sudoku correctness or a subjective feeling. The app UI has direct access to its own board state. Executable skills receive
only the basic canvas, workspace and clock ports; no rich Sudoku adapter is available.

Click **Load reading lesson**, inspect it, then **Teach / revise lesson** and
**Run stored lesson**. The example explicitly teaches blank → 0 and each digit
symbol → its number. Use **Teach a symbol meaning** to edit the table without
editing JSON graph nodes, then teach the revision. Unknown symbols cause a
request for another interpretation. The same interpreter can read another
surface with different marks when given a corresponding table.

**Load action lesson** teaches move → click → key → observe. Supply
`{"x":0.277778,"y":0.055556,"key":"4"}` to enter 4 in the third position of the
top row of the default board. Clicking the board fills coordinates into the
input editor. Each action records its observed result; edits to starting clues and conflicting digits are accepted. A failed later step does not undo earlier
device actions, which remain visible in the experience history.

The two examples (`examples/read_marks.graph.json`, `examples/type_at.graph.json`)
are never automatically installed. Teaching and revisions persist as normal
procedure graphs. Forgetting a procedure removes its execution capability;
historical lessons do not resurrect it on restart. Saved action experiences are
never re-executed during notebook loading. No LLM participates in these runs.

The interpreter supplies generic `Data`, field access, table lookup, records,
map/filter, comparisons, sequencing and sensor I/O. Symbol meanings and action
order are supplied by the lessons. Autonomous perceptual learning and autonomous algorithm discovery remain future work. This foundation is not AGI.

## Authoritative graph memory

The live preview stores its memory in `preview-memory.graph.sqlite3`. Python's
standard-library SQLite engine holds typed nodes, ordered edges and named roots.
Objects and procedure instructions are decomposed into nodes and edges; they are
not JSON document blobs. Application mappings are database views.

The same database holds:

- `knowledge.*`: assertions, negation, inference proofs, subtype and symmetry rules,
  definitions, executable programs and explicit mathematical rewrite lessons.
- `experience.*`: conversation provenance, execution traces and sensor events.
- `world.*`: observed features, action vocabulary, episodes, learning-context
  boundaries, hypothesis space and the toy world's evidence graph.
- `session.settings` and `environment.state`: identity, routing settings and the
  saved canvas state. The live canvas and sensor drivers remain environment code.

`Session.load` imports an existing JSON notebook once if no sibling graph database
exists. The JSON file is preserved as a legacy backup. Subsequent starts read
current graph roots directly, never replay teaching messages or device actions.
Deleting an executable root disables that lesson even if its original teaching
remains in historical evidence. Deleting a lesson is not a privacy purge of its
history. Re-teaching requires an explicit teaching action.

Transactions commit database changes atomically. Structured messages are validated
in an isolated staging graph before their knowledge changes are committed. Physical
input effects cannot be rolled back; their sensor evidence remains recorded. Back
up the SQLite file while the preview is stopped, or use SQLite's backup API.
The `--memory` argument accepts a SQLite path or the old JSON name (which resolves
to its sibling `.graph.sqlite3` database). Do not delete the graph database while
leaving the old notebook in place unless you intend to import that notebook again.

`/api/graph` returns stored IDs and edges, including roots that distinguish current
capabilities from inert history. The generic runtime still implements execution,
symbol/collection operations, graph access and device I/O in code. Live arithmetic, inference, rewriting,
hypothesis revision, planning, calendar interpretation, counting, Sudoku and
algebra methods are taught graph programs. Autonomous procedure synthesis
remains unimplemented. The earlier `meaning.py` / `adaptive.py` CLI demonstrations
retain their original engines; they are not the preview's inference implementation.


## Unified skills, goals and interface use

The **Skills, senses & goals** panel now runs every supported procedure type.
The same `knowledge.procedures` roots hold application skills and the methods
for matching, inference, rewriting, planning, calendar interpretation and use
of the workspace/clock/canvas ports. There is no per-skill Python registration.
Existing English shortcuts remain syntax/routing adapters. The kernel implements
execution, symbol/collection operations, type/resource checks and raw device I/O.
This remains software; the domain algorithms are editable program data.

A new notebook receives an explicit starter curriculum from
`curriculum/numbers.json` and `curriculum/foundation.json`. Existing notebooks load only their current roots.
`Teach foundations` explicitly installs/replaces those lessons. Forgetting a method
never reloads its source file. Without inference methods, only directly stored
assertions remain available; deductions are discarded. The latest inputs/results
and program-root IDs for core methods are stored in `knowledge.executions`.

To test a new skill family without editing Python:

1. Open **03 / Teach a new skill family and pursue a goal**.
2. Click **Load temperature example** and inspect the three graph lessons.
3. Click **Teach this package**, then **Find a plan & run**.
4. The planner combines Fahrenheit conversion with temperature assessment. The
   supplied input of 86 yields `{"celsius":30,"warm":true}`. Try 32 or 68 next.
5. Select and revise `temperature_assess` in the lesson editor. Changing its
   threshold while keeping the original checker makes the outcome check fail.
   Forgetting the conversion procedure removes the available plan.

The same request works in chat:

```text
Goal: {"have":["fahrenheit_reading"],"want":["temperature_assessed"],"input":{"fahrenheit":86},"check":"temperature_check"}
Run skill temperature_convert: {"fahrenheit":68}
Run skill workspace_read: {"namespace":"knowledge.procedures","key":"temperature_convert"}
```

Skill graph metadata declares `requires`, `provides`, and optional `deletes` tags.
`plan_search` implements breadth-first search under the limits in `plan_policy`
(default 12 actions / 128 explored states). `plan_execute` passes the current
result through each chosen program. Contracts are teacher claims: without an
explicit Bool checker, a run is marked `executed_unverified`. A checker verifies
only the conditions it was taught; the example checker tests the warm flag, not
sensor truth or the conversion formula. Goals, plans, outcomes, actual traces and
failures persist under `skills.goals` / `skills.runs`.

`workspace_read`, `workspace_write`, `workspace_keys`, and `workspace_forget`
are taught usage programs over a raw, local record API. They let a program inspect
and revise knowledge or other programs. Changes take effect on the next invocation;
each invocation uses a consistent procedure snapshot. Actions and their before/after
records remain in experience history. This is explicit revision, not autonomous
self-improvement. Sensor history cannot be rewritten through this port.

Calendar names, ordinal endings, leap-year logic, field bindings and interpretation
of the clock's date string are in `calendar_*` / `clock_*` methods. The host reads
the clock; `clock_calendar` is the taught binding for the `current_date` instruction.
The birthday replacement policy is in `memory_policy`, rather than an implicit
birthdate special case in the chat handler.

Arbitrary skill prose, automatic algorithm invention, unbounded reasoning, raw-pixel
vision and AGI remain outside the implemented scope. A teacher must supply methods
expressible with the existing primitives and available ports. New external hardware
still needs a driver, and new primitive operations still require implementation.

The taught Sudoku entry point also declares a skill contract. With the current
Sudoku curriculum installed, the generic planner can select and execute it:

```text
Goal: {"have":["sudoku_canvas"],"want":["filled_sudoku_canvas"],"input":null,"check":"sudoku_goal_check"}
```

This executes the same taught solver and canvas inputs, then independently reads
the actual board again for the taught outcome check. Its correctness criterion
still depends on the validity of the supplied Sudoku rules.

## Taught numbers and inspectable execution

Teaching now stages an isolated database snapshot and adopts its computed facts
without recomputing inference during either copy or commit. The taught
`horn_join` narrows constant-relation candidates before structural matching;
variable relations still consider all facts. This remains a graph algorithm.
The interpreter shares immutable literals within each run and keeps a bounded
validation cache, avoiding repeated copies of the same arithmetic tables.

The browser loads one initial view and requests changes using `state_version`.
Unchanged procedure/board sections are omitted; conversation updates contain only
changed rows. Unknown or expired versions receive a complete view. Large messages
and traces have short previews, with links to `/api/record` for full stored
evidence. The graph database retains all originals. Clients that omit
`state_version` still receive a complete display view on each request.

`curriculum/numbers.json` supplies decimal symbols, quantity marks, carry/borrow
and multiplication tables, long division, rational reduction, comparison, powers,
counting and numeric parsing as ordinary Data graph programs. Numerical opcodes
resolve their current `interface` binding in `knowledge.procedures`. These number
lessons contain no numerical arithmetic instructions themselves: they manipulate
symbols and collections. Deleting a required method blocks the operation; no
native arithmetic solver is used as a fallback. Editing a digit table changes
the next result. Pure memoization lasts for one library snapshot only.

The host still validates and transports rational values using `Fraction`, formats
numbers and equations, parses expression syntax, and enforces size/step limits.
Those boundaries remain code. Supplied numeric conventions and algorithms are
teacher-authored knowledge, not a demonstration of independently discovering
mathematics or understanding quantities from raw perception.

Open **The graph notebook** to follow incoming/outgoing facts or select an
**Executable procedure**, such as `number_add`. Click a green call node to open
its dependency. **Recorded execution** shows actual recorded events, including
taught-arithmetic usage. It is a partial execution trace, not a claim that every
instruction or possible branch was executed.

## Taught questions, waiting and an algebra introduction

`Teach conversation methods` explicitly installs `curriculum/conversation.json`.
Then ask `Teach me algebra` with the algebra and number curricula present. It
runs a short teacher-authored course: undo multiplication, undo addition, collect
terms. Examples and exercises execute the current `algebra_solve`; answers are
not embedded in the course. Reply with a number, `x=4`, `help`, or `stop`.

The `tutor_*` graphs choose questions, hints, answer checks, progression and
requests for missing knowledge. `dialogue_ask` / `dialogue_wait` use a raw local
text port. A question, continuation name and lesson state persist under
`interaction.state`; the host delivers the next message to that named graph.
Restarting neither repeats a question action nor restores a deleted continuation.
Use **Waiting and continuation** in the graph view to inspect this state, or
**Leave this conversation step** to cancel it. Dialogue events and runs retain
their actual graph paths and sensor evidence.

The generic `attempt` node lets a taught policy handle a failed computation as
data. It never rolls back earlier effects or replenishes execution budgets.
This course demonstrates reusable taught interaction, not a general teacher that
can explain every skill, autonomously invent a curriculum, or learn every behavior
from unconstrained conversation. More courses can be supplied as graph data.

### Learning general rules from observations

`curriculum/learning.json` contains twelve editable graph programs for a bounded
observe → propose → check → ask → revise loop. The initial candidate methods cover
mutual relationships and type inclusion. They operate on direct assertions, never
on their own deductions. Two distinct witnesses are required by the starter
policy; the two directions of one mutual pair count as one witness. Missing
conclusions remain unknown, while explicit negations are counterexamples.

New chat assertions and corrections trigger the stored `learning_cycle`.
**Look for patterns** in chat or **Graph notebook → Learning & hypotheses** runs a
full review. Proposals, evidence, decisions and their executable rules live under
`knowledge.hypotheses` in the same graph database. The UI projects a few cases;
the full record retains all evaluated cases. Choose **Ask me about this rule** and
reply **yes**, **no**, or **skip**. A proposal cannot supply deductions before
confirmation, and acceptance rechecks current evidence and the exact pending rule.

Confirmed rules are rechecked during knowledge rebuilding. Counterexamples,
contested supporting facts or loss of the required support disable them; the next
learning review marks them suspended. Reconfirmation is needed after suspension.
Rule proofs retain supporting training observations as well as the current
premise. Workspace actions preserve before/after decision records in attributed
sensor history. The new `entries` memory action is raw I/O, not an induction helper.

Learning methods, thresholds, candidate generators, question selection and reply
handling are stored graph instructions. `learning_policy` controls discovery and
questions. Host code delivers change events, serializes data, interprets graphs,
serves the UI and provides memory/dialogue I/O. This is bounded, teacher-confirmed
symbolic induction, not unrestricted rule or algorithm discovery.

### Taught phrase meanings and separate referents

`curriculum/meaning.json` supplies seven editable graph lessons. `meaning_policy`
contains an explicit vocabulary of modifier meanings and permitted noun heads;
`meaning_phrase` interprets those combinations and preserves unknown phrases.
For example, `red ball` entails `ball` and `color red`, whereas an untaught phrase
such as `fake gun` does not entail `gun`. This starter vocabulary is deliberately
small; it is not general adjective understanding.

`meaning_fact` separates a name expression such as `Julia (name)` from the person
Julia. The adjective in `female name` describes the name; it does not infer a
person's gender. `meaning_rules` compiles the taught positive entailments as Horn
rules. Negative compound membership alone does not imply either negative part.
These deductions are not counted as independent observations by the learner.

`meaning_assertions` applies explicitly taught source-qualified identities before
inference and learning. The live notebook was taught separate labels for Mercury
(the planet) and Mercury (the element), using its existing reference source
markers. Original assertion text and sources remain stored for provenance.
`meaning_reference_question` asks which qualified label is intended for a bare
ambiguous name; `meaning_retraction_keys` resolves corrections to the original
stored assertion keys. The starter policy has no Mercury-specific mappings.

The Python adapters call these graph methods, and Gemma receives instructions to
preserve noun phrases and qualified labels. The interpreter, language parser and
UI remain code. These changes do not make all natural-language interpretation
learned or eliminate the host runtime.

The learning panel initially shows actionable and active proposals. Enable
**Show early observations and reviewed proposals** to inspect the rest. Authorized
Codex teacher reviews are labelled separately from user messages; their replies,
reasons, sources and executed graph runs are retained in the notebook.

### Teaching days between dates, then applying it to birthdays

`curriculum/calendar_reasoning.json` is an explicit lesson package, generated by
`build_calendar_reasoning_curriculum.py`. It is not automatically restored when
forgotten. It teaches Gregorian leap years, day of year, a date's day number,
and `calendar_days_between`: end day number minus start day number. This works
for dates across months/years, including leap days, zero and negative intervals.
The arithmetic calls the existing taught number procedures.

`calendar_next_annual_date` separately finds the next occurrence of an anchor's
month/day on or after a given date. `calendar_question_policy` teaches the
birthday connection: obtain the person's birth date using `calendar_find_birth`,
observe the clock, find the next yearly occurrence, and invoke the general
interval method. Missing/conflicting/future birth dates block an answer. A
February 29 birthday in a non-leap year requests an observance convention; the
system does not silently choose February 28 or March 1.

`language_question_policy` supplies a bounded set of question templates, including
“In how many days is [person] his birthday” and “How many days until my birthday?”.
`language_interpret` matches these supplied forms, then requests the taught
computed property. `computed_question_policy` links that property to its graph
method. These forms run without Gemma; unmatched phrasing still uses the language
interface. The host additions only invoke an optional taught language method,
display text returned by a taught lookup method, and retain its execution trace.
There is no new birthday arithmetic or birthday-specific routing branch in Python.

The live notebook was explicitly taught all thirteen lessons and retains the
teacher's explanation. Removing `calendar_days_between` prevents answering the
birthday countdown; it does not fall back to age or a native date subtraction.

### Taught participant references and concept word forms

`curriculum/identity.json`, authored by `build_identity_curriculum.py`, is an
explicit, removable lesson package. `dialogue_reference_policy` maps user-message
pronouns to the current speaker/addressee; `dialogue_resolve_operation` applies
those mappings only to participant fields. The host passes current names into
that graph and uses its returned references. Self-descriptions include the
ordinary retrieved facts through `dialogue_self_description`.

`relationship_language_policy` teaches that A created B means B created by A.
`meaning_fact` normalizes both positive and negative evidence with that lesson.
`dialogue_question_policy` teaches bounded question forms and lookup direction:
“Who created you?” and “Who created Nex?” retrieve the same known creator.
The answers come from evidence, with no creator names in these policies. Other
language forms retain the existing calendar and Gemma interpretation paths.

`meaning_reference_policy` explicitly links the concept labels human and humans.
`meaning_reference` resolves these uniquely declared forms for both concept
membership and relationship endpoints. It does not strip word endings or equate
every individual human with the human concept. A relationship to that concept
does not automatically imply a relationship to all its members. Raw assertions
and their original wording remain in the notebook; interpreted graph facts use
the shared label. Unknown or ambiguously declared labels remain unchanged.

The package preserves earlier meaning and language methods under
`*_before_identity`. Rebuilding it preserves those original methods rather than
wrapping the dispatcher recursively. Existing notebooks require explicit teaching;
startup never reinstalls a missing identity lesson.

### Linked commands in ordinary chat

The explicitly taught `curriculum/sequences.json` package lets chat compile and
execute up to eight ordered calls to available graph procedures. Try:

```text
Start with 5, then double it, then add 3, then tell me the result.
Get my birth date, then get today's date, then find the next birthday, then calculate how many days are left, then tell me the result.
Start with 5, then run factorial on that, then tell me the result.
```

`sequence_clause_policy` supplies editable language forms. `sequence_interpret`
compiles entirely recognized requests without a model call; an unknown clause
hands the whole request to Gemma's separate sequence schema. That translation
can request clarification, and can still misinterpret unfamiliar wording.
Its instructions forbid supplying calculated results. A `{"var":"s1"}` placeholder links to the
actual value produced by step s1, including nested record/list inputs. The
existing taught tree traversal and substitution methods resolve these references.

`sequence_catalog` selects public numeric procedures, skill contracts and methods
declaring `sequence_input`. Consequently a newly taught compatible procedure can
be used as “then run NAME on that” without adding host dispatch code. Learned
helpers supply arithmetic, live dates, memory property lookup and explicit field
selection; the sequence host does not implement their calculations.

`sequence_prepare` checks named dependencies before the first action; the host
also checks every selected program's static dependencies. `sequence_execute`
passes values in order and stops at the first runtime failure. Completed steps
and effects remain recorded; failed sequences are not automatically retried.
Missing initial references ask for a starting value. A numeric reply continues
the unstarted request, while other clarifications are reinterpreted with the
original instruction. Stop/cancel leaves it unexecuted. This is bounded sequential
composition, not arbitrary natural-language control flow.

Original instructions, translated plans, actual per-step arguments/results and
execution traces are stored under `skills.sequences` and in conversation records.
The existing graph inspector exposes the recorded execution. The transport/UI
adapter is `sequences.py`; the behavior is authored in
`build_sequence_curriculum.py` and `build_sequence_language.py` and explicitly
taught to the live notebook. Missing lessons are not restored on startup.

Assistant renames are taught by `curriculum/rename.json`. The stored
`meaning_rename_reference` program revises `meaning_reference_policy`, keeping
one identity and its historical names. Fact subjects and objects resolve through
that policy, so existing incoming/outgoing relationships survive subsequent
renames. Original assertion wording and conversation history remain evidence.
The host validates and saves the computed policy in the same transaction as the
assistant display name; a failed operation leaves both unchanged. The inspector
follows the renamed assistant. A name already assigned to another entity or
concept is refused to prevent accidental merges. If the rename lesson is removed,
renaming requires teaching it again. Explicit forms include “Your name is now
Echo”, “You are Echo now”, and “Update all Nex references to Echo” when Nex is a
known name of the current assistant. Other wording can still use Gemma.

The dark assistant workspace has Conversation, Memory, Internal state, Routines,
Tools, and Teach & inspect tabs. The toy-world UI and Seed branding are removed;
existing observations remain in storage. Chat has a fixed composer and opens at
the newest message. Graph identity remains amber; state cards have separate
accent colors. Background messages arrive through incremental state polling.

`curriculum/affect.json` teaches persistent functional curiosity, uncertainty,
satisfaction, and sympathy in `skills.affect/current`. `affect_policy` supplies
editable 0–100 activation changes, and `affect_update` executes taught arithmetic
and records the last twenty causes. These are functional signals, not calibrated
confidence or a claim of subjective experience. Explicit phrases such as
“How are you feeling?”, “I feel sad”, and “No advice” run the stored report or
support methods. Unknown wording still depends on the existing language layer.
Concern can schedule one gentle follow-up after three minutes; the follow-up
stays quiet if a later meaningful event has superseded the difficulty.

`curriculum/background.json` teaches named subroutine scheduling, execution,
reminders, cancellation, and failure handling in `skills.subroutines`. The engine
delivers a timer every five seconds; the graph chooses which due job to invoke.
It runs at most one per tick, defers during a pending dialogue continuation, and
stops failed jobs instead of retrying indefinitely. Deadlines persist; the local
server must run for delivery. No OS notifications or external messaging.
Try “Remind me in 30 seconds to take a break”, or use the Routines form. General
`background_schedule` takes id, method, argument, delay_seconds, repeat_seconds
(0 for once). Any compatible taught routine can be scheduled.

`session.behavior` binds the interpreter, after-turn observer, and background
method. Python delivers raw events and validates execution; graph lessons
classify outcomes and choose responses. Deleting a bound lesson produces an
explicit error; it is never silently restored. The clock port now additionally
provides unix_seconds for general scheduling. Existing date fields are retained.
