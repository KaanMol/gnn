// Generic callable composition. No environment names, laws, or continuations.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};const save=(name,g,x)=>suite[name]={graph:{...g.finish(x),execution_budget:10000000},source:'Generic callable search with expanded primitive length metering.'};
const call=(g,name,x)=>g.op('call',[x],{name});
let g=new G();
const expanded=call(g,'manager_canonicalize',g.rec({ops:g.get(g.input,'ops'),catalog:g.get(g.input,'catalog')}));
const allowed=g.and(g.bool(g.get(expanded,'valid')),g.not(g.lt(g.get(g.input,'max_depth'),g.len(g.get(expanded,'ops')))));
const evaluation=call(g,'synth_evaluate_candidate',g.rec({ops:g.get(g.input,'ops'),examples:g.get(g.input,'examples'),predicate:g.get(g.input,'predicate'),projector:g.get(g.input,'projector')}));
save('composition_evaluate',g,g.rec({expanded:g.get(expanded,'ops'),allowed:g.datum(allowed),evaluation:g.choose(allowed,evaluation,g.data({accepted:false}))}));
const logged=new G();
g=new G();const s=g.input;
const ops=call(g,'bench_candidate_at',g.rec({depth:g.get(s,'depth'),rank:g.get(s,'rank'),vocabulary:g.get(s,'vocabulary')}));
const e=call(g,'composition_evaluate',g.rec({ops,catalog:g.get(s,'catalog'),max_depth:g.get(s,'max_depth'),examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector')}));
const nextRank=g.calc('add',g.get(s,'rank'),g.data(1));
const width=g.op('as_data',[g.op('power',[g.num(g.len(g.get(s,'vocabulary'))),g.num(g.get(s,'depth'))],{},'Number')]);
const exhausted=g.eq(nextRank,width),depth=g.choose(exhausted,g.calc('add',g.get(s,'depth'),g.data(1)),g.get(s,'depth'));
const accepted=g.bool(g.get(e,'evaluation','accepted'));
save('composition_search_step',g,g.rec({vocabulary:g.get(s,'vocabulary'),catalog:g.get(s,'catalog'),examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector'),max_depth:g.get(s,'max_depth'),rank:g.choose(exhausted,g.data(0),nextRank),depth,found:g.choose(accepted,ops,g.data(null)),done:g.datum(g.op('or',[accepted,g.lt(g.get(s,'max_depth'),depth)],{},'Bool')),evaluated:g.calc('add',g.get(s,'evaluated'),g.data(1)),last:ops,last_evaluation:e,last_log:g.choose(g.bool(g.get(e,'allowed')),g.op('map',[ops],{body:logged.finish(logged.rec({ops:logged.list(logged.input)}))}),g.data([]))}));
g=new G();const p=call(g,'manager_prepare',g.rec({base:g.get(g.input,'base')}));
// Recency selection is inherited. The same rule places learned callables first
// in the mixed alphabet; every position can contain any selected callable.
save('composition_prepare',g,g.rec({catalog:g.get(p,'catalog'),selected:g.get(p,'selected'),prelude:g.get(p,'prelude'),vocabulary:g.choose(g.bool(g.get(g.input,'compose')),g.concat(g.get(p,'selected'),g.get(g.input,'base')),g.get(g.input,'base'))}));
fs.writeFileSync(new URL('../curriculum/compositional-transfer.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
