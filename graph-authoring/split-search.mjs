// Fixed budget reservations between original-only and memory-assisted search.
// This file contains no environment names and does not change memory or scoring.
import fs from 'node:fs';import {G} from './graph.mjs';
const suite={};const save=(name,g,x)=>suite[name]={graph:{...g.finish(x),execution_budget:10000000},source:'Generic fixed-share discovery/reuse allocator.'};
const call=(g,name,x)=>g.op('call',[x],{name});const put=(g,x,key,v)=>g.op('set_item',[x,g.data(key),v]);
let g=new G();const prepared=call(g,'fair_init',g.input);
const discovery=put(g,put(g,prepared,'vocabulary',g.get(g.input,'base')),'selected',g.data([]));
const distinct=g.not(g.eq(g.get(prepared,'vocabulary'),g.get(g.input,'base')));
save('split_init',g,g.rec({discovery,reuse:prepared,distinct:g.datum(distinct),selected:g.get(prepared,'selected')}));
g=new G();const budget=g.get(g.input,'remaining');
const reserved=g.op('as_data',[g.op('floor',[g.num(g.calc('divide',g.calc('multiply',budget,g.get(g.input,'percent')),g.data(100)))],{},'Number')]);
save('split_caps',g,g.choose(g.bool(g.get(g.input,'distinct')),g.rec({discovery:reserved,reuse:g.calc('subtract',budget,reserved)}),g.rec({discovery:budget,reuse:g.data(0)})));
g=new G();const d=g.bool(g.get(g.input,'discovery_active')),r=g.bool(g.get(g.input,'reuse_active'));
// Compare used fractions by cross multiplication. Ties start with discovery.
const reuseBehind=g.lt(g.calc('multiply',g.get(g.input,'reuse_spent'),g.get(g.input,'discovery_cap')),g.calc('multiply',g.get(g.input,'discovery_spent'),g.get(g.input,'reuse_cap')));
save('split_choose',g,g.choose(d,g.choose(r,g.choose(reuseBehind,g.data('reuse'),g.data('discovery')),g.data('discovery')),g.choose(r,g.data('reuse'),g.data(null))));
fs.writeFileSync(new URL('../curriculum/split-search.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
