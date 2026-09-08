"""Symbolic rewriting as taught data: interpretation, matching, traversal, control."""
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description,kind='Data'):
        suite[name]={'graph':g.finish(out,kind,trace_mode='explicit',description=description),'source':'Foundational symbolic lesson: '+description}
    g=G(); islist=g.eq(g.op('kind_of',g.input),g.data('list'))
    term=g.choose(islist,g.choose(g.nonempty(g.input),g.op('contains',g.data(['number','symbol','negate','+','-','*','/','^','=']),g.item(g.input,g.data(0)),kind='Bool'),g.eq(g.data(0),g.data(1)),kind='Bool'),g.eq(g.data(0),g.data(1)),kind='Bool')
    save('math_is_term',g,term,'Interpret these list tags as symbolic syntax nodes.','Bool')
    filt=G(); yes=filt.call('math_is_term',filt.get(filt.input,'value'),kind='Bool')
    g=G(); save('math_tree_terms',g,g.map(g.call('tree_nodes',g.input),filt.finish(yes,'Bool'),filter=True),'Read syntax nodes in preorder using the general taught tree traversal.')
    filt=G(); value=filt.get(filt.input,'value'); yes=filt.eq(filt.item(value,filt.data(0)),filt.data('symbol'))
    extract=G(); name=extract.get(extract.input,'value',1)
    g=G(); variables=g.map(g.call('math_tree_terms',g.input),filt.finish(yes,'Bool'),filter=True)
    save('math_symbols',g,g.op('unique',g.map(variables,extract.finish(name))),'Extract distinct names from symbolic syntax nodes.')

    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'variables')))
    body=G(); s=body.input; i=body.get(s,'i'); variables=body.get(s,'variables'); entry=body.item(variables,i)
    tree=body.call('tree_replace',body.record(tree=body.get(s,'tree'),path=body.get(entry,'path'),value=body.record(var=body.get(entry,'value',1))))
    updated=body.record(tree=tree,variables=variables,i=body.calc('add',i,body.data(1)))
    g=G(); variables=g.map(g.call('math_tree_terms',g.input),filt.finish(yes,'Bool'),filter=True)
    loop=g.loop(g.record(tree=g.input,variables=variables,i=g.data(0)),guard.finish(run,'Bool'),body.finish(updated))
    save('math_pattern',g,g.get(loop,'tree'),'In a teacher-supplied rewrite rule, each symbolic name is a placeholder for a whole expression.')

    g=G(); lhs=g.get(g.input,'left'); rhs=g.get(g.input,'right')
    checked=g.op('require',g.inverse(g.eq(g.item(lhs,g.data(0)),g.data('symbol'))),g.input,message='Give the rule a structured left side, such as x + 0, rather than matching everything.')
    checked=g.op('require',g.inverse(g.nonempty(g.op('difference',g.call('math_symbols',rhs),g.call('math_symbols',lhs)))),checked,message='Every placeholder on the right must appear on the left.')
    checked=g.op('require',g.eq(g.datum(g.eq(g.item(lhs,g.data(0)),g.data('='))),g.datum(g.eq(g.item(rhs,g.data(0)),g.data('=')))),checked,message='An equation lesson must transform one equation into another equation.')
    checked=g.op('require',g.inverse(g.eq(lhs,rhs)),checked,message='That rule would leave the expression unchanged.')
    save('math_rule_check',g,g.record(left=g.call('math_pattern',g.get(checked,'left')),right=g.call('math_pattern',g.get(checked,'right'))),'Check placeholder scope and equation shape before storing a rewrite pattern.')

    g=G(); op=g.item(g.input,g.data(0)); children=g.op('slice',g.input,start=1)
    number=G(); child=number.input; yes=number.choose(number.call('math_is_term',child,kind='Bool'),number.eq(number.item(child,number.data(0)),number.data('number')),number.eq(number.data(0),number.data(1)),kind='Bool')
    numeric=g.eq(g.length(g.map(children,number.finish(yes,'Bool'),filter=True)),g.length(children))
    allowed=g.both(g.op('contains',g.data(['+','-','*','/','^','negate']),op,kind='Bool'),numeric)
    a=g.get(g.input,1,1); b=g.get(g.input,2,1)
    result=g.data(0)
    for symbol,operation in reversed([('+','add'),('-','subtract'),('*','multiply'),('/','divide'),('^','power'),('negate','negate')]):
        value=g.calc(operation,a,*([] if symbol=='negate' else [b]))
        result=g.choose(g.eq(op,g.data(symbol)),value,result)
    value=g.op('data_list',g.data('number'),g.op('text',result))
    save('math_numeric_step',g,g.choose(allowed,g.record(changed=g.data(True),value=value,rule=g.data('arithmetic evaluation')),g.record(changed=g.data(False),value=g.input,rule=g.data(''))),'Evaluate a fully numeric arithmetic node using taught operator meanings and the runtime arithmetic primitives.')

    guard=G(); run=guard.both(guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'rules'))),guard.inverse(guard.boolean(guard.get(guard.input,'result','changed'))))
    body=G(); s=body.input; i=body.get(s,'i'); rules=body.get(s,'rules'); rule=body.item(rules,i); term=body.get(s,'term')
    match=body.call('pattern_match',body.record(pattern=body.get(rule,'left'),value=term,bindings=body.data({})))
    replacement=body.call('pattern_substitute',body.record(template=body.get(rule,'right'),bindings=body.get(match,'bindings')))
    changed=body.inverse(body.eq(term,replacement)); result=body.choose(body.boolean(body.get(match,'matched')),body.record(changed=body.datum(changed),value=replacement,rule=body.get(rule,'name')),body.get(s,'result'))
    updated=body.record(i=body.calc('add',i,body.data(1)),rules=rules,term=term,result=result)
    g=G(); term=g.get(g.input,'term'); initial=g.call('math_numeric_step',term)
    loop=g.loop(g.record(i=g.data(0),rules=g.get(g.input,'rules'),term=term,result=initial),guard.finish(run,'Bool'),body.finish(updated))
    save('math_rewrite_at',g,g.get(loop,'result'),'Try numeric evaluation, then the taught rewrite patterns in order at one syntax node.')

    guard=G(); run=guard.both(guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'terms'))),guard.inverse(guard.boolean(guard.get(guard.input,'result','changed'))))
    body=G(); s=body.input; i=body.get(s,'i'); terms=body.get(s,'terms'); entry=body.item(terms,i); tree=body.get(s,'tree'); rules=body.get(s,'rules')
    result=body.call('math_rewrite_at',body.record(term=body.get(entry,'value'),rules=rules))
    replacement=body.call('tree_replace',body.record(tree=tree,path=body.get(entry,'path'),value=body.get(result,'value')))
    updated=body.record(i=body.calc('add',i,body.data(1)),terms=terms,tree=tree,rules=rules,result=body.record(changed=body.get(result,'changed'),value=body.choose(body.boolean(body.get(result,'changed')),replacement,tree),rule=body.get(result,'rule')))
    g=G(); tree=g.get(g.input,'tree'); initial=g.record(changed=g.data(False),value=tree,rule=g.data(''))
    loop=g.loop(g.record(i=g.data(0),terms=g.call('math_tree_terms',tree),tree=tree,rules=g.get(g.input,'rules'),result=initial),guard.finish(run,'Bool'),body.finish(updated))
    save('math_rewrite_once',g,g.get(loop,'result'),'Find the first applicable rewrite in preorder and rebuild the surrounding expression through the taught path-replacement method.')

    g=G(); save('math_rewrite_policy',g,g.data({'steps':40,'nodes':1000}),'Stop after 40 transformations or a thousand syntax nodes; repeated expressions are detected separately.')
    guard=G(); run=guard.both(guard.eq(guard.get(guard.input,'status'),guard.data('running')),guard.lt(guard.get(guard.input,'i'),guard.get(guard.input,'policy','steps')))
    body=G(); s=body.input; tree=body.get(s,'tree'); rules=body.get(s,'rules'); result=body.call('math_rewrite_once',body.record(tree=tree,rules=rules)); value=body.get(result,'value'); seen=body.get(s,'seen')
    repeated=body.op('contains',seen,value,kind='Bool'); too_big=body.lt(body.get(s,'policy','nodes'),body.length(body.call('math_tree_terms',value)))
    status=body.choose(body.inverse(body.boolean(body.get(result,'changed'))),body.data('no_rule'),body.choose(repeated,body.data('repeat'),body.choose(too_big,body.data('size_limit'),body.data('running'))))
    accepted=body.eq(status,body.data('running'))
    trace=body.choose(accepted,body.append(body.get(s,'trace'),body.record(before=tree,after=value,rule=body.get(result,'rule'))),body.get(s,'trace'))
    updated=body.record(i=body.calc('add',body.get(s,'i'),body.data(1)),tree=body.choose(accepted,value,tree),rules=rules,seen=body.choose(accepted,body.append(seen,value),seen),trace=trace,status=status,policy=body.get(s,'policy'))
    g=G(); tree=g.get(g.input,'tree'); policy=g.call('math_rewrite_policy',g.input)
    loop=g.loop(g.record(i=g.data(0),tree=tree,rules=g.get(g.input,'rules'),seen=g.op('data_list',tree),trace=g.data([]),status=g.data('running'),policy=policy),guard.finish(run,'Bool'),body.finish(updated))
    value=g.get(loop,'tree'); iseq=g.eq(g.item(value,g.data(0)),g.data('=')); lhs=g.item(value,g.data(1)); rhs=g.item(value,g.data(2))
    isolated=g.choose(iseq,g.choose(g.eq(g.item(lhs,g.data(0)),g.data('symbol')),g.inverse(g.op('contains',g.call('math_symbols',rhs),g.item(lhs,g.data(1)),kind='Bool')),g.eq(g.data(0),g.data(1)),kind='Bool'),g.eq(g.data(0),g.data(1)),kind='Bool')
    save('math_rewrite',g,g.record(expression=value,trace=g.get(loop,'trace'),status=g.choose(g.eq(g.get(loop,'status'),g.data('running')),g.data('step_limit'),g.get(loop,'status')),isolated=g.datum(isolated)),'Repeatedly apply taught symbolic transformations; detect cycles and limits and identify an isolated variable without assuming the lessons are true.')
    return suite
