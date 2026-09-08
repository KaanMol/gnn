// Adaptive allocation; frozen scoring, memory management and fair search reused.
import fs from 'node:fs';import {G} from './graph.mjs';
const suite={};const save=(name,g,x)=>suite[name]={graph:{...g.finish(x),execution_budget:10000000},source:'Generic progress-per-work allocation across independent frontiers.'};
const call=(g,name,x)=>g.op('call',[x],{name});const put=(g,x,key,v)=>g.op('set_item',[x,g.data(key),v]);
const eligible=new G(),nameOf=new G(),lane=new G();
let g=new G();const state=call(g,'fair_init',g.input);
// Reuse the exact existing rank computation, widening only the shortlist.
const ranked=g.choose(g.eq(g.get(g.input,'mode'),g.data('no_memory')),g.data({ranking:[]}),call(g,'activation_select',g.rec({state,mode:g.data('top_k')})));
const valid=g.op('filter',[g.get(ranked,'ranking')],{body:eligible.finish(eligible.and(eligible.bool(eligible.get(eligible.input,'compatible')),eligible.lt(eligible.data(0),eligible.get(eligible.input,'overlap'))),'Bool')});
const shortlist=g.op('slice',[g.op('sort',[valid],{key:'priority'})],{start:0,stop:4});
const selected=g.op('map',[shortlist],{body:nameOf.finish(nameOf.get(nameOf.input,'name'))});
const primitive=put(g,put(g,state,'vocabulary',g.get(g.input,'base')),'selected',g.data([]));
const ls=lane.get(lane.input,'context','state'),method=lane.get(lane.input,'item');
const memoryState=put(lane,put(lane,ls,'vocabulary',lane.concat(lane.list(method),lane.get(lane.input,'context','base'))),'selected',lane.list(method));
const states=g.concat(g.list(primitive),g.op('map',[selected,g.rec({state,base:g.get(g.input,'base')})],{body:lane.finish(memoryState)}));
save('lanes_init',g,g.rec({states,selected,ranking:g.get(ranked,'ranking')}));
const initStat=new G();g=new G();
save('lanes_stats',g,g.op('map',[g.op('indices',[g.input])],{body:initStat.finish(initStat.rec({id:initStat.input,spent:initStat.data(0),best:initStat.data(0),gains:initStat.data([]),costs:initStat.data([]),stalls:initStat.data(0),live:initStat.data(true)}))}));
const live=new G(),probe=new G(),score=new G();
const gains=call(score,'priority_sum',score.get(score.input,'gains')),costs=call(score,'priority_sum',score.get(score.input,'costs'));
const rate=score.op('as_data',[score.op('floor',[score.num(score.calc('divide',score.calc('multiply',gains,score.data(1000000)),score.calc('add',costs,score.data(1))))],{},'Number')]);
const scored=put(score,score.input,'priority',score.calc('subtract',score.data(0),rate));
g=new G();const stats=g.input,primitives=g.item(stats,g.data(0));
const active=g.op('filter',[stats],{body:live.finish(live.bool(live.get(live.input,'live')),'Bool')});
const pending=g.op('filter',[active],{body:probe.finish(probe.lt(probe.get(probe.input,'spent'),probe.data(20000)),'Bool')});
const rankedActive=g.op('map',[g.op('sort',[active],{key:'spent'})],{body:score.finish(scored)});
const best=g.get(g.item(g.op('sort',[rankedActive],{key:'priority'}),g.data(0)),'id');
const pick=g.choose(g.lt(g.data(0),g.len(pending)),g.get(g.item(g.op('sort',[pending],{key:'spent'}),g.data(0)),'id'),best);
save('lanes_choose',g,g.choose(g.and(g.bool(g.get(primitives,'live')),g.lt(g.get(primitives,'spent'),g.data(100000))),g.data(0),g.choose(g.lt(g.data(0),g.len(active)),pick,g.data(null))));
// Recent gain is improvement over that lane's best agreement, not task labels.
g=new G();const previous=g.get(g.input,'stat');
const raw=g.calc('add',g.calc('multiply',g.get(g.input,'evaluation','matches'),g.data(1000000)),g.op('as_data',[g.op('floor',[g.num(g.calc('multiply',g.get(g.input,'evaluation','progress'),g.data(1000)))],{},'Number')]));
const improved=g.lt(g.get(previous,'best'),raw),gain=g.choose(improved,g.calc('subtract',raw,g.get(previous,'best')),g.data(0));
const stalls=g.choose(improved,g.data(0),g.calc('add',g.get(previous,'stalls'),g.data(1)));
const spent=g.calc('add',g.get(previous,'spent'),g.get(g.input,'charged'));
const stalled=g.and(g.not(g.eq(g.get(previous,'id'),g.data(0))),g.and(g.not(g.lt(spent,g.data(20000))),g.not(g.lt(stalls,g.data(8)))));
save('lanes_observe',g,g.rec({id:g.get(previous,'id'),spent,best:g.choose(improved,raw,g.get(previous,'best')),gains:g.op('slice',[g.push(g.get(previous,'gains'),gain)],{start:-4}),costs:g.op('slice',[g.push(g.get(previous,'costs'),g.get(g.input,'charged'))],{start:-4}),stalls,live:g.datum(g.and(g.not(g.bool(g.get(g.input,'done'))),g.not(stalled)))}));
fs.writeFileSync(new URL('../curriculum/adaptive-lanes.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
