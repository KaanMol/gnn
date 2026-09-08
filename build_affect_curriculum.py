"""Teacher-authored functional affect and sympathy, executed entirely as graphs."""
import copy
from graph_dsl import G


def build(library):
    suite={}
    def save(name,g,out,description):
        suite[name]={'graph':g.finish(out,trace_mode='explicit',description=description),
                     'source':'Explicit functional affect teaching: '+description}
    def read(g):
        return g.call('affect_read',g.data(None))
    g=G();save('affect_policy',g,g.data({
        'initial':{'curiosity':0,'uncertainty':0,'satisfaction':0,'sympathy':0},
        'changes':{'missing':{'curiosity':25,'uncertainty':30,'satisfaction':-10,'sympathy':0},
                   'learned':{'curiosity':-10,'uncertainty':-20,'satisfaction':20,'sympathy':0},
                   'answered':{'curiosity':-10,'uncertainty':-15,'satisfaction':10,'sympathy':0},
                   'difficulty_shared':{'curiosity':0,'uncertainty':0,'satisfaction':0,'sympathy':30},
                   'positive_shared':{'curiosity':0,'uncertainty':0,'satisfaction':10,'sympathy':-10}},
        'ask_at':25,'minimum':0,'maximum':100,
        'learning_operations':['assert','subtype','define','redefine','symmetric','define_procedure','redefine_procedure'],
        'answer_operations':['query','describe','calculate','count','date_procedure','run_procedure'],
        'unknown_phrases':["I haven't learned", "I don't know", 'Unknown:', 'Conflicting evidence', 'Clarification needed'],
        'ignored_skills':['affect_report','affect_support','affect_initialize'],
        'question':'Can you teach me the missing fact or explain what you mean?',
        'note':'Functional activation levels from 0 to 100, not probabilities or evidence of subjective feelings.'
    }),'Teach state ranges, event changes and the curiosity threshold for requesting teaching. These are editable activation signals, not subjective emotions or calibrated confidence.')
    load=G();value=load.op('act',load.input,load.record(namespace=load.data('skills.affect'),key=load.data('current')),surface='workspace',action='read')
    g=G();attempt=g.op('attempt',g.input,body=load.finish(value));initial=g.record(values=g.get(g.call('affect_policy',g.input),'initial'),revision=g.data(0),history=g.data([]),last=g.data(None))
    save('affect_read',g,g.choose(g.boolean(g.get(attempt,'ok')),g.get(attempt,'result'),initial),'Read persistent graph state. A new notebook starts at the explicitly taught baseline; merely reading does not change it.')
    g=G();s=read(g);write=g.op('act',g.input,g.record(namespace=g.data('skills.affect'),key=g.data('current'),value=s),surface='workspace',action='write')
    save('affect_initialize',g,g.get(write,'after'),'Explicitly persist the taught initial state, preserving any state that already exists.')
    each=G();key=each.get(each.input,'item');ctx=each.get(each.input,'context')
    value=each.calc('add',each.item(each.get(ctx,'values'),key),each.item(each.get(ctx,'delta'),key))
    lo=each.get(ctx,'minimum');hi=each.get(ctx,'maximum')
    value=each.choose(each.lt(value,lo),lo,each.choose(each.lt(hi,value),hi,value))
    row=each.record(key=key,value=value)
    guard=G();again=guard.nonempty(guard.get(guard.input,'pending'))
    body=G();first=body.get(body.input,'pending',0)
    next_=body.record(pending=body.op('slice',body.get(body.input,'pending'),start=1),values=body.op('set_item',body.get(body.input,'values'),body.get(first,'key'),body.get(first,'value')))
    g=G();s=read(g);p=g.call('affect_policy',g.input);event=g.get(g.input,'event')
    delta=g.item(g.get(p,'changes'),event)
    rows=g.map(g.op('keys',g.get(p,'initial')),each.finish(row),g.record(values=g.get(s,'values'),delta=delta,minimum=g.get(p,'minimum'),maximum=g.get(p,'maximum')))
    values=g.get(g.loop(g.record(pending=rows,values=g.data({})),guard.finish(again,'Bool'),body.finish(next_)),'values')
    revision=g.calc('add',g.get(s,'revision'),g.data(1))
    cause=g.record(event=event,evidence=g.get(g.input,'evidence'),before=g.get(s,'values'),after=values,revision=revision)
    updated=g.record(values=values,revision=revision,last=cause,history=g.op('slice',g.append(g.get(s,'history'),cause),start=-20))
    saved=g.op('act',g.input,g.record(namespace=g.data('skills.affect'),key=g.data('current'),value=updated),surface='workspace',action='write')
    save('affect_update',g,g.get(saved,'after'),'Apply the taught event deltas with taught arithmetic, clamp to the taught bounds, and retain the last twenty causes. Workspace observation history retains the actual writes.')
    op=G();kind=op.get(op.input,'op')
    match=G();phrase=match.get(match.input,'item');text=match.get(match.input,'context')
    found=match.nonempty(match.op('slice',match.op('split_text',text,phrase),start=1))
    g=G();p=g.call('affect_policy',g.input);ops=g.map(g.get(g.input,'operations'),op.finish(kind))
    unknown=g.nonempty(g.map(g.get(p,'unknown_phrases'),match.finish(found,'Bool'),g.get(g.input,'answer'),filter=True))
    missing=g.either(g.inverse(g.eq(g.get(g.input,'error'),g.data(''))),g.either(g.boolean(g.get(g.input,'waiting')),unknown))
    member=G();yes=member.op('contains',member.get(member.input,'context'),member.get(member.input,'item'),kind='Bool')
    learned=g.nonempty(g.map(ops,member.finish(yes,'Bool'),g.get(p,'learning_operations'),filter=True))
    answered=g.nonempty(g.map(ops,member.finish(yes,'Bool'),g.get(p,'answer_operations'),filter=True))
    event=g.choose(missing,g.data('missing'),g.choose(learned,g.data('learned'),g.choose(answered,g.data('answered'),g.data(''))))
    ignore=g.op('contains',g.get(p,'ignored_skills'),g.get(g.input,'skill'),kind='Bool')
    save('affect_classify',g,g.choose(ignore,g.data(''),event),'Classify actual dialogue outcomes. Unanswered or conflicting responses raise uncertainty; stored learning and successful answers reduce it. Self-reports do not reward themselves.')
    g=G();event=g.call('affect_classify',g.input)
    s=g.call('affect_update',g.record(event=event,evidence=g.get(g.input,'text')))
    p=g.call('affect_policy',g.input)
    curious=g.inverse(g.lt(g.get(s,'values','curiosity'),g.get(p,'ask_at')))
    already_asked=g.nonempty(g.op('slice',g.op('split_text',g.get(g.input,'answer'),g.data('?')),start=1))
    ask=g.both(g.eq(event,g.data('missing')),g.both(curious,g.inverse(g.either(already_asked,g.boolean(g.get(g.input,'waiting'))))))
    response=g.record(state=s,text=g.choose(ask,g.get(p,'question'),g.data('')),decision=g.choose(ask,g.data('ask for teaching'),g.data('continue')))
    save('affect_observe_turn',g,g.choose(g.eq(event,g.data('')),g.record(text=g.data(''),decision=g.data('unchanged')),response),'Use state to choose whether to request teaching when stuck. Do not duplicate an existing question or replace an active continuation.')
    g=G();s=read(g);v=g.get(s,'values');text=g.data('My functional state levels (0–100): ')
    for i,key in enumerate(['curiosity','uncertainty','satisfaction','sympathy']):
        text=g.textcat(text,g.data((', ' if i else '')+key+' '),g.op('text',g.get(v,key)))
    last=g.get(s,'last');cause=g.choose(g.eq(last,g.data(None)),g.data('No events recorded yet.'),g.textcat(g.data('Last cause: '),g.get(last,'event'),g.data(' — '),g.get(last,'evidence')))
    text=g.textcat(text,g.data('.\n'),cause,g.data('\nThese are taught functional states, not a claim that I experience feelings.'))
    save('affect_report',g,g.record(text=text,state=s),'Explain current state values and their recorded cause without claiming subjective experience.')
    g=G();save('sympathy_policy',g,g.data([
      {'phrases':['i feel sad',"i'm sad",'i am sad',"i'm having a hard day",'i am having a hard day',"i'm upset",'i feel lonely'], 'event':'difficulty_shared','reply':'That sounds difficult. Would you prefer to talk about it, or think through something that might help?'},
      {'phrases':['i feel happy',"i'm feeling better",'i am feeling better'],'event':'positive_shared','reply':'Good to hear. What helped?'},
      {'phrases':['just listen','i just want to talk',"i don't want advice",'no advice'],'event':'difficulty_shared','reply':"Okay. I won't jump into advice. You can tell me what happened, if you want."}
    ]),'Respond sympathetically to explicitly shared feelings using bounded taught phrases. Offer a choice, respect requests for no advice, and never infer distress from ordinary task errors.')
    g=G();rule=g.get(g.input,'rule');s=g.call('affect_update',g.record(event=g.get(rule,'event'),evidence=g.get(g.input,'text')))
    # A recorded update is a dependency of the reply, so reporting sympathy is not cosmetic.
    scheduled=g.call('background_schedule',g.record(id=g.data('gentle-follow-up'),method=g.data('affect_followup'),argument=g.data(None),delay_seconds=g.data(180),repeat_seconds=g.data(0)))
    reply=g.choose(g.eq(g.get(s,'last','event'),g.data('difficulty_shared')),
        g.choose(g.eq(g.get(scheduled,'job','status'),g.data('scheduled')),g.get(rule,'reply'),g.data('')),g.get(rule,'reply'))
    save('affect_support',g,g.record(text=reply,state=s),'Record concern for a user’s explicitly shared difficulty, then offer the taught supportive response. Listening is offered without pressure or a claim of feeling the user’s emotion.')
    g=G();s=read(g);last=g.get(s,'last')
    unresolved=g.choose(g.eq(last,g.data(None)),g.eq(g.data(0),g.data(1)),g.eq(g.get(last,'event'),g.data('difficulty_shared')),kind='Bool')
    save('affect_followup',g,g.record(text=g.choose(unresolved,g.data('Hey, would you like to talk more about what you mentioned earlier? It is fine to leave it there.'),g.data(''))),'A single delayed offer to continue after explicit difficulty. Stay quiet if another meaningful event has superseded it. The scheduler prevents repeated delivery.')
    g=G();text=g.op('lower',g.get(g.input,'text'))
    for punctuation in ['.','!','?']:text=g.op('replace_text',text,g.data(punctuation),g.data(''))
    text=g.op('replace_text',text,g.data('’'),g.data("'"))
    r=G();yes=r.op('contains',r.get(r.get(r.input,'item'),'phrases'),r.get(r.input,'context'),kind='Bool')
    matches=g.map(g.call('sympathy_policy',g.input),r.finish(yes,'Bool'),text,filter=True)
    report=g.op('contains',g.data(['how are you feeling','how do you feel','show your feelings','show your states','what are your feelings']),text,kind='Bool')
    argument=g.record(rule=g.get(matches,0),text=g.get(g.input,'text'))
    # Structured skill arguments are serialized by the existing JSON port below.
    # The language interpreter's graph_run protocol carries Data without JSON conversion.
    support=g.record(kind=g.data('graph_run'),name=g.data('affect_support'),argument=argument)
    report_op=g.record(kind=g.data('graph_run'),name=g.data('affect_report'),argument=g.data(None))
    save('affect_interpret',g,g.choose(report,report_op,g.choose(g.nonempty(matches),support,g.data(None))),'Recognize taught self-report and sympathy phrases. Unrecognized wording remains with the existing language interface; this is not unrestricted emotion understanding.')
    return suite
