// A bounded observation-to-predictor experiment, not semantic understanding.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};const save=(name,g,out)=>suite[name]={graph:{...g.finish(out),execution_budget:1000000},source:'Supplied synthetic environment / generic field hypothesis learner.'};
const call=(g,name,x)=>g.op('call',[x],{name});
// Environment implementations are graphs too. Their hidden keys are never
// supplied to the learner; it only invokes these worlds and observes results.
for(const [name,key] of [['grounded_world_one','q7'],['grounded_world_two','m3']]){
 const g=new G();save(name,g,g.datum(g.bool(g.get(g.input,key))));
}
const observe=new G(),item=observe.get(observe.input,'item');
const observation=observe.rec({features:item,outcome:observe.op('invoke',[observe.get(observe.input,'context'),item])});
let g=new G();save('grounded_observe',g,g.op('map',[g.get(g.input,'items'),g.get(g.input,'world')],{body:observe.finish(observation)}));

const sample=new G(),features=sample.get(sample.input,'item','features'),key=sample.get(sample.input,'context');
const present=sample.op('has_key',[features,key],{},'Bool');
const match=sample.choose(present,sample.datum(sample.eq(sample.item(features,key),sample.get(sample.input,'item','outcome'))),sample.data(false));
const hypothesis=new G();const checks=hypothesis.op('map',[hypothesis.get(hypothesis.input,'context'),hypothesis.get(hypothesis.input,'item')],{body:sample.finish(match)});
const consistent=hypothesis.not(hypothesis.contains(checks,hypothesis.data(false)));
g=new G();const observations=g.get(g.input,'observations');
const keys=g.op('keys',[g.get(g.item(observations,g.data(0)),'features')]);
const candidates=g.op('filter',[keys,observations],{body:hypothesis.finish(consistent,'Bool')});
save('grounded_hypotheses',g,g.choose(g.lt(g.data(0),g.len(observations)),candidates,g.data([])));

// Choose a probe whose predicted outcomes disagree across surviving hypotheses.
// The environment supplies a bounded pool; the graph chooses the experiment.
const predictionForKey=new G();const fieldValue=predictionForKey.item(predictionForKey.get(predictionForKey.input,'context'),predictionForKey.get(predictionForKey.input,'item'));
const probe=new G();const predictions=probe.op('map',[probe.get(probe.input,'context'),probe.get(probe.input,'item')],{body:predictionForKey.finish(fieldValue)});
const informative=probe.lt(probe.data(1),probe.len(probe.op('unique',[predictions])));
g=new G();const hypotheses=call(g,'grounded_hypotheses',g.input);
const useful=g.op('filter',[g.get(g.input,'pool'),hypotheses],{body:probe.finish(informative,'Bool')});
save('grounded_choose_probe',g,g.choose(g.lt(g.data(0),g.len(useful)),g.list(g.item(useful,g.data(0))),g.data([])));

// Save only an unambiguous, observed field hypothesis. No host chooses the key.
g=new G();const possible=call(g,'grounded_hypotheses',g.input),unique=g.eq(g.len(possible),g.data(1)),field=g.item(possible,g.data(0));
const graph=g.rec({input_type:g.data('Data'),output_type:g.data('Data'),trace_mode:g.data('explicit'),nodes:g.list(g.data({id:'n0',op:'input',inputs:[],type:'Data'}),g.rec({id:g.data('n1'),op:g.data('get'),inputs:g.data(['n0']),type:g.data('Data'),path:g.list(field)})),output:g.data('n1')});
const name=g.get(g.input,'name');
const existing=g.op('act',[g.input,g.data({namespace:'knowledge.procedures'})],{surface:'workspace',action:'keys'});
const unused=g.op('require',[g.not(g.contains(existing,name)),name],{message:'Refusing to replace a learned predictor.'});
const saved=g.op('act',[existing,g.rec({namespace:g.data('knowledge.procedures'),key:unused,value:g.rec({graph,source:g.data('Field predictor inferred from simulated action outcomes; not a semantic definition.'),observations,field})})],{surface:'workspace',action:'write'});
save('grounded_learn',g,g.choose(unique,g.rec({status:g.data('learned'),field,saved}),g.rec({status:g.data('insufficient_evidence'),candidates:possible})));

// A missing renamed field is unknown, rather than a confident negative answer.
const prediction=new G();const result=prediction.op('invoke',[prediction.get(prediction.input,'name'),prediction.get(prediction.input,'features')]);
g=new G();const attempted=g.op('attempt',[g.input],{body:prediction.finish(result)});
save('grounded_predict',g,g.choose(g.bool(g.get(attempted,'ok')),g.rec({known:g.data(true),outcome:g.get(attempted,'result')}),g.rec({known:g.data(false),outcome:g.data(null)})));
fs.writeFileSync(new URL('../curriculum/grounded-adapter.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log('Grounded adapter graph rules:',Object.keys(suite).length);
