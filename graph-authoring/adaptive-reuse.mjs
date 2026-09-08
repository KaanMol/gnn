// Policies are executable graph data. The host only supplies measured evidence.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};
const save=(name,g,out)=>suite[name]={graph:{...g.finish(out),execution_budget:10000000},source:'Supplied generic evidence and prefix-search policy; learned evidence is separate.'};
const call=(g,name,x)=>g.op('call',[x],{name});
const put=(g,x,k,v)=>g.op('set_item',[x,g.data(k),v]);

// Record paired, budget-censored utility. A success lost is penalized by the
// budget; two failures provide no evidence of benefit. This is not exact savings.
let g=new G();let old=g.get(g.input,'record'),base=g.get(g.input,'baseline'),trial=g.get(g.input,'trial');
let utility=g.choose(g.bool(g.get(trial,'success')),g.calc('subtract',g.get(base,'graph_steps'),g.get(trial,'graph_steps')),g.choose(g.bool(g.get(base,'success')),g.calc('subtract',g.data(0),g.get(g.input,'budget')),g.data(0)));
save('adaptive_record',g,g.rec({name:g.get(old,'name'),trials:g.calc('add',g.get(old,'trials'),g.data(1)),utility:g.calc('add',g.get(old,'utility'),utility),evidence:g.push(g.get(old,'evidence'),g.rec({baseline:base,trial,budget:g.get(g.input,'budget'),utility}))}));
g=new G();save('adaptive_save_evidence',g,g.op('act',[g.input,g.rec({namespace:g.data('knowledge.reuse_evidence'),key:g.data('calibration'),value:g.input})],{surface:'workspace',action:'write'}));

// Include only methods with positive measured aggregate utility. No domain name,
// field name, expected answer or held-out result is inspected by this policy.
const keep=new G();let profitable=keep.and(keep.lt(keep.data(0),keep.get(keep.input,'trials')),keep.lt(keep.data(0),keep.get(keep.input,'utility')));
const name=new G();
const extension=new G();let extended=extension.list(extension.get(extension.input,'context'),extension.get(extension.input,'item'));
const prefix=new G();let p=prefix.get(prefix.input,'item');
let extensions=prefix.op('map',[prefix.get(prefix.input,'context'),p],{body:extension.finish(extended)});
g=new G();let selected=g.op('map',[g.op('filter',[g.get(g.input,'evidence')],{body:keep.finish(profitable,'Bool')})],{body:name.finish(name.get(name.input,'name'))});
let prelude=g.op('flatten',[g.op('map',[selected,g.get(g.input,'base')],{body:prefix.finish(prefix.concat(prefix.list(prefix.list(p)),extensions))})]);
save('adaptive_prepare',g,g.rec({vocabulary:g.concat(g.get(g.input,'base'),selected),selected,prelude:g.choose(g.bool(g.get(g.input,'extend')),prelude,g.data([]))}));

// Resume useful learned prefixes before ordinary exhaustive search. Every trial
// still runs the graph evaluator, including unsuccessful prefixes and nested work.
g=new G();let s=g.input,i=g.get(s,'prefix_i');
let ops=g.item(g.get(s,'prelude'),i);
let evaluation=call(g,'synth_evaluate_candidate',g.rec({ops,examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector')}));
let accepted=g.bool(g.get(evaluation,'accepted'));
let next=put(g,put(g,put(g,put(g,put(g,put(g,s,'prefix_i',g.calc('add',i,g.data(1))),'evaluated',g.calc('add',g.get(s,'evaluated'),g.data(1))),'found',g.choose(accepted,ops,g.data(null))),'done',g.datum(accepted)),'last',ops),'last_evaluation',evaluation);
let fallback=call(g,'bench_search_step',s);
fallback=put(g,put(g,fallback,'prelude',g.get(s,'prelude')),'prefix_i',i);
save('adaptive_search_step',g,g.choose(g.and(g.lt(i,g.len(g.get(s,'prelude'))),g.not(g.lt(g.get(s,'max_depth'),g.data(2)))),next,fallback));

fs.writeFileSync(new URL('../curriculum/adaptive-reuse.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log('Adaptive reuse graph rules:',Object.keys(suite).length);
