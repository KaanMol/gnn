"""Graph-authored plain-data objects and explicit array callback continuations.

There is no native callback evaluator. A continuation switches the existing
expression machine's token stream and environment, then restores its caller.
"""
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description):
        suite[name]={'graph':g.finish(out,trace_mode='explicit',description=description),
                     'source':'Explicit JavaScript data lesson: '+description}
    def require(g,ok,value,message):return g.op('require',ok,value,message=message)
    def kind(g,value,name):return g.eq(g.op('kind_of',value),g.data(name))
    def state(g,i,tokens,env,stack,frames):return g.record(i=i,tokens=tokens,env=env,stack=stack,frames=frames)
    def fields(g,value,keys):return {key:g.get(value,key) for key in keys.split()}
    def dispatch(g,tag,options,default):
        out=default
        for name,value in reversed(list(options.items())):out=g.choose(g.eq(tag,g.data(name)),value,out)
        return out
    undefined={'__js_type':'undefined'}

    g=G();v=g.input
    tagged=g.choose(g.has(v,g.data('__js_type')),g.eq(g.get(v,'__js_type'),g.data('object')),g.eq(g.data(0),g.data(1)),kind='Bool')
    props=require(g,tagged,g.get(v,'properties'),'Property operation requires a supported plain object.')
    save('js_object_properties',g,props,'Unwrap supported own data properties; tagged objects cannot be confused with undefined.')

    g=G();props=g.call('js_object_properties',g.get(g.input,'object'));key=g.get(g.input,'key')
    key=g.choose(kind(g,key,'number'),g.op('text',g.call('programming_safe_integer',key)),key)
    key=require(g,kind(g,key,'text'),key,'Property keys require strings or safe integers.')
    inherited=g.op('contains',g.data(['__proto__','constructor','toString','toLocaleString','valueOf','hasOwnProperty',
        'isPrototypeOf','propertyIsEnumerable','__defineGetter__','__defineSetter__','__lookupGetter__','__lookupSetter__']),key,kind='Bool')
    missing=require(g,g.inverse(inherited),g.data(undefined),'Inherited Object.prototype properties are not implemented.')
    save('js_object_get',g,g.choose(g.has(props,key),g.item(props,key),missing),'Read own data properties; absent own names return undefined, while unimplemented prototype lookups are rejected.')

    g=G();props=g.call('js_object_properties',g.get(g.input,'object'))
    key=g.get(g.input,'key')
    key=g.choose(kind(g,key,'number'),g.op('text',g.call('programming_safe_integer',key)),key)
    key=require(g,kind(g,key,'text'),key,'Computed property keys require strings or safe integers; general coercion is not implemented.')
    updated=g.op('set_item',props,key,g.get(g.input,'value'))
    save('js_object_put',g,g.record(__js_type=g.data('object'),properties=updated),'Build a new plain object value with an added or replaced own data property.')

    guard=G();ok=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'keys')))
    b=G();s=b.input;key=b.item(b.get(s,'keys'),b.get(s,'i'))
    copied=b.op('set_item',b.get(s,'target'),key,b.item(b.get(s,'source'),key))
    step=b.record(i=b.calc('add',b.get(s,'i'),b.data(1)),keys=b.get(s,'keys'),source=b.get(s,'source'),target=copied)
    g=G();left=g.call('js_object_properties',g.get(g.input,'left'));right=g.get(g.input,'right')
    source=g.choose(g.boolean(g.call('js_is_nullish',right)),g.data({}),g.call('js_object_properties',right))
    loop=g.loop(g.record(i=g.data(0),keys=g.op('keys',source),source=source,target=left),guard.finish(ok,'Bool'),b.finish(step))
    save('js_object_spread',g,g.record(__js_type=g.data('object'),properties=g.get(loop,'target')),'Copy supported own data properties in spread order, ignoring null/undefined and preserving the source.')

    g=G();v=g.get(g.input,'object');key=g.get(g.input,'key')
    arrayvalue=g.choose(g.eq(key,g.data('length')),g.length(v),g.call('programming_index',g.record(array=v,index=key)))
    save('js_property_get',g,g.choose(kind(g,v,'list'),arrayvalue,g.call('js_object_get',g.input)),'Read supported array or plain-object properties without a native JavaScript runtime.')

    # Construct callback bindings over the caller's current lexical values.
    guard=G();ok=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'parameters')))
    b=G();s=b.input;i=b.get(s,'i');args=b.get(s,'arguments')
    value=b.choose(b.lt(i,b.length(args)),b.item(args,i),b.data(undefined))
    env=b.op('set_item',b.get(s,'env'),b.item(b.get(s,'parameters'),i),value)
    step=b.record(i=b.calc('add',i,b.data(1)),parameters=b.get(s,'parameters'),arguments=args,env=env)
    g=G();f=g.input;array=g.get(f,'array');i=g.get(f,'index');value=g.item(array,i)
    ordinary=g.op('data_list',value,i,array)
    reduction=g.op('data_list',g.get(f,'result'),value,i,array)
    args=g.choose(g.eq(g.get(f,'method'),g.data('reduce')),reduction,ordinary)
    initial=g.record(i=g.data(0),parameters=g.get(f,'callback','parameters'),arguments=args,env=g.get(f,'env'))
    loop=g.loop(initial,guard.finish(ok,'Bool'),b.finish(step))
    save('js_callback_environment',g,g.get(loop,'env'),'Bind callback item/index/array or accumulator/item/index/array in an isolated expression environment.')

    g=G();s=g.input;stack=g.get(s,'stack');token=g.item(g.get(s,'tokens'),g.get(s,'i'))
    method=g.get(token,'method');reduce=g.eq(method,g.data('reduce'))
    top=g.item(stack,g.data(-1));left=g.item(stack,g.data(-2))
    array=g.choose(reduce,left,top)
    array=require(g,kind(g,array,'list'),array,'Array callbacks require a dense array.')
    array=require(g,g.inverse(g.lt(g.data(64),g.length(array))),array,'Array callbacks accept at most 64 elements.')
    result=dispatch(g,method,{'reduce':top,'find':g.data(undefined),'findIndex':g.data(-1),
        'some':g.data(False),'every':g.data(True)},g.data([]))
    rest=g.choose(reduce,g.op('slice',stack,stop=-2),g.op('slice',stack,stop=-1))
    nexti=g.calc('add',g.get(s,'i'),g.data(1))
    frame=g.record(i=nexti,tokens=g.get(s,'tokens'),env=g.get(s,'env'),stack=rest,
        method=method,array=array,index=g.data(0),result=result,callback=g.get(token,'callback'))
    frames=g.get(s,'frames')
    frames=require(g,g.lt(g.length(frames),g.data(8)),g.append(frames,frame),'Array callback nesting exceeds eight frames.')
    started=state(g,g.data(0),g.get(token,'callback','tokens'),g.call('js_callback_environment',frame),g.data([]),frames)
    empty=state(g,nexti,g.get(s,'tokens'),g.get(s,'env'),g.append(rest,result),g.get(s,'frames'))
    save('js_array_callback_start',g,g.choose(g.eq(g.length(array),g.data(0)),empty,started),'Start a supported array callback with an explicit continuation and method-specific empty result; empty arrays never evaluate callback bodies.')

    g=G();s=g.input;frames=g.get(s,'frames');f=g.item(frames,g.data(-1));stack=g.get(s,'stack')
    value=require(g,g.eq(g.length(stack),g.data(1)),g.item(stack,g.data(0)),'Invalid callback expression stack.')
    method=g.get(f,'method');oldresult=g.get(f,'result');i=g.get(f,'index');array=g.get(f,'array')
    filtered=g.choose(g.boolean(g.call('js_to_boolean',value)),g.append(oldresult,g.item(array,i)),oldresult)
    truth=g.boolean(g.call('js_to_boolean',value))
    result=dispatch(g,method,{'map':g.append(oldresult,value),'filter':filtered,
        'find':g.choose(truth,g.item(array,i),oldresult),'findIndex':g.choose(truth,i,oldresult),
        'some':g.datum(truth),'every':g.datum(truth)},value)
    stop=dispatch(g,method,{'find':g.datum(truth),'findIndex':g.datum(truth),
        'some':g.datum(truth),'every':g.datum(g.inverse(truth))},g.data(False))
    nextindex=g.calc('add',i,g.data(1))
    updatedframe=g.record(**fields(g,f,'i tokens env stack method array callback'),index=nextindex,result=result)
    rest=g.op('slice',frames,stop=-1)
    continued=state(g,g.data(0),g.get(f,'callback','tokens'),g.call('js_callback_environment',updatedframe),g.data([]),g.append(rest,updatedframe))
    finished=state(g,g.get(f,'i'),g.get(f,'tokens'),g.get(f,'env'),g.append(g.get(f,'stack'),result),rest)
    more=g.both(g.inverse(g.boolean(stop)),g.lt(nextindex,g.length(array)))
    save('js_array_callback_resume',g,g.choose(more,continued,finished),'Collect callback results and short-circuit find/findIndex/some/every at the decisive element; restore the enclosing expression through the shared continuation stack.')
    return suite
