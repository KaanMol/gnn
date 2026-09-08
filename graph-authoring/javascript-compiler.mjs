// Emits executable graph data. Never loaded to parse/compile submitted source.
import fs from 'node:fs';
import {G} from './graph.mjs';
const suite={};
const save=(name,g,out)=>{const graph=g.finish(out),needed=new Set();const visit=id=>{if(needed.has(id))return;needed.add(id);for(const input of graph.nodes.find(n=>n.id===id).inputs)visit(input);};visit(out);graph.nodes=graph.nodes.filter(n=>needed.has(n.id));suite[name]={graph:{...graph,description:'Graph syntax-tree lowering rule: '+name},source:'Stored graph compiler rules. No host-language source parser or compiler is invoked.'};};
const D=(g,x)=>g.data(x), get=(g,x,k)=>g.get(x,k);
const call=(g,name,x)=>g.op('call',[x],{name});
const join=(g,x)=>g.op('join_text',[x,g.data('')]);
const slice=(g,x,start,stop)=>g.op('slice',[x],{start,stop});
const req=(g,c,x,message)=>g.op('require',[c,x],{message});
const reject=(g,msg)=>req(g,g.eq(g.data(0),g.data(1)),g.data(null),msg);
const dispatch=(g,t,opts,fallback)=>Object.entries(opts).reverse().reduce((out,[k,v])=>g.choose(g.eq(t,g.data(k)),v,out),fallback);
const token=(g,kind,fields={})=>g.rec({kind:g.data(kind),...fields});
const constant=(g,value)=>g.list(token(g,'constant',{value}));
const result=(g,fields={})=>g.rec({kind:g.data('value'),text:g.data(''),tokens:g.data([]),code:g.data([]),items:g.data([]),program:g.data(null),...fields});
function mapField(g,x,key){const m=new G();return g.op('map',[x],{body:m.finish(m.get(m.input,key))});}
const flatField=(g,x,key)=>g.op('flatten',[mapField(g,x,key)]);
function fold(name,initial,build){const g=new G(),guard=new G(),b=new G();const keep=guard.lt(guard.get(guard.input,'i'),guard.len(guard.get(guard.input,'items')));const out=build(b);const loop=g.op('while',[initial(g)],{guard:guard.finish(keep,'Bool'),body:b.finish(out)});save(name,g,loop);}
// Decode supported JS escapes using a graph state machine, not JSON.parse.
fold('js_source_decode_string',g=>g.rec({i:g.data(0),items:slice(g,g.input,1,-1),text:g.data(''),escaped:g.data(false)}),b=>{
 const s=b.input,c=b.item(b.get(s,'items'),b.get(s,'i')),esc=b.bool(b.get(s,'escaped'));
 const table=b.data({'n':'\n','r':'\r','t':'\t','\\':'\\','"':'"',"'":"'"});
 const append=b.choose(esc,b.item(table,c),b.choose(b.eq(c,b.data('\\')),b.data(''),c));
 return b.rec({i:b.calc('add',b.get(s,'i'),b.data(1)),items:b.get(s,'items'),text:join(b,b.list(b.get(s,'text'),append)),escaped:b.datum(b.and(b.not(esc),b.eq(c,b.data('\\'))))});
});
fold('js_source_binary',g=>g.rec({i:g.data(1),items:g.input,tokens:g.get(g.item(g.input,g.data(0)),'tokens')}),b=>{
 const s=b.input,items=b.get(s,'items'),i=b.get(s,'i'),op=b.get(b.item(items,i),'text'),rhs=b.get(b.item(items,b.calc('add',i,b.data(1))),'tokens');
 const ordinary=b.push(b.concat(b.get(s,'tokens'),rhs),token(b,'binary',{operator:op}));
 const short=b.concat(b.push(b.get(s,'tokens'),token(b,'short_circuit',{operator:op,skip:b.len(rhs)})),rhs);
 return b.rec({i:b.calc('add',i,b.data(2)),items,tokens:b.choose(b.contains(b.data(['&&','||','??']),op),short,ordinary)});
});
fold('js_source_array',g=>g.rec({i:g.data(0),items:g.input,tokens:constant(g,g.data([]))}),b=>{
 const s=b.input,x=b.item(b.get(s,'items'),b.get(s,'i'));
 const op=b.choose(b.eq(b.get(x,'kind'),b.data('Spread')),b.data('array_spread'),b.data('array_append'));
 return b.rec({i:b.calc('add',b.get(s,'i'),b.data(1)),items:b.get(s,'items'),tokens:b.push(b.concat(b.get(s,'tokens'),b.get(x,'tokens')),b.rec({kind:op}))});
});
fold('js_source_postfix',g=>g.rec({i:g.data(1),items:g.input,value:g.item(g.input,g.data(0)),member:g.data('')}),b=>{
 const s=b.input,items=b.get(s,'items'),i=b.get(s,'i'),x=b.item(items,i),v=b.get(s,'value'),kind=b.get(x,'kind');
 const ts=b.get(v,'tokens'),args=b.get(x,'items'),method=b.get(s,'member'),base=b.get(v,'text');
 const next=b.calc('add',i,b.data(1));
 const nextCall=b.choose(b.lt(next,b.len(items)),b.datum(b.eq(b.get(b.item(items,next),'kind'),b.data('Call'))),b.data(false));
 const property=result(b,{tokens:b.push(ts,token(b,'property',{key:b.get(x,'text')}))});
 const member=b.choose(b.bool(nextCall),v,property);
 const indexed=result(b,{tokens:b.push(b.concat(ts,b.get(x,'tokens')),token(b,'index'))});
 const callback=b.item(args,b.data(0));
 let cbTokens=b.concat(ts,b.choose(b.eq(method,b.data('reduce')),b.get(b.item(args,b.data(1)),'tokens'),b.data([])));
 cbTokens=b.push(cbTokens,token(b,'array_callback',{method,callback:b.rec({parameters:mapField(b,b.get(callback,'items'),'text'),tokens:b.get(callback,'tokens')})}));
 let cb=result(b,{tokens:cbTokens});
 cb=req(b,b.eq(b.get(callback,'kind'),b.data('ArrowFunction')),cb,'Array methods require an inline arrow callback.');
 cb=req(b,b.eq(b.len(args),b.choose(b.eq(method,b.data('reduce')),b.data(2),b.data(1))),cb,'Wrong callback argument count.');
 const logsValue=result(b,{code:b.list(b.rec({op:b.data('log'),expressions:mapField(b,args,'tokens')}))});
 const logs=req(b,b.not(b.contains(mapField(b,args,'kind'),b.data('ArrowFunction'))),logsValue,'console.log cannot accept a function value in this graph subset.');
 const mathUnary=result(b,{tokens:b.push(b.get(b.item(args,b.data(0)),'tokens'),token(b,'math_unary',{method}))});
 const mathBinary=result(b,{tokens:b.push(b.concat(b.get(b.item(args,b.data(0)),'tokens'),b.get(b.item(args,b.data(1)),'tokens')),token(b,'math_binary',{method}))});
 const math=b.choose(b.contains(b.data(['abs','sign','floor','ceil','round','trunc']),method),req(b,b.eq(b.len(args),b.data(1)),mathUnary,'Math unary method requires one argument.'),
 req(b,b.and(b.contains(b.data(['min','max','pow']),method),b.eq(b.len(args),b.data(2))),mathBinary,'Graph compiler currently supports pairwise min/max/pow.'));
 const called=b.choose(b.and(b.eq(base,b.data('console')),b.eq(method,b.data('log'))),logs,
 b.choose(b.eq(base,b.data('Math')),req(b,b.not(b.contains(mapField(b,args,'kind'),b.data('ArrowFunction'))),math,'Math arguments cannot be function values.'),b.choose(b.contains(b.data(['map','filter','reduce','find','findIndex','some','every']),method),cb,reject(b,'General function calls are not lowered by this graph compiler yet.'))));
 const value=dispatch(b,kind,{Member:member,Index:indexed,Call:called},reject(b,'Unknown postfix syntax.'));
 return b.rec({i:next,items,value,member:b.choose(b.eq(kind,b.data('Member')),b.get(x,'text'),b.data(''))});
});
// Relocate control-flow targets whenever instruction sequences are composed.
const rel=new G(),rm=new G(),ri=rm.get(rm.input,'item'),rc=rm.get(rm.input,'context');
const relocated=rm.choose(rm.contains(rm.data(['branch','jump']),rm.get(ri,'op')),rm.op('set_item',[ri,rm.data('target'),rm.calc('add',rm.get(ri,'target'),rc)]),ri);
save('js_source_relocate',rel,rel.op('map',[rel.get(rel.input,'code'),rel.get(rel.input,'offset')],{body:rm.finish(relocated)}));
fold('js_source_join_code',g=>g.rec({i:g.data(0),items:g.input,code:g.data([])}),b=>{
 const s=b.input,code=b.get(s,'code'),item=b.item(b.get(s,'items'),b.get(s,'i'));
 const shifted=call(b,'js_source_relocate',b.rec({code:b.get(item,'code'),offset:b.len(code)}));
 return b.rec({i:b.calc('add',b.get(s,'i'),b.data(1)),items:b.get(s,'items'),code:b.concat(code,shifted)});
});
fold('js_source_validate_bindings',g=>g.rec({i:g.data(0),items:g.get(g.input,'code'),bindings:g.op('set_item',[g.data({}),g.get(g.input,'parameter'),g.data('parameter')])}),b=>{
 const s=b.input,bindings=b.get(s,'bindings'),x=b.item(b.get(s,'items'),b.get(s,'i')),op=b.get(x,'op'),name=b.get(x,'name');
 const declaration=req(b,b.not(b.op('has_key',[bindings,name],{},'Bool')),b.op('set_item',[bindings,name,b.get(x,'binding_kind')]),'Duplicate lexical declaration or parameter.');
 const writable=b.choose(b.op('has_key',[bindings,name],{},'Bool'),b.datum(b.not(b.eq(b.item(bindings,name),b.data('const')))),b.data(true));
 const update=req(b,b.bool(writable),bindings,'Cannot assign to a const binding.');
 const next=dispatch(b,op,{uninitialize:b.choose(b.eq(b.get(x,'binding_kind'),b.data('scope_exit')),bindings,declaration),update},bindings);
 return b.rec({i:b.calc('add',b.get(s,'i'),b.data(1)),items:b.get(s,'items'),bindings:next});
});
// JSX whitespace: trim each line according to JSX's multiline text rules.
const trimGuard=new G(),tg=trimGuard.input;
const trimKeep=trimGuard.bool(trimGuard.choose(trimGuard.lt(trimGuard.get(tg,'start'),trimGuard.get(tg,'end')),trimGuard.datum(trimGuard.eq(trimGuard.item(trimGuard.get(tg,'chars'),trimGuard.get(tg,'start')),trimGuard.data(' '))),trimGuard.data(false)));
const trimBody=new G(),tb=trimBody.input;
const trimStep=trimBody.rec({chars:trimBody.get(tb,'chars'),start:trimBody.calc('add',trimBody.get(tb,'start'),trimBody.data(1)),end:trimBody.get(tb,'end')});
const tr=new G();const trimmed=tr.op('while',[tr.rec({chars:tr.input,start:tr.data(0),end:tr.len(tr.input)})],{guard:trimGuard.finish(trimKeep,'Bool'),body:trimBody.finish(trimStep)});
const tm=new G();const keepIndex=tm.not(tm.lt(tm.get(tm.input,'item'),tm.get(tm.get(tm.input,'context'),'start')));
const indices=tr.op('filter',[tr.op('indices',[tr.input]),trimmed],{body:tm.finish(keepIndex,'Bool')});
const cm=new G();const cvalue=cm.item(cm.get(cm.input,'context'),cm.get(cm.input,'item'));
save('js_source_trim_left',tr,tr.op('map',[indices,tr.input],{body:cm.finish(cvalue)}));
const jtxt=new G();let jsxText=jtxt.op('replace_text',[jtxt.input,jtxt.data('&#x20;'),jtxt.data(' ')]);jsxText=jtxt.op('replace_text',[jsxText,jtxt.data('\t'),jtxt.data(' ')]);
jsxText=req(jtxt,jtxt.not(jtxt.contains(jtxt.op('characters',[jsxText]),jtxt.data('&'))),jsxText,'JSX entities await graph decoding; use a brace string expression for now.');
const lines=jtxt.op('split_text',[jsxText,jtxt.data('\n')]);
const lm=new G(),li=lm.get(lm.input,'item'),lc=lm.get(lm.input,'context'),line=lm.item(lc,li);let linechars=lm.op('characters',[line]);
linechars=lm.choose(lm.eq(li,lm.data(0)),linechars,call(lm,'js_source_trim_left',linechars));
linechars=lm.choose(lm.eq(li,lm.calc('subtract',lm.len(lc),lm.data(1))),linechars,lm.op('reverse',[call(lm,'js_source_trim_left',lm.op('reverse',[linechars]))]));
const lineTexts=jtxt.op('map',[jtxt.op('indices',[lines]),lines],{body:lm.finish(join(lm,linechars))});
const fm=new G();const nonempty=fm.not(fm.eq(fm.input,fm.data('')));
const nonemptyLines=jtxt.op('filter',[lineTexts],{body:fm.finish(nonempty,'Bool')});
save('js_source_jsx_text',jtxt,jtxt.op('join_text',[nonemptyLines,jtxt.data(' ')]));
// JSX construction is emitted as ordinary object/array graph instructions.
const jsx=new G(),children=jsx.input;
const sel=(kind)=>{const f=new G();return jsx.op('filter',[children],{body:f.finish(f.eq(f.get(f.input,'kind'),f.data(kind)),'Bool')});};
const tags=sel('TagName'),attrs=sel('JSXAttribute');
const childFilter=new G();const childOK=childFilter.not(childFilter.contains(childFilter.data(['TagName','JSXAttribute']),childFilter.get(childFilter.input,'kind')));
const blank=childFilter.choose(childFilter.eq(childFilter.get(childFilter.input,'kind'),childFilter.data('JSXText')),childFilter.datum(childFilter.eq(childFilter.get(childFilter.item(childFilter.get(childFilter.input,'tokens'),childFilter.data(0)),'value'),childFilter.data(''))),childFilter.data(false));
const kids=jsx.op('filter',[children],{body:childFilter.finish(childFilter.and(childOK,childFilter.not(childFilter.bool(blank))),'Bool')});
const obj=()=>constant(jsx,jsx.data({__js_type:'object',properties:{}}));
const put=(ts,key,val)=>jsx.push(jsx.concat(ts,val),token(jsx,'object_put',{key:jsx.data(key)}));
const tagText=jsx.choose(jsx.eq(jsx.len(tags),jsx.data(0)),jsx.data('Fragment'),jsx.get(jsx.item(tags,jsx.data(0)),'text'));
const tagChars=jsx.op('characters',[tagText]);
let type=req(jsx,jsx.bool(jsx.choose(jsx.eq(jsx.len(tags),jsx.data(2)),jsx.datum(jsx.eq(jsx.get(jsx.item(tags,jsx.data(0)),'text'),jsx.get(jsx.item(tags,jsx.data(1)),'text'))),jsx.data(true))),tagText,'Mismatched JSX opening and closing tags.');
type=req(jsx,jsx.op('or',[jsx.eq(tagText,jsx.data('Fragment')),jsx.contains(jsx.data([...'abcdefghijklmnopqrstuvwxyz']),jsx.item(tagChars,jsx.data(0)))],{},'Bool'),type,'Custom JSX component calls are not supported yet.');
const props=jsx.concat(obj(),flatField(jsx,attrs,'tokens'));
let jsxTokens=put(obj(),'type',constant(jsx,type));jsxTokens=put(jsxTokens,'props',props);jsxTokens=put(jsxTokens,'children',jsx.get(call(jsx,'js_source_array',kids),'tokens'));
save('js_source_jsx',jsx,jsxTokens);
// Lower one syntax node after its children have been lowered.
const n=new G(),node=n.get(n.input,'node'),ch=n.get(n.input,'children'),kind=n.get(node,'kind'),raw=n.get(node,'children');
const c=i=>n.item(ch,n.data(i)),t=i=>n.get(c(i),'tokens'),textOf=i=>n.get(c(i),'text');
const text=join(n,mapField(n,ch,'text'));
const res=fields=>result(n,{kind,items:ch,...fields});
const expr=tokens=>res({tokens});
const num=call(n,'programming_safe_integer',n.op('as_data',[n.op('as_number',[text],{},'Number')]));
const string=n.get(call(n,'js_source_decode_string',raw),'text');
const leafText=res({text});
const identifierValue=res({text,tokens:n.choose(n.eq(text,n.data('undefined')),constant(n,n.data({__js_type:'undefined'})),n.list(token(n,'variable',{name:text})))});
const identifier=req(n,n.not(n.contains(n.data('export default function return const let if else while for do break continue true false null typeof void var new this class import switch throw try catch await yield'.split(' ')),text)),identifierValue,'Reserved word is not a supported identifier.');
const binary=n.choose(n.eq(n.len(ch),n.data(1)),c(0),expr(n.get(call(n,'js_source_binary',ch),'tokens')));
const condition=n.choose(n.eq(n.len(ch),n.data(1)),t(0),n.concat(n.concat(n.push(t(0),token(n,'branch_false',{skip:n.calc('add',n.len(t(1)),n.data(1))})),t(1)),n.concat(n.list(token(n,'jump',{skip:n.len(t(2))})),t(2))));
const params=n.get(c(0),'items');const paramNames=mapField(n,params,'text');
const callbackCode=n.get(c(1),'code');
const callbackReturn=req(n,n.eq(n.len(callbackCode),n.data(1)),n.item(callbackCode,n.data(0)),'Callback blocks currently require exactly one return statement.');
const callbackExpression=req(n,n.eq(n.get(callbackReturn,'op'),n.data('return')),n.get(callbackReturn,'expression'),'Callback blocks currently require exactly one return statement.');
const arrow=req(n,n.eq(n.len(paramNames),n.len(n.op('unique',[paramNames]))),res({tokens:n.choose(n.eq(n.get(c(1),'kind'),n.data('Block')),callbackExpression,t(1)),items:params}),'Duplicate callback parameter.');
const propValue=n.choose(n.eq(n.len(ch),n.data(1)),t(0),t(1));
const propKey=n.get(c(0),'text');
const propTokens=n.choose(n.eq(n.get(c(0),'kind'),n.data('ComputedKey')),n.push(n.concat(t(0),t(1)),token(n,'object_computed_put')),
 n.push(propValue,token(n,'object_put',{key:propKey})));
const prop=expr(req(n,n.not(n.eq(propKey,n.data('__proto__'))),propTokens,'Prototype-setting object syntax is not supported.'));
const objectProps=new G();const px=objectProps.input;
const pt=objectProps.choose(objectProps.eq(objectProps.get(px,'kind'),objectProps.data('Spread')),objectProps.push(objectProps.get(px,'tokens'),token(objectProps,'object_spread')),objectProps.get(px,'tokens'));
const propertyLists=n.op('map',[ch],{body:objectProps.finish(pt)});
const object=expr(n.concat(constant(n,n.data({__js_type:'object',properties:{}})),n.op('flatten',[propertyLists])));
const attributeValue=n.choose(n.eq(n.len(ch),n.data(1)),constant(n,n.data(true)),t(1));
const attribute=expr(n.push(attributeValue,token(n,'object_put',{key:textOf(0)})));
const decName=textOf(1),init=t(2);
const declarationValue=res({text:decName,code:n.list(n.rec({op:n.data('uninitialize'),name:decName,binding_kind:textOf(0)}),n.rec({op:n.data('assign'),name:decName,expression:init}))});
const declaration=req(n,n.not(n.contains(n.data(['console','Math','undefined','Boolean']),decName)),declarationValue,'Shadowing built-in names awaits graph scope rules.');
const blockCode=n.get(call(n,'js_source_join_code',ch),'code');
const isDecl=new G();const filtered=n.op('filter',[ch],{body:isDecl.finish(isDecl.eq(isDecl.get(isDecl.input,'kind'),isDecl.data('VariableDeclaration')),'Bool')});
const names=mapField(n,filtered,'text');
let block=res({code:blockCode});block=req(n,n.eq(n.len(names),n.len(n.op('unique',[names]))),block,'Duplicate lexical declaration.');
const returnExpr=n.choose(n.eq(n.len(ch),n.data(0)),constant(n,n.data({__js_type:'undefined'})),t(0));
const ret=res({code:n.list(n.rec({op:n.data('return'),expression:returnExpr}))});
const parameterItems=n.get(c(1),'items');
const parameter=n.choose(n.eq(n.len(parameterItems),n.data(0)),n.data('$unused_input'),n.get(n.item(parameterItems,n.data(0)),'text'));
const funcProgram=n.rec({name:textOf(0),parameter,code:n.push(n.get(c(2),'code'),n.rec({op:n.data('return'),expression:constant(n,n.data({__js_type:'undefined'}))})),script:n.data(false),requires_input:n.datum(n.lt(n.data(0),n.len(parameterItems)))});
const func=req(n,n.not(n.lt(n.data(1),n.len(parameterItems))),res({text:textOf(0),program:funcProgram}),'Graph entry functions currently accept zero or one parameter.');
const singleFunction=n.and(n.eq(n.len(ch),n.data(1)),n.eq(n.get(c(0),'kind'),n.data('FunctionDeclaration')));
const scriptProgram=n.rec({name:n.data('script'),parameter:n.data('$unused_input'),code:n.push(n.get(block,'code'),n.rec({op:n.data('return'),expression:constant(n,n.data({__js_type:'undefined'}))})),script:n.data(true),requires_input:n.data(false)});
const childKinds=mapField(n,ch,'kind');
const validScript=n.and(n.not(n.contains(childKinds,n.data('FunctionDeclaration'))),n.not(n.contains(childKinds,n.data('ReturnStatement'))));
const program=res({program:n.choose(singleFunction,n.get(c(0),'program'),req(n,validScript,scriptProgram,'Only one entry function, without appended calls, is supported.'))});
const jsxStringText=join(n,slice(n,raw,1,-1));
const controlBody=i=>req(n,n.not(n.contains(mapField(n,n.get(c(i),'items'),'kind'),n.data('VariableDeclaration'))),n.get(c(i),'code'),'Declarations inside control-flow blocks await graph lexical-scope rules.');
const thenCode=controlBody(1),elseCode=n.choose(n.eq(n.len(ch),n.data(3)),controlBody(2),n.data([]));
const elseStart=n.calc('add',n.len(thenCode),n.data(2)),endIf=n.calc('add',elseStart,n.len(elseCode));
const ifCode=n.concat(n.concat(n.list(n.rec({op:n.data('branch'),expression:t(0),target:elseStart})),call(n,'js_source_relocate',n.rec({code:thenCode,offset:n.data(1)}))),n.concat(n.list(n.rec({op:n.data('jump'),target:endIf})),call(n,'js_source_relocate',n.rec({code:elseCode,offset:elseStart}))));
const whileCode=n.concat(n.concat(n.list(n.rec({op:n.data('branch'),expression:t(0),target:n.calc('add',n.len(thenCode),n.data(2))})),call(n,'js_source_relocate',n.rec({code:thenCode,offset:n.data(1)}))),n.list(n.rec({op:n.data('jump'),target:n.data(0)})));
const updateOp=textOf(1),updateRhs=n.choose(n.contains(n.data(['++','--']),updateOp),constant(n,n.data(1)),t(2));
const updateExpression=n.choose(n.eq(updateOp,n.data('=')),updateRhs,n.push(n.concat(t(0),updateRhs),token(n,'binary',{operator:n.item(n.op('characters',[updateOp]),n.data(0))})));
const update=res({code:n.list(n.rec({op:n.data('update'),name:textOf(0),expression:updateExpression}))});
const doBody=controlBody(0);
const doCode=n.concat(doBody,n.list(n.rec({op:n.data('branch'),expression:t(1),target:n.calc('add',n.len(doBody),n.data(2))}),n.rec({op:n.data('jump'),target:n.data(0)})));
const initCode=n.get(c(0),'code'),forUpdate=n.get(c(2),'code'),forBody=controlBody(3),forStart=n.len(initCode);
const updateStart=n.calc('add',n.calc('add',forStart,n.data(1)),n.len(forBody));
const forEnd=n.calc('add',n.calc('add',updateStart,n.len(forUpdate)),n.data(1));
const forHasBinding=n.not(n.eq(textOf(0),n.data('')));
const scopeExit=n.choose(forHasBinding,n.list(n.rec({op:n.data('uninitialize'),name:textOf(0),binding_kind:n.data('scope_exit')})),n.data([]));
const forCode=n.concat(n.concat(n.concat(n.concat(initCode,n.list(n.rec({op:n.data('branch'),expression:t(1),target:forEnd}))),call(n,'js_source_relocate',n.rec({code:forBody,offset:n.calc('add',forStart,n.data(1))}))),call(n,'js_source_relocate',n.rec({code:forUpdate,offset:updateStart}))),n.concat(n.list(n.rec({op:n.data('jump'),target:forStart})),scopeExit));
const forInitName=n.choose(n.eq(n.len(ch),n.data(0)),n.data(''),n.choose(n.eq(n.get(c(0),'kind'),n.data('VariableDeclaration')),textOf(0),n.data('')));
const outputs={ForInit:res({text:forInitName,code:blockCode}),ForUpdate:res({code:blockCode}),ForTest:expr(n.choose(n.eq(n.len(ch),n.data(0)),constant(n,n.data(true)),t(0))),ForStatement:res({code:forCode}),DoWhileStatement:res({code:doCode}),UpdateOperator:leafText,UpdateStatement:update,IfStatement:res({code:ifCode}),WhileStatement:res({code:whileCode}),Identifier:identifier,TagName:leafText,AttributeName:leafText,Operator:leafText,DeclarationKind:leafText,
 NumberLiteral:res({text,tokens:constant(n,num)}),StringLiteral:res({text:string,tokens:constant(n,string)}),
 BooleanLiteral:expr(constant(n,n.datum(n.eq(text,n.data('true'))))),NullLiteral:expr(constant(n,n.data(null))),
 Parameters:res({}),Member:res({text:textOf(0)}),Index:expr(t(0)),ComputedKey:expr(t(0)),Call:res({}),
 ArrowFunction:arrow,PostfixExpression:n.get(call(n,'js_source_postfix',ch),'value'),
 ConditionalExpression:n.choose(n.eq(n.len(ch),n.data(1)),c(0),expr(condition)),Logical:binary,Equality:binary,Relational:binary,Additive:binary,Multiplicative:binary,
 UnaryExpression:expr(n.push(t(1),token(n,'unary',{operator:textOf(0)}))),
 ArrayExpression:expr(n.get(call(n,'js_source_array',ch),'tokens')),Property:prop,ObjectExpression:object,Spread:expr(t(0)),
 JSXElement:expr(call(n,'js_source_jsx',ch)),JSXFragment:expr(call(n,'js_source_jsx',ch)),
 JSXExpression:expr(n.choose(n.eq(n.len(ch),n.data(0)),constant(n,n.data(null)),t(0))),
 JSXText:expr(constant(n,call(n,'js_source_jsx_text',text))),JSXString:expr(constant(n,req(n,n.not(n.contains(n.op('characters',[jsxStringText]),n.data('&'))),jsxStringText,'JSX attribute entities await graph decoding.'))),JSXAttribute:attribute,
 VariableDeclaration:declaration,Block:req(n,n.not(n.contains(mapField(n,ch,'kind'),n.data('Block'))),req(n,n.not(n.contains(mapField(n,ch,'kind'),n.data('FunctionDeclaration'))),block,'Nested functions await graph lowering.'),'Nested lexical blocks await graph lowering.'),ReturnStatement:ret,FunctionDeclaration:func,Program:program,
 ExpressionStatement:res({code:req(n,n.lt(n.data(0),n.len(n.get(c(0),'code'))),n.get(c(0),'code'),'Only console.log is supported as a standalone expression in this graph compiler.')})};
const route=new G();let routed=reject(route,'Syntax is recognized but has no graph lowering rule yet.');
const pairs=Object.entries(outputs);
for(let i=0;i<pairs.length;i+=8){const group=Object.fromEntries(pairs.slice(i,i+8)),name='js_source_lower_group_'+i;
 save(name,n,dispatch(n,kind,group,reject(n,'Unknown syntax in lowering group.')));
 routed=route.choose(route.contains(route.data(Object.keys(group)),route.get(route.get(route.input,'node'),'kind')),call(route,name,route.input),routed);
}
const arrowChildren=mapField(route,route.get(route.input,'children'),'kind');
const permittedArrows=route.op('or',[route.eq(route.get(route.get(route.input,'node'),'kind'),route.data('Call')),route.not(route.contains(arrowChildren,route.data('ArrowFunction')))],{},'Bool');
save('js_source_lower_node',route,req(route,permittedArrows,routed,'Function values are supported only as inline array callbacks.'));
// Generic postorder traversal: explicit frames, no recursive host compiler.
const w=new G(),ws=w.input,stack=w.get(ws,'stack'),top=w.item(stack,w.data(-1)),ast=w.get(top,'node'),index=w.get(top,'i'),values=w.get(top,'children');
const isText=w.eq(w.op('kind_of',[ast]),w.data('text'));
const walkKids=w.choose(isText,w.data([]),w.get(ast,'children'));
const done=w.not(w.lt(index,w.len(walkKids))),pop=slice(w,stack,0,-1);
const pushed=w.push(w.push(pop,w.rec({node:ast,i:w.calc('add',index,w.data(1)),children:values})),w.rec({node:w.item(walkKids,index),i:w.data(0),children:w.data([])}));
const lowered=w.choose(isText,result(w,{kind:w.data('text'),text:ast}),call(w,'js_source_lower_node',w.rec({node:w.rec({kind:w.get(ast,'kind'),children:w.choose(w.contains(w.data(['StringLiteral','JSXString']),w.get(ast,'kind')),w.get(ast,'children'),w.data([]))}),children:values})));
const parent=w.item(pop,w.data(-1));const resumed=w.push(slice(w,pop,0,-1),w.rec({node:w.get(parent,'node'),i:w.get(parent,'i'),children:w.push(w.get(parent,'children'),lowered)}));
const nextstack=w.choose(w.eq(w.len(pop),w.data(0)),w.data([]),resumed);
const walked=w.choose(done,w.rec({stack:nextstack,value:lowered}),w.rec({stack:pushed,value:w.get(ws,'value')}));
const cg=new G();const keep=cg.lt(cg.data(0),cg.len(cg.get(cg.input,'stack')));
const co=new G();const walk=co.op('while',[co.rec({stack:co.list(co.rec({node:co.input,i:co.data(0),children:co.data([])})),value:co.data(null)})],{guard:cg.finish(keep,'Bool'),body:w.finish(walked)});
save('js_source_lower_tree',co,co.get(co.get(walk,'value'),'program'));
const compile=new G();const parsed=call(compile,'javascript_read_source',compile.input);
const tree=req(compile,compile.bool(compile.get(parsed,'accepted')),compile.get(parsed,'tree'),'Source does not match the stored JavaScript/JSX grammar. No Python parser fallback.');
const loweredProgram=call(compile,'js_source_lower_tree',compile.item(tree,compile.data(0)));
const validation=call(compile,'js_source_validate_bindings',loweredProgram);
save('javascript_compile_source',compile,req(compile,compile.eq(compile.get(validation,'i'),compile.len(compile.get(loweredProgram,'code'))),loweredProgram,'Graph binding validation failed.'));
// Editable policy: prepare this compiler section when its current dependency closure is cold.
const warm=new G();const target=warm.data({section:'javascript_compile_source'});
const status=warm.op('act',[warm.input,target],{surface:'engine',action:'status'});
const prepared=warm.choose(warm.bool(warm.get(status,'warm')),status,warm.op('act',[status,target],{surface:'engine',action:'prepare'}));
save('javascript_warm_policy',warm,warm.rec({input:warm.input,warming:prepared}));
const release=new G();save('javascript_release_policy',release,release.op('act',[release.input,release.data({section:'javascript_compile_source'})],{surface:'engine',action:'release'}));
const run=new G();const ready=call(run,'javascript_warm_policy',run.input);
const program2=call(run,'javascript_compile_source',run.get(ready,'input','source'));
let checked=req(run,run.op('or',[run.not(run.bool(run.get(program2,'requires_input'))),run.bool(run.get(run.input,'has_input'))],{},'Bool'),program2,'Supply an input for this function. Appended function calls are not supported by this graph compiler yet.');
const execution=call(run,'js_execute',run.rec({program:checked,argument:run.get(run.input,'argument')}));
save('javascript_run_source',run,run.rec({execution,compiled_program:checked}));
for(const name of ['javascript_compile_source','js_source_lower_node'])suite[name].graph.cache_across_runs=true;
for(const [k,v] of Object.entries(suite))if(v.graph.nodes.length>500)throw new Error(k+' exceeds node limit: '+v.graph.nodes.length);
for(const name of ['javascript_read_source','javascript_compile_source','javascript_run_source'])if(suite[name])suite[name].graph.execution_budget=10000000;
fs.writeFileSync(new URL('../curriculum/source-compiler.json',import.meta.url),JSON.stringify(suite,null,2)+'\n');
console.log(Object.fromEntries(Object.entries(suite).map(([k,v])=>[k,v.graph.nodes.length])));
