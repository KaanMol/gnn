"""Generic goal search and learned use of memory/canvas interfaces."""
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description,kind='Data'):
        suite[name]={'graph':g.finish(out,kind,trace_mode='explicit',description=description),'source':'Foundational skill-system teaching: '+description}
    g=G(); save('plan_policy',g,g.data({'depth':12,'states':128}),'Bound breadth-first planning to 12 actions and 128 distinct states.')
    # Canonical sets use the already exposed collection-ordering primitive.
    wrap=G(); row=wrap.record(tag=wrap.input)
    unwrap=G(); tag=unwrap.get(unwrap.input,'tag')
    g=G(); sortedrows=g.op('sort',g.map(g.op('unique',g.input),wrap.finish(row)),key='tag')
    save('plan_tags',g,g.map(sortedrows,unwrap.finish(tag)),'Treat capability tags as a canonical set, so different action orders reaching the same state can be recognized.')
    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'items')))
    body=G(); s=body.input; i=body.get(s,'i'); items=body.get(s,'items'); item=body.item(items,i); key=body.item(item,body.get(s,'key')); seen=body.get(s,'seen'); fresh=body.inverse(body.op('contains',seen,key,kind='Bool'))
    out=body.record(i=body.calc('add',i,body.data(1)),items=items,key=body.get(s,'key'),seen=body.choose(fresh,body.append(seen,key),seen),result=body.choose(fresh,body.append(body.get(s,'result'),item),body.get(s,'result')))
    g=G(); loop=g.loop(g.record(i=g.data(0),items=g.get(g.input,'items'),key=g.get(g.input,'key'),seen=g.data([]),result=g.data([])),guard.finish(run,'Bool'),body.finish(out))
    save('records_unique_by',g,g.get(loop,'result'),'Keep the first record for each distinct selected field value.')
    action=G(); step=action.get(action.input,'item'); state=action.get(action.input,'context'); have=action.get(state,'have')
    applicable=action.inverse(action.nonempty(action.op('difference',action.get(step,'requires'),have)))
    after=action.call('plan_tags',action.op('concat',action.op('difference',have,action.get(step,'deletes')),action.get(step,'provides')))
    changed=action.inverse(action.eq(have,after)); child=action.record(have=after,plan=action.append(action.get(state,'plan'),action.get(step,'name')))
    children=action.choose(action.both(applicable,changed),action.op('data_list',child),action.data([]))
    guard=G(); s=guard.input; run=guard.both(guard.inverse(guard.boolean(guard.get(s,'found'))),guard.both(guard.lt(guard.get(s,'i'),guard.length(guard.get(s,'queue'))),guard.lt(guard.get(s,'i'),guard.get(s,'policy','states'))))
    body=G(); s=body.input; i=body.get(s,'i'); queue=body.get(s,'queue'); current=body.item(queue,i); wanted=body.get(s,'wanted')
    reached=body.inverse(body.nonempty(body.op('difference',wanted,body.get(current,'have'))))
    successors=body.op('flatten',body.map(body.get(s,'actions'),action.finish(children),current))
    expanded=body.call('records_unique_by',body.record(items=body.op('concat',queue,successors),key=body.data('have')))
    expand=body.both(body.inverse(reached),body.lt(body.length(body.get(current,'plan')),body.get(s,'policy','depth')))
    updated=body.record(i=body.calc('add',i,body.data(1)),queue=body.choose(expand,expanded,queue),wanted=wanted,actions=body.get(s,'actions'),policy=body.get(s,'policy'),found=body.datum(reached),plan=body.choose(reached,body.get(current,'plan'),body.get(s,'plan')))
    g=G(); initial=g.record(have=g.call('plan_tags',g.get(g.input,'have')),plan=g.data([]))
    loop=g.loop(g.record(i=g.data(0),queue=g.op('data_list',initial),wanted=g.get(g.input,'wanted'),actions=g.get(g.input,'actions'),policy=g.call('plan_policy',g.input),found=g.data(False),plan=g.data([])),guard.finish(run,'Bool'),body.finish(updated))
    save('plan_search',g,g.record(found=g.get(loop,'found'),plan=g.get(loop,'plan'),explored=g.get(loop,'i'),states=g.get(loop,'queue')),'Search action contracts breadth-first for a plan reaching the requested tags; return the explored states and report failure without inventing a capability.')
    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'plan')))
    body=G(); s=body.input; i=body.get(s,'i'); plan=body.get(s,'plan'); name=body.item(plan,i); value=body.get(s,'value')
    result=body.op('invoke',name,value)
    result=body.op('emit',result,body.record(procedure=name,input=value,result=result),label='execute_plan_step')
    updated=body.record(i=body.calc('add',i,body.data(1)),plan=plan,value=result)
    g=G(); loop=g.loop(g.record(i=g.data(0),plan=g.get(g.input,'plan'),value=g.get(g.input,'input')),guard.finish(run,'Bool'),body.finish(updated))
    save('plan_execute',g,g.get(loop,'value'),'Invoke each selected graph program in order, pass its result to the next, and keep step inputs and outcomes as evidence.')
    # These programs contain all usage knowledge; adapters only expose raw ports.
    g=G(); observed=g.op('observe',g.input,surface='workspace')
    save('workspace_observe',g,observed,'Observe which local memory namespaces and raw operations are exposed.')
    g=G(); result=g.op('act',g.input,g.input,surface='workspace',action='read')
    save('workspace_read',g,result,'Read a memory record by supplying its namespace and key to the workspace read operation.')
    g=G(); result=g.op('act',g.input,g.input,surface='workspace',action='write')
    save('workspace_write',g,result,'Revise memory by supplying namespace, key and replacement value; inspect the attributed before/after response.')
    g=G(); result=g.op('act',g.input,g.input,surface='workspace',action='keys')
    save('workspace_keys',g,result,'Ask the workspace port for the current keys of a named namespace.')
    g=G(); result=g.op('act',g.input,g.input,surface='workspace',action='delete')
    save('workspace_forget',g,result,'Remove a named active record through the workspace delete port; history is retained as evidence.')
    g=G(); moved=g.op('act',g.input,g.record(x=g.get(g.input,'x'),y=g.get(g.input,'y')),surface='canvas',action='move')
    clicked=g.op('act',moved,g.data({}),surface='canvas',action='click')
    typed=g.op('act',clicked,g.record(key=g.get(g.input,'key')),surface='canvas',action='key')
    checked=g.op('require',g.boolean(g.get(typed,'feedback','accepted')),typed,message='The canvas did not accept the taught input sequence.')
    save('canvas_type_at',g,checked,'To type at a point, move the pointer, click to focus, send a key, and check the returned input feedback.')
    return suite
