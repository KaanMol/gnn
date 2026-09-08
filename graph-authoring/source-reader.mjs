// Authoring only: emit graph JSON. This file is never invoked by source reading.
// Every parsing decision below becomes a generic node in an editable graph.
import fs from 'node:fs';
import { G } from './graph.mjs';
const packageData={};
function save(name,g,out,description){packageData[name]={graph:{...g.finish(out),description},source:'Editable source-reading graph; generic PEG parsing with explicit continuation frames.'};}
const dispatch=(g,tag,entries,fallback)=>Object.entries(entries).reverse().reduce((out,[key,value])=>g.choose(g.eq(tag,g.data(key)),value,out),fallback);
// State: grammar, characters, rule, position, returning, ok, nodes, frames.
// Frame: parent rule, starting position, next sequence/choice index, captures.
const b=new G(),s=b.input,rule=b.get(s,'rule'),grammar=b.get(s,'grammar'),r=b.item(grammar,rule);
const op=b.get(r,'op'),pos=b.get(s,'position'),frames=b.get(s,'frames'),nodes=b.get(s,'nodes');
const chars=b.get(s,'characters'),zero=b.data(0),one=b.data(1),yes=b.data(true),no=b.data(false),empty=b.data([]);
const plus=(x,y=one)=>b.calc('add',x,y);
function state(fields={}){return b.rec(Object.fromEntries(['grammar','characters','rule','position','returning','ok','nodes','frames','memo','length'].map(k=>[k,fields[k]??b.get(s,k)])));}
function returned(ok,end=pos,values=empty,stack=frames){return state({returning:yes,ok,position:end,nodes:values,frames:stack});}
const frame=b.rec({rule,start:pos,index:zero,nodes:empty});
const stack=b.push(frames,frame);
const enterChild=(child)=>state({rule:child,returning:no,frames:stack,nodes:empty});
const children=b.get(r,'children'),child0=b.item(children,zero);
const inBounds=b.lt(pos,b.get(s,'length')),char=b.choose(inBounds,b.item(chars,pos),b.data(''));
const charAllowed=b.contains(b.get(r,'characters'),char);
const charMatch=b.and(inBounds,b.eq(b.datum(charAllowed),b.get(r,'positive')));
const matchedChar=returned(b.datum(charMatch),b.choose(charMatch,plus(pos),pos),b.choose(charMatch,b.list(char),empty));
// Literal matching is a graph map over expected characters, with guarded reads.
const m=new G(),mi=m.get(m.input,'item'),mc=m.get(m.input,'context');
const at=m.calc('add',m.get(mc,'position'),mi),cs=m.get(mc,'characters');
const same=m.choose(m.lt(at,m.get(mc,'length')),m.datum(m.eq(m.item(cs,at),m.item(m.get(mc,'expected'),mi))),m.data(false));
const expected=b.get(r,'characters');
const flags=b.op('map',[b.op('indices',[expected]),b.rec({position:pos,characters:chars,expected,length:b.get(s,'length')})],{body:m.finish(same)});
const literalOK=b.not(b.contains(flags,no));
const matchedLiteral=returned(b.datum(literalOK),b.choose(literalOK,plus(pos,b.get(r,'width')),pos),b.choose(literalOK,expected,empty));
const sequence=b.choose(b.eq(b.get(r,'arity'),zero),returned(yes),enterChild(child0));
const choices=b.choose(b.eq(b.get(r,'arity'),zero),returned(no),enterChild(child0));
const enter=dispatch(b,op,{literal:matchedLiteral,character:matchedChar,sequence,choice:choices,
  repeat:enterChild(b.get(r,'child')),capture:enterChild(b.get(r,'child')),drop:enterChild(b.get(r,'child')),
  not:enterChild(b.get(r,'child')),end:returned(b.datum(b.eq(pos,b.get(s,'length'))))},
  b.op('require',[b.eq(zero,one),s],{message:'Unknown stored grammar operation.'}));
// Resume a parent from a child success or failure. All backtracking is graph data.
const parent=b.item(frames,b.data(-1)),prule=b.get(parent,'rule'),pr=b.item(grammar,prule),pop=b.op('slice',[frames],{stop:-1});
const start=b.get(parent,'start'),idx=b.get(parent,'index'),next=plus(idx),saved=b.get(parent,'nodes'),ok=b.bool(b.get(s,'ok'));
const collected=b.concat(saved,nodes),pchildren=b.get(pr,'children');
const advance=(child,index,values,position)=>state({rule:child,position,returning:no,nodes:empty,
  frames:b.push(pop,b.rec({rule:prule,start,index,nodes:values}))});
const sequenceDone=returned(yes,pos,collected,pop);
const sequenceNext=advance(b.item(pchildren,next),next,collected,pos);
const sequenceResume=b.choose(ok,b.choose(b.lt(next,b.get(pr,'arity')),sequenceNext,sequenceDone),returned(no,start,empty,pop));
const choiceResume=b.choose(ok,returned(yes,pos,nodes,pop),
  b.choose(b.lt(next,b.get(pr,'arity')),advance(b.item(pchildren,next),next,empty,start),returned(no,start,empty,pop)));
// The frame's start is updated per repetition; prior captures remain in nodes.
const repeatNext=state({rule:b.get(pr,'child'),returning:no,nodes:empty,
  frames:b.push(pop,b.rec({rule:prule,start:pos,index:next,nodes:collected}))});
const repeated=b.op('require',[b.lt(start,pos),repeatNext],{message:'Stored repetition rule matched empty input.'});
const repeatResume=b.choose(ok,repeated,returned(yes,start,saved,pop));
const captureRecord=b.list(b.rec({kind:b.get(pr,'name'),start,end:pos,children:nodes}));
const collapse=b.choose(b.op('has_key',[pr,b.data('collapse')],{},'Bool'),b.get(pr,'collapse'),b.data(false));
const captured=b.choose(b.and(b.bool(collapse),b.eq(b.len(nodes),one)),nodes,captureRecord);
const captureResume=b.choose(ok,returned(yes,pos,captured,pop),returned(no,start,empty,pop));
const dropResume=returned(b.get(s,'ok'),pos,empty,pop);
const notResume=returned(b.datum(b.not(ok)),start,empty,pop);
const resume=dispatch(b,b.get(pr,'op'),{sequence:sequenceResume,choice:choiceResume,repeat:repeatResume,capture:captureResume,drop:dropResume,not:notResume},
 b.op('require',[b.eq(zero,one),s],{message:'Invalid parser continuation.'}));
const memo=b.get(s,'memo');
const memoRules=b.data(['Expression','Primary','Postfix','Unary','Conditional','Logical','LogicalAnd','LogicalOr','Equality','Relational','Additive','Multiplicative','JSX','JSXElement','JSXFragment','Identifier','String','Number']);
const key=(name,position)=>b.op('join_text',[b.list(name,b.data('@'),b.op('text',[position])),b.data('')]);
const currentKey=key(rule,pos),parentKey=key(prule,start);
const cached=b.item(memo,currentKey);
const entered=b.choose(b.op('has_key',[memo,currentKey],{},'Bool'),returned(b.get(cached,'ok'),b.get(cached,'position'),b.get(cached,'nodes')),enter);
const memoValue=b.rec({ok:b.get(resume,'ok'),position:b.get(resume,'position'),nodes:b.get(resume,'nodes')});
const memoAfter=b.op('set_item',[memo,parentKey,memoValue]);
const cacheFinished=b.and(b.bool(b.get(resume,'returning')),b.contains(memoRules,prule));
const resumed=b.choose(cacheFinished,b.op('set_item',[resume,b.data('memo'),memoAfter]),resume);
const out=b.choose(b.bool(b.get(s,'returning')),resumed,entered);
save('source_reader_step',b,out,'One generic parsing transition. Character matching, alternatives, captures, lookahead and repetitions are executed as graph nodes.');
const guard=new G();const keep=guard.op('or',[guard.not(guard.bool(guard.get(guard.input,'returning'))),guard.not(guard.eq(guard.get(guard.input,'frames'),guard.data([])))],{},'Bool');
const body=new G();const bodyOut=body.op('call',[body.input],{name:'source_reader_step'});
const g=new G();let source=g.get(g.input,'source');
source=g.op('require',[g.eq(g.op('kind_of',[source]),g.data('text')),source],{message:'Source must be text.'});
source=g.op('require',[g.not(g.lt(g.data(1800),g.len(source))),source],{message:'Graph source reader currently accepts at most 1,800 characters.'});
const initial=g.rec({grammar:g.get(g.input,'grammar'),characters:g.op('characters',[source]),rule:g.get(g.input,'root'),position:g.data(0),returning:g.data(false),ok:g.data(false),nodes:g.data([]),frames:g.data([]),memo:g.data({}),length:g.len(source)});
const loop=g.op('while',[initial],{guard:guard.finish(keep,'Bool'),body:body.finish(bodyOut)});
save('source_read_grammar',g,g.rec({accepted:g.get(loop,'ok'),position:g.get(loop,'position'),tree:g.get(loop,'nodes')}),'Read text using supplied graph grammar data. Produces syntax captures; does not invoke any host tokenizer, parser, compiler or JS engine.');
const grammarData=JSON.parse(fs.readFileSync(new URL('../curriculum/javascript-grammar.json',import.meta.url)));
const j=new G();const table=j.data(grammarData.rules);
save('javascript_read_source',j,j.op('call',[j.rec({source:j.input,grammar:table,root:j.data(grammarData.root)})],{name:'source_read_grammar'}),'Read raw JavaScript and JSX into a captured syntax tree using stored grammar rules. Syntax only: no semantic validation, lowering or execution.');
for(const name of ['javascript_read_source','javascript_compile_source','javascript_run_source'])if(packageData[name])packageData[name].graph.execution_budget=10000000;
fs.writeFileSync(new URL('../curriculum/source-reader.json',import.meta.url),JSON.stringify(packageData,null,2)+'\n');
console.log(Object.fromEntries(Object.entries(packageData).map(([k,v])=>[k,v.graph.nodes.length])));
