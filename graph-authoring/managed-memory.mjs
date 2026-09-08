import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};const save=(name,g,out)=>suite[name]={graph:{...g.finish(out),execution_budget:10000000},source:'Supplied managed-memory policy for the fixed pure reduction benchmark.'};
const call=(g,name,x)=>g.op('call',[x],{name});const put=(g,x,k,v)=>g.op('set_item',[x,g.data(k),v]);
const read=g=>g.op('act',[g.input,g.data({namespace:'knowledge.economics',key:'catalog'})],{surface:'workspace',action:'read'});
const write=(g,token,value)=>g.op('act',[token,g.rec({namespace:g.data('knowledge.economics'),key:g.data('catalog'),value})],{surface:'workspace',action:'write'});

// Catalog entries contain expanded canonical primitives, so expansion is one
// level. No equivalence is inferred from a behavioral fingerprint.
const match=new G();const matches=match.eq(match.get(match.input,'item','name'),match.get(match.input,'context'));
const expand=new G(),op=expand.get(expand.input,'item');const entries=expand.op('filter',[expand.get(expand.input,'context'),op],{body:match.finish(matches,'Bool')});
const expanded=expand.choose(expand.lt(expand.data(0),expand.len(entries)),expand.get(expand.item(entries,expand.data(0)),'ops'),expand.list(op));
const guard=new G();const more=guard.lt(guard.get(guard.input,'i'),guard.len(guard.get(guard.input,'ops')));
const b=new G(),s=b.input,x=b.item(b.get(s,'ops'),b.get(s,'i')),reduced=b.bool(b.get(s,'reduced'));
const isReduce=b.contains(b.data(['synth_sum','synth_count']),x),isSelect=b.and(b.eq(x,b.data('synth_select')),b.eq(b.len(b.get(s,'prefix')),b.data(0)));
const isDouble=b.eq(x,b.data('bench_double')),isNegate=b.eq(x,b.data('bench_negate'));
const validStep=b.choose(reduced,b.datum(b.op('or',[isDouble,isNegate],{},'Bool')),b.datum(b.op('or',[isReduce,isSelect],{},'Bool')));
const next=b.rec({ops:b.get(s,'ops'),i:b.calc('add',b.get(s,'i'),b.data(1)),valid:b.datum(b.and(b.bool(b.get(s,'valid')),b.bool(validStep))),reduced:b.datum(b.op('or',[reduced,isReduce],{},'Bool')),prefix:b.choose(reduced,b.get(s,'prefix'),b.push(b.get(s,'prefix'),x)),doubles:b.choose(b.and(reduced,isDouble),b.push(b.get(s,'doubles'),x),b.get(s,'doubles')),negative:b.choose(b.and(reduced,isNegate),b.datum(b.not(b.bool(b.get(s,'negative')))),b.get(s,'negative'))});
let g=new G();const flat=g.op('flatten',[g.op('map',[g.get(g.input,'ops'),g.get(g.input,'catalog')],{body:expand.finish(expanded)})]);
const normalized=g.op('while',[g.rec({ops:flat,i:g.data(0),valid:g.data(true),reduced:g.data(false),prefix:g.data([]),doubles:g.data([]),negative:g.data(false)})],{guard:guard.finish(more,'Bool'),body:b.finish(next)});
save('manager_canonicalize',g,g.rec({valid:g.datum(g.and(g.bool(g.get(normalized,'valid')),g.bool(g.get(normalized,'reduced')))),ops:g.concat(g.concat(g.get(normalized,'prefix'),g.get(normalized,'doubles')),g.choose(g.bool(g.get(normalized,'negative')),g.data(['bench_negate']),g.data([])))}));

const active=new G();const eligible=active.bool(active.get(active.input,'active'));
const names=new G();const name=names.get(names.input,'name');
const probe=new G();const n=probe.input;
// Typed continuation templates are supplied graph data for reduced scalar state.
const probes=probe.list(probe.list(n),probe.list(n,probe.data('bench_double')),probe.list(n,probe.data('bench_negate')));
g=new G();const catalog=read(g),selected=g.op('slice',[g.op('reverse',[g.op('filter',[catalog],{body:active.finish(eligible,'Bool')})])],{start:0,stop:4});
const selectedNames=g.op('map',[selected],{body:names.finish(name)});
save('manager_prepare',g,g.rec({catalog,vocabulary:g.get(g.input,'base'),selected:selectedNames,prelude:g.op('flatten',[g.op('map',[selectedNames],{body:probe.finish(probes)})])}));

// Cheap screening on two examples precedes complete training validation. The
// host caps this probe phase, then resumes the unchanged original-only search.
g=new G();const state=g.input,index=g.get(state,'prefix_i'),candidate=g.item(g.get(state,'prelude'),index);
const short=call(g,'synth_evaluate_candidate',g.rec({ops:candidate,examples:g.op('slice',[g.get(state,'examples')],{start:0,stop:2}),predicate:g.get(state,'predicate'),projector:g.get(state,'projector')}));
const full=g.choose(g.bool(g.get(short,'accepted')),call(g,'synth_evaluate_candidate',g.rec({ops:candidate,examples:g.get(state,'examples'),predicate:g.get(state,'predicate'),projector:g.get(state,'projector')})),short);
const accepted=g.bool(g.get(full,'accepted'));
save('manager_probe_step',g,g.rec({prelude:g.get(state,'prelude'),prefix_i:g.calc('add',index,g.data(1)),examples:g.get(state,'examples'),predicate:g.get(state,'predicate'),projector:g.get(state,'projector'),found:g.choose(accepted,candidate,g.data(null)),done:g.datum(g.op('or',[accepted,g.eq(g.calc('add',index,g.data(1)),g.len(g.get(state,'prelude')))],{},'Bool')),evaluated:g.calc('add',g.get(state,'evaluated'),g.data(1)),log:g.push(g.get(state,'log'),g.rec({ops:candidate,accepted:g.datum(accepted)}))}));

// Update only methods actually probed. Retirement removes search eligibility,
// preserving the executable graph and evidence for inspection/dependencies.
const update=new G(),record=update.get(update.input,'item'),ctx=update.get(update.input,'context');
const touched=update.contains(update.get(ctx,'probed'),update.get(record,'name'));
const won=update.contains(update.get(ctx,'used'),update.get(record,'name'));
const misses=update.choose(won,update.data(0),update.calc('add',update.get(record,'misses'),update.data(1)));
const revised=put(update,put(update,put(update,record,'misses',misses),'wins',update.calc('add',update.get(record,'wins'),update.choose(won,update.data(1),update.data(0)))),'active',update.datum(update.lt(misses,update.data(24))));
const logged=new G();
g=new G();const prior=read(g),probed=g.op('unique',[g.op('map',[g.get(g.input,'log')],{body:logged.finish(logged.item(logged.get(logged.input,'ops'),logged.data(0)))})]);
const context=g.rec({probed,used:g.choose(g.bool(g.get(g.input,'validated')),g.get(g.input,'found'),g.data([]))});
const changed=g.op('map',[prior,context],{body:update.finish(update.choose(touched,revised,record))});
save('manager_update',g,g.choose(g.lt(g.data(0),g.len(probed)),write(g,g.input,changed),g.data({updated:false})));

const opList=new G();
g=new G();const old=read(g),canonical=call(g,'manager_canonicalize',g.rec({ops:g.get(g.input,'ops'),catalog:old}));
const canonOps=g.get(canonical,'ops');
const duplicate=g.contains(g.op('map',[old],{body:opList.finish(opList.get(opList.input,'ops'))}),canonOps);
const worth=g.and(g.bool(g.get(canonical,'valid')),g.and(g.lt(g.data(1),g.len(canonOps)),g.not(duplicate)));
const verification=call(g,'synth_evaluate_candidate',g.rec({ops:canonOps,examples:g.get(g.input,'validation'),predicate:g.get(g.input,'predicate'),projector:g.get(g.input,'projector')}));
const promoted=call(g,'bench_promote',g.rec({name:g.get(g.input,'name'),ops:canonOps,vocabulary:g.get(g.input,'base')}));
const saved=write(g,promoted,g.push(old,g.rec({name:g.get(g.input,'name'),ops:canonOps,active:g.data(true),wins:g.data(0),misses:g.data(0),validation:g.get(g.input,'validation')})));
const rejected=g.rec({retained:g.data(false),canonical:canonOps});
save('manager_retain',g,g.choose(worth,g.choose(g.bool(g.get(verification,'accepted')),g.rec({retained:g.data(true),canonical:canonOps,saved}),rejected),rejected));
fs.writeFileSync(new URL('../curriculum/managed-memory.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log('Managed memory graph rules:',Object.keys(suite).length);
