"""Generic graph-selected dialogue hooks and timer delivery; no affect policy."""
import time
import foundation


def interpret(session,text):
    method=session.store.map('session.behavior').get('interpret')
    if not method:return None
    # Commit the short interpretation's observation records together.
    with session.store.transaction():
        return foundation.run(session.core.procedures,method,{'text':text},session.sensors)[0]


def after_turn(session,text,answer,record,error=''):
    method=session.store.map('session.behavior').get('after_turn')
    if not method:return answer
    translation=record.get('translation',{})
    event={'text':text,'answer':answer,'error':error,'operations':translation.get('operations',[]),
           'skill':translation.get('name',''),'waiting':session.store.map('interaction.state').get('waiting') is not None}
    try:
        with session.store.transaction():
            result,trace=foundation.run(session.core.procedures,method,event,session.sensors)
            extra=result.get('text','')
            if extra:answer+='\n\n'+extra
            if record:
                record=dict(record);record['answer']=answer
                record.setdefault('tool_runs',[]).append({'procedure':method,'result':result,'trace':trace})
                session.language_records[-1]=record
    except (ValueError,KeyError) as exc:
        # The main operation may already have succeeded. Preserve that outcome.
        session.store.map('session.behavior')['last_error']=str(exc)
    return answer


def _deliver(session, method, result, trace):
    for item in result:
        text=item.get('text','')
        if text:
            session.language_records.append({'source':'assistant-background','original':'',
                'answer':text,'interpretation':'Background routine: '+item['id'],
                'translation':{'kind':'graph_run','name':method},'trace':trace})


def tick(session):
    hooks=session.store.map('session.behavior')
    event={'now':int(time.time()),'waiting':session.store.map('interaction.state').get('waiting') is not None}
    method=hooks.get('background')
    if method:
        with session.store.transaction():
            result,trace=foundation.run(session.core.procedures,method,event,session.sensors)
            _deliver(session,method,result,trace)
    # Durable graph programs commit their workspace checkpoints before effects.
    # Keep this generic hook outside an enclosing rollback transaction.
    method=hooks.get('background_progress')
    event['waiting']=session.store.map('interaction.state').get('waiting') is not None
    if method:
        result,trace=foundation.run(session.core.procedures,method,event,session.sensors)
        _deliver(session,method,result,trace)
