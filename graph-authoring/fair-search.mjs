// Fair allocation only: reuse the frozen scorer, evaluator and memory rules.
import fs from 'node:fs';import {G} from './graph.mjs';
const suite={};const save=(name,g,x)=>suite[name]={graph:{...g.finish(x),execution_budget:10000000},source:'Quota sharing among near-tied partial programs; no domain rules.'};
const call=(g,name,x)=>g.op('call',[x],{name});
// Within five integer priority units of the best, pick the least-served parent.
// next_i counts child expansions already allocated. Stable ties rotate because
// a served parent is reinserted at the end of the queue.
const eligible=new G(),remove=new G();let g=new G();
const ordered=g.op('sort',[g.input],{key:'priority'}),best=g.item(ordered,g.data(0));
const band=g.op('filter',[g.input,g.calc('add',g.get(best,'priority'),g.data(5))],{body:eligible.finish(eligible.not(eligible.lt(eligible.get(eligible.input,'context'),eligible.get(eligible.input,'item','priority'))),'Bool')});
const chosen=g.item(g.op('sort',[band],{key:'next_i'}),g.data(0));
const rest=g.op('filter',[g.input,chosen],{body:remove.finish(remove.not(remove.eq(remove.get(remove.input,'item'),remove.get(remove.input,'context'))),'Bool')});
save('fair_choose',g,g.rec({parent:chosen,queue:rest,band_size:g.len(band)}));
g=new G();save('fair_init',g,call(g,'priority_init',g.input));
const logged=new G();g=new G();const s=g.input;
const ops=g.push(g.get(s,'parent','ops'),g.item(g.get(s,'vocabulary'),g.get(s,'next_i')));
const canonical=g.get(call(g,'manager_canonicalize',g.rec({ops,catalog:g.get(s,'catalog')})),'ops');
const duplicate=g.contains(g.get(s,'seen'),canonical),length=g.len(canonical);
const allowed=g.and(g.not(duplicate),g.not(g.lt(g.get(s,'max_depth'),length)));
const ev=g.choose(allowed,call(g,'priority_evaluate',g.rec({ops,examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector')})),g.data({accepted:false,executable:false,progress:0,matches:0}));
const scaled=g.op('as_data',[g.op('floor',[g.num(g.calc('multiply',g.get(ev,'progress'),g.data(1000)))],{},'Number')]);
const priority=g.calc('subtract',length,g.calc('add',g.calc('multiply',g.get(ev,'matches'),g.data(1000000)),scaled));
const child=g.rec({ops,priority,next_i:g.data(0)});
const queued=g.choose(g.and(g.bool(g.get(ev,'executable')),g.lt(length,g.get(s,'max_depth'))),g.push(g.get(s,'queue'),child),g.get(s,'queue'));
const nextI=g.calc('add',g.get(s,'next_i'),g.data(1)),more=g.lt(nextI,g.len(g.get(s,'vocabulary')));
const root=g.eq(g.len(g.get(s,'parent','ops')),g.data(0)),rootContinues=g.and(root,more);
const returned=g.choose(g.and(g.not(root),more),g.push(queued,g.rec({ops:g.get(s,'parent','ops'),priority:g.get(s,'parent','priority'),next_i:nextI})),queued);
// Preserve queue age normally. Only truncate by score if the beam overflows.
const bounded=g.choose(g.lt(g.get(s,'beam'),g.len(returned)),g.op('slice',[g.op('sort',[returned],{key:'priority'})],{start:0,stop:100}),returned);
const empty=g.eq(g.len(bounded),g.data(0));
const choice=g.choose(g.and(g.not(rootContinues),g.not(empty)),call(g,'fair_choose',bounded),g.rec({parent:g.rec({ops:g.get(s,'parent','ops'),priority:g.get(s,'parent','priority'),next_i:nextI}),queue:bounded,band_size:g.data(0)}));
const done=g.op('or',[g.bool(g.get(ev,'accepted')),g.and(g.not(rootContinues),empty)],{},'Bool');
save('fair_step',g,g.rec({vocabulary:g.get(s,'vocabulary'),catalog:g.get(s,'catalog'),selected:g.get(s,'selected'),examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector'),max_depth:g.get(s,'max_depth'),beam:g.get(s,'beam'),parent:g.get(choice,'parent'),next_i:g.get(choice,'parent','next_i'),queue:g.get(choice,'queue'),seen:g.choose(allowed,g.push(g.get(s,'seen'),canonical),g.get(s,'seen')),found:g.choose(g.bool(g.get(ev,'accepted')),ops,g.data(null)),done:g.datum(done),evaluated:g.calc('add',g.get(s,'evaluated'),g.choose(allowed,g.data(1),g.data(0))),last:ops,last_expanded:canonical,last_duplicate:g.datum(duplicate),last_allowed:g.datum(allowed),last_evaluation:ev,last_parent:g.get(s,'parent','ops'),last_child_index:g.get(s,'next_i'),last_band_size:g.get(choice,'band_size'),last_log:g.choose(allowed,g.op('map',[ops],{body:logged.finish(logged.rec({ops:logged.list(logged.input)}))}),g.data([]))}));
fs.writeFileSync(new URL('../curriculum/fair-search.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
