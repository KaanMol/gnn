Generic prepared-plan optimization (September 7, 2026)

Prepared sections now use version 1 of the generic register-bytecode format: integer
opcodes, tuple input-register addresses, source IDs, metadata, and an output register,
and per-instruction validation requirements derived from generic operation semantics.
Projections and bounded-subset operations reuse already validated immutable data;
constructors and external inputs still enforce collection, scalar and aggregate bounds.
Graph-to-graph Data ports for size/indices no longer serialize and deserialize JSON.
Interface resolution is cached only within the current library snapshot, so edits and
removed bindings still take effect on the next execution. No stored arithmetic or
language procedure is replaced by a native implementation. Logical node budgets,
lazy branches and effects retain their original execution order.

`ExecutionCache(optimize=False)` supplies the reference path for differential tests.
This bytecode is currently held as Python instruction tuples, with metadata tables.
It is not machine code, a JIT, a portable binary file format, or parallel execution.
The existing stored graph policy continues to control section preparation/release.

Graph-orchestrated RAM sections (September 7, 2026)

`javascript_run_source` calls the stored `javascript_warm_policy` before compiling.
The policy asks the generic engine surface for the current compiler section status,
then requests preparation only when cold or changed. The section includes reader,
compiler, numeric dependencies and nested graph bodies. `javascript_release_policy`
requests release. These decisions and target names are editable graph data.

The engine provides `status`, `prepare` and `release`, content-addressed immutable
instruction layouts, shared-section ownership and hard capacity bounds. Cold layouts
are temporary: visiting a graph alone does not retain it. Preparation refuses over-capacity
requests rather than choosing another section to evict. Byte accounting is serialized
size, not an exact measurement of Python RAM overhead. Changes select new layouts;
section refresh drops obsolete unshared layouts. Each execution still validates rules
and enforces its step budget. Existing pure-result memoization is separate and still
uses host LRU bookkeeping. This is explicit graph policy, not autonomous policy learning.

Prepared layouts reuse instructions across changed inputs; they do not skip parsing
changed source or make the remaining graph interpreter steps free.

# Execution cache and prepared graph instructions

The generic interpreter prepares graph nodes into indexed instructions once
per run. Per-session caching is enabled only for graph procedures explicitly
marked `cache_across_runs`, with Data input/output and no observable effects
in their dependencies. Compiling source and lowering syntax nodes use this.

Each invocation validates dependencies first and fingerprints the complete
current procedure library. Any procedure change clears cached results; deleting
a dependency still fails before any action. Cached results are copied, bounded
to 1,024 entries and approximately 16 MB of serialized keys/values, and charged
against the caller's logical step budget. Sensor observations and actions are
never cached. The cache is in memory and starts empty after restart.

Repeated source can reuse compiled instructions. Changed source is still parsed
in full, but unchanged syntax subtrees reuse compilation results. This is not
full incremental parsing. Source positions are excluded from the graph lowering
interface by an explicit graph rule, not by a host-language cache special case.
The cache hit/miss summary appears in the execution trace.

Validation: `python3 -B -m unittest test_execution_cache test_graph_source_pipeline
test_foundations test_sensory_graphs -q` (write on one shell line).

# Graph syntax expansion and learning update

The source reader now carries source length and grammar arity/width as graph
state instead of repeatedly counting collections. No interpreter shortcut or
host language parser was added for this optimization.

Executable additions: assignment, compound assignment, increment/decrement
statements, if/else, while, traditional for, and do/while. Graph rules relocate
branch targets, reject const updates, and make for-loop declaration bindings
unreadable after the loop. General lexical scopes and closure behavior remain
incomplete; declarations inside control-flow bodies explicitly fail.

`source_learning_discover` generates a bounded set of character-class grammar
candidates, checks labeled examples and regressions, and saves the evidence to
`knowledge.source_learning`. `source_learning_evaluate` also accepts supplied
candidate rules. This is finite hypothesis selection, not autonomous discovery
of JavaScript semantics. It does not overwrite production grammar based only
on recognition tests. A future adoption rule needs syntax-tree and execution
regressions as well.

Full syntax support is NOT complete. See SYNTAX_COVERAGE.json for the target and
known gaps. The official Test262 suite has not been run; these are local
acceptance tests, not a conformance percentage.

# Current source pipeline: graph only

Chat and the playground invoke `javascript_run_source` using raw source text.
The stored `javascript_read_source` grammar parser and `javascript_compile_source`
lowering rules produce instructions for the stored `js_execute` evaluator.
`javascript.py` contains transport, typed input conversion, graph dispatch and
output formatting. It contains no JavaScript parser. The Python JSX parser has
been removed. Offline `compile_source` also dispatches to graph procedures.

Authoring files in `graph-authoring/*.mjs` emit JSON graph data; Node is not
invoked when submitted code runs. The live source of truth is the procedures
in the graph database. Removing a reader rule fails execution; there is no
Python or native-JavaScript parser fallback.

This switch deliberately has a narrower supported grammar than the former
Python parser. Supported: simple declarations, scalar expressions, arrays and
objects, expression-bodied map/filter/reduce callbacks, console.log, selected
Math methods, assignments, if/else, while/for/do-while, and a single component with intrinsic JSX. Source is bounded to
1,800 characters and 10 million graph steps. Function arguments go in the
playground JSON input; appended calls, general function calls, break/continue,
lexical declarations within control-flow blocks, destructuring, hooks, custom components and
general JSX entities still need graph lowering rules. Rejected syntax never
falls back. This is not full JavaScript or React conformance.

Acceptance tests: `python3 -B -m unittest test_graph_source_pipeline -v`.
The prior Python-parser tests below describe historical coverage and are not
evidence of current graph-parser compatibility.

---

## Historical implementation notes (superseded by the graph source switch)

# Programming lessons and JavaScript adapter

The programming package teaches 23 inspectable graph procedures and 36 general programming
concepts. `programming_execute` consumes a language-independent instruction
representation; JavaScript is its first source parser. Variable state, expression
evaluation, branching, looping, returns, execution traces, and checking examples
are executed by stored graphs. Forgetting an execution lesson disables its use.

The Python adapter parses and lowers source syntax, validates the subset, formats
answers, and contains failed candidate executions. This parser/compiler is host
code. Numeric operations use the existing taught arithmetic. Candidate source
templates and replacement proposals are explicitly teacher-authored data, not
unrestricted program synthesis. No submitted source is passed to eval or Node;
Node is used only as an independent oracle in tests.

## Try in the preview chat

The **JS playground** link in the preview header opens the integrated editor.
Run a script or function there, optionally supply a JSON input, and inspect
captured output, statement transitions, compiled instructions and stored graph
evidence. The playground calls `js_execute` through a dedicated API, preserving
any pending conversational question. It does not execute code in the browser.

The React learning notebook contains HTML foundations, JSX and React concepts,
plus reference component patterns, read through the stored `react_explain` graph.
`Teach me HTML`, `Teach me JSX`, `Teach me React`, and `Explain React: state` also
work in chat. `jsx_attribute_name` applies selected HTML-to-JSX attribute-name
correspondences. These two lessons are additional to the 23 programming procedures.
They are reference knowledge and one small conversion rule, not a React runtime,
full HTML/JSX parser, general component generator, or ability to run hooks.

You can paste a function followed by one call with a literal argument, as plain
text or in a JavaScript code fence:

```javascript
function double(x) { return x * 2; }
double(21);
```

A definition without a call is parsed and prompts you to add an input. The
definition is not automatically installed as a reusable procedure.

Scripts with declarations and console output also run directly:

```javascript
const xs = [-3, 9];
console.log("largest", Math.max(xs[0], xs[1]));
console.log("power", Math.pow(2, 5));
```

Console calls capture ordered argument lists in the execution result's `logs`.
The display shows those lists; browser formatting and `%s` substitutions are not
implemented. Log-only scripts/functions return a tagged `undefined`, shown as
`undefined` in the answer. Logs are program data, not external console I/O.

```text
Teach me programming
```

```text
Run JavaScript: {"source":"function double(x) { return x * 2; }","input":21}
```

```text
Explain JavaScript: {"source":"function sum(xs) { let total = 0; for (let i = 0; i < xs.length; i++) { total += xs[i]; } return total; }","input":[3,-2,9]}
```

```text
Write JavaScript: {"task":"maximum"}
```

```text
Fix JavaScript: {"source":"function max(xs) { if (xs.length === 0) { return null; } let best = 0; for (let i = 1; i < xs.length; i++) { if (xs[i] > best) { best = xs[i]; } } return best; }","tests":[{"input":[],"expected":null},{"input":[-9,-2,-7],"expected":-2},{"input":[3,8,1],"expected":8}]}
```

Writing tasks: `maximum`, `minimum`, `sum`, `count_positive`, `product`,
`absolute`, `factorial`, `toggle_todo`, `visible_todos`, and `cart_total` (integer cents).
Optional `tests` override the teacher's examples.
The selector runs candidates and returns one that passes all supplied examples.
This does not establish correctness for all inputs. Unsupported repairs report
that no supplied candidate passes. Explanations currently show executed state
transitions rather than free-form natural-language explanations of arbitrary code.

## Supported boundary

- One named function with one parameter, explicit semicolons and brace blocks.
- Standalone scripts with declarations, blocks, conditionals, loops and console output.
- Safe integers, Boolean values, null, tagged undefined, short strings, dense arrays and plain data objects. External data is bounded to eight nested levels and 64 entries per container.
- Block-scoped `let`/`const`, shadowing, temporal dead zone checks, uninitialized `let`, assignments, `+=`, `-=`, `*=`, `++`, `--`.
- Arithmetic `+`, `-`, `*`, comparisons, scalar `===`/`!==`, unary `-`, `!`, `typeof` and `void`.
- Truthiness, `Boolean()`, lazy `&&`, `||`, `??` and `?:`. Skipped expression branches are not executed.
- Array indexing and `.length`; `if`/`else if`/`else`, `while`, `do`/`while`, `for`, `break`, `continue`, `return`.
- `console.log` with up to eight arguments, string literals/simple escapes, and string-to-string concatenation.
- Integer-domain `Math.abs`, `sign`, `floor`, `ceil`, `round`, `trunc`, `min`, `max`, and `pow`. Min/max require 1–8 arguments; powers require exponents 0–32 and safe-integer results.
- For-loop lexical declarations can shadow outer variables and are unavailable
  outside their loop. Per-iteration captured bindings require closures, which are missing.
- Object literals with shorthand properties, dot/bracket own-property access,
  object/array spreads, and shallow declaration destructuring with object aliases.
- `map`, `filter`, and `reduce` with an explicit initial accumulator, using inline
  arrow callbacks. Expression bodies and a block containing one return are supported.
  Callbacks receive the usual item/index/array or accumulator/item/index/array
  arguments, read enclosing bindings, and can nest through eight graph continuation
  frames. Arrays are dense and limited to 64 elements for these methods.

This is a restricted JavaScript subset. Apart from truthiness, it does not implement general coercion,
floating-point arithmetic, division, general objects, array mutation, first-class callbacks,
closures, function-to-function calls, recursion, modules, async, the DOM, or Node APIs.
Unsafe integer results, array reference equality,
out-of-bounds indexing are explicit errors rather than full
JavaScript behavior. Programs stop after 300 executed instructions, so large or
long-running programs may exceed the budget even with otherwise supported syntax.
`typeof` accepts known bindings and supported expressions; its special behavior on
undeclared identifiers is not implemented. Selected built-in names cannot be
shadowed. Lexical names are resolved to slots by the Python compiler; the stored
`js_read_binding` procedure enforces initialization and reads their values.
`js_to_boolean`, `js_is_nullish`, and `js_typeof` implement their supported value
rules as editable graph data, with no changes to native interpreter operations.
Plain objects are tagged data records, not identity-bearing heap objects. Equality
between objects is rejected, as are prototype lookups not present as own fields.
Spread supports plain objects (and ignores null/undefined), not primitive boxing,
symbols or getters. Destructuring defaults, rest, nested patterns and iterators are
missing. Short array destructuring currently rejects missing positions.
Inline callbacks cannot be stored, returned, passed by variable or contain arbitrary
statements. Their entry, parameter binding, iteration and return are stored graph
procedures; no Python callback evaluator or JavaScript engine is involved.

General concept descriptions include functions, scope, invariants, preconditions,
postconditions, counterexamples, debugging, and generalization. A description
does not imply that every related capability (such as proving invariants) exists.

## Procedure capacity

The graph validator now accepts up to **500 nodes per procedure or nested graph**,
up from 100. Execution-step, call-depth, and data-size limits still apply. Capacity
tests execute a full 500-node graph, reject 501 nodes, and confirm that the runtime
step budget still stops work. This is distinct from the knowledge graph's fact count.

Semantics reference: [ECMAScript language specification](https://tc39.es/ecma262/).
The documented subset deliberately rejects cases it cannot faithfully represent.
`ES2026_SUPPORT.json` inventories the target's implemented and missing areas.
The project is not ES2026-conformant and has not passed Test262. Integer rounding
methods currently return the integer unchanged; fractional arguments are rejected
by the source/input adapter. `Math.sqrt`, trigonometry, `Math.random`, constants,
and the remaining Math API are not implemented. Console is a host API specified
by the [Console Standard](https://console.spec.whatwg.org/), separate from ECMA-262.

Run checks with `python3 -m unittest test_javascript test_javascript_semantics test_javascript_data test_programming_preview test_graph_capacity`.
The differential tests compare 18 generated cases, 3 Math/log cases and 14
value/control/scope scripts, plus 20 data-transformation scripts with Node.
These are project regressions, not Test262; other
checks cover negative/empty inputs, control flow, types, budgets, teaching changes,
missing methods, language-independent input, candidate selection, and repair.


### Verified React Learn JSX entry point

The playground now accepts the unchanged `Profile` default-exported function
from React Learn “Your First Component”, and the first `MyButton` function from
Quick Start. `test_react_jsx.py` extracts their source directly from the pinned
official snapshot and checks graph execution results. Select **React Learn:
Profile (element tree)** in the playground.

`jsx_syntax.py` lowers intrinsic JSX, attributes, brace expressions, child lists,
and fragments into object-construction expressions. Stored JS graph procedures
evaluate those expressions and return `{type, props, children}` element trees.
This is a structural output format, not a React element identity implementation
or a DOM renderer. It preserves raw children (including arrays and booleans).
The entry function may have zero arguments and an optional default export.
Custom component calls, imports, hook state, event dispatch, reconciliation, and
effects are not executed yet. The full React Learn goal remains incomplete.
