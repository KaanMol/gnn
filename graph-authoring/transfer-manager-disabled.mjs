// Exactly two graph-rule replacements: no domain equivalences or continuations.
import fs from 'node:fs';import {G} from './graph.mjs';
const suite={};const save=(n,g,out)=>suite[n]={graph:{...g.finish(out),execution_budget:10000000},source:'Rules-disabled manager: order-preserving expansion/dedup only; singleton probes.'};
const match=new G();const predicate=match.eq(match.get(match.input,'item','name'),match.get(match.input,'context'));
const expand=new G(),op=expand.get(expand.input,'item');const found=expand.op('filter',[expand.get(expand.input,'context'),op],{body:match.finish(predicate,'Bool')});
const replacement=expand.choose(expand.lt(expand.data(0),expand.len(found)),expand.get(expand.item(found,expand.data(0)),'ops'),expand.list(op));
let g=new G();save('manager_canonicalize',g,g.rec({valid:g.data(true),ops:g.op('flatten',[g.op('map',[g.get(g.input,'ops'),g.get(g.input,'catalog')],{body:expand.finish(replacement)})])}));
const active=new G(),names=new G(),single=new G();
g=new G();const catalog=g.op('act',[g.input,g.data({namespace:'knowledge.economics',key:'catalog'})],{surface:'workspace',action:'read'});
const recent=g.op('slice',[g.op('reverse',[g.op('filter',[catalog],{body:active.finish(active.bool(active.get(active.input,'active')),'Bool')})])],{start:0,stop:4});
const selected=g.op('map',[recent],{body:names.finish(names.get(names.input,'name'))});
save('manager_prepare',g,g.rec({catalog,vocabulary:g.get(g.input,'base'),selected,prelude:g.op('map',[selected],{body:single.finish(single.list(single.input))})}));
fs.writeFileSync(new URL('../curriculum/transfer-manager-disabled.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
