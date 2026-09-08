"""Author portable foundation lessons. Never imported by live execution."""
import json
from pathlib import Path
from graph_dsl import G


def build():
    suite = {}
    def save(name,g,out,description,kind='Data'):
        suite[name]={'graph':g.finish(out,kind,trace_mode='explicit',description=description),
                     'source':'Explicit foundational teaching: '+description}
    def var(name): return {'var':name}

    g=G(); isvar=g.choose(g.has(g.input,g.data('var')),g.eq(g.length(g.input),g.data(1)),g.eq(g.data(0),g.data(1)),kind='Bool')
    save('pattern_is_variable',g,isvar,'A record with exactly one var field denotes a named placeholder.','Bool')

    # Generic structural matching, with an explicit work stack and shared bindings.
    guard=G(); run=guard.both(guard.nonempty(guard.get(guard.input,'stack')),guard.boolean(guard.get(guard.input,'ok')))
    child=G(); k=child.get(child.input,'item'); ctx=child.get(child.input,'context')
    pair=child.record(p=child.item(child.get(ctx,'p'),k),v=child.item(child.get(ctx,'v'),k))
    body=G(); s=body.input; stack=body.get(s,'stack'); pair0=body.item(stack,body.data(-1)); p=body.get(pair0,'p'); v=body.get(pair0,'v'); bindings=body.get(s,'bindings')
    rest=body.op('slice',stack,stop=-1); isp=body.call('pattern_is_variable',p,kind='Bool'); name=body.get(p,'var')
    samekind=body.eq(body.op('kind_of',p),body.op('kind_of',v)); plist=body.eq(body.op('kind_of',p),body.data('list')); prec=body.eq(body.op('kind_of',p),body.data('record'))
    keys=body.choose(plist,body.op('indices',p),body.op('keys',p)); vkeys=body.choose(plist,body.op('indices',v),body.op('keys',v))
    shape=body.choose(samekind,body.both(body.eq(body.length(keys),body.length(vkeys)),body.eq(body.op('difference',keys,vkeys),body.data([]))),body.eq(body.data(0),body.data(1)),kind='Bool')
    container=body.either(plist,prec)
    structural=body.choose(container,shape,body.eq(p,v),kind='Bool')
    matched=body.choose(isp,body.choose(body.has(bindings,name),body.eq(body.item(bindings,name),v),body.eq(body.data(1),body.data(1)),kind='Bool'),structural,kind='Bool')
    newbindings=body.choose(isp,body.op('set_item',bindings,name,v),bindings)
    children=body.map(keys,child.finish(pair),pair0)
    newstack=body.choose(body.both(body.inverse(isp),body.both(container,matched)),body.op('concat',rest,body.op('reverse',children)),rest)
    updated=body.record(stack=newstack,bindings=body.choose(matched,newbindings,bindings),ok=body.datum(matched))
    g=G(); stack=g.op('data_list',g.record(p=g.get(g.input,'pattern'),v=g.get(g.input,'value')))
    loop=g.loop(g.record(stack=stack,bindings=g.get(g.input,'bindings'),ok=g.data(True)),guard.finish(run,'Bool'),body.finish(updated))
    save('pattern_match',g,g.record(matched=g.get(loop,'ok'),bindings=g.get(loop,'bindings')),'Match nested records/lists, require repeated placeholders to agree, and retain bindings; use an explicit stack.')

    # Traversal and path replacement are data algorithms too, not native tree helpers.
    guard=G(); run=guard.nonempty(guard.get(guard.input,'stack'))
    child=G(); k=child.get(child.input,'item'); ctx=child.get(child.input,'context')
    out=child.record(path=child.append(child.get(ctx,'path'),k),value=child.item(child.get(ctx,'value'),k))
    body=G(); s=body.input; stack=body.get(s,'stack'); entry=body.item(stack,body.data(-1)); value=body.get(entry,'value'); kind=body.op('kind_of',value)
    keys=body.choose(body.eq(kind,body.data('list')),body.op('indices',value),body.choose(body.eq(kind,body.data('record')),body.op('keys',value),body.data([])))
    children=body.map(keys,child.finish(out),entry)
    updated=body.record(stack=body.op('concat',body.op('slice',stack,stop=-1),body.op('reverse',children)),items=body.append(body.get(s,'items'),entry))
    g=G(); loop=g.loop(g.record(stack=g.op('data_list',g.record(path=g.data([]),value=g.input)),items=g.data([])),guard.finish(run,'Bool'),body.finish(updated))
    save('tree_nodes',g,g.get(loop,'items'),'Enumerate a JSON tree in preorder with explicit paths and a traversal stack.')

    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'path')))
    body=G(); s=body.input; i=body.get(s,'i'); path=body.get(s,'path'); key=body.item(path,i); value=body.get(s,'value')
    updated=body.record(i=body.calc('add',i,body.data(1)),path=path,value=body.item(value,key),parents=body.append(body.get(s,'parents'),body.record(value=value,key=key)))
    unwindguard=G(); run2=unwindguard.nonempty(unwindguard.get(unwindguard.input,'parents'))
    unwind=G(); s=unwind.input; parents=unwind.get(s,'parents'); entry=unwind.item(parents,unwind.data(-1))
    updated2=unwind.record(parents=unwind.op('slice',parents,stop=-1),value=unwind.op('set_item',unwind.get(entry,'value'),unwind.get(entry,'key'),unwind.get(s,'value')))
    g=G(); climbed=g.loop(g.record(i=g.data(0),path=g.get(g.input,'path'),value=g.get(g.input,'tree'),parents=g.data([])),guard.finish(run,'Bool'),body.finish(updated))
    final=g.loop(g.record(parents=g.get(climbed,'parents'),value=g.get(g.input,'value')),unwindguard.finish(run2,'Bool'),unwind.finish(updated2))
    save('tree_replace',g,g.get(final,'value'),'Follow a path, retain parent containers, then rebuild outward with the replacement.')

    filt=G(); test=filt.call('pattern_is_variable',filt.get(filt.input,'value'),kind='Bool')
    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'variables')))
    body=G(); s=body.input; i=body.get(s,'i'); variables=body.get(s,'variables'); entry=body.item(variables,i)
    replacement=body.item(body.get(s,'bindings'),body.get(entry,'value','var'))
    tree=body.call('tree_replace',body.record(tree=body.get(s,'tree'),path=body.get(entry,'path'),value=replacement))
    updated=body.record(i=body.calc('add',i,body.data(1)),variables=variables,bindings=body.get(s,'bindings'),tree=tree)
    g=G(); variables=g.map(g.call('tree_nodes',g.get(g.input,'template')),filt.finish(test,'Bool'),filter=True)
    loop=g.loop(g.record(i=g.data(0),variables=variables,bindings=g.get(g.input,'bindings'),tree=g.get(g.input,'template')),guard.finish(run,'Bool'),body.finish(updated))
    save('pattern_substitute',g,g.get(loop,'tree'),'Find named placeholders in a template and replace their paths with the supplied bindings.')

    # Join a conjunction of relational patterns against known facts.
    factbody=G(); ctx=factbody.get(factbody.input,'context'); fact=factbody.get(factbody.input,'item'); state=factbody.get(ctx,'state')
    matched=factbody.call('pattern_match',factbody.record(pattern=factbody.get(ctx,'pattern'),value=factbody.get(fact,'fact'),bindings=factbody.get(state,'bindings')))
    state2=factbody.record(bindings=factbody.get(matched,'bindings'),premises=factbody.append(factbody.get(state,'premises'),factbody.get(fact,'fact')))
    result=factbody.choose(factbody.boolean(factbody.get(matched,'matched')),factbody.op('data_list',state2),factbody.data([]))
    joinbody=G(); ctx=joinbody.get(joinbody.input,'context'); state=joinbody.get(joinbody.input,'item')
    joined=joinbody.op('flatten',joinbody.map(joinbody.get(ctx,'facts'),factbody.finish(result),joinbody.record(state=state,pattern=joinbody.get(ctx,'pattern'))))
    # A known relation can discard unrelated facts before structural matching.
    # Variable relation patterns retain the complete candidate set.
    candidate=G(); fact=candidate.get(candidate.input,'item','fact')
    head=candidate.choose(candidate.eq(candidate.op('kind_of',fact),candidate.data('list')),
        candidate.choose(candidate.eq(fact,candidate.data([])),candidate.data(None),candidate.item(fact,candidate.data(0))),candidate.data(None))
    eligible=candidate.eq(head,candidate.get(candidate.input,'context'))
    guard=G(); run=guard.both(guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'patterns'))),guard.nonempty(guard.get(guard.input,'states')))
    body=G(); s=body.input; i=body.get(s,'i'); patterns=body.get(s,'patterns'); facts=body.get(s,'facts')
    pattern=body.item(patterns,i)
    anchor=body.choose(body.eq(body.op('kind_of',pattern),body.data('list')),
        body.choose(body.eq(pattern,body.data([])),body.data(None),body.item(pattern,body.data(0))),body.data(None))
    selected=body.choose(body.eq(body.op('kind_of',anchor),body.data('text')),
        body.map(facts,candidate.finish(eligible,'Bool'),anchor,filter=True),facts)
    # Ground tuple fields can narrow the candidates as well as the relation.
    # This is only a prefilter; nested patterns and shared variables still go
    # through the same general structural matcher afterwards.
    for position in (1, 2):
        field=body.choose(body.eq(body.op('kind_of',pattern),body.data('list')),
            body.op('slice',pattern,start=position,stop=position+1),body.data([]))
        scalar=body.choose(body.eq(field,body.data([])),body.data(None),body.item(field,body.data(0)))
        constant=body.eq(body.op('kind_of',scalar),body.data('text'))
        matchfield=G(); f=matchfield.get(matchfield.input,'item','fact')
        match=matchfield.choose(matchfield.eq(matchfield.op('kind_of',f),matchfield.data('list')),
            matchfield.eq(matchfield.op('slice',f,start=position,stop=position+1),matchfield.get(matchfield.input,'context')),
            matchfield.eq(matchfield.data(0),matchfield.data(1)),kind='Bool')
        selected=body.choose(constant,body.map(selected,matchfield.finish(match,'Bool'),field,filter=True),selected)
    states=body.op('flatten',body.map(body.get(s,'states'),joinbody.finish(joined),body.record(facts=selected,pattern=pattern)))
    updated=body.record(i=body.calc('add',i,body.data(1)),patterns=patterns,facts=facts,states=states)
    g=G(); loop=g.loop(g.record(i=g.data(0),patterns=g.get(g.input,'patterns'),facts=g.get(g.input,'facts'),states=g.data([{'bindings':{},'premises':[]}])),guard.finish(run,'Bool'),body.finish(updated))
    save('horn_join',g,g.get(loop,'states'),'Narrow candidates by constant relation and tuple fields before structural matching; join premise patterns using shared bindings and retain each proof witness. Unbound fields never discard candidates.')

    body=G(); state=body.get(body.input,'item'); rule=body.get(body.input,'context')
    evidence=body.choose(body.has(rule,body.data('evidence')),body.get(rule,'evidence'),body.data([]))
    result=body.record(fact=body.call('pattern_substitute',body.record(template=body.get(rule,'then'),bindings=body.get(state,'bindings'))),source=body.get(rule,'source'),premises=body.op('concat',body.get(state,'premises'),evidence))
    g=G(); states=g.call('horn_join',g.record(patterns=g.get(g.input,'rule','when'),facts=g.get(g.input,'facts')))
    save('horn_apply',g,g.map(states,body.finish(result),g.get(g.input,'rule')),'Instantiate a rule conclusion for each matching conjunction, retaining the rule source and premise facts.')

    body=G(); result=body.call('horn_apply',body.record(rule=body.get(body.input,'item'),facts=body.get(body.input,'context')))
    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'candidates')))
    step=G(); s=step.input; i=step.get(s,'i'); candidates=step.get(s,'candidates'); candidate=step.item(candidates,i); known=step.get(s,'known'); fresh=step.inverse(step.op('contains',known,step.get(candidate,'fact'),kind='Bool'))
    updated=step.record(i=step.calc('add',i,step.data(1)),candidates=candidates,known=step.choose(fresh,step.append(known,step.get(candidate,'fact')),known),facts=step.choose(fresh,step.append(step.get(s,'facts'),candidate),step.get(s,'facts')))
    extract=G(); fact=extract.get(extract.input,'fact')
    g=G(); facts=g.get(g.input,'facts'); candidates=g.op('flatten',g.map(g.get(g.input,'rules'),body.finish(result),facts))
    loop=g.loop(g.record(i=g.data(0),candidates=candidates,known=g.map(facts,extract.finish(fact)),facts=facts),guard.finish(run,'Bool'),step.finish(updated))
    save('horn_step',g,g.get(loop,'facts'),'Apply all Horn rules once and add only new conclusions, retaining the first proof for each fact.')

    guard=G(); run=guard.boolean(guard.get(guard.input,'changed'))
    body=G(); s=body.input; facts=body.get(s,'facts'); rules=body.get(s,'rules'); nextfacts=body.call('horn_step',body.record(facts=facts,rules=rules))
    updated=body.record(facts=nextfacts,rules=rules,changed=body.datum(body.inverse(body.eq(body.length(facts),body.length(nextfacts)))))
    g=G(); loop=g.loop(g.record(facts=g.get(g.input,'facts'),rules=g.get(g.input,'rules'),changed=g.data(True)),guard.finish(run,'Bool'),body.finish(updated))
    save('horn_closure',g,g.get(loop,'facts'),'Repeat rule application until no new fact is derived; the runtime budget bounds unsuccessful convergence.')

    # Teach how the notebook's declarations map into general relational rules.
    sym=G(); rel=sym.get(sym.input,'relation'); clause=sym.record(when=sym.op('data_list',sym.op('data_list',rel,sym.data(var('x')),sym.data(var('y')))),then=sym.op('data_list',rel,sym.data(var('y')),sym.data(var('x'))),source=sym.get(sym.input,'source'))
    sub=G(); clause2=sub.record(when=sub.op('data_list',sub.op('data_list',sub.data('is'),sub.data(var('x')),sub.get(sub.input,'sub'))),then=sub.op('data_list',sub.data('is'),sub.data(var('x')),sub.get(sub.input,'parent')),source=sub.get(sub.input,'source'))
    condition=G(); idx=condition.get(condition.input,'item'); rule=condition.get(condition.input,'context'); item=condition.item(condition.get(rule,'conditions'),idx)
    rel=condition.item(item,condition.data(0)); obj=condition.item(item,condition.data(1)); target=condition.boolean(condition.item(item,condition.data(2)))
    witness=condition.record(var=condition.textcat(condition.data('target_'),condition.op('text',idx)))
    typed=condition.both(condition.inverse(condition.eq(rel,condition.data('is'))),target)
    direct=condition.op('data_list',rel,condition.data(var('x')),obj)
    two=condition.op('data_list',condition.op('data_list',rel,condition.data(var('x')),witness),condition.op('data_list',condition.data('is'),witness,obj))
    premises=condition.choose(typed,two,condition.op('data_list',direct))
    definition=G(); rule=definition.input
    when=definition.op('flatten',definition.map(definition.op('indices',definition.get(rule,'conditions')),condition.finish(premises),rule))
    clause3=definition.record(when=when,then=definition.op('data_list',definition.data('is'),definition.data(var('x')),definition.get(rule,'concept')),source=definition.get(rule,'source'))
    base=G(); item=base.get(base.input,'item'); rule=base.get(base.input,'context')
    generator=base.record(sub=base.get(rule,'concept'),parent=base.item(item,base.data(1)),source=base.get(rule,'source'))
    baseout=base.choose(base.eq(base.item(item,base.data(0)),base.data('is')),base.op('data_list',generator),base.data([]))
    bases=G(); generators=bases.op('flatten',bases.map(bases.get(bases.input,'conditions'),base.finish(baseout),bases.input))
    g=G(); definitions=g.get(g.input,'definitions'); generators=g.op('concat',g.get(g.input,'subtypes'),g.op('flatten',g.map(definitions,bases.finish(generators))))
    clauses=g.op('concat',g.map(g.get(g.input,'symmetric'),sym.finish(clause)),g.op('concat',g.map(generators,sub.finish(clause2)),g.map(definitions,definition.finish(clause3))))
    names=g.call('knowledge_name_rules',g.input)
    policy=g.call('knowledge_lookup_policy',g.input)
    clauses=g.op('concat',clauses,g.op('concat',names,g.get(policy,'rules')))
    clauses=g.op('concat',clauses,g.call('learning_active_rules',g.input))
    clauses=g.op('concat',clauses,g.call('meaning_rules',g.input))
    save('knowledge_rules',g,g.record(rules=clauses,name_rules=names,generators=generators),'Interpret symmetry, subtype inclusion, conjunctive definitions, declared concept names and teacher-supplied if/then rules as general Horn rules.')

    positive=G(); yes=positive.inverse(positive.boolean(positive.get(positive.input,'negative')))
    negative=G(); no=negative.boolean(negative.get(negative.input,'negative'))
    strip=G(); record=strip.record(fact=strip.get(strip.input,'fact'),source=strip.get(strip.input,'source'),premises=strip.data([]))
    entities=G(); fact=entities.get(entities.input,'fact'); result=entities.choose(entities.eq(entities.item(fact,entities.data(0)),entities.data('is')),entities.op('data_list',entities.item(fact,entities.data(1))),entities.op('slice',fact,start=1))
    concepts=G(); fact=concepts.get(concepts.input,'fact'); result2=concepts.choose(concepts.eq(concepts.item(fact,concepts.data(0)),concepts.data('is')),concepts.op('data_list',concepts.item(fact,concepts.data(2))),concepts.data([]))
    g=G(); assertions=g.call('meaning_assertions',g.get(g.input,'assertions')); compiled=g.call('knowledge_rules',g.input)
    facts=g.call('horn_closure',g.record(facts=g.map(g.map(assertions,positive.finish(yes,'Bool'),filter=True),strip.finish(record)),rules=g.get(compiled,'rules')))
    negatives=g.call('horn_closure',g.record(facts=g.map(g.map(assertions,negative.finish(no,'Bool'),filter=True),strip.finish(record)),rules=g.get(compiled,'name_rules')))
    save('knowledge_rebuild',g,g.record(facts=facts,negatives=negatives,entities=g.op('unique',g.op('flatten',g.map(assertions,entities.finish(result)))),concepts=g.op('unique',g.op('flatten',g.map(facts,concepts.finish(result2)))),generators=g.get(compiled,'generators')),'Rebuild current proofs solely from assertions and taught rule interpretation; retraction removes unsupported conclusions.')

    filt=G(); result=filt.eq(filt.get(filt.get(filt.input,'item'),'fact'),filt.get(filt.get(filt.input,'context'),'fact'))
    g=G(); pos=g.nonempty(g.map(g.get(g.input,'facts'),filt.finish(result,'Bool'),g.input,filter=True)); neg=g.nonempty(g.map(g.get(g.input,'negatives'),filt.finish(result,'Bool'),g.input,filter=True))
    answer=g.choose(g.both(pos,neg),g.data('conflict'),g.choose(g.inverse(g.either(pos,neg)),g.data('unknown'),g.choose(g.choose(g.boolean(g.get(g.input,'negative')),neg,pos,kind='Bool'),g.data('yes'),g.data('no'))))
    save('knowledge_query',g,answer,'Answer with four evidence states: supported, refuted, unknown, or conflicting; negated questions invert support.')

    extract=G(); value=extract.get(extract.input,'fact')
    candidate=G(); f=candidate.get(candidate.get(candidate.input,'item'),'fact'); ctx=candidate.get(candidate.input,'context'); concept=candidate.get(ctx,'concept')
    member=candidate.op('data_list',candidate.data('is'),candidate.item(f,candidate.data(1)),concept)
    typeok=candidate.choose(candidate.eq(concept,candidate.data('')),candidate.eq(candidate.data(1),candidate.data(1)),candidate.op('contains',candidate.get(ctx,'positive'),member,kind='Bool'),kind='Bool')
    matched=candidate.both(candidate.both(candidate.eq(candidate.item(f,candidate.data(0)),candidate.get(ctx,'relation')),candidate.eq(candidate.item(f,candidate.data(2)),candidate.get(ctx,'object'))),typeok)
    conflict=candidate.either(candidate.op('contains',candidate.get(ctx,'negative'),f,kind='Bool'),candidate.both(candidate.inverse(candidate.eq(concept,candidate.data(''))),candidate.op('contains',candidate.get(ctx,'negative'),member,kind='Bool')))
    result=candidate.record(fact=f,matched=candidate.datum(matched),conflict=candidate.datum(conflict))
    yesfilter=G(); yes=yesfilter.both(yesfilter.boolean(yesfilter.get(yesfilter.input,'matched')),yesfilter.inverse(yesfilter.boolean(yesfilter.get(yesfilter.input,'conflict'))))
    nofilter=G(); no=nofilter.both(nofilter.boolean(nofilter.get(nofilter.input,'matched')),nofilter.boolean(nofilter.get(nofilter.input,'conflict')))
    g=G(); ctx=g.record(relation=g.get(g.input,'relation'),object=g.get(g.input,'object'),concept=g.get(g.input,'concept'),positive=g.map(g.get(g.input,'facts'),extract.finish(value)),negative=g.map(g.get(g.input,'negatives'),extract.finish(value)))
    candidates=g.map(g.get(g.input,'facts'),candidate.finish(result),ctx)
    save('knowledge_find',g,g.record(matches=g.map(g.map(candidates,yesfilter.finish(yes,'Bool'),filter=True),extract.finish(value)),conflicts=g.map(g.map(candidates,nofilter.finish(no,'Bool'),filter=True),extract.finish(value))),'Find incoming relationships and exclude contradictory evidence, including contradictory requested type membership.')

    # Generic selection for entity descriptions.
    filt=G(); f=filt.get(filt.get(filt.input,'item'),'fact'); ctx=filt.get(filt.input,'context')
    yes=filt.both(filt.eq(filt.item(f,filt.data(1)),filt.get(ctx,'subject')),filt.either(filt.eq(filt.get(ctx,'relation'),filt.data('')),filt.eq(filt.item(f,filt.data(0)),filt.get(ctx,'relation'))))
    g=G(); save('knowledge_describe',g,g.record(facts=g.map(g.get(g.input,'facts'),filt.finish(yes,'Bool'),g.input,filter=True),negatives=g.map(g.get(g.input,'negatives'),filt.finish(yes,'Bool'),g.input,filter=True)),'Select facts and negations about a subject with an optional relation filter.')

    # Counts and inclusive sequences use the same executable representation.
    guard=G(); run=guard.inverse(guard.eq(guard.get(guard.input,'current'),guard.get(guard.input,'stop')))
    body=G(); s=body.input; n=body.get(s,'current'); out=body.record(current=body.calc('add',n,body.get(s,'step')),stop=body.get(s,'stop'),step=body.get(s,'step'),values=body.append(body.get(s,'values'),n))
    g=G(); a=g.get(g.input,'start'); b=g.get(g.input,'end'); step=g.choose(g.lt(b,a),g.data(-1),g.data(1))
    loop=g.loop(g.record(current=a,stop=g.calc('add',b,step),step=step,values=g.data([])),guard.finish(run,'Bool'),body.finish(out))
    save('count_sequence',g,g.get(loop,'values'),'Start at the first integer and repeatedly add one or minus one until the inclusive endpoint is reached.')
    g=G(); save('count_items',g,g.length(g.input),'Count a collection using its length.')

    edge=G(); record=edge.record(fact=edge.op('concat',edge.data(['edge']),edge.input),source=edge.data('Declared inclusion'),premises=edge.data([]))
    reflexive=G(); record2=reflexive.record(fact=reflexive.op('data_list',reflexive.data('edge'),reflexive.input,reflexive.input),source=reflexive.data('Identity'),premises=reflexive.data([]))
    extract=G(); pair=extract.op('slice',extract.get(extract.input,'fact'),start=1)
    g=G(); facts=g.op('concat',g.map(g.get(g.input,'edges'),edge.finish(record)),g.map(g.get(g.input,'objects'),reflexive.finish(record2)))
    closed=g.call('horn_closure',g.record(facts=facts,rules=g.data([{'when':[['edge',var('a'),var('b')],['edge',var('b'),var('c')]],'then':['edge',var('a'),var('c')],'source':'Transitivity'}])))
    save('relation_closure',g,g.map(closed,extract.finish(pair)),'Supply identity arrows and repeatedly compose matching inclusion edges using the taught general rule engine.')
    from build_world_curriculum import build as world
    suite.update(world())
    from build_rewrite_curriculum import build as rewriting
    suite.update(rewriting())
    from build_skill_curriculum import build as skills
    suite.update(skills())
    from build_date_curriculum import build as calendar
    suite.update(calendar())
    from build_memory_curriculum import build as memory
    suite.update(memory())
    from build_lookup_curriculum import build as lookup
    suite.update(lookup())
    for entry in suite.values():
        entry['graph']['internal'] = True
    return suite


if __name__=='__main__':
    target=Path(__file__).parent/'curriculum/foundation.json'
    target.write_text(json.dumps(build(),indent=2)+'\n')
    print(target)
