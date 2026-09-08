"""Authored HTML/JSX/React lessons and reference patterns stored in the graph.

Reference source is not evidence that the JS subset can execute hooks or JSX.
"""


def lessons():
    react='https://react.dev/learn/'
    html='https://html.spec.whatwg.org/multipage/'
    def lesson(title,explanation,example,source):return dict(title=title,explanation=explanation,example=example,source=source)
    result={
      'overview':lesson('HTML → JavaScript → JSX → React','HTML supplies semantic page structure. JavaScript supplies computation. JSX describes element trees using JavaScript expressions. React components combine those trees with props and state. These are taught reference lessons; the graph interpreter does not yet execute JSX, hooks, or React reconciliation.','Start with html_structure, html_semantics, html_forms, then jsx, components, props, state and events.',react),
      'html_structure':lesson('HTML document and element structure','HTML describes a document tree. Elements may contain attributes, text, and child elements. A document normally separates metadata in head from visible content in body. Nesting must follow each element’s content rules.','<!doctype html>\n<html lang="en">\n<head><title>My page</title></head>\n<body><main><h1>Hello</h1><p>A paragraph.</p></main></body>\n</html>',html+'semantics.html'),
      'html_semantics':lesson('Choose elements by meaning','Use headings for hierarchy, main for primary content, nav for navigation, button for an action and a with href for navigation. A styled div does not acquire keyboard or button behavior by looking like a button.','<main>\n  <h1>Tasks</h1>\n  <button type="button">Add task</button>\n  <a href="/help">Read help</a>\n</main>',html+'sections.html'),
      'html_attributes':lesson('HTML attributes','Attributes configure elements. id identifies an element in the document; class groups elements for styling. Boolean attributes depend on presence: disabled="false" still disables a native HTML control.','<button disabled>Unavailable</button>\n<input id="email" name="email" type="email" required>',html+'common-microsyntaxes.html#boolean-attributes'),
      'html_forms':lesson('Forms, labels and inputs','Associate a label with an input using for and id, or wrap the input in the label. Input type supplies native behavior; name supplies the field name when a form is submitted. Use appropriate button types.','<form>\n  <label for="email">Email</label>\n  <input id="email" name="email" type="email" required>\n  <button type="submit">Save</button>\n</form>',html+'forms.html'),
      'html_accessibility':lesson('Accessible interaction','Prefer native controls, meaningful headings and descriptive link text. Inputs need accessible names. Images need alt text reflecting their purpose; decorative images use empty alt. Preserve visible keyboard focus. ARIA does not automatically add keyboard behavior.','<img src="portrait.jpg" alt="Portrait of the author">\n<button type="button" aria-label="Remove task">×</button>',html+'interaction.html'),
      'html_void_elements':lesson('Void elements','Elements such as input, img, br, hr, meta and link cannot contain children in HTML. JSX requires explicit closing syntax even for these elements.','HTML: <input type="text">\nJSX:  <input type="text" />',html+'syntax.html#void-elements'),
      'html_text':lesson('Text and markup','Text content is different from markup. Escape special characters when serializing HTML text. React normally escapes strings inserted as children; inserting raw HTML is a separate operation and requires trustworthy content.','HTML text: &lt;button&gt;\nJSX text: <p>{"<button>"}</p>',react+'writing-markup-with-jsx'),
      'components':lesson('Components and composition','A function component returns renderable content. Component names begin with a capital letter in JSX; lowercase names refer to host elements. Components can receive other content through children.','function Greeting({name}) {\n  return <h1>Hello, {name}</h1>;\n}\n// Usage: <Greeting name="Kaan" />',react+'your-first-component'),
      'jsx':lesson('JSX describes an element tree','JSX is JavaScript syntax for constructing element descriptions. It is not an HTML string. Close tags, wrap sibling elements in a parent or fragment, and use braces for JavaScript expressions. class becomes className and label for becomes htmlFor. JSX requires a compiler transform before a browser can run it.','const name = "Kaan";\nconst view = <section className="welcome">\n  <h1>Hello, {name}</h1>\n  <input aria-label="Name" />\n</section>;',react+'writing-markup-with-jsx'),
      'props':lesson('Props are component inputs','A parent supplies props. Treat props as read-only. To request a change, call a callback supplied by the parent or update state owned by the component.','function Action({label, onAction}) {\n  return <button onClick={onAction}>{label}</button>;\n}',react+'passing-props-to-a-component'),
      'state':lesson('State and updates','useState supplies a value for this render and a setter that schedules an update. When the next state depends on the previous state, use a pure updater function. Calling a setter does not change the value already captured by the current render.','const [count, setCount] = useState(0);\n<button onClick={() => setCount(previous => previous + 1)}>{count}</button>',react+'state-a-components-memory'),
      'events':lesson('Event handlers','Pass an event handler function to onClick or onChange. Calling the function while rendering is different from passing it. Read input values from the event in the handler.','<input value={name} onChange={event => setName(event.target.value)} />',react+'responding-to-events'),
      'lists':lesson('Render lists with data transformations','Use filter to select records and map to produce elements. Each directly mapped element needs a stable key. The graph now executes a restricted data-only version of these transformations; producing JSX from callbacks remains a separate missing capability.','todos.filter(todo => !todo.done).map(todo =>\n  <li key={todo.id}>{todo.title}</li>\n)',react+'rendering-lists'),
      'keys':lesson('Stable list keys','A key identifies an item among its siblings across renders. Prefer stable IDs from the data. Generate IDs when creating records, not during render. Index keys can associate the wrong state with an item when a list changes order.','items.map(item => <Row key={item.id} item={item} />)',react+'rendering-lists'),
      'forms':lesson('Controlled forms','A controlled input receives value and updates state in onChange. Prevent the default submission when handling a form in JavaScript. Connect validation messages to their fields and preserve labels.','<form onSubmit={event => { event.preventDefault(); save(values); }}>\n  <label htmlFor="name">Name</label>\n  <input id="name" value={name} onChange={event => setName(event.target.value)} />\n  <button type="submit">Save</button>\n</form>', 'https://react.dev/reference/react-dom/components/input'),
      'immutability':lesson('Immutable object and array updates','Treat state objects and arrays as read-only. Construct replacements using spreads, map and filter. Spread copies only one level, so nested updates need copies along the changed path.','setTodos(previous => previous.map(todo =>\n  todo.id === selectedId ? {...todo, done: !todo.done} : todo\n));',react+'updating-arrays-in-state'),
      'refs':lesson('Refs','useRef retains a mutable value between renders without scheduling a render when current changes. Use state for values shown by the UI. Refs can hold DOM handles or non-rendering bookkeeping.','const nextId = useRef(0);\n// In an event handler:\nconst id = nextId.current++;',react+'referencing-values-with-refs'),
      'effects':lesson('Effects synchronize with external systems','Effects run after rendering to synchronize with an external system. Declare reactive dependencies and clean up subscriptions or connections. Derivable values usually belong in rendering, not an effect that copies them into state.','useEffect(() => {\n  const connection = connect(roomId);\n  return () => connection.disconnect();\n}, [roomId]);',react+'synchronizing-with-effects'),
      'hook_rules':lesson('Rules of Hooks','Call hooks at the top level of function components or custom hooks, never in conditions, loops or ordinary callbacks. Keep rendering pure. These are reference rules, not a claim that the graph implements hook scheduling.','function Counter() {\n  const [count, setCount] = useState(0);\n  return <button onClick={() => setCount(c => c + 1)}>{count}</button>;\n}', 'https://react.dev/reference/rules/rules-of-hooks'),
    }
    result.update({
      'effect_lifecycle':lesson('Practice effect setup and cleanup','For a normal lifecycle pass, mounting runs setup. Changed dependencies cause the previous cleanup, if registered, followed by new setup. Stable dependencies skip this work; unmount runs a registered cleanup. No dependency array reruns after every committed render, while an empty array stays stable. React compares dependencies with Object.is. Development Strict Mode adds a setup/cleanup replay to detect bugs. The graph exercise below models scalar dependencies and action ordering only.',
        'Run React effect: {"phase":"update","previous":["room-a"],"next":["room-b"],"cleanup":true}', 'https://react.dev/reference/react/useEffect'),
      'effect_cleanup':lesson('Subscriptions and request cleanup','Pair a subscription with an unsubscribe cleanup. For asynchronous requests, abort when supported and/or ignore stale results so an older request cannot replace a newer result. Include the reactive values used by the effect in its dependency list. Effects run on the client; the examples are reference code, not executable in the graph JS subset.',
        'useEffect(() => {\n  const controller = new AbortController();\n  let active = true;\n  fetch(url, {signal: controller.signal})\n    .then(response => response.json())\n    .then(data => { if (active) setData(data); })\n    .catch(error => { if (active && error.name !== "AbortError") setError(error); });\n  return () => { active = false; controller.abort(); };\n}, [url]);', 'https://react.dev/reference/react/useEffect'),
      'state_queue':lesson('Practice ordered state updates','Replacement updates ignore the accumulated value; an updater uses the value left by earlier updates. Three replacements with 1 finish at 1; three increments by 1 from zero finish at 3. Run the graph exercise below to inspect each transition. It supports integer replacements/increments only, not hooks or scheduling.',
        'Run React state queue: {"initial":0,"updates":[{"kind":"replace","value":5},{"kind":"increment","value":1}]}',react+'queueing-a-series-of-state-updates'),
      'reducers':lesson('Reducers separate state transitions from UI','A reducer computes next state from previous state and an action. Keep it pure, return replacements instead of mutating the input, and define how unknown actions are handled. React useReducer connects this logic to dispatch and rendering. The playground can execute the data-only example below; it does not execute useReducer.',
        'function counterReducer(input) {\n  const {state, action} = input;\n  if (action.type === "increment") { return state + action.amount; }\n  if (action.type === "reset") { return 0; }\n  return state;\n}\ncounterReducer({"state":2,"action":{"type":"increment","amount":3}});',react+'extracting-state-logic-into-a-reducer'),
      'derived_state':lesson('Compute derived values from source state','Avoid storing a second state value when it can be calculated from existing props or state. A visible list, total, or all-complete flag can be derived during rendering. The following data calculations run in the graph playground.',
        'const todos = [{id: 1, done: false}, {id: 2, done: true}];\nconsole.log("Any complete", todos.some(todo => todo.done));\nconsole.log("All complete", todos.every(todo => todo.done));\nconsole.log("Next", todos.find(todo => !todo.done));',react+'choosing-the-state-structure'),
      'computed_fields':lesson('Update a field without mutating form state','A computed property name selects a key from a JavaScript expression. Combined with object spread, it constructs a replacement form value. In React an event handler can supply the field name and value to a functional state updater. The data-only example is executable in the graph.',
        'const form = {name: "", subscribed: false};\nconst field = "name";\nconst next = {...form, [field]: "Kaan"};\nconsole.log(form, next);',react+'updating-objects-in-state'),
    })
    for kind,source in [('counter',COUNTER),('todos',TODOS),('form',FORM)]:
        result[kind+'_pattern']=lesson(kind.title()+' component pattern',
          'Teacher-authored source pattern. Requires React hooks and a Panel component; placeholders name the configuration points. This is reference code, not execution support in the graph JS subset.',source,react)
    return result

COUNTER = '''function __COMPONENT__() {
  const [count, setCount] = useState(__INITIAL__);
  return <Panel title={__TITLE__} description={__DESCRIPTION__} kind="counter">
    <output className="count" aria-live="polite">{count}</output>
    <div className="button-row">
      <button aria-label={"Decrease " + __TITLE__} onClick={() => setCount(n => n - 1)}>−</button>
      <button className="primary" aria-label={"Increase " + __TITLE__} onClick={() => setCount(n => n + 1)}>Add one ↗</button>
      <button className="quiet" onClick={() => setCount(__INITIAL__)}>Reset</button>
    </div>
  </Panel>;
}
'''

TODOS = '''function __COMPONENT__() {
  const [items, setItems] = useState(() => __ITEMS__.map((text, id) => ({id, text, done: false})));
  const [draft, setDraft] = useState("");
  const [filter, setFilter] = useState("all");
  const nextId = useRef(__ITEM_COUNT__);
  const inputId = useId();
  const remaining = items.filter(item => !item.done).length;
  const visible = items.filter(item => filter === "all" || (filter === "done" ? item.done : !item.done));
  function addItem(event) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    const id = nextId.current++;
    setItems(previous => [...previous, {id, text, done: false}]);
    setDraft("");
  }
  return <Panel title={__TITLE__} description={__DESCRIPTION__} kind="todos">
    <div className="list-meta"><span aria-live="polite">{remaining} left to do</span><span>{items.length} total</span></div>
    <form className="add-item" onSubmit={addItem}>
      <label className="sr-only" htmlFor={inputId}>New item</label>
      <input id={inputId} value={draft} onChange={event => setDraft(event.target.value)} placeholder="Something worth doing…" maxLength={200}/>
      <button className="primary" disabled={!draft.trim()}>Add item</button>
    </form>
    <div className="filters" aria-label="Filter items">{["all", "active", "done"].map(option =>
      <button key={option} aria-pressed={filter === option} onClick={() => setFilter(option)}>{option}</button>
    )}</div>
    <ul className="items">{visible.map(item => <li key={item.id}>
      <label className={item.done ? "completed" : ""}>
        <input type="checkbox" checked={item.done} onChange={() => setItems(previous => previous.map(value => value.id === item.id ? {...value, done: !value.done} : value))}/>
        <span>{item.text}</span>
      </label>
      <button className="remove" aria-label={"Remove " + item.text} onClick={() => setItems(previous => previous.filter(value => value.id !== item.id))}>×</button>
    </li>)}</ul>
    {visible.length === 0 && <p className="empty">A little breathing room. Nothing here yet.</p>}
  </Panel>;
}
'''

FORM = '''function __COMPONENT__() {
  const [values, setValues] = useState({name: "", email: ""});
  const [errors, setErrors] = useState({});
  const [saved, setSaved] = useState(null);
  const id = useId();
  function submit(event) {
    event.preventDefault();
    const next = {};
    if (!values.name.trim()) next.name = "Please enter your name.";
    if (!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(values.email.trim())) next.email = "Please enter a valid email address.";
    setErrors(next);
    if (Object.keys(next).length === 0) setSaved({...values, name: values.name.trim(), email: values.email.trim()});
    else setSaved(null);
  }
  return <Panel title={__TITLE__} description={__DESCRIPTION__} kind="form">
    <form noValidate onSubmit={submit}>
      <div className="fields">{["name", "email"].map(field => <div key={field}>
        <label htmlFor={id + field}>{field === "name" ? "Your name" : "Email address"}</label>
        <input id={id + field} type={field === "email" ? "email" : "text"} autoComplete={field} value={values[field]} maxLength={200}
          aria-invalid={Boolean(errors[field])} aria-describedby={errors[field] ? id + field + "-error" : undefined}
          onChange={event => {setValues(previous => ({...previous, [field]: event.target.value})); setSaved(null);}}/>
        {errors[field] && <p className="error" id={id + field + "-error"}>{errors[field]}</p>}
      </div>)}</div>
      <button className="primary">Save details ↗</button>
      <p className="form-status" role="status">{saved ? "Saved for this session. Thank you, " + saved.name + "." : "Stays in this page. No data is sent."}</p>
    </form>
  </Panel>;
}
'''
