Programming additions
=====================

The source reader, callback lowering, pipeline composer, test selection and static
analysis are executable graph lessons. Python routes requests and converts input/output
values. The Node authoring scripts emit lesson JSON and never execute submitted code.

Callback blocks
---------------

Single-return callback bodies now work for map/filter/reduce/find/findIndex/some/every:

```javascript
function total(items) {
  return items
    .filter(item => { return item.active; })
    .map(item => { return item.price * item.quantity; })
    .reduce((sum, value) => { return sum + value; }, 0);
}
```

Use the playground Input field for the array argument. Blocks containing declarations,
updates, multiple statements or other control flow are still rejected. This is not full
JavaScript callback support; existing safe-integer, source-size and array limits remain.

Compose and test a function
---------------------------

Paste this command into chat:

```text
Write JavaScript: {"pipeline":[{"operation":"filter","expression":"x.active"},{"operation":"map","expression":"x.price * x.quantity"}],"finish":"sum","tests":[{"input":[],"expected":0},{"input":[{"active":true,"price":5,"quantity":3},{"active":false,"price":100,"quantity":1}],"expected":15}]}
```

The graph composes a new function from 1–8 ordered filter/map stages. Each expression
uses `x` as the current item; `finish` is `array`, `sum`, or `count`. It parses the emitted
source with the stored reader and executes all 1–12 supplied tests. A failed test rejects
the function. This is constrained composition from a structured specification, not
arbitrary natural-language app generation or autonomous learning. Passing examples
is not proof of correctness for every input.

Explain supported source without running it
------------------------------------------

```text
Explain JavaScript: {"source":"function count(xs) { const n = xs.length; return n; }"}
```

This returns the function name, parameter and ordered statement descriptions, including
bindings, branch targets and expression instructions. It does not require an input or
execute the source. Expression details are currently structured instruction data rather
than a full natural-language explanation. Existing Run JavaScript commands still execute
and show actual values and traces. Existing named starter Write tasks remain available.
