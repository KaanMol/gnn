// A semantic view of stored facts and executable ports, plus actual run evidence.
const graphWorkspace = document.createElement('section');
graphWorkspace.className = 'senses graph-workspace';
graphWorkspace.innerHTML = `
  <header><div><div class="eyebrow">Knowledge · methods · evidence</div><h2>The graph notebook</h2></div>
  <p>Follow incoming and outgoing facts, open a procedure’s dependencies, or inspect recorded execution events. A connection expresses a relationship; it does not by itself justify an inference.</p></header>
  <div class="graph-controls"><label for="graph-mode">View</label><select id="graph-mode"><option value="facts">Facts and connections</option><option value="learning">Learning & hypotheses</option><option value="lookup">Lookup behavior</option><option value="programs">Executable procedure</option><option value="runs">Recorded execution</option><option value="interaction">Waiting and continuation</option></select>
  <label for="graph-focus">Focus</label><select id="graph-focus"></select><button class="secondary" id="graph-back">← Previous node</button>
  <button class="secondary graph-self-link" id="graph-self" type="button">Inspect assistant</button>
  <a href="/api/graph" target="_blank">Inspect stored graph IDs ↗</a></div>
  <p id="graph-caption" class="sense-hint"></p>
  <div id="learning-panel" class="learning-panel" hidden>
    <div class="learning-heading"><div><div class="eyebrow">Observe · propose · check · ask · revise</div><h3>Learned rules and proposals</h3></div><button class="secondary" id="learning-scan">Look for patterns</button></div>
    <p>A repeated pattern is a proposal. Confirmed rules can be used while their evidence holds; explicit counterexamples suspend them. New observations trigger a review automatically.</p>
    <label class="learning-history-toggle"><input type="checkbox" id="learning-show-history"> Show early observations and reviewed proposals</label>
    <div id="learning-list" class="learning-list"></div><p id="learning-status" role="status"></p>
    <button class="secondary" id="learning-review">Ask me about this rule</button> <button class="secondary" id="learning-method">Inspect learning behavior</button>
  </div>
  <details id="lookup-editor-panel" hidden><summary>Edit the taught lookup policy</summary>
    <p class="sense-hint">Name relations connect concept labels. Explicit spelling variants have variant, canonical and source fields. General rules use when (premise triples), then (a conclusion triple), and source; {"var":"x"} reuses a named placeholder. Change ask_when_unknown to control whether unresolved questions ask for teaching.</p>
    <button class="secondary" id="lookup-load">Load current policy</button>
    <label for="lookup-policy">Lookup policy in graph memory</label><textarea id="lookup-policy" spellcheck="false" aria-label="Lookup policy" placeholder="Load the current policy to edit it."></textarea>
    <button class="primary" id="lookup-save">Teach revised policy</button><p id="lookup-status" role="status"></p>
    <details><summary>General rule example</summary><pre>{"when":[["inside",{"var":"a"},{"var":"b"}],["inside",{"var":"b"},{"var":"c"}]],"then":["inside",{"var":"a"},{"var":"c"}],"source":"Teacher: containment composes"}</pre></details>
  </details>
  <div id="graph-drawing" class="graph-drawing" role="region" aria-label="Interactive knowledge and procedure graph" tabindex="0"></div>
  <details><summary>Selected node and evidence</summary><pre id="graph-evidence">Select a node to inspect its data.</pre><a id="graph-record-link" hidden target="_blank">Open the full stored execution record ↗</a></details>`;
document.querySelector('main').after(graphWorkspace);
const waitingPanel = document.createElement('div');
waitingPanel.className = 'dialogue-waiting';
waitingPanel.hidden = true;
waitingPanel.innerHTML = '<strong>Waiting for your reply</strong><p id="waiting-text"></p><button type="button" class="secondary" id="waiting-cancel">Leave this conversation step</button>';
document.querySelector('#chat').before(waitingPanel);
$('waiting-cancel').onclick = () => act('cancel_wait');
let graphState = null, graphTrail = [], graphRuns = [];
function visibleHypotheses(){return (graphState?.hypotheses||[]).map((h,i)=>({h,i})).filter(({h})=>$('learning-show-history').checked||['proposed','active','suspended'].includes(h.status));}
function selectedHypothesis(){return $('graph-focus').value===''?undefined:(graphState?.hypotheses||[])[Number($('graph-focus').value)];}
function hypothesisTitle(h){
  if(h.status!=='active')return h.label;
  if(h.kind==='inclusion'&&h.id?.length===3)return `${h.id[1]} → ${h.id[2]}`;
  if(h.kind==='mutual'&&h.id?.length===2)return `“${h.id[1]}” is mutual`;
  return 'Confirmed rule';
}
function hypothesisStatus(h){return ({active:'Confirmed · in use',proposed:'Awaiting an answer',suspended:'Needs review',observing:'Observing',rejected:'Rejected',deferred:'Deferred'})[h.status]||h.status;}
function learningSummary(){
  const rows=graphState?.hypotheses||[],pending=rows.filter(h=>h.status==='proposed').length,active=rows.filter(h=>h.status==='active').length,suspended=rows.filter(h=>h.status==='suspended').length;
  return (pending?`${pending} proposal${pending===1?'':'s'} awaiting an answer.`:'No proposals awaiting an answer.')+` ${active} confirmed rule${active===1?'':'s'} in use.`+(suspended?` ${suspended} suspended rule${suspended===1?' needs':'s need'} review.`:'');
}
const svgNS = 'http://www.w3.org/2000/svg';
function svgElement(tag, attrs = {}, text) {
  const node = document.createElementNS(svgNS, tag);
  for (const [key,value] of Object.entries(attrs)) node.setAttribute(key, value);
  if (text !== undefined) node.textContent = text;
  return node;
}
function graphCanvas(width, height) {
  const svg = svgElement('svg', {width, height, viewBox:`0 0 ${width} ${height}`, 'aria-label':'Directed graph'});
  const defs=svgElement('defs'),marker=svgElement('marker',{id:'graph-arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:7,markerHeight:7,orient:'auto-start-reverse'});
  marker.append(svgElement('path',{d:'M 0 0 L 10 5 L 0 10 z',fill:'#66816c'}));defs.append(marker);svg.append(defs);
  $('graph-drawing').replaceChildren(svg);return svg;
}
function graphEdge(svg,a,b,label='') {
  const ax=a.x+180,ay=a.y+29,bx=b.x,by=b.y+29,mid=(ax+bx)/2;
  svg.append(svgElement('path',{d:`M ${ax} ${ay} C ${mid} ${ay}, ${mid} ${by}, ${bx-5} ${by}`,fill:'none',stroke:'#66816c','stroke-width':1.4,'marker-end':'url(#graph-arrow)'}));
  if(label)svg.append(svgElement('text',{x:mid,y:(ay+by)/2-8,'text-anchor':'middle',class:'graph-edge-label'},label));
}
function isAssistantEntity(name) {
  return Boolean(graphState?.assistant_name) && name.trim().toLowerCase() === graphState.assistant_name.trim().toLowerCase();
}
function graphNode(svg,p,title,subtitle,data,open,self=false) {
  const label=self?title+' — This assistant':title;
  const detail=self?'This assistant':subtitle;
  const evidence=self?{identity:{role:'assistant',name:graphState.assistant_name,source:'session.settings.assistant_name'},evidence:data}:data;
  const group=svgElement('g',{transform:`translate(${p.x},${p.y})`,class:'graph-node'+(self?' graph-node-self':''),tabindex:0,role:'button','aria-label':label});
  group.append(svgElement('rect',{width:180,height:58,rx:7,fill:self?'#f4e6c9':open?'#e3ecd9':'#f7f4e9',stroke:self?'#9b742c':open?'#6c855f':'#b6bbaa','stroke-width':self?2:1}));
  group.append(svgElement('text',{x:12,y:23,class:'graph-node-title'},title.length>24?title.slice(0,22)+'…':title));
  group.append(svgElement('text',{x:12,y:43,class:'graph-node-detail'},detail.length>29?detail.slice(0,27)+'…':detail));
  group.append(svgElement('title',{},label+'\n'+subtitle));
  const activate=()=>{ $('graph-evidence').textContent=JSON.stringify(evidence,null,2);const link=$('graph-record-link');link.hidden=!data?.record_url;if(data?.record_url)link.href=data.record_url;if(open)open(); };
  group.addEventListener('click',activate);group.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});
  svg.append(group);
}
function graphNavigate(mode,focus) {
  graphTrail.push({mode:$('graph-mode').value,focus:$('graph-focus').value});
  $('graph-mode').value=mode;populateGraphFocus(focus);drawGraph();
}
function populateGraphFocus(preferred) {
  if(!graphState)return;
  const mode=$('graph-mode').value,old=preferred || $('graph-focus').value;
  let options=[];
  if(mode==='facts'){
    const names=[...new Set(graphState.facts.flatMap(f=>[f[1],f[2]]))];
    if(graphState.assistant_name&&!names.some(isAssistantEntity))names.push(graphState.assistant_name);
    options=names.sort().map(n=>[n,isAssistantEntity(n)?n+' · This assistant':n]);
  }
  else if(mode==='programs')options=Object.keys(graphState.procedures||{}).sort().map(n=>[n,n]);
  else if(mode==='lookup')options=[['lookup','Taught lookup behavior']];
  else if(mode==='learning')options=visibleHypotheses().map(({h,i})=>[String(i),hypothesisTitle(h)+' · '+hypothesisStatus(h)]);
  else if(mode==='interaction')options=[['waiting','Current waiting state']];
  else options=graphRuns.map((r,i)=>[String(i),r.label]);
  $('graph-focus').replaceChildren(...options.map(([value,label])=>new Option(label,value)));
  if(options.some(([v])=>v===old))$('graph-focus').value=old;
  else if(mode==='facts'&&options.some(([v])=>v===(graphState.speaker||'Kaan')))$('graph-focus').value=graphState.speaker||'Kaan';
}
function drawGraph() {
  if(!graphState)return;
  const mode=$('graph-mode').value,focus=$('graph-focus').value;
  $('graph-self').textContent=(graphState.assistant_name||'Assistant')+' · This assistant';
  $('graph-self').disabled=!graphState.assistant_name;
  $('lookup-editor-panel').hidden=mode!=='lookup';
  $('learning-panel').hidden=mode!=='learning';
  if(mode==='facts') {
    const incoming=graphState.facts.filter(f=>f[2]===focus&&f[1]!==focus),outgoing=graphState.facts.filter(f=>f[1]===focus);
    const total=Math.max(incoming.length,outgoing.length,1),height=Math.max(280,total*94+70),svg=graphCanvas(1080,height),center={x:450,y:height/2-29};
    incoming.forEach((f,i)=>{const p={x:30,y:40+i*94};graphEdge(svg,p,center,f[0]);graphNode(svg,p,f[1],'Incoming relationship',f,()=>graphNavigate('facts',f[1]),isAssistantEntity(f[1]));});
    outgoing.forEach((f,i)=>{const p={x:870,y:40+i*94};graphEdge(svg,center,p,f[0]);graphNode(svg,p,f[2],'Outgoing relationship',f,()=>graphNavigate('facts',f[2]),isAssistantEntity(f[2]));});
    graphNode(svg,center,focus||'No facts yet','Selected entity or concept',{incoming,outgoing},null,isAssistantEntity(focus));
    $('graph-caption').textContent=`${incoming.length} incoming and ${outgoing.length} outgoing facts. Click a neighboring node to follow its connections. Amber marks the current assistant identity: ${graphState.assistant_name||'unassigned'}.`;
  } else if(mode==='learning') {
    const h=selectedHypothesis();
    $('learning-status').textContent=learningSummary();
    $('learning-list').replaceChildren();
    for(const {i,h:item} of visibleHypotheses()){
      const button=document.createElement('button');button.className='learning-row'+(item===h?' selected':'');button.type='button';
      const title=document.createElement('span');title.textContent=hypothesisTitle(item);
      const state=document.createElement('span');state.className='learning-state';const count=item.evidence?.support_count||0;state.textContent=hypothesisStatus(item)+' · '+count+(count===1?' witness':' witnesses');
      button.append(title,state);button.onclick=()=>{populateGraphFocus(String(i));drawGraph();};$('learning-list').append(button);
    }
    $('learning-review').hidden=!h||!['proposed','suspended'].includes(h.status);$('learning-review').disabled=busy||!h?.evidence?.eligible;
    if(!h){graphCanvas(1000,180);$('graph-caption').textContent='No rules ready for review in this view. Show early observations and reviewed proposals to inspect the complete history, or teach more independent examples.';return;}
    const support=h.evidence?.support||[],counter=[...(h.evidence?.counterexamples||[]),...(h.evidence?.contested||[])],svg=graphCanvas(1100,Math.max(340,Math.max(support.length,counter.length)*95+90)),center={x:450,y:125};
    support.forEach((e,i)=>{const p={x:25,y:35+i*95};graphEdge(svg,p,center,'supports');graphNode(svg,p,'Observation '+(i+1),e.conclusion.join(' / '),{...e,record_url:h.record_url});});
    counter.forEach((e,i)=>{const p={x:865,y:35+i*95};graphEdge(svg,center,p,'challenged by');graphNode(svg,p,e.status,e.conclusion.join(' / '),{...e,record_url:h.record_url});});
    graphNode(svg,center,hypothesisTitle(h),hypothesisStatus(h),h,()=>{ $('graph-evidence').textContent=JSON.stringify(h,null,2);$('graph-record-link').hidden=false;$('graph-record-link').href=h.record_url; });
    $('graph-caption').textContent=`${hypothesisStatus(h)} · ${h.evidence?.support_count||0} distinct supporting witnesses. Unknown conclusions count as neither support nor counterexamples. This view shows up to four cases per category; the full record preserves all checked cases. Proposed, rejected, deferred and suspended rules are inactive.`;
  } else if(mode==='lookup') {
    const names=['knowledge_lookup_policy','knowledge_name_links','knowledge_name_rules','knowledge_rules','knowledge_rebuild','knowledge_query','knowledge_lookup_response','knowledge_lookup_reply'];
    const svg=graphCanvas(2020,290),positions=names.map((_,i)=>({x:25+i*250,y:90}));
    names.forEach((name,i)=>{if(i)graphEdge(svg,positions[i-1],positions[i],['','declares','interprets','compiles','applies','checks','answers / asks','resumes'][i]);const entry=graphState.procedures[name];graphNode(svg,positions[i],name,entry?'Stored, editable lesson':'Lesson missing',entry||{missing:name},entry?()=>graphNavigate('programs',name):null);});
    $('graph-caption').textContent='These stored lessons define how lookup works: interpret named relationships, apply general rules, check evidence, and optionally ask for an explanation. Click a lesson to inspect its nodes. This overview shows their roles; open each program for its exact dependencies.';
  } else if(mode==='programs') {
    const entry=graphState.procedures[focus];if(!entry){graphCanvas(900,180);return;}
    const program=entry.graph,positions={},levels={},rows={};
    for(const node of program.nodes){const level=node.inputs.length?Math.max(...node.inputs.map(id=>levels[id]||0))+1:0;levels[node.id]=level;const row=rows[level]||0;rows[level]=row+1;positions[node.id]={x:25+level*245,y:30+row*92};}
    const width=Math.max(900,Math.max(...Object.values(levels))*245+230),height=Math.max(260,Math.max(...Object.values(rows))*92+50),svg=graphCanvas(width,height);
    for(const node of program.nodes)for(const input of node.inputs)graphEdge(svg,positions[input],positions[node.id]);
    for(const node of program.nodes){let target=node.op==='call'?node.name:null;
      if(!target){const name=node.op==='tool'?node.name:node.op;target=Object.keys(graphState.procedures).find(n=>{const binding=graphState.procedures[n].graph.interface;return binding===name||(Array.isArray(binding)&&binding.includes(name));});}
      const detail=target||node.name||(node.value!==undefined?JSON.stringify(node.value):node.type);
      graphNode(svg,positions[node.id],node.id+' · '+node.op,detail,{procedure:focus,instruction:node},target?()=>graphNavigate('programs',target):null);
    }
    $('graph-caption').textContent=(program.description||focus)+` — ${program.nodes.length} instruction nodes. Arrows carry inputs. Green nodes can open a linked lesson. Scroll across to follow the graph. This is stored structure, not a claim that every branch ran.`;
  } else if(mode==='interaction') {
    const waiting=graphState.waiting,svg=graphCanvas(1010,240);
    if(!waiting){graphNode(svg,{x:35,y:70},'No pending continuation','Ready for a new request',{});$('graph-caption').textContent='No graph program is currently waiting for a reply.';return;}
    const left={x:25,y:70},middle={x:400,y:70},right={x:790,y:70};
    graphEdge(svg,left,middle,'retains');graphEdge(svg,middle,right,'next input resumes');
    graphNode(svg,left,'Question / wait',waiting.text||'Wait without a prompt',waiting);
    graphNode(svg,middle,'Stored state',waiting.state?.mode||'Continuation data',waiting.state);
    const present=!!graphState.procedures[waiting.resume];
    graphNode(svg,right,waiting.resume,present?'Taught continuation':'Missing lesson',{resume:waiting.resume},present?()=>graphNavigate('programs',waiting.resume):null);
    $('graph-caption').textContent='A stored procedure chose this question or wait and its continuation. The next reply is delivered with this retained state. Click the continuation to inspect how it chooses the next step.';
  } else {
    const run=graphRuns[Number(focus)];if(!run){graphCanvas(900,180);$('graph-caption').textContent='Run a stored lesson or goal to record execution evidence.';return;}
    const trace=run.trace||[],svg=graphCanvas(Math.max(900,trace.length*235+40),200);
    trace.forEach((step,i)=>{const p={x:25+i*235,y:60};if(i)graphEdge(svg,{x:25+(i-1)*235,y:60},p);graphNode(svg,p,step.operation||'step',step.result||'',{...step,record_url:run.record_url});});
    $('graph-caption').textContent=`${run.label}: ${trace.length} recorded events, in execution order. Select an event to open its full stored record. This preview shortens results; explicit traces omit many internal instructions. Arrows show chronology.`;
  }
}
$('graph-self').onclick=()=>{
  const name=graphState?.facts.flatMap(f=>[f[1],f[2]]).find(isAssistantEntity)||graphState?.assistant_name;
  if(name)graphNavigate('facts',name);
};
const previousGraphRender=render;
render=function(state){
  if(state.partial){
    const patch=state.language_patch;state={...graphState,...state};
    if(patch){state.language=[...graphState.language];state.language.length=patch.length;for(const item of patch.items)state.language[item.index]=item.value;}
    delete state.partial;delete state.language_patch;
  }
  const followSelf=$('graph-mode').value==='facts'&&isAssistantEntity($('graph-focus').value);
  stateVersion=state.state_version;previousGraphRender(state);graphState=state;graphRuns=[];
  waitingPanel.hidden=!state.waiting;
  $('waiting-text').textContent=state.waiting?.text||'The taught procedure is waiting for input. Reply in the chat to continue.';
  for(const record of state.language||[]){if(record.trace?.length)graphRuns.push({label:record.original,trace:record.trace,record_url:record.record_url});for(const run of record.tool_runs||[])if(run.trace?.length)graphRuns.push({label:record.original,trace:run.trace,record_url:record.record_url});}
  for(const run of state.runs||[])if(run.trace?.length)graphRuns.push({label:run.procedure+' · '+run.status,trace:run.trace,record_url:run.record_url});
  for(const run of state.goals||[])if(run.trace?.length)graphRuns.push({label:'Goal · '+run.status,trace:run.trace});
  graphRuns=graphRuns.slice(-20).reverse();populateGraphFocus(followSelf?state.assistant_name:undefined);drawGraph();
};
$('graph-mode').onchange=()=>{populateGraphFocus();drawGraph();};$('graph-focus').onchange=drawGraph;
$('graph-back').onclick=()=>{const previous=graphTrail.pop();if(previous){$('graph-mode').value=previous.mode;populateGraphFocus(previous.focus);drawGraph();}};
$('lookup-load').onclick=()=>{
  const graph=graphState.procedures.knowledge_lookup_policy?.graph;
  const node=graph?.nodes.find(n=>n.id===graph.output&&n.op==='data_literal');
  if(!node){$('lookup-status').textContent='This policy is missing or computes its data. Open its executable procedure to edit it.';return;}
  $('lookup-policy').value=JSON.stringify(node.value,null,2);$('lookup-status').textContent='Loaded from the active graph. Edits are taught only when you save.';
};
$('lookup-save').onclick=async()=>{
  try {
    const policy=JSON.parse($('lookup-policy').value);
    if(!Array.isArray(policy.name_relations)||!policy.name_relations.every(x=>typeof x==='string')||!Array.isArray(policy.spelling_variants)||!Array.isArray(policy.rules)||typeof policy.ask_when_unknown!=='boolean')throw new Error('Use name_relations, spelling_variants and rules lists, plus ask_when_unknown: true or false.');
    if(!policy.spelling_variants.every(v=>v&&['variant','canonical','source'].every(k=>typeof v[k]==='string')))throw new Error('Each spelling needs variant, canonical and source text.');
    if(!policy.rules.every(r=>r&&Array.isArray(r.when)&&r.when.length&&r.when.every(p=>Array.isArray(p)&&p.length===3)&&Array.isArray(r.then)&&r.then.length===3&&typeof r.source==='string'))throw new Error('Each rule needs when (premise triples), then (a conclusion triple), and source.');
    const graph=structuredClone(graphState.procedures.knowledge_lookup_policy.graph);
    const node=graph.nodes.find(n=>n.id===graph.output&&n.op==='data_literal');
    if(!node)throw new Error('Open the executable procedure to edit this computed policy.');
    node.value=policy;$('lookup-status').textContent='Teaching the revised policy…';
    const result=await sensoryRequest({action:'teach_graph',name:'knowledge_lookup_policy',graph,replace:true});
    $('lookup-status').textContent=result?'Policy taught. Current conclusions now use these rules.':'Policy could not be taught. See the request error above.';
  }catch(error){$('lookup-status').textContent=error.message;}
};
$('learning-scan').onclick=async()=>{
  $('learning-status').textContent='The stored learner is reviewing observations…';
  const result=await sensoryRequest({action:'run_skill',name:'learning_cycle',argument:{changed:null,ask:true}});
  $('learning-status').textContent=result?learningSummary():'Could not finish the review; see the request error above.';
};
$('learning-review').onclick=async()=>{
  const h=selectedHypothesis();if(!h||!['proposed','suspended'].includes(h.status)||!h.evidence?.eligible)return;
  const result=await sensoryRequest({action:'run_skill',name:'learning_review',argument:h.id});
  if(result){$('learning-status').textContent=result.answer;$('input').focus();}
};
$('learning-method').onclick=()=>graphNavigate('programs','learning_cycle');
$('learning-show-history').onchange=()=>{populateGraphFocus();drawGraph();};
fetch('/api/state').then(r=>r.json()).then(data=>render(data)).catch(e=>$('graph-caption').textContent=e.message);
