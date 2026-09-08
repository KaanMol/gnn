// Authoring only: source composition, analysis and test selection execute as graph data.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};
const save=(name,g,out)=>suite[name]={graph:{...g.finish(out),execution_budget:10000000},source:'Graph-owned data-processing composition and source-analysis lessons.'};
const call=(g,name,arg)=>g.op('call',[arg],{name});
const require=(g,condition,value,message)=>g.op('require',[condition,value],{message});
const join=(g,...parts)=>g.op('join_text',[g.list(...parts),g.data('')]);
const has=(g,value,key)=>g.op('has_key',[value,g.data(key)],{},'Bool');
const optional=(g,value,key,fallback)=>g.choose(has(g,value,key),g.get(value,key),g.data(fallback));

const stage=new G(),operation=stage.get(stage.input,'operation'),expression=stage.get(stage.input,'expression');
const fragment=join(stage,stage.data('.'),operation,stage.data('(x => ('),expression,stage.data('))'));
save('javascript_pipeline_stage',stage,require(stage,stage.contains(stage.data(['filter','map']),operation),fragment,'Pipeline stages currently support filter and map.'));

const writer=new G(),steps=writer.get(writer.input,'pipeline');
const validSteps=require(writer,writer.and(writer.not(writer.lt(writer.data(8),writer.len(steps))),writer.not(writer.eq(writer.len(steps),writer.data(0)))),steps,'Supply 1–8 pipeline stages.');
const each=new G();const fragments=writer.op('map',[validSteps],{body:each.finish(call(each,'javascript_pipeline_stage',each.input))});
const end=writer.get(writer.input,'finish');
const endings=writer.data({array:'',sum:'.reduce((total, x) => total + x, 0)',count:'.length'});
const suffix=require(writer,writer.contains(writer.data(['array','sum','count']),end),writer.op('lookup',[endings,end]),'Finish must be array, sum, or count.');
const source=join(writer,writer.data('function transform(xs) { return xs'),writer.op('join_text',[fragments,writer.data('')]),suffix,writer.data('; }'));
const warm=call(writer,'javascript_warm_policy',source);
const compiled=call(writer,'javascript_compile_source',writer.get(warm,'input'));
save('javascript_compose_pipeline',writer,writer.rec({source,program:compiled}));

const checked=new G(),tests=checked.get(checked.input,'tests');
const validTests=require(checked,checked.and(checked.lt(checked.data(0),checked.len(tests)),checked.not(checked.lt(checked.data(12),checked.len(tests)))),tests,'Supply 1–12 input/output tests.');
const candidate=call(checked,'javascript_compose_pipeline',checked.input);
const matches=call(checked,'js_choose_program',checked.rec({candidates:checked.list(candidate),tests:validTests}));
const selected=require(checked,checked.eq(checked.len(matches),checked.data(1)),checked.item(matches,checked.data(0)),'The composed pipeline did not pass every supplied test.');
save('javascript_write_pipeline',checked,checked.rec({source:checked.get(selected,'source'),tests_passed:checked.len(validTests),verification:checked.data('Passed supplied examples; this is not a proof for all inputs.')}));

const statement=new G(),instruction=statement.input,op=statement.get(instruction,'op');
const descriptions=statement.data({uninitialize:'Introduce or end a binding before a value can be read.',assign:'Evaluate an expression and initialize a binding.',update:'Evaluate an expression and update an existing mutable binding.',return:'Return the expression value and finish this function.',branch:'Evaluate a condition and jump when it is false.',jump:'Continue at another instruction; this can form a loop.',log:'Evaluate and capture console output.'});
const description=statement.op('lookup',[descriptions,op]);
save('javascript_explain_statement',statement,statement.rec({operation:op,meaning:description,binding:optional(statement,instruction,'name',null),target:optional(statement,instruction,'target',null),expression:optional(statement,instruction,'expression',[]),console_arguments:optional(statement,instruction,'expressions',[])}));
const explain=new G(),ready=call(explain,'javascript_warm_policy',explain.input);
const program=call(explain,'javascript_compile_source',explain.get(ready,'input'));
const mapper=new G();const statements=explain.op('map',[explain.get(program,'code')],{body:mapper.finish(call(mapper,'javascript_explain_statement',mapper.input))});
save('javascript_analyze_source',explain,explain.rec({name:explain.get(program,'name'),parameter:explain.get(program,'parameter'),requires_input:explain.get(program,'requires_input'),statements,scope:explain.data('Static explanation of the supported source subset; expressions are shown as graph instruction data. No source execution is needed.')}));
fs.writeFileSync(new URL('../curriculum/programming-workbench.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log(Object.keys(suite));
