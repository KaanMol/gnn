"""Taught durable task execution over existing generic graph/IO primitives."""
from graph_dsl import G


def build(library):
    suite={}
    def save(name,g,out,description,**meta):
        suite[name]={'graph':g.finish(out,trace_mode='explicit',description=description,**meta),'source':'Explicit persistent task teaching: '+description}
    def read(g,key):return g.op('act',g.input,g.record(namespace=g.data('skills.tasks'),key=key),surface='workspace',action='read')
    def write(g,key,value,dependency=None):return g.op('act',dependency or g.input,g.record(namespace=g.data('skills.tasks'),key=key,value=value),surface='workspace',action='write')
    def now(g,dependency=None):return g.get(g.op('observe',dependency or g.input,surface='clock'),'unix_seconds')
    def reply(g,saved,text):return g.record(text=text,task=g.get(saved,'after'))
    g=G();save('task_input',g,g.op('require',g.eq(g.data(0),g.data(1)),g.data(None),message='An input-request step must run in a persistent task so its answer can be saved.'),'An input-request step in a persistent task. The task runner asks the supplied question and binds your text reply under the step ID before continuing.',sequence_input='{question: text}; returns user reply text when used in a persistent task')
    g=G();base=g.get(g.call('sequence_policy',g.input),'instructions')
    instructions=g.textcat(base,g.data(' For persistent tasks you may use task_input with {"question":"specific question"} when a needed input is unknown. The user reply becomes the result of that step and can be referenced with {"var":"step_id"}. Never guess missing inputs. Do not use other dialogue methods. Return clarification for missing capabilities or unsupported recurrence/conditions; do not pretend a one-shot plan satisfies an ongoing request. The plan is saved for inspection before starting. You are ONLY writing a plan, not executing it this turn. task_input IS supported: it pauses the persistent task across future turns. Do not reject a plan because it asks the user a question. Example: start with 5, ask what to add, then add the reply -> steps s1 sequence_value argument_json {\"value\":5}; s2 task_input argument_json {\"question\":\"What number should I add?\"}; s3 sequence_add argument_json {\"left\":{\"var\":\"s1\"},\"right\":{\"var\":\"s2\"}}. clarification must be empty for this supported task.'))
    save('task_plan_policy',g,instructions,'Ask the language interface for a proposed sequence of known methods, retaining missing values as explicit input-request steps. Unsupported tasks remain questions, not invented workflows.')
    g=G();stamp=now(g);steps=g.get(g.input,'steps');question=g.get(g.input,'question')
    value=g.record(id=g.get(g.input,'id'),title=g.get(g.input,'title'),original=g.get(g.input,'original'),steps=steps,pending=steps,completed=g.data([]),bindings=g.get(g.input,'bindings'),status=g.choose(g.nonempty(steps),g.data('ready'),g.data('needs_plan')),question=question,error=g.data(''),created_at=stamp,updated_at=stamp,inflight=g.data(None))
    saved=write(g,g.get(g.input,'id'),value)
    save('task_create',g,reply(g,saved,g.choose(g.nonempty(steps),g.data('Task saved. Open Tasks to inspect its steps and start it.'),g.textcat(g.data('Task saved, but its plan needs clarification: '),question))),'Store the original request, proposed steps, bindings and missing information. Saving a plan does not execute its actions.')
    g=G();task=read(g,g.get(g.input,'id'));status=g.get(task,'status')
    allowed=g.op('contains',g.data(['ready','paused','blocked','needs_review']),status,kind='Bool')
    value=g.op('require',allowed,task,message='Only a ready, paused or blocked task can resume. Answer a waiting question first.')
    value=g.put(g.put(g.put(value,'status',g.data('queued')),'error',g.data('')),'updated_at',now(g))
    saved=write(g,g.get(g.input,'id'),value)
    save('task_resume',g,reply(g,saved,g.data('Task queued. Completed steps will not be repeated.')),'Queue the remaining steps. Resuming an interrupted step is an explicit retry; completed steps stay saved.')
    for action,state in [('pause','paused'),('cancel','cancelled')]:
        g=G();task=read(g,g.get(g.input,'id'));value=g.put(g.put(task,'status',g.data(state)),'updated_at',now(g));saved=write(g,g.get(g.input,'id'),value)
        save('task_'+action,g,reply(g,saved,g.data('Task '+state+'. Saved steps and results remain available.')),'Set a task to '+state+' without deleting its record or undoing already performed actions.')
    # A missing-input question belongs to the task, not to an ambiguous global pronoun.
    g=G();task=read(g,g.get(g.input,'id'));step=g.get(task,'pending',0)
    value=g.put(g.put(g.put(task,'status',g.data('waiting')),'question',g.get(step,'argument','question')),'updated_at',now(g))
    saved=write(g,g.get(g.input,'id'),value)
    save('task_question',g,reply(g,saved,g.textcat(g.get(saved,'after','title'),g.data(': '),g.get(saved,'after','question'),g.data(' Reply in its Tasks card so the answer stays attached to the right task.'))),'Persist an explicit missing input and ask once. Answers are attached to a task ID, so multiple waiting tasks cannot capture each other’s replies.')
    g=G();task=read(g,g.get(g.input,'id'));task=g.op('require',g.eq(g.get(task,'status'),g.data('waiting')),task,message='This task is not waiting for an answer.')
    step=g.get(task,'pending',0);answer=g.get(g.input,'answer')
    bindings=g.op('set_item',g.get(task,'bindings'),g.get(step,'id'),answer)
    completed=g.append(g.get(task,'completed'),g.record(id=g.get(step,'id'),method=g.get(step,'method'),argument=g.get(step,'argument'),result=answer))
    value=g.put(g.put(g.put(g.put(g.put(task,'bindings',bindings),'completed',completed),'pending',g.op('slice',g.get(task,'pending'),start=1)),'status',g.data('queued')),'question',g.data(''))
    saved=write(g,g.get(g.input,'id'),g.put(value,'updated_at',now(g)))
    save('task_answer',g,reply(g,saved,g.data('Answer saved. Continuing with the remaining steps.')),'Bind an answer to the pending input step and resume; prior completed steps are not rerun.')
    g=G();task=read(g,g.get(g.input,'id'));pending=g.get(task,'pending');step=g.get(pending,0)
    allowed=g.op('contains',g.data(['ready','paused','blocked','needs_review']),g.get(task,'status'),kind='Bool')
    step=g.put(g.op('require',allowed,step,message='Pause the task before revising its current step.'),'argument',g.get(g.input,'argument'))
    value=g.put(g.put(task,'pending',g.op('set_item',pending,g.data(0),step)),'updated_at',now(g));saved=write(g,g.get(g.input,'id'),value)
    save('task_revise',g,reply(g,saved,g.data('Updated the current step input. Resume when ready.')),'Revise only the current unfinished step’s argument. Completed results and the original request remain available.')

    g=G();task=read(g,g.get(g.input,'id'));task=g.op('require',g.eq(g.get(task,'status'),g.data('queued')),task,message='This task is not queued.')
    step=g.get(task,'pending',0)
    # This write is committed by the generic workspace port before invocation.
    running=g.put(g.put(g.put(task,'status',g.data('running')),'inflight',step),'updated_at',now(g))
    checkpoint=write(g,g.get(g.input,'id'),running)
    attempt=G();state=attempt.input;step0=attempt.get(state,'inflight')
    argument=attempt.call('pattern_substitute',attempt.record(template=attempt.get(step0,'argument'),bindings=attempt.get(state,'bindings')))
    result=attempt.op('invoke',attempt.get(step0,'method'),argument)
    result=attempt.record(id=attempt.get(step0,'id'),method=attempt.get(step0,'method'),argument=argument,result=result)
    tried=g.op('attempt',g.get(checkpoint,'after'),body=attempt.finish(result));ok=g.boolean(g.get(tried,'ok'));row=g.get(tried,'result')
    completed=g.choose(ok,g.append(g.get(task,'completed'),row),g.get(task,'completed'))
    pending=g.choose(ok,g.op('slice',g.get(task,'pending'),start=1),g.get(task,'pending'))
    bindings=g.choose(ok,g.op('set_item',g.get(task,'bindings'),g.get(step,'id'),g.get(row,'result')),g.get(task,'bindings'))
    updated=g.put(g.put(g.put(g.put(g.put(task,'completed',completed),'pending',pending),'bindings',bindings),'inflight',g.data(None)),'status',g.choose(ok,g.choose(g.nonempty(pending),g.data('queued'),g.data('completed')),g.data('blocked')))
    updated=g.put(g.put(updated,'error',g.choose(ok,g.data(''),g.get(tried,'error'))),'updated_at',now(g,tried));saved=write(g,g.get(g.input,'id'),updated)
    finish=g.textcat(g.get(task,'title'),g.data(' completed. Result: '),g.call('sequence_display',g.get(row,'result')))
    blocked=g.textcat(g.get(task,'title'),g.data(' is blocked at '),g.get(step,'id'),g.data(': '),g.get(saved,'after','error'),g.data(' Check or revise that step in Tasks, then resume.'))
    text=g.choose(ok,g.choose(g.nonempty(pending),g.data(''),finish),blocked)
    execution=reply(g,saved,text)
    # A final input-only step completes without trying to invoke an empty queue.
    completed_task=g.put(g.put(task,'status',g.data('completed')),'updated_at',now(g));done=write(g,g.get(g.input,'id'),completed_task)
    save('task_step',g,g.choose(g.nonempty(g.get(task,'pending')),g.choose(g.eq(g.get(step,'method'),g.data('task_input')),g.call('task_question',g.input),execution),reply(g,done,g.textcat(g.get(task,'title'),g.data(' completed.')))),'Advance one queued step. Persist intent before effects, then result and remaining steps. Failure blocks the task. A restart never automatically repeats an uncertain in-flight action.')
    row=G();task=row.get(row.input,'value');ready=row.eq(row.get(task,'status'),row.data('queued'))
    g=G();all_tasks=g.op('act',g.input,g.record(namespace=g.data('skills.tasks')),surface='workspace',action='entries');queued=g.map(all_tasks,row.finish(ready,'Bool'),filter=True)
    value=G();t=value.get(value.input,'value');ordered=g.op('sort',g.map(queued,value.finish(t)),key='updated_at')
    result=g.call('task_step',g.record(id=g.get(ordered,0,'id')))
    output=g.record(id=g.get(result,'task','id'),text=g.get(result,'text'))
    save('task_tick',g,g.choose(g.boolean(g.get(g.input,'waiting')),g.data([]),g.choose(g.nonempty(queued),g.op('data_list',output),g.data([]))),'Run at most one queued task step per timer signal, oldest update first. Return only completion, blocked or input-question notifications.')
    row=G();t=row.get(row.input,'value');running=row.eq(row.get(t,'status'),row.data('running'))
    fix=G();t=fix.get(fix.input,'value');value=fix.put(fix.put(t,'status',fix.data('needs_review')),'error',fix.data('The server stopped during this step. Its external action may have completed. Check before retrying; completed steps will not be replayed.'));changed=write(fix,fix.get(t,'id'),value)
    g=G();entries=g.op('act',g.input,g.record(namespace=g.data('skills.tasks')),surface='workspace',action='entries')
    save('task_recover',g,g.map(g.map(entries,row.finish(running,'Bool'),filter=True),fix.finish(changed)),'On startup mark unfinished in-flight actions for review instead of silently executing them twice. Other queued steps and waiting inputs survive normally.')
    g=G();parts=g.op('split_text',g.input,g.data(':'));prefix=g.call('language_normalize',g.get(parts,0));matched=g.both(g.op('contains',g.data(['task','taak']),prefix,kind='Bool'),g.nonempty(g.op('slice',parts,start=1)))
    save('task_detect',g,g.choose(matched,g.op('join_text',g.op('slice',parts,start=1),g.data(':')),g.data(None)),'Recognize explicit Task: and Taak: requests without treating ordinary statements as new tasks.')
    import copy
    for name,signature in {'web_weather_read':'{url: explicitly supplied public weather page URL}; returns the published report', 'web_open':'{url: explicitly supplied public URL}; returns DOM observation', 'web_find':'{page: prior DOM result, query: text}', 'dashboard_add':'{id: card name, title: text, method: taught procedure, argument: JSON input, refresh_seconds: integer >=60}'}.items():
        suite[name]=copy.deepcopy(library[name]);suite[name]['graph']['sequence_input']=signature
    return suite
