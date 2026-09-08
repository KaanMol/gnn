(() => {
  const examples = {
  "Graph control flow": "let total = 0;\nfor (let i = 0; i < 5; i++) {\n  if (i > 1) { total += i; }\n}\nconsole.log(total);",
  "React task list \u00b7 graph source": "export default function TaskList() {\n  const tasks = [\n    { id: 1, title: \"Learn JSX\", done: true },\n    { id: 2, title: \"Build an app\", done: false },\n    { id: 3, title: \"Practice JavaScript\", done: false }\n  ];\n  const remaining = tasks.filter(task => !task.done);\n  return (\n    <section>\n      <h1>My tasks</h1>\n      <p>Remaining: {remaining.length}</p>\n      <ul>\n        {remaining.map(task => (\n          <li key={task.id}>{task.title}</li>\n        ))}\n      </ul>\n    </section>\n  );\n}",
  "Graph arithmetic": "console.log(2 + 3 * 4);",
  "Graph array callbacks": "console.log([1,2,3].filter(x => x > 1).map(x => x * 2));",
  "Graph component": "export default function Greeting() { return <h1>Hello from the graph</h1>; }"
};
  const panel = document.createElement('section'); panel.className = 'js-playground'; panel.id = 'javascript-playground';
  panel.innerHTML = `<div class="js-heading"><div><span class="eyebrow">Code · execute · inspect</span><h2>JavaScript playground</h2><p>Stored graph rules read, compile, and execute your source. No host parser fallback.</p></div><span class="pill">Graph reader → compiler → execution</span></div>
  <div class="js-grid"><div class="js-editor-pane"><div class="js-toolbar"><label for="js-example">Example</label><select id="js-example"></select><button class="secondary" id="js-load-example">Load example</button></div>
  <label class="sr-only" for="js-source">JavaScript source</label><textarea id="js-source" spellcheck="false" maxlength="1800" aria-label="JavaScript source"></textarea>
  <label class="js-input-label" for="js-input">Function input · optional JSON, required for a function with a parameter</label><textarea id="js-input" spellcheck="false" aria-label="JavaScript function input" placeholder="Leave blank for scripts or zero-argument components"></textarea>
  <div class="js-actions"><button class="primary" id="js-run">Run in graph ↗</button><small>⌘ / Ctrl + Enter · 1,800 characters</small></div><p id="js-error" class="js-error" role="alert"></p></div>
  <div class="js-output-pane"><div class="js-output-head"><h3>Execution</h3><span id="js-status" class="js-status" role="status">Ready</span></div><div class="js-result-line"><span class="js-label">Return value</span><code id="js-result">Run a program to see its result.</code></div><div class="js-console"><p class="js-label">Console · captured arguments</p><pre id="js-console">No output yet.</pre></div><details><summary>Statement trace</summary><pre id="js-trace"></pre></details><details><summary>Compiled graph input</summary><pre id="js-compiled"></pre></details><details><summary>Stored execution evidence</summary><pre id="js-evidence"></pre></details></div></div>
  <div class="js-lessons"><h3>React learning notebook</h3><p>Read the taught concepts and component patterns. The runner executes single components with intrinsic JSX into element trees. Nested custom components and hooks remain reference code.</p><div class="js-toolbar"><label for="react-topic">Lesson</label><select id="react-topic"></select><button id="react-read" class="secondary">Ask the graph</button></div><p id="react-status" role="status"></p><pre id="react-lesson">Choose a React lesson to read from the graph.</pre></div>`;
  document.querySelector('.workspace').after(panel);
  const jump = document.createElement('a'); jump.className = 'js-jump'; jump.href = '#javascript-playground'; jump.textContent = 'JS playground ↗'; document.querySelector('.brand').append(jump);
  const get = id => document.getElementById(id);
  for (const name of Object.keys(examples)) { const option=document.createElement('option'); option.textContent=name; get('js-example').append(option); }
  for (const topic of ['overview','html_structure','html_semantics','html_attributes','html_forms','html_accessibility','html_void_elements','html_text','jsx','components','props','state','events','lists','keys','forms','immutability','refs','effects','hook_rules','state_queue','effect_lifecycle','effect_cleanup','reducers','derived_state','computed_fields','counter_pattern','todos_pattern','form_pattern']) {
    const option=document.createElement('option'); option.value=topic; option.textContent=topic.replaceAll('_',' '); get('react-topic').append(option);
  }
  get('js-example').value='React task list · graph source';get('js-source').value=examples['React task list · graph source'];
  get('js-load-example').onclick=()=>{get('js-source').value=examples[get('js-example').value];get('js-input').value='';};
  function plain(value) {
    if(Array.isArray(value)) return value.map(plain);
    if(value && value.__js_type==='object') return Object.fromEntries(Object.entries(value.properties).map(([k,v])=>[k,plain(v)]));
    return value;
  }
  const show=value=>value && value.__js_type==='undefined'?'undefined':JSON.stringify(plain(value),null,2);
  async function request(body) {
    const response=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,state_version:stateVersion})});
    const data=await response.json(); if(!response.ok) throw new Error(data.error||'Request failed');
    if(data.state)render(data.state); return data;
  }
  get('js-run').onclick=async()=>{
    if(busy)return; busy=true;get('js-run').disabled=true;get('js-error').textContent='';get('js-status').textContent='Executing graph…';
    get('js-result').textContent='';get('js-console').textContent='';get('js-trace').textContent='';get('js-evidence').textContent='';get('js-compiled').textContent='';
    try {
      const body={action:'javascript_run',source:get('js-source').value};
      if(get('js-input').value.trim())body.input=JSON.parse(get('js-input').value);
      const data=await request(body), execution=data.execution, result=execution.result;
      get('js-result').textContent=show(result.value);
      get('js-console').textContent=result.logs.length?result.logs.map(line=>line.map(show).join('  ')).join('\n'):'No console calls.';
      get('js-trace').textContent=JSON.stringify(result.steps,null,2);
      get('js-compiled').textContent=JSON.stringify(execution.compiled_program,null,2);
      get('js-evidence').textContent=JSON.stringify({procedure:execution.procedure,status:execution.status,program_roots:execution.program_roots,trace:execution.trace},null,2);
      get('js-status').textContent=`Complete · ${result.steps.length} statements`;
    } catch(error) {get('js-error').textContent=error.message;get('js-status').textContent='Not completed';}
    finally {busy=false;get('js-run').disabled=false;}
  };
  get('js-source').addEventListener('keydown',event=>{if((event.metaKey||event.ctrlKey)&&event.key==='Enter'){event.preventDefault();get('js-run').click();}});
  get('react-read').onclick=async()=>{
    if(busy)return;busy=true;get('react-read').disabled=true;get('react-status').textContent='Reading taught lesson…';
    try {const data=await request({action:'run_skill',name:'react_explain',argument:get('react-topic').value});const lesson=data.execution.result;
      get('react-lesson').textContent=lesson.title+'\n\n'+lesson.explanation+'\n\n'+lesson.example+'\n\nSource: '+lesson.source;
      get('react-status').textContent='Read from the current graph lesson.';
    } catch(error) {get('react-status').textContent=error.message;} finally {busy=false;get('react-read').disabled=false;}
  };
})();
