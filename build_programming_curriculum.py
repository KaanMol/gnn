"""Author reusable program execution and example-driven selection as graphs."""
import json
from pathlib import Path
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description):
        suite[name]={'graph':g.finish(out,trace_mode='explicit',description=description),
                     'source':'Explicit programming lesson: '+description}
    def reject(g,message):
        return g.op('require',g.eq(g.data(0),g.data(1)),g.data(None),message=message)
    def dispatch(g,tag,options,default):
        out=default
        for name,value in reversed(list(options.items())):out=g.choose(g.eq(tag,g.data(name)),value,out)
        return out
    def kind(g,value,name):return g.eq(g.op('kind_of',value),g.data(name))
    def safe(g,value):
        return g.call('programming_safe_integer',value)
    def number(g,value):return g.call('programming_require_number',value)
    def truth(g,value):return g.boolean(g.call('js_to_boolean',value))
    undefined={'__js_type':'undefined'}
    uninitialized={'__js_type':'uninitialized'}

    g=G();env=g.get(g.input,'environment');name=g.get(g.input,'name')
    value=g.item(env,name)
    initialized=g.both(g.has(env,name),g.inverse(g.eq(value,g.data(uninitialized))))
    save('js_read_binding',g,g.op('require',initialized,value,message='ReferenceError: binding is not initialized (temporal dead zone).'),'Resolve a lowered lexical binding and reject reads before initialization.')

    g=G();value=g.input
    nullish=g.either(kind(g,value,'null'),g.eq(value,g.data(undefined)))
    save('js_is_nullish',g,g.datum(nullish),'Recognize null and the tagged undefined value without treating false, zero, or empty text as nullish.')
    g=G();value=g.input
    falsey=g.either(g.boolean(g.call('js_is_nullish',value)),
        g.either(g.eq(value,g.data(False)),g.either(g.eq(value,g.data(0)),g.eq(value,g.data('')))))
    save('js_to_boolean',g,g.datum(g.inverse(falsey)),'ECMAScript ToBoolean for the supported value domain: arrays including empty arrays are truthy; zero, false, empty strings, null and undefined are falsey. NaN and BigInt await their value models.')
    g=G();value=g.input
    typename=dispatch(g,g.op('kind_of',value),{'number':g.data('number'),'text':g.data('string'),
        'bool':g.data('boolean'),'null':g.data('object'),'list':g.data('object'),
        'record':g.op('require',g.eq(g.get(value,'__js_type'),g.data('object')),g.data('object'),message='Unsupported value tag.')},reject(g,'Unsupported JavaScript value type.'))
    save('js_typeof',g,g.choose(g.eq(value,g.data(undefined)),g.data('undefined'),typename),'Return JavaScript typeof names for supported values, including typeof null being object.')

    g=G();value=g.input
    inside=g.both(g.inverse(g.lt(value,g.data(-9007199254740991))),g.inverse(g.lt(g.data(9007199254740991),value)))
    inside=g.both(g.op('is_integer',g.num(value),kind='Bool'),inside)
    save('programming_safe_integer',g,g.op('require',inside,value,message='Result exceeds the safe-integer JavaScript subset.'),'Require an exact result within the supported safe-integer interval.')
    g=G();save('programming_require_number',g,g.op('require',kind(g,g.input,'number'),g.input,message='This operator requires a number; implicit coercion is not taught.'),'Require numeric operands rather than implicitly converting Boolean, null, or array values.')

    g=G();a=g.get(g.input,'left');b=g.get(g.input,'right');operator=g.get(g.input,'operator')
    x=number(g,a);y=number(g,b)
    same=g.both(g.eq(g.op('kind_of',a),g.op('kind_of',b)),g.eq(a,b))
    scalar=g.both(g.inverse(kind(g,a,'list')),g.inverse(kind(g,b,'list')))
    for value in (a,b):
        scalar=g.both(scalar,g.either(g.inverse(kind(g,value,'record')),g.eq(value,g.data(undefined))))
    eq=g.op('require',scalar,g.datum(same),message='Object/array reference equality is not supported in this subset.')
    ne=g.op('require',scalar,g.datum(g.inverse(same)),message='Object/array reference equality is not supported in this subset.')
    addition=g.choose(g.both(kind(g,a,'text'),kind(g,b,'text')),g.textcat(a,b),safe(g,g.calc('add',x,y)))
    out=dispatch(g,operator,{'+':addition,'-':safe(g,g.calc('subtract',x,y)),
        '*':safe(g,g.calc('multiply',x,y)),'<':g.datum(g.lt(x,y)),'>':g.datum(g.lt(y,x)),
        '<=':g.datum(g.inverse(g.lt(y,x))),'>=':g.datum(g.inverse(g.lt(x,y))),
        '===':eq,'!==':ne},reject(g,'Unknown taught operator.'))
    save('programming_binary',g,out,'Evaluate typed safe-integer arithmetic, order comparisons, and scalar strict equality without implicit coercion.')

    g=G();collection=g.get(g.input,'array');index=number(g,g.get(g.input,'index'))
    collection=g.op('require',kind(g,collection,'list'),collection,message='Indexing requires an array.')
    valid=g.both(g.inverse(g.lt(index,g.data(0))),g.lt(index,g.length(collection)))
    save('programming_index',g,g.op('require',valid,g.item(collection,index),message='Array index is out of bounds in this subset.'),'Read an array element after checking nonnegative in-range indexing.')

    g=G();x=number(g,g.get(g.input,'value'));method=g.get(g.input,'method')
    absolute=g.choose(g.lt(x,g.data(0)),g.calc('negate',x),x)
    sign=g.choose(g.lt(x,g.data(0)),g.data(-1),g.choose(g.eq(x,g.data(0)),g.data(0),g.data(1)))
    unary=dispatch(g,method,{'abs':absolute,'sign':sign,'floor':x,'ceil':x,'round':x,'trunc':x,'require_number':x},reject(g,'Unsupported taught Math method.'))
    save('js_math_unary',g,unary,'Math.abs/sign and integer-domain floor/ceil/round/trunc. Fractional numbers and signed-zero distinctions are outside this lesson.')
    g=G();x=number(g,g.get(g.input,'left'));y=number(g,g.get(g.input,'right'));method=g.get(g.input,'method')
    exponent=g.op('require',g.both(g.inverse(g.lt(y,g.data(0))),g.inverse(g.lt(g.data(32),y))),y,message='Math.pow currently requires an integer exponent from 0 to 32.')
    value=dispatch(g,method,{'min':g.choose(g.lt(x,y),x,y),'max':g.choose(g.lt(x,y),y,x),
        'pow':safe(g,g.calc('power',x,exponent))},reject(g,'Unsupported taught Math method.'))
    save('js_math_binary',g,value,'Evaluate pairwise min/max and bounded nonnegative integer powers using stored arithmetic procedures.')

    # Postfix expressions are evaluated by a general stack machine.
    guard=G();condition=guard.either(guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'tokens'))),
        guard.lt(guard.data(0),guard.length(guard.get(guard.input,'frames'))))
    body=G();s=body.input;stack=body.get(s,'stack');token=body.item(body.get(s,'tokens'),body.get(s,'i'));tag=body.get(token,'kind')
    top=body.item(stack,body.data(-1));left=body.item(stack,body.data(-2))
    pop1=body.op('slice',stack,stop=-1);pop2=body.op('slice',stack,stop=-2)
    binary=body.call('programming_binary',body.record(left=left,right=top,operator=body.get(token,'operator')))
    unary=dispatch(body,body.get(token,'operator'),{'-':safe(body,body.calc('negate',number(body,top))),
        '!':body.datum(body.inverse(truth(body,top))),
        'Boolean':body.call('js_to_boolean',top),'typeof':body.call('js_typeof',top),
        'require_array':body.op('require',kind(body,top,'list'),top,message='Array destructuring requires a supported array.'),
        'void':body.data(undefined)},reject(body,'Unknown unary operator.'))
    indexed=body.call('js_property_get',body.record(object=left,key=top))
    property_value=body.call('js_property_get',body.record(object=top,key=body.get(token,'key')))
    object_put=body.call('js_object_put',body.record(object=left,key=body.get(token,'key'),value=top))
    computed_put=body.call('js_object_put',body.record(object=body.item(stack,body.data(-3)),key=left,value=top))
    object_spread=body.call('js_object_spread',body.record(left=left,right=top))
    array_spread=body.op('require',body.both(kind(body,left,'list'),kind(body,top,'list')),
        body.op('concat',left,top),message='Array spread requires a supported array.')
    math_unary=body.call('js_math_unary',body.record(method=body.get(token,'method'),value=top))
    math_binary=body.call('js_math_binary',body.record(method=body.get(token,'method'),left=left,right=top))
    array=body.op('require',kind(body,top,'list'),top,message='length requires an array.')
    short=dispatch(body,body.get(token,'operator'),{
        '&&':body.datum(body.inverse(truth(body,top))),
        '||':body.call('js_to_boolean',top),
        '??':body.datum(body.inverse(body.boolean(body.call('js_is_nullish',top))))},reject(body,'Unknown logical operator.'))
    short=body.boolean(short)
    skip=body.choose(body.eq(tag,body.data('short_circuit')),short,
        body.choose(body.eq(tag,body.data('branch_false')),body.inverse(truth(body,top)),
                    body.eq(tag,body.data('jump')),kind='Bool'),kind='Bool')
    nexti=body.calc('add',body.get(s,'i'),body.data(1))
    nexti=body.choose(skip,body.calc('add',nexti,body.get(token,'skip')),nexti)
    nextstack=dispatch(body,tag,{
        'constant':body.append(stack,body.get(token,'value')),
        'variable':body.append(stack,body.call('js_read_binding',body.record(environment=body.get(s,'env'),name=body.get(token,'name')))),
        'binary':body.append(pop2,binary),'unary':body.append(pop1,unary),
        'array_append':body.append(pop2,body.append(left,top)),
        'array_spread':body.append(pop2,array_spread),'object_put':body.append(pop2,object_put),
        'object_spread':body.append(pop2,object_spread),'property':body.append(pop1,property_value),
        'object_computed_put':body.append(body.op('slice',stack,stop=-3),computed_put),
        'short_circuit':body.choose(short,stack,pop1),'branch_false':pop1,'jump':stack,
        'index':body.append(pop2,indexed),'length':body.append(pop1,body.length(array)),
        'math_unary':body.append(pop1,math_unary),'math_binary':body.append(pop2,math_binary)},reject(body,'Unknown expression instruction.'))
    updated=body.record(i=nexti,tokens=body.get(s,'tokens'),env=body.get(s,'env'),stack=nextstack,frames=body.get(s,'frames'))
    updated=body.choose(body.eq(tag,body.data('array_callback')),body.call('js_array_callback_start',s),updated)
    completed=body.inverse(body.lt(body.get(s,'i'),body.length(body.get(s,'tokens'))))
    updated=body.choose(completed,body.call('js_array_callback_resume',s),updated)
    g=G();loop=g.loop(g.record(i=g.data(0),tokens=g.get(g.input,'tokens'),env=g.get(g.input,'env'),stack=g.data([]),frames=g.data([])),guard.finish(condition,'Bool'),body.finish(updated))
    stack=g.get(loop,'stack');valid=g.eq(g.length(stack),g.data(1))
    save('programming_expression',g,g.op('require',valid,g.item(stack,g.data(0)),message='Invalid expression stack.'),'Read expression instructions, resolve variables, and evaluate with a stack of intermediate values.')

    logarg=G();logged=logarg.call('programming_expression',logarg.record(tokens=logarg.get(logarg.input,'item'),env=logarg.get(logarg.input,'context')))
    guard=G();s=guard.input;condition=guard.both(guard.inverse(guard.boolean(guard.get(s,'done'))),guard.lt(guard.get(s,'count'),guard.data(300)))
    body=G();s=body.input;pc=body.get(s,'pc');instruction=body.item(body.get(s,'code'),pc);op=body.get(instruction,'op');env=body.get(s,'env')
    value=body.call('programming_expression',body.record(tokens=body.get(instruction,'expression'),env=env))
    logline=body.map(body.get(instruction,'expressions'),logarg.finish(logged),env)
    logs=body.choose(body.eq(op,body.data('log')),body.append(body.get(s,'logs'),logline),body.get(s,'logs'))
    after=body.op('set_item',env,body.get(instruction,'name'),value)
    cleared=body.op('set_item',env,body.get(instruction,'name'),body.data(uninitialized))
    old=body.call('js_read_binding',body.record(environment=env,name=body.get(instruction,'name')))
    updated_binding=body.op('require',body.inverse(body.eq(old,body.data(uninitialized))),after,message='ReferenceError: binding is not initialized.')
    nextpc=body.calc('add',pc,body.data(1))
    def state(pc2,env2,done,value2):return body.record(pc=pc2,env=env2,done=body.data(done),value=value2)
    chosen=dispatch(body,op,{
        'assign':state(nextpc,after,False,body.data(None)),
        'update':state(nextpc,updated_binding,False,body.data(None)),
        'uninitialize':state(nextpc,cleared,False,body.data(None)),
        'branch':state(body.choose(truth(body,value),nextpc,body.get(instruction,'target')),env,False,body.data(None)),
        'jump':state(body.get(instruction,'target'),env,False,body.data(None)),
        'log':state(nextpc,env,False,body.data(None)),
        'return':state(nextpc,env,True,value)},reject(body,'Function reached its end without a supported explicit return.'))
    count=body.calc('add',body.get(s,'count'),body.data(1))
    step=body.record(step=count,instruction=pc,operation=op,variables=body.get(chosen,'env'),next_instruction=body.get(chosen,'pc'),value=body.get(chosen,'value'))
    updated=body.record(pc=body.get(chosen,'pc'),env=body.get(chosen,'env'),done=body.get(chosen,'done'),value=body.get(chosen,'value'),
        count=count,code=body.get(s,'code'),steps=body.append(body.get(s,'steps'),step),logs=logs)
    g=G();program=g.get(g.input,'program');env=g.op('set_item',g.data({}),g.get(program,'parameter'),g.get(g.input,'argument'))
    initial=g.record(pc=g.data(0),env=env,done=g.data(False),value=g.data(None),count=g.data(0),steps=g.data([]),logs=g.data([]),code=g.get(program,'code'))
    loop=g.loop(initial,guard.finish(condition,'Bool'),body.finish(updated))
    result=g.record(value=g.get(loop,'value'),steps=g.get(loop,'steps'),logs=g.get(loop,'logs'))
    save('programming_execute',g,g.op('require',g.boolean(g.get(loop,'done')),result,message='Program exceeded the 300-instruction lesson budget.'),'Execute assignments, branches, jumps and returns; retain state transitions and bound execution to 300 instructions.')
    g=G();save('js_execute',g,g.call('programming_execute',g.input),'Execute the program representation supplied by the JavaScript syntax adapter.')

    test=G();case=test.get(test.input,'item');candidate=test.get(test.input,'context')
    result=test.call('programming_execute',test.record(program=test.get(candidate,'program'),argument=test.get(case,'input')))
    actual=test.get(result,'value');expected=test.get(case,'expected')
    passed=test.both(test.eq(test.op('kind_of',actual),test.op('kind_of',expected)),test.eq(actual,expected))
    candidate=G();item=candidate.get(candidate.input,'item');tests=candidate.get(candidate.input,'context')
    flags=candidate.map(tests,test.finish(test.datum(passed)),item)
    allpassed=candidate.inverse(candidate.op('contains',flags,candidate.data(False),kind='Bool'))
    g=G();out=g.map(g.get(g.input,'candidates'),candidate.finish(allpassed,'Bool'),g.get(g.input,'tests'),filter=True)
    save('js_choose_program',g,out,'Select supplied candidate programs by executing every input/output example; passing examples is not proof of general correctness.')
    from javascript_lessons import CONCEPTS
    g=G();save('programming_overview',g,g.data([{'concept':name,'meaning':meaning,'related_procedure':procedure} for name,meaning,procedure in CONCEPTS]),'Explain general programming concepts and connect them to the executable lessons that use them.')
    from build_js_data_curriculum import build as data_lessons
    suite.update(data_lessons())
    return suite


if __name__=='__main__':
    target=Path(__file__).parent/'curriculum/programming.json'
    target.write_text(json.dumps(build(),indent=2)+'\n')
