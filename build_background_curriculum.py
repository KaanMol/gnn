"""Taught scheduling, execution, reminders and cancellation on generic ports."""
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description):
        suite[name]={'graph':g.finish(out,trace_mode='explicit',description=description),
                     'source':'Explicit background routine teaching: '+description}
    g=G();clock=g.op('observe',g.input,surface='clock');delay=g.get(g.input,'delay_seconds');repeat=g.get(g.input,'repeat_seconds')
    valid=g.both(g.inverse(g.lt(delay,g.data(1))),g.both(g.inverse(g.lt(repeat,g.data(0))),g.inverse(g.lt(g.data(31536000),delay))))
    job=g.record(id=g.get(g.input,'id'),method=g.get(g.input,'method'),argument=g.get(g.input,'argument'),
        next_at=g.calc('add',g.get(clock,'unix_seconds'),delay),repeat_seconds=repeat,status=g.data('scheduled'))
    job=g.op('require',valid,job,message='Use a delay of at least one second, at most one year, and a nonnegative repeat interval.')
    write=g.op('act',g.input,g.record(namespace=g.data('skills.subroutines'),key=g.get(g.input,'id'),value=job),surface='workspace',action='write')
    save('background_schedule',g,g.record(text=g.data('Scheduled. I will post here when it is due, while the server is running.'),job=g.get(write,'after')),'Persist a named subroutine, input, deadline and optional repeat interval. Scheduling uses the clock port and taught arithmetic; deadlines survive restarts.')
    g=G();save('background_say',g,g.record(text=g.get(g.input,'text')),'Return the taught reminder text for delivery to the conversation.')
    g=G();save('background_remind',g,g.call('background_schedule',g.record(id=g.get(g.input,'text'),method=g.data('background_say'),argument=g.record(text=g.get(g.input,'text')),delay_seconds=g.get(g.input,'after_seconds'),repeat_seconds=g.data(0))),'Teach a one-time reminder as an instance of the general subroutine scheduler.')
    g=G();removed=g.op('act',g.input,g.record(namespace=g.data('skills.subroutines'),key=g.get(g.input,'id')),surface='workspace',action='delete')
    save('background_cancel',g,g.record(text=g.data('Cancelled that routine.'),change=removed),'Explicitly remove a scheduled routine.')
    due=G();job=due.get(due.input,'item','value');now=due.get(due.input,'context')
    yes=due.both(due.eq(due.get(job,'status'),due.data('scheduled')),due.inverse(due.lt(now,due.get(job,'next_at'))))
    invoke=G();result=invoke.op('invoke',invoke.get(invoke.input,'method'),invoke.get(invoke.input,'argument'))
    each=G();job=each.get(each.input,'item','value');now=each.get(each.input,'context')
    attempt=each.op('attempt',job,body=invoke.finish(result));ok=each.boolean(each.get(attempt,'ok'))
    repeats=each.both(ok,each.lt(each.data(0),each.get(job,'repeat_seconds')))
    updated=each.put(job,'status',each.choose(ok,each.choose(repeats,each.data('scheduled'),each.data('completed')),each.data('failed')))
    updated=each.put(updated,'next_at',each.choose(repeats,each.calc('add',now,each.get(job,'repeat_seconds')),each.get(job,'next_at')))
    updated=each.put(updated,'last_result',attempt)
    saved=each.op('act',each.input,each.record(namespace=each.data('skills.subroutines'),key=each.get(job,'id'),value=updated),surface='workspace',action='write')
    output=each.get(attempt,'result')
    text=each.choose(ok,each.choose(each.has(output,each.data('text')),each.get(output,'text'),each.data('')),
        each.textcat(each.data('A background routine stopped: '),each.get(attempt,'error')))
    out=each.record(id=each.get(saved,'after','id'),text=text)
    g=G();jobs=g.op('act',g.input,g.record(namespace=g.data('skills.subroutines')),surface='workspace',action='entries')
    ready=g.map(jobs,due.finish(yes,'Bool'),g.get(g.input,'now'),filter=True)
    results=g.map(g.op('slice',ready,stop=1),each.finish(out),g.get(g.input,'now'))
    save('background_tick',g,g.choose(g.boolean(g.get(g.input,'waiting')),g.data([]),results),'On a timer signal, run at most one due subroutine. Defer while a conversation continuation is waiting, persist its outcome, and do not repeatedly retry failures.')
    return suite


def interpretation():
    g=G();text=g.get(g.input,'text');lower=g.op('lower',text)
    prefix=g.op('split_text',lower,g.data('remind me in '))
    starts=g.both(g.eq(g.length(prefix),g.data(2)),g.eq(g.get(prefix,0),g.data('')))
    parts=g.op('split_text',g.get(prefix,1),g.data(' seconds to '))
    matches=g.eq(g.length(parts),g.data(2))
    start=g.calc('add',g.data(len('remind me in ')+len(' seconds to ')),g.length(g.op('characters',g.get(parts,0))))
    content=g.call('identity_text_range',g.record(text=text,start=start,stop=g.length(g.op('characters',text))))
    delay=g.op('as_data',g.num(g.get(parts,0)))
    reminder=g.record(kind=g.data('graph_run'),name=g.data('background_remind'),argument=g.record(text=content,after_seconds=delay))
    found=g.choose(starts,g.choose(matches,reminder,g.data(None)),g.data(None))
    affect=g.call('affect_interpret',g.input)
    return {'behavior_interpret':{'graph':g.finish(g.choose(g.eq(affect,g.data(None)),found,affect),trace_mode='explicit'),
        'source':'Teach explicit sympathy and state questions, plus: Remind me in N seconds to TEXT. Other wording uses the existing language interface.'}}
