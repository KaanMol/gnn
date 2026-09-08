"""Teacher-authored observation learning methods, emitted as graph programs."""
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description,kind='Data'):
        suite[name]={'graph':g.finish(out,kind,trace_mode='explicit',description=description),'source':'Foundational world-learning lesson: '+description}
    condition=G(); pair=condition.get(condition.input,'item'); features=condition.get(condition.input,'context'); key=condition.item(pair,condition.data(0))
    match=condition.choose(condition.has(features,key),condition.eq(condition.item(features,key),condition.item(pair,condition.data(1))),condition.eq(condition.data(0),condition.data(1)),kind='Bool')
    mismatch=condition.inverse(match)
    g=G(); hypothesis=g.get(g.input,'hypothesis'); features=g.get(g.input,'features')
    allmatch=g.inverse(g.nonempty(g.map(hypothesis,condition.finish(mismatch,'Bool'),features,filter=True)))
    yes=g.choose(g.eq(hypothesis,g.data(None)),g.eq(g.data(0),g.data(1)),allmatch,kind='Bool')
    save('world_matches',g,yes,'A conjunction predicts success when every feature condition matches; null predicts failure and an empty conjunction predicts success.','Bool')

    f=G(); key=f.get(f.input,'item'); features=f.get(f.input,'context'); pair=f.op('data_list',key,f.item(features,key))
    obj=G(); key=obj.get(obj.input,'item'); observations=obj.get(obj.input,'context'); features=obj.item(observations,key)
    pairs=obj.map(obj.op('keys',features),f.finish(pair),features)
    one=G(); single=one.op('data_list',one.input)
    two=G(); j=two.get(two.input,'item'); ctx=two.get(two.input,'context'); i=two.get(ctx,'i'); features=two.get(ctx,'features')
    pair=two.op('data_list',two.item(features,i),two.item(features,j))
    selected=two.choose(two.lt(i,j),two.op('data_list',pair),two.data([]))
    outer=G(); i=outer.get(outer.input,'item'); features=outer.get(outer.input,'context'); result=outer.op('flatten',outer.map(outer.op('indices',features),two.finish(selected),outer.record(i=i,features=features)))
    g=G(); features=g.op('unique',g.op('flatten',g.map(g.op('keys',g.input),obj.finish(pairs),g.input)))
    pairs=g.op('flatten',g.map(g.op('indices',features),outer.finish(result),features))
    save('world_hypothesis_space',g,g.op('concat',g.data([None,[]]),g.op('concat',g.map(features,one.finish(single)),pairs)),'Construct a finite hypothesis space from observed features: constant predictions, single conditions and pairs of conditions.')

    filt=G(); i=filt.get(filt.input,'item'); ctx=filt.get(filt.input,'context'); event=filt.item(filt.get(ctx,'episodes'),i)
    yes=filt.both(filt.inverse(filt.lt(i,filt.get(ctx,'start'))),filt.eq(filt.get(event,'action'),filt.get(ctx,'action')))
    read=G(); event=read.item(read.get(read.input,'context'),read.get(read.input,'item'))
    g=G(); indices=g.map(g.op('indices',g.get(g.input,'episodes')),filt.finish(yes,'Bool'),g.input,filter=True)
    save('world_evidence',g,g.map(indices,read.finish(event),g.get(g.input,'episodes')),'Select observations of this action in its current learning context.')

    evidence=G(); e=evidence.get(evidence.input,'item'); h=evidence.get(evidence.input,'context')
    vote=evidence.call('world_matches',evidence.record(hypothesis=h,features=evidence.get(e,'features')),kind='Bool')
    mismatch=evidence.inverse(evidence.eq(evidence.datum(vote),evidence.get(e,'outcome')))
    hyp=G(); h=hyp.get(hyp.input,'item'); es=hyp.get(hyp.input,'context'); keep=hyp.inverse(hyp.nonempty(hyp.map(es,evidence.finish(mismatch,'Bool'),h,filter=True)))
    g=G(); es=g.call('world_evidence',g.input)
    save('world_hypotheses',g,g.map(g.get(g.input,'space'),hyp.finish(keep,'Bool'),es,filter=True),'Retain precisely the candidate rules that agree with every recorded outcome in the current context.')

    vote=G(); yes=vote.call('world_matches',vote.record(hypothesis=vote.get(vote.input,'item'),features=vote.get(vote.input,'context')),kind='Bool')
    g=G(); candidates=g.call('world_hypotheses',g.input); positives=g.map(candidates,vote.finish(yes,'Bool'),g.get(g.input,'features'),filter=True)
    answer=g.choose(g.inverse(g.nonempty(candidates)),g.data('unknown'),g.choose(g.eq(g.length(positives),g.length(candidates)),g.data('yes'),g.choose(g.inverse(g.nonempty(positives)),g.data('no'),g.data('uncertain'))))
    save('world_predict',g,answer,'Report agreement of the surviving hypotheses; a mixture of predictions remains uncertain.')

    attempted=G(); entity=attempted.get(attempted.input,'entity')
    choice=G(); entity=choice.get(choice.input,'item'); ctx=choice.get(choice.input,'context'); candidates=choice.get(ctx,'candidates'); features=choice.item(choice.get(ctx,'observations'),entity)
    positives=choice.map(candidates,vote.finish(yes,'Bool'),features,filter=True); total=choice.length(candidates); n=choice.length(positives)
    score=choice.calc('divide',choice.calc('multiply',n,choice.calc('subtract',total,n)),choice.calc('multiply',total,total))
    possible=choice.both(choice.nonempty(candidates),choice.inverse(choice.op('contains',choice.get(ctx,'attempted'),entity,kind='Bool')))
    record=choice.record(score=score,action=choice.get(ctx,'action'),entity=entity,name=choice.textcat(choice.get(ctx,'action'),choice.data('/'),entity))
    selected=choice.choose(possible,choice.choose(choice.lt(choice.data(0),score),choice.op('data_list',record),choice.data([])),choice.data([]))
    action=G(); name=action.get(action.input,'item'); ctx=action.get(action.input,'context'); args=action.record(action=name,start=action.item(action.get(ctx,'starts'),name),episodes=action.get(ctx,'episodes'),space=action.get(ctx,'space'))
    candidates=action.call('world_hypotheses',args); tried=action.map(action.call('world_evidence',args),attempted.finish(entity))
    choices=action.op('flatten',action.map(action.op('keys',action.get(ctx,'observations')),choice.finish(selected),action.record(candidates=candidates,attempted=tried,observations=action.get(ctx,'observations'),action=name)))
    guard=G(); run=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'choices')))
    body=G(); s=body.input; choices0=body.get(s,'choices'); i=body.get(s,'i'); candidate=body.item(choices0,i)
    better=body.inverse(body.lt(body.get(candidate,'score'),body.get(s,'score')))
    updated=body.record(i=body.calc('add',i,body.data(1)),choices=choices0,score=body.choose(better,body.get(candidate,'score'),body.get(s,'score')),best=body.choose(better,body.op('data_list',body.get(candidate,'action'),body.get(candidate,'entity')),body.get(s,'best')))
    g=G(); choices=g.op('sort',g.op('flatten',g.map(g.get(g.input,'actions'),action.finish(choices),g.input)),key='name')
    loop=g.loop(g.record(i=g.data(0),choices=choices,score=g.data(0),best=g.data(None)),guard.finish(run,'Bool'),body.finish(updated))
    save('world_choose_experiment',g,g.get(loop,'best'),'Choose an untried action/object with maximum hypothesis disagreement; resolve equal scores by the action/object name.')

    g=G(); prediction=g.call('world_predict',g.input); action=g.get(g.input,'action'); episodes=g.get(g.input,'episodes'); features=g.get(g.input,'features')
    episode=g.record(action=action,entity=g.get(g.input,'entity'),features=features,outcome=g.get(g.input,'outcome'),prediction=prediction)
    newepisodes=g.append(episodes,episode); revised=g.inverse(g.nonempty(g.call('world_hypotheses',g.record(action=action,start=g.get(g.input,'start'),episodes=newepisodes,space=g.get(g.input,'space')))))
    save('world_update',g,g.record(episode=episode,prediction=prediction,revised=g.datum(revised),start=g.choose(revised,g.length(episodes),g.get(g.input,'start'))),'Record a measured outcome; if it contradicts every current hypothesis, retain history and start a new learning context at this observation.')
    return suite
