// Generic best-first allocation over Data -> Data callables. No domain names.
import fs from 'node:fs';import {G} from './graph.mjs';
const suite={};const save=(name,g,x)=>suite[name]={graph:{...g.finish(x),execution_budget:10000000},source:'Generic changed-target-leaf best-first search; supplied allocator, not learned domain knowledge.'};
const call=(g,name,x)=>g.op('call',[x],{name});
// Sum a list of Data numbers, entirely through graph operations.
let guard=new G(),body=new G(),g=new G();
let more=guard.lt(guard.get(guard.input,'i'),guard.len(guard.get(guard.input,'values')));
let next=body.rec({values:body.get(body.input,'values'),i:body.calc('add',body.get(body.input,'i'),body.data(1)),total:body.calc('add',body.get(body.input,'total'),body.item(body.get(body.input,'values'),body.get(body.input,'i')))});
let loop=g.op('while',[g.rec({values:g.input,i:g.data(0),total:g.data(0)})],{guard:guard.finish(more,'Bool'),body:body.finish(next)});save('priority_sum',g,g.get(loop,'total'));
// Flatten any target tree to scalar paths. No selected field names or types.
const child=new G(),cx=child.get(child.input,'context'),key=child.get(child.input,'item');
const childValue=child.rec({value:child.item(child.get(cx,'value'),key),path:child.push(child.get(cx,'path'),key)});
guard=new G();body=new G();g=new G();
more=guard.lt(guard.data(0),guard.len(guard.get(guard.input,'todo')));
const entry=body.item(body.get(body.input,'todo'),body.data(0)),value=body.get(entry,'value'),kind=body.op('kind_of',[value]);
const compound=body.op('or',[body.eq(kind,body.data('record')),body.eq(kind,body.data('list'))],{},'Bool');
const keys=body.choose(body.eq(kind,body.data('record')),body.op('keys',[value]),body.op('indices',[value]));
const remaining=body.op('slice',[body.get(body.input,'todo')],{start:1});
next=body.rec({todo:body.choose(compound,body.concat(body.op('map',[keys,entry],{body:child.finish(childValue)}),remaining),remaining),leaves:body.choose(compound,body.get(body.input,'leaves'),body.push(body.get(body.input,'leaves'),entry))});
loop=g.op('while',[g.rec({todo:g.list(g.input),leaves:g.data([])})],{guard:guard.finish(more,'Bool'),body:body.finish(next)});save('priority_leaves',g,g.get(loop,'leaves'));
// Safe arbitrary path lookup, including missing paths in intermediate outputs.
guard=new G();body=new G();g=new G();
more=guard.lt(guard.get(guard.input,'i'),guard.len(guard.get(guard.input,'path')));
next=body.rec({path:body.get(body.input,'path'),i:body.calc('add',body.get(body.input,'i'),body.data(1)),value:body.item(body.get(body.input,'value'),body.item(body.get(body.input,'path'),body.get(body.input,'i')))});
loop=g.op('while',[g.rec({path:g.get(g.input,'path'),value:g.get(g.input,'value'),i:g.data(0)})],{guard:guard.finish(more,'Bool'),body:body.finish(next)});save('priority_lookup',g,g.get(loop,'value'));
const attemptBody=new G();const looked=call(attemptBody,'priority_lookup',attemptBody.input);
const feature=new G(),f=feature.get(feature.input,'item');
let attempt=feature.op('attempt',[feature.rec({value:feature.get(feature.input,'context'),path:feature.get(f,'path')})],{body:attemptBody.finish(looked)});
const unchanged=feature.choose(feature.bool(feature.get(attempt,'ok')),feature.datum(feature.eq(feature.get(attempt,'result'),feature.get(f,'value'))),feature.data(false));
g=new G();save('priority_features',g,g.rec({input:g.get(g.input,'input'),expected:g.get(g.input,'expected'),features:g.op('filter',[call(g,'priority_leaves',g.rec({value:g.get(g.input,'expected'),path:g.data([])})),g.get(g.input,'input')],{body:feature.finish(feature.not(feature.bool(unchanged)),'Bool')})}));
// Score a successful intermediate output against changed target leaves.
const match=new G(),mf=match.get(match.input,'item');
attempt=match.op('attempt',[match.rec({value:match.get(match.input,'context'),path:match.get(mf,'path')})],{body:attemptBody.finish(looked)});
const equal=match.choose(match.bool(match.get(attempt,'ok')),match.datum(match.eq(match.get(attempt,'result'),match.get(mf,'value'))),match.data(false));
const one=match.choose(match.bool(equal),match.data(1),match.data(0));
const scoreCase=new G(),sc=scoreCase.get(scoreCase.input,'context'),ix=scoreCase.get(scoreCase.input,'item');
const observation=scoreCase.item(scoreCase.get(sc,'cases'),ix),features=scoreCase.get(scoreCase.item(scoreCase.get(sc,'examples'),ix),'features');
const score=scoreCase.choose(scoreCase.lt(scoreCase.data(0),scoreCase.len(features)),scoreCase.calc('divide',call(scoreCase,'priority_sum',scoreCase.op('map',[features,scoreCase.get(observation,'execution','result')],{body:match.finish(one)})),scoreCase.len(features)),scoreCase.data(0));
const safeScore=scoreCase.choose(scoreCase.bool(scoreCase.get(observation,'execution','ok')),score,scoreCase.data(0));
const flag=new G(),valid=new G();
g=new G();const evaluation=call(g,'synth_evaluate_candidate',g.input),cases=g.get(evaluation,'cases');
const matches=call(g,'priority_sum',g.op('map',[cases],{body:flag.finish(flag.choose(flag.bool(flag.get(flag.input,'passed')),flag.data(1),flag.data(0)))}));
const progress=call(g,'priority_sum',g.op('map',[g.op('indices',[cases]),g.rec({cases,examples:g.get(g.input,'examples')})],{body:scoreCase.finish(safeScore)}));
const executable=g.not(g.contains(g.op('map',[cases],{body:valid.finish(valid.get(valid.input,'execution','ok'))}),g.data(false)));
save('priority_evaluate',g,g.rec({accepted:g.get(evaluation,'accepted'),executable:g.datum(executable),progress,matches}));
const enrich=new G();g=new G();const prepared=call(g,'composition_prepare',g.rec({base:g.get(g.input,'base'),compose:g.data(true)}));
save('priority_init',g,g.rec({vocabulary:g.get(prepared,'vocabulary'),catalog:g.get(prepared,'catalog'),selected:g.get(prepared,'selected'),examples:g.op('map',[g.get(g.input,'examples')],{body:enrich.finish(call(enrich,'priority_features',enrich.input))}),predicate:g.get(g.input,'predicate'),projector:g.get(g.input,'projector'),max_depth:g.data(5),beam:g.data(100),parent:g.data({ops:[],priority:0}),next_i:g.data(0),queue:g.data([]),seen:g.data([]),found:g.data(null),done:g.data(false),evaluated:g.data(0)}));
// One child evaluation per resumable graph transition. Finish a parent's
// children, then expand the best queued partial program, regardless of depth.
const logged=new G();g=new G();const s=g.input;
const ops=g.push(g.get(s,'parent','ops'),g.item(g.get(s,'vocabulary'),g.get(s,'next_i')));
const canonical=g.get(call(g,'manager_canonicalize',g.rec({ops,catalog:g.get(s,'catalog')})),'ops');
const duplicate=g.contains(g.get(s,'seen'),canonical),length=g.len(canonical);
const allowed=g.and(g.not(duplicate),g.not(g.lt(g.get(s,'max_depth'),length)));
const ev=g.choose(allowed,call(g,'priority_evaluate',g.rec({ops,examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector')})),g.data({accepted:false,executable:false,progress:0,matches:0}));
// Exact-example matches dominate; target-leaf progress follows. Lower expanded
// cost breaks ties, then stable generation order. No action-specific heuristics.
const scaled=g.op('as_data',[g.op('floor',[g.num(g.calc('multiply',g.get(ev,'progress'),g.data(1000)))],{},'Number')]);
const priority=g.calc('subtract',length,g.calc('add',g.calc('multiply',g.get(ev,'matches'),g.data(1000000)),scaled));
const candidate=g.rec({ops,priority});
const queued=g.choose(g.and(g.bool(g.get(ev,'executable')),g.lt(length,g.get(s,'max_depth'))),g.push(g.get(s,'queue'),candidate),g.get(s,'queue'));
const sorted=g.op('slice',[g.op('sort',[queued],{key:'priority'})],{start:0,stop:100});
const end=g.eq(g.calc('add',g.get(s,'next_i'),g.data(1)),g.len(g.get(s,'vocabulary'))),empty=g.eq(g.len(sorted),g.data(0));
const done=g.op('or',[g.bool(g.get(ev,'accepted')),g.and(end,empty)],{},'Bool');
save('priority_step',g,g.rec({vocabulary:g.get(s,'vocabulary'),catalog:g.get(s,'catalog'),selected:g.get(s,'selected'),examples:g.get(s,'examples'),predicate:g.get(s,'predicate'),projector:g.get(s,'projector'),max_depth:g.get(s,'max_depth'),beam:g.get(s,'beam'),parent:g.choose(g.and(end,g.not(empty)),g.item(sorted,g.data(0)),g.get(s,'parent')),next_i:g.choose(end,g.data(0),g.calc('add',g.get(s,'next_i'),g.data(1))),queue:g.choose(g.and(end,g.not(empty)),g.op('slice',[sorted],{start:1}),sorted),seen:g.choose(allowed,g.push(g.get(s,'seen'),canonical),g.get(s,'seen')),found:g.choose(g.bool(g.get(ev,'accepted')),ops,g.data(null)),done:g.datum(done),evaluated:g.calc('add',g.get(s,'evaluated'),g.choose(allowed,g.data(1),g.data(0))),last:ops,last_expanded:canonical,last_duplicate:g.datum(duplicate),last_allowed:g.datum(allowed),last_evaluation:ev,last_log:g.choose(allowed,g.op('map',[ops],{body:logged.finish(logged.rec({ops:logged.list(logged.input)}))}),g.data([]))}));
fs.writeFileSync(new URL('../curriculum/prioritized-search.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
