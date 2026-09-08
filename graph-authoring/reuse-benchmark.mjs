// Controlled macro-reuse benchmark machinery, expressed as executable graph data.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};const save=(name,g,x)=>suite[name]={graph:{...g.finish(x),execution_budget:10000000},source:'Controlled composition-reuse benchmark: supplied experimental machinery.'};
const call=(g,name,x)=>g.op('call',[x],{name});const put=(g,x,k,v)=>g.op('set_item',[x,g.data(k),v]);const req=(g,c,x,msg)=>g.op('require',[c,x],{message:msg});
let g=new G();save('bench_identity_state',g,g.input);
for(const [name,operation] of [['bench_double','multiply'],['bench_negate','negate']]){
 g=new G();const value=g.num(g.get(g.input,'result'));
 const changed=g.op('as_data',[g.op(operation,operation==='multiply'?[value,g.num(g.data(2))]:[value],{},'Number')]);
 save(name,g,req(g,g.bool(g.get(g.input,'done')),put(g,g.input,'result',changed),'This scalar operation requires a reduced result.'));
}
g=new G();save('bench_enabled',g,g.datum(g.bool(g.get(g.input,'enabled'))));
g=new G();save('bench_reading',g,g.get(g.input,'reading'));
// Identical adapters are supplied to all arms; only macro vocabulary differs.
g=new G();let valid=g.and(g.contains(g.data(['synth_positive','synth_available','bench_enabled']),g.get(g.input,'predicate')),g.contains(g.data(['synth_identity','synth_price','bench_reading']),g.get(g.input,'projector')));
valid=g.and(valid,g.not(g.lt(g.data(64),g.len(g.get(g.input,'items')))));
save('synth_init',g,req(g,valid,g.rec({items:g.get(g.input,'items'),predicate:g.get(g.input,'predicate'),projector:g.get(g.input,'projector'),done:g.data(false),result:g.data(null)}),'Unsupported adapter or oversized input.'));
// Convert a rank into a call sequence without materializing an exponential frontier.
const guard=new G();const more=guard.lt(guard.get(guard.input,'i'),guard.get(guard.input,'depth'));
const b=new G(),s=b.input,base=b.len(b.get(s,'vocabulary'));
const quotient=b.op('as_data',[b.op('floor',[b.num(b.calc('divide',b.get(s,'rank'),base))],{},'Number')]);
const digit=b.calc('subtract',b.get(s,'rank'),b.calc('multiply',quotient,base));
const next=b.rec({i:b.calc('add',b.get(s,'i'),b.data(1)),depth:b.get(s,'depth'),rank:quotient,vocabulary:b.get(s,'vocabulary'),ops:b.concat(b.list(b.item(b.get(s,'vocabulary'),digit)),b.get(s,'ops'))});
g=new G();const loop=g.op('while',[g.rec({i:g.data(0),depth:g.get(g.input,'depth'),rank:g.get(g.input,'rank'),vocabulary:g.get(g.input,'vocabulary'),ops:g.data([])})],{guard:guard.finish(more,'Bool'),body:b.finish(next)});
save('bench_candidate_at',g,g.get(loop,'ops'));
// One resumable learner transition. The host supplies budgets, never candidates.
g=new G();const current=g.input;
const ops=call(g,'bench_candidate_at',g.rec({depth:g.get(current,'depth'),rank:g.get(current,'rank'),vocabulary:g.get(current,'vocabulary')}));
const evaluation=call(g,'synth_evaluate_candidate',g.rec({ops,examples:g.get(current,'examples'),predicate:g.get(current,'predicate'),projector:g.get(current,'projector')}));
const nextRank=g.calc('add',g.get(current,'rank'),g.data(1));
const width=g.op('as_data',[g.op('power',[g.num(g.len(g.get(current,'vocabulary'))),g.num(g.get(current,'depth'))],{},'Number')]);
const exhausted=g.eq(nextRank,width),newDepth=g.choose(exhausted,g.calc('add',g.get(current,'depth'),g.data(1)),g.get(current,'depth'));
const accepted=g.bool(g.get(evaluation,'accepted'));
save('bench_search_step',g,g.rec({vocabulary:g.get(current,'vocabulary'),examples:g.get(current,'examples'),predicate:g.get(current,'predicate'),projector:g.get(current,'projector'),max_depth:g.get(current,'max_depth'),rank:g.choose(exhausted,g.data(0),nextRank),depth:newDepth,found:g.choose(accepted,ops,g.data(null)),done:g.datum(g.op('or',[accepted,g.lt(g.get(current,'max_depth'),newDepth)],{},'Bool')),evaluated:g.calc('add',g.get(current,'evaluated'),g.data(1)),last:ops,last_evaluation:evaluation}));
// Emit and save a state-to-state macro from a discovered solution. The nested
// calls remain ordinary graph calls: their full execution work is metered.
g=new G();const graph=call(g,'synth_materialize',g.get(g.input,'ops')),nodes=g.get(graph,'nodes');
const fix=new G(),node=fix.input;const isCall=fix.eq(fix.get(node,'op'),fix.data('call'));
const boundary=fix.choose(isCall,fix.datum(fix.contains(fix.data(['synth_init','synth_finish']),fix.get(node,'name'))),fix.data(false));
const changed=fix.choose(fix.bool(boundary),put(fix,node,'name',fix.data('bench_identity_state')),node);
const macro=put(g,graph,'nodes',g.op('map',[nodes],{body:fix.finish(changed)}));
const keys=g.op('act',[g.input,g.data({namespace:'knowledge.procedures'})],{surface:'workspace',action:'keys'});
const name=req(g,g.not(g.contains(keys,g.get(g.input,'name'))),g.get(g.input,'name'),'Refusing to overwrite an existing macro.');
const saved=g.op('act',[keys,g.rec({namespace:g.data('knowledge.procedures'),key:name,value:g.rec({graph:macro,source:g.data('Whole-solution macro discovered on separate training tasks.'),ops:g.get(g.input,'ops')})})],{surface:'workspace',action:'write'});
save('bench_promote',g,g.rec({name,saved,vocabulary:g.push(g.get(g.input,'vocabulary'),name)}));
fs.writeFileSync(new URL('../curriculum/reuse-benchmark.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log('Benchmark rules:',Object.keys(suite).length);
