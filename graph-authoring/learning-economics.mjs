// Online retention policy, stored and executed as graph data.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};const save=(name,g,out)=>suite[name]={graph:{...g.finish(out),execution_budget:10000000},source:'Supplied online retention and bounded-recency retrieval policy.'};
const call=(g,name,x)=>g.op('call',[x],{name});
const read=g=>g.op('act',[g.input,g.data({namespace:'knowledge.economics',key:'catalog'})],{surface:'workspace',action:'read'});
const write=(g,token,value)=>g.op('act',[token,g.rec({namespace:g.data('knowledge.economics'),key:g.data('catalog'),value})],{surface:'workspace',action:'write'});
let g=new G();save('economy_init',g,write(g,g.input,g.data([])));

const names=new G();
const extension=new G();const extended=extension.list(extension.get(extension.input,'context'),extension.get(extension.input,'item'));
const prefix=new G();const p=prefix.get(prefix.input,'item');const extensions=prefix.op('map',[prefix.get(prefix.input,'context'),p],{body:extension.finish(extended)});
g=new G();const catalog=read(g),methods=g.op('map',[catalog],{body:names.finish(names.get(names.input,'name'))});
const recent=g.op('slice',[g.op('reverse',[methods])],{start:0,stop:4});
const prelude=g.op('flatten',[g.op('map',[recent,g.get(g.input,'base')],{body:prefix.finish(prefix.concat(prefix.list(prefix.list(p)),extensions))})]);
save('economy_prepare',g,g.rec({catalog,vocabulary:g.concat(g.get(g.input,'base'),methods),prelude,selected:recent}));

g=new G();const ops=g.get(g.input,'ops');
save('economy_validate',g,g.choose(g.eq(ops,g.data(null)),g.rec({accepted:g.data(false),cases:g.data([])}),call(g,'synth_evaluate_candidate',g.input)));
g=new G();save('economy_refine',g,g.concat(g.get(g.input,'examples'),g.get(g.input,'validation')));

// Reject unsuccessful, redundant and single-instruction aliases. A stored macro
// can contain other learned macros; all nested work remains ordinary graph work.
const programs=new G();
g=new G();const existing=read(g),candidate=g.get(g.input,'ops');
const previous=g.op('map',[existing],{body:programs.finish(programs.get(programs.input,'ops'))});
const useful=g.choose(g.eq(candidate,g.data(null)),g.data(false),g.datum(g.and(g.lt(g.data(1),g.len(candidate)),g.not(g.contains(previous,candidate)))));
const retain=g.and(g.bool(g.get(g.input,'retain')),g.and(g.bool(g.get(g.input,'validated')),g.bool(useful)));
const promoted=call(g,'bench_promote',g.rec({name:g.get(g.input,'name'),ops:candidate,vocabulary:g.get(g.input,'vocabulary')}));
const entry=g.rec({name:g.get(g.input,'name'),ops:candidate,validation:g.get(g.input,'validation')});
const saved=write(g,promoted,g.push(existing,entry));
save('economy_retain',g,g.choose(retain,g.rec({retained:g.data(true),saved,name:g.get(g.input,'name')}),g.rec({retained:g.data(false)})));

fs.writeFileSync(new URL('../curriculum/learning-economics.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log('Online economics graph rules:',Object.keys(suite).length);
