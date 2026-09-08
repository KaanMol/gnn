// Environment definitions and a common Data->Data boundary. No manager rules.
import fs from 'node:fs';import {G} from './graph.mjs';
const suite={};const save=(n,g,out)=>suite[n]={graph:{...g.finish(out),execution_budget:10000000},source:'Supplied transfer environment primitive, shared by all experimental arms.'};
const put=(g,x,k,v)=>g.op('set_item',[x,g.data(k),v]);const req=(g,c,x)=>g.op('require',[c,x],{message:'Environment action precondition failed.'});
let g=new G();save('synth_init',g,g.get(g.input,'items'));g=new G();save('synth_finish',g,g.input);
g=new G();save('text_lower',g,g.op('lower',[g.input]));
g=new G();save('text_split',g,g.op('split_text',[g.input,g.data(' ')]));
g=new G();save('text_join',g,g.op('join_text',[g.input,g.data(' ')]));
g=new G();save('text_reverse',g,g.op('reverse',[g.input]));
const keep=new G();g=new G();save('text_clean',g,g.op('filter',[g.input],{body:keep.finish(keep.not(keep.eq(keep.input,keep.data(''))),'Bool')}));
g=new G();save('text_dash',g,g.op('replace_text',[g.input,g.data('-'),g.data(' ')]));

for(const [name,index] of [['tree_left',0],['tree_right',1]]){
 g=new G();const focus=g.get(g.input,'focus'),children=g.get(focus,'children');
 const crumb=g.rec({parent:focus,index:g.data(index)});
 save(name,g,req(g,g.eq(g.len(children),g.data(2)),g.rec({focus:g.item(children,g.data(index)),crumbs:g.push(g.get(g.input,'crumbs'),crumb)})));
}
g=new G();const crumbs=g.get(g.input,'crumbs'),crumb=g.item(crumbs,g.calc('subtract',g.len(crumbs),g.data(1))),parent=g.get(crumb,'parent');
const kids=g.get(parent,'children');
const replaced=g.choose(g.eq(g.get(crumb,'index'),g.data(0)),g.list(g.get(g.input,'focus'),g.item(kids,g.data(1))),g.list(g.item(kids,g.data(0)),g.get(g.input,'focus')));
save('tree_up',g,req(g,g.lt(g.data(0),g.len(crumbs)),g.rec({focus:put(g,parent,'children',replaced),crumbs:g.op('slice',[crumbs],{stop:-1})})));
g=new G();save('tree_swap',g,put(g,g.input,'focus',put(g,g.get(g.input,'focus'),'children',g.op('reverse',[g.get(g.input,'focus','children')]))));
g=new G();save('tree_mark',g,put(g,g.input,'focus',put(g,g.get(g.input,'focus'),'label',g.data('*'))));

for(const [name,delta] of [['plan_east',1],['plan_west',-1]]){
 g=new G();const x=g.calc('add',g.get(g.input,'x'),g.data(delta));
 const ok=g.and(g.lt(g.data(0),g.get(g.input,'energy')),g.and(g.not(g.lt(x,g.data(0))),g.not(g.lt(g.data(3),x))));
 let state=put(g,put(g,g.input,'x',x),'energy',g.calc('subtract',g.get(g.input,'energy'),g.data(1)));
 state=put(g,state,'log',g.push(g.get(g.input,'log'),g.data(name)));
 save(name,g,req(g,ok,state));
}
for(const [name,position,carrying] of [['plan_pick',1,true],['plan_drop',0,false]]){
 g=new G();const ok=g.and(g.eq(g.get(g.input,'x'),g.data(position)),g.eq(g.get(g.input,'carrying'),g.data(!carrying)));
 const state=put(g,put(g,g.input,'carrying',g.data(carrying)),'log',g.push(g.get(g.input,'log'),g.data(name)));
 save(name,g,req(g,ok,state));
}
g=new G();save('plan_charge',g,put(g,put(g,g.input,'energy',g.calc('add',g.get(g.input,'energy'),g.data(2))),'log',g.push(g.get(g.input,'log'),g.data('plan_charge'))));
fs.writeFileSync(new URL('../curriculum/transfer-environments.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
