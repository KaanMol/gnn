const sensoryPanel = document.createElement('section');
sensoryPanel.className = 'senses';
sensoryPanel.innerHTML = `
  <header><div><div class="eyebrow">Observe → interpret → act → observe</div><h2>Skills, senses & goals</h2></div>
    <p>Inspect and revise the programs in memory. Give a skill an input, or ask the taught planner to combine skills toward a checked outcome. Canvas observations expose text and geometry.</p></header>
  <div class="sense-columns"><div class="sense-column">
    <div class="sense-step">01 / Observe and check</div>
    <button class="secondary" id="sense-observe">Observe canvas</button>
    <p class="sense-hint">Raw observations contain marks, lines, pointer position, and input feedback. A reading lesson gives the marks meaning.</p>
    <pre id="sense-output" aria-live="polite">Observe the canvas to inspect its input.</pre>
    <div class="sense-step">Recent experiences</div><div id="sense-history" class="sense-history"></div>
    <details><summary>Last procedure trace</summary><pre id="sense-trace"></pre></details>
  </div><div class="sense-column">
    <div class="sense-step">02 / Teach, try, revise</div>
    <p class="sense-hint">Load an example, inspect its lesson, then teach it. Reading maps blank to 0 and digit symbols to numbers. The action lesson teaches move → click → type. Neither example is installed automatically.</p>
    <div class="sense-toolbar"><button class="secondary" id="sense-load-read">Load reading lesson</button><button class="secondary" id="sense-load-action">Load action lesson</button></div>
    <label for="sense-saved">Stored procedures</label><select id="sense-saved"><option value="">Choose a stored lesson…</option></select>
    <label for="sense-name">Lesson name</label><input id="sense-name" placeholder="Load or name a lesson" maxlength="60">
    <details><summary>Teach a symbol meaning</summary>
      <p class="sense-hint">For a reading lesson, add or correct a symbol here. Leave the symbol empty for a blank mark. Then teach the revised lesson.</p>
      <label for="sense-symbol">Visible symbol</label><input id="sense-symbol" placeholder="For example: 5" maxlength="100">
      <label for="sense-meaning">Meaning (number or quoted text)</label><input id="sense-meaning" value="5" maxlength="100">
      <button class="secondary" id="sense-set-meaning">Set meaning in lesson</button>
    </details>
    <details id="sense-lesson-details"><summary>Edit the lesson graph</summary><textarea id="sense-editor" aria-label="Sensory lesson graph" spellcheck="false" placeholder="Load a lesson to inspect its executable graph"></textarea></details>
    <div class="sense-toolbar"><button class="primary" id="sense-teach">Teach / revise lesson</button><button class="secondary" id="sense-forget">Forget lesson</button></div>
    <label for="sense-argument">Input for this run</label><textarea id="sense-argument" spellcheck="false">null</textarea>
    <p class="sense-hint">Enter JSON matching the lesson’s input type: a number, a list, or structured data. Canvas action input uses x, y and key.</p>
    <button class="primary" id="sense-run">Run stored lesson ↗</button>
    <p id="sense-status" role="status">Start by loading a lesson.</p><p id="sense-error" role="alert"></p>
  </div></div>
  <details class="sense-goals"><summary>03 / Teach a new skill family and pursue a goal</summary>
    <p class="sense-hint">A goal names what the input provides and what you want. Each lesson declares its requirements and outcomes. The stored planner chooses a sequence; an optional taught checker tests its result. Declaring an outcome alone does not prove it happened.</p>
    <button class="secondary" id="skill-load-example">Load temperature example</button>
    <label for="skill-package">Lesson package</label><textarea id="skill-package" spellcheck="false" placeholder="Load an example or paste named graph lessons"></textarea>
    <button class="secondary" id="skill-teach-package">Teach this package</button>
    <label for="skill-goal">Goal and input</label><textarea id="skill-goal" spellcheck="false">{"have":["fahrenheit_reading"],"want":["temperature_assessed"],"input":{"fahrenheit":86},"check":"temperature_check"}</textarea>
    <button class="primary" id="skill-achieve">Find a plan & run</button>
    <div id="skill-catalog" class="sense-hint"></div>
    <details><summary>Stored goals and outcomes</summary><pre id="skill-goals"></pre></details>
  </details>`;
document.querySelector('.sudoku-panel').after(sensoryPanel);
let sensoryProcedures = {};
const previousSensoryRender = render;
render = function(state) {
  previousSensoryRender(state);
  sensoryProcedures = state.procedures || {};
  const selected = $('sense-saved').value;
  $('sense-saved').replaceChildren(new Option('Choose a stored lesson…', ''));
  for (const [name, entry] of Object.entries(sensoryProcedures)) {
    $('sense-saved').append(new Option(name, name));
  }
  $('sense-saved').value = selected;
  $('skill-catalog').textContent = (state.skills || []).map(s => s.name + ': ' + s.requires.join(', ') + ' → ' + s.provides.join(', ')).join(' · ') || 'No skill contracts taught yet. Load, inspect and teach the example.';
  $('skill-goals').textContent = JSON.stringify((state.goals || []).map(g => ({status:g.status, request:g.request, plan:g.plan?.plan, result:g.result, error:g.error})), null, 2);
  $('sense-history').replaceChildren();
  for (const event of [...(state.sensory_events || [])].reverse()) {
    const feedback = event.payload?.feedback;
    $('sense-history').append(el('div', '', `${event.kind}${event.action ? ' · ' + event.action : ''}${event.kind === 'action' && feedback ? ' · ' + (feedback.accepted ? 'accepted' : feedback.message) : ''}`));
  }
  const pointer = state.canvas_device?.pointer;
  if (pointer) {
    const x = pointer.x * 450, y = pointer.y * 450;
    sudokuCtx.strokeStyle = '#b66437'; sudokuCtx.lineWidth = 2;
    sudokuCtx.beginPath(); sudokuCtx.arc(x, y, 15, 0, Math.PI * 2); sudokuCtx.stroke();
  }
};
async function sensoryRequest(body) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(b => b.disabled = true);
  $('sense-error').textContent = '';
  $('sense-status').textContent = 'Working…';
  try {
    const response = await fetch('/api/action', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({...body,state_version:stateVersion})});
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'The request failed.');
    render(data.state);
    $('sense-status').textContent = data.answer.split('\n')[0];
    if (data.execution) {
      $('sense-output').textContent = JSON.stringify(data.execution.result, null, 2);
      $('sense-trace').textContent = JSON.stringify(data.execution.trace, null, 2);
    }
    return data;
  } catch (error) {
    $('sense-error').textContent = error.message;
    $('sense-status').textContent = 'Could not complete this request.';
  } finally {
    busy = false;
    document.querySelectorAll('button').forEach(b => b.disabled = false);
  }
}
async function loadSensoryLesson(name) {
  try {
    const response = await fetch('/api/lessons/' + name);
    if (!response.ok) throw new Error('Could not load the lesson.');
    const lesson = await response.json();
    $('sense-name').value = lesson.name;
    $('sense-editor').value = JSON.stringify(lesson.graph, null, 2);
    $('sense-argument').value = name === 'type_at' ? JSON.stringify({x:2.5/9, y:.5/9, key:'4'}, null, 2) : 'null';
    $('sense-lesson-details').open = true;
    $('sense-status').textContent = 'Example loaded. Teach it to store the procedure.';
    $('sense-error').textContent = '';
  } catch(error) { $('sense-error').textContent = error.message; }
}
$('sense-load-read').onclick = () => loadSensoryLesson('read_marks');
$('sense-load-action').onclick = () => loadSensoryLesson('type_at');
$('sense-observe').onclick = () => sensoryRequest({action:'sense'});
$('sense-set-meaning').onclick = () => {
  try {
    const graph = JSON.parse($('sense-editor').value);
    function findTable(program) {
      for (const lookup of program.nodes || []) {
        if (lookup.op === 'lookup') {
          const literal = program.nodes.find(n => n.id === lookup.inputs[0] && n.op === 'data_literal');
          if (literal && literal.value && !Array.isArray(literal.value) && typeof literal.value === 'object') return literal.value;
        }
        for (const field of ['body', 'guard']) {
          if (lookup[field]) { const found = findTable(lookup[field]); if (found) return found; }
        }
      }
    }
    const table = findTable(graph);
    if (!table) throw new Error('Load a reading lesson with a symbol table first.');
    Object.defineProperty(table, $('sense-symbol').value, {value:JSON.parse($('sense-meaning').value), enumerable:true, configurable:true, writable:true});
    $('sense-editor').value = JSON.stringify(graph, null, 2);
    $('sense-status').textContent = 'Meaning edited. Click Teach / revise lesson to store it.';
    $('sense-error').textContent = '';
  } catch(error) { $('sense-error').textContent = error.message; }
};
$('sense-teach').onclick = () => {
  try { sensoryRequest({action:'teach_graph', name:$('sense-name').value, graph:JSON.parse($('sense-editor').value), replace:true}); }
  catch(error) { $('sense-error').textContent = 'Check the lesson JSON: ' + error.message; }
};
$('sense-forget').onclick = () => sensoryRequest({action:'forget_graph', name:$('sense-name').value});
$('sense-run').onclick = () => {
  try { sensoryRequest({action:'run_skill', name:$('sense-name').value, argument:JSON.parse($('sense-argument').value)}); }
  catch(error) { $('sense-error').textContent = 'Check the input JSON: ' + error.message; }
};
$('sense-saved').onchange = () => {
  const name = $('sense-saved').value;
  if (!sensoryProcedures[name]) return;
  $('sense-name').value = name;
  $('sense-editor').value = JSON.stringify(sensoryProcedures[name].graph, null, 2);
  $('sense-status').textContent = 'Stored lesson loaded for inspection or revision.';
};
sudokuCanvas.addEventListener('click', event => {
  const bounds = sudokuCanvas.getBoundingClientRect();
  let argument;
  try { argument = JSON.parse($('sense-argument').value); } catch { return; }
  if (argument && typeof argument === 'object' && 'x' in argument && 'y' in argument) {
    argument.x = Math.min(.999, Math.max(0, (event.clientX - bounds.left) / bounds.width));
    argument.y = Math.min(.999, Math.max(0, (event.clientY - bounds.top) / bounds.height));
    $('sense-argument').value = JSON.stringify(argument, null, 2);
  }
});
$('skill-load-example').onclick = async () => {
  try {
    const response = await fetch('/api/lessons/temperature_skills');
    if (!response.ok) throw new Error('Could not load the example.');
    $('skill-package').value = JSON.stringify(await response.json(), null, 2);
    $('sense-status').textContent = 'Example loaded for inspection. Teach this package to make its skills available.';
  } catch(error) { $('sense-error').textContent = error.message; }
};
$('skill-teach-package').onclick = () => {
  try { sensoryRequest({action:'teach_graph_package', entries:JSON.parse($('skill-package').value)}); }
  catch(error) { $('sense-error').textContent = 'Check the package JSON: ' + error.message; }
};
$('skill-achieve').onclick = () => {
  try { sensoryRequest({action:'achieve_goal', goal:JSON.parse($('skill-goal').value)}); }
  catch(error) { $('sense-error').textContent = 'Check the goal JSON: ' + error.message; }
};
