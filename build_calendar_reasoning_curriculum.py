"""Author reusable calendar arithmetic and taught question-to-method links.

This file generates lesson data. The application does not import it at runtime.
"""
import copy
import json
from pathlib import Path
from graph_dsl import G


def build(base):
    suite = {}
    def save(name, g, out, description, kind='Data', **meta):
        suite[name] = {'graph':g.finish(out, kind, internal=True, trace_mode='explicit', description=description, **meta),
                       'source':'Codex teacher: '+description}
    def emit(g, value, label):
        return g.op('emit', value, value, label=label)

    g=G();y=g.input
    leap=g.either(g.eq(g.call('integer_modulo',g.record(a=y,b=g.data(400))),g.data(0)),
        g.both(g.eq(g.call('integer_modulo',g.record(a=y,b=g.data(4))),g.data(0)),
        g.inverse(g.eq(g.call('integer_modulo',g.record(a=y,b=g.data(100))),g.data(0)))))
    save('calendar_is_leap',g,leap,'A Gregorian year is leap when divisible by 400, or divisible by 4 but not 100.','Bool',memoize=True)

    guard=G();again=guard.lt(guard.get(guard.input,'month'),guard.get(guard.input,'date',1))
    body=G();s=body.input;m=body.get(s,'month');length=body.item(body.get(body.call('calendar_vocabulary',s),'month_lengths'),body.calc('subtract',m,body.data(1)))
    length=body.choose(body.both(body.eq(m,body.data(2)),body.call('calendar_is_leap',body.get(s,'date',0),'Bool')),body.data(29),length)
    step=body.record(date=body.get(s,'date'),month=body.calc('add',m,body.data(1)),days=body.calc('add',body.get(s,'days'),length))
    g=G();date=g.call('calendar_validate',g.input)
    loop=g.loop(g.record(date=date,month=g.data(1),days=g.data(0)),guard.finish(again,'Bool'),body.finish(step))
    save('calendar_day_of_year',g,g.calc('add',g.get(loop,'days'),g.get(date,2)),
         'Add the lengths of completed months, including February’s leap day, then the day within the current month.',memoize=True)

    g=G();date=g.call('calendar_validate',g.input);years=g.calc('subtract',g.get(date,0),g.data(1))
    def quotient(n): return g.calc('floor',g.calc('divide',years,g.data(n)))
    completed=g.calc('add',g.calc('subtract',g.calc('add',g.calc('multiply',years,g.data(365)),quotient(4)),quotient(100)),quotient(400))
    save('calendar_day_number',g,g.calc('add',completed,g.call('calendar_day_of_year',date)),
         'Represent a Gregorian date by completed common-year days plus leap days plus its day of year; 0001-01-01 is day 1.',memoize=True)

    g=G();start=emit(g,g.call('calendar_day_number',g.get(g.input,'start')),'start_day_number');end=emit(g,g.call('calendar_day_number',g.get(g.input,'end')),'end_day_number')
    save('calendar_days_between',g,emit(g,g.calc('subtract',end,start),'subtract_day_numbers'),
         'Days from start to end equals end’s day number minus start’s. Equal dates give zero; reversed dates give a negative result. This method is independent of birthdays.')

    g=G();anchor=g.get(g.input,'anchor');year=g.get(g.input,'year')
    feb29=g.both(g.eq(g.get(anchor,1),g.data(2)),g.eq(g.get(anchor,2),g.data(29)))
    save('calendar_annual_date_exists',g,g.either(g.inverse(feb29),g.call('calendar_is_leap',year,'Bool')),
         'A validated month/day recurs every year except February 29, which exists only in leap years.','Bool',memoize=True)
    guard=G();again=guard.both(guard.inverse(guard.boolean(guard.get(guard.input,'found'))),guard.lt(guard.get(guard.input,'year'),guard.data(10000)))
    body=G();s=body.input;y=body.get(s,'year');anchor=body.get(s,'anchor');candidate=body.op('data_list',y,body.get(anchor,1),body.get(anchor,2))
    exists=body.call('calendar_annual_date_exists',body.record(anchor=anchor,year=y),'Bool')
    reached=body.both(exists,body.inverse(body.call('calendar_before',body.record(a=candidate,b=body.get(s,'from')),'Bool')))
    step=body.record(anchor=anchor,**{'from':body.get(s,'from')},year=body.calc('add',y,body.data(1)),found=body.datum(reached),date=candidate)
    g=G();anchor=g.call('calendar_validate',g.get(g.input,'anchor'));start=g.call('calendar_validate',g.get(g.input,'from'))
    loop=g.loop(g.record(anchor=anchor,**{'from':start},year=g.get(start,0),found=g.data(False),date=g.data(None)),guard.finish(again,'Bool'),body.finish(step))
    result=g.op('require',g.boolean(g.get(loop,'found')),g.get(loop,'date'),message='No next occurrence exists within the taught calendar range.')
    save('calendar_next_annual_date',g,emit(g,result,'next_annual_occurrence'),
         'Find the first valid occurrence of an anchor’s month/day on or after the supplied date. Today counts; February 29 skips years in which that date does not exist.')

    # These are executable links, not an explanatory label on a native solver.
    g=G();save('calendar_question_policy',g,g.data([{
        'relation':'days until birthday','event':'birthday','source_method':'calendar_find_birth',
        'occurrence_method':'calendar_next_annual_date','distance_method':'calendar_days_between',
        'source_must_not_be_future':True,'invalid_annual_date':'ask',
        'explanation':'A birthday repeats the month and day of a person’s birth date each year. Count from today to its next occurrence.'}]),
        'To answer days until a birthday, retrieve the birth date, find its next yearly occurrence, and apply the general days-between method. Do not substitute age in years. Ask about non-leap-year observance for a February 29 birthday.')
    raw=G();f=raw.get(raw.input,'fact')
    g=G();policy=g.get(g.input,'binding');subject=g.get(g.input,'subject')
    record=g.op('invoke',g.get(policy,'source_method'),g.record(subject=subject,facts=g.map(g.get(g.input,'facts'),raw.finish(f)),negatives=g.map(g.get(g.input,'negatives'),raw.finish(f))))
    record=emit(g,record,'date_from_memory');anchor=g.get(record,'parts')
    observation=emit(g,g.call('clock_observe',g.input),'clock_observation');today=g.call('calendar_parse',g.get(observation,'date'))
    allowed=g.either(g.inverse(g.boolean(g.get(policy,'source_must_not_be_future'))),g.inverse(g.call('calendar_before',g.record(a=today,b=anchor),'Bool')))
    anchor=g.op('require',allowed,anchor,message='That source date is in the future. Please correct it before asking about its anniversary.')
    occurrence=g.op('invoke',g.get(policy,'occurrence_method'),g.record(anchor=anchor,**{'from':today}))
    days=g.op('invoke',g.get(policy,'distance_method'),g.record(start=today,end=occurrence))
    # If this year's month/day has passed, check next year's validity before
    # choosing a birthday convention. The general recurrence has no convention.
    thisyear=g.op('data_list',g.get(today,0),g.get(anchor,1),g.get(anchor,2))
    candidateyear=g.choose(g.call('calendar_before',g.record(a=thisyear,b=today),'Bool'),g.calc('add',g.get(today,0),g.data(1)),g.get(today,0))
    needs_policy=g.both(g.eq(g.get(policy,'invalid_annual_date'),g.data('ask')),g.inverse(g.call('calendar_annual_date_exists',g.record(anchor=anchor,year=candidateyear),'Bool')))
    text=g.textcat(subject,g.data(' — next '),g.get(policy,'event'),g.data(': '),g.call('calendar_format',occurrence),g.data('. '),g.op('text',days),g.choose(g.eq(days,g.data(1)),g.data(' day left.'),g.data(' days left.')),
        g.data('\nToday: '),g.get(observation,'date'),g.data(' ('),g.get(observation,'timezone'),g.data(', live clock).\nUsed the taught links: source date → next yearly occurrence → days between dates.'))
    result=g.record(text=text,method=g.data('calendar_event_countdown'),days=days,next_date=occurrence,source=record,observation=observation,binding=policy)
    question=g.record(text=g.data('This birthday falls on February 29. In a non-leap year, should I use February 28, March 1, or the next actual February 29? That observance rule still needs teaching.'),method=g.data('calendar_event_countdown'))
    save('calendar_event_countdown',g,g.choose(needs_policy,question,result),
         'Follow the supplied event-to-method links, obtain a date from memory and today from the clock, select the next occurrence, and count days. Return the answer and its actual source/method evidence.')

    # Extend ordinary description lookup through a general table of computed
    # properties. The host simply displays a taught method’s returned text.
    suite['knowledge_describe_facts']=copy.deepcopy(base['knowledge_describe'])
    g=G();save('computed_question_policy',g,g.data([{'relation':'days until birthday','method':'calendar_event_countdown'}]),
        'This requested property is answered by an executable method instead of looking for a stored scalar value.')
    match=G();yes=match.eq(match.get(match.input,'item','relation'),match.get(match.input,'context','relation'))
    g=G();matches=g.map(g.call('computed_question_policy',g.input),match.finish(yes,'Bool'),g.input,filter=True)
    bindings=g.map(g.call('calendar_question_policy',g.input),match.finish(yes,'Bool'),g.input,filter=True)
    argument=g.put(g.input,'binding',g.item(bindings,g.data(0)))
    answer=g.op('invoke',g.get(g.item(matches,g.data(0)),'method'),argument)
    save('knowledge_describe',g,g.choose(g.nonempty(matches),answer,g.call('knowledge_describe_facts',g.input)),
         'Look up a requested property in the taught computed-question table and invoke its method; otherwise retrieve ordinary stored facts.')

    # Small taught language examples. The matcher has no birthday branches:
    # every prefix, suffix, output relation and role alias is supplied as data.
    templates=[]
    for prefix in ['in how many days is ','how many days until ','how many days till ','how many days are left until ','how many days left until ','when is ']:
        for suffix in [' his birthday',' her birthday',"'s birthday",' birthday']:
            templates.append({'prefix':prefix,'suffix':suffix,'relation':'days until birthday'})
    g=G();save('language_question_policy',g,g.data({'templates':templates,'subject_aliases':{'my':'speaker','your':'assistant'},
        'replace':[['’',"'"],['?',''],['!','']]}),
        'Interpret these birthday-countdown question forms as a request for the days-until-birthday property. The relation then finds its taught calculation method; this is not a request for age.')
    nonempty=G();nonempty_word=nonempty.inverse(nonempty.eq(nonempty.input,nonempty.data('')))
    each=G();template=each.get(each.input,'item');text=each.get(each.input,'context');left=each.op('split_text',text,each.get(template,'prefix'))
    prefixok=each.both(each.eq(each.length(left),each.data(2)),each.eq(each.item(left,each.data(0)),each.data('')))
    tail=each.item(left,each.data(1));right=each.op('split_text',tail,each.get(template,'suffix'))
    suffixok=each.both(each.eq(each.length(right),each.data(2)),each.eq(each.item(right,each.data(-1)),each.data('')))
    subject=each.item(right,each.data(0));valid=each.both(suffixok,each.inverse(each.eq(subject,each.data(''))))
    candidate=each.record(subject=subject,relation=each.get(template,'relation'))
    found=each.choose(prefixok,each.choose(valid,each.op('data_list',candidate),each.data([])),each.data([]))
    g=G();policy=g.call('language_question_policy',g.input);text=g.op('lower',g.get(g.input,'text'))
    # The only normalization choices here are also explicit lesson data.
    guard=G();again=guard.nonempty(guard.get(guard.input,'pending'))
    body=G();s=body.input;replacement=body.item(body.get(s,'pending'),body.data(0))
    step=body.record(text=body.op('replace_text',body.get(s,'text'),body.get(replacement,0),body.get(replacement,1)),pending=body.op('slice',body.get(s,'pending'),start=1))
    normalized=g.loop(g.record(text=text,pending=g.get(policy,'replace')),guard.finish(again,'Bool'),body.finish(step))
    text=g.op('join_text',g.map(g.op('split_text',g.get(normalized,'text'),g.data(' ')),nonempty.finish(nonempty_word,'Bool'),filter=True),g.data(' '))
    matches=g.op('flatten',g.map(g.get(policy,'templates'),each.finish(found),text));first=g.item(matches,g.data(0));subject=g.get(first,'subject');aliases=g.get(policy,'subject_aliases')
    subject=g.choose(g.has(aliases,subject),g.item(aliases,subject),subject)
    op=g.record(op=g.data('describe'),subject=subject,relation=g.get(first,'relation'),object=g.data(''),negative=g.data(False),conditions=g.data([]),text=g.data(''))
    save('language_interpret',g,g.choose(g.nonempty(matches),g.record(operations=g.op('data_list',op)),g.data(None)),
        'Match taught question templates in priority order, capture the subject and bind role aliases. Return a description request for the taught property, or no match so the ordinary language interface can continue.')
    return suite


if __name__=='__main__':
    root=Path(__file__).parent
    base=json.loads((root/'curriculum/foundation.json').read_text())
    target=root/'curriculum/calendar_reasoning.json'
    target.write_text(json.dumps(build(base),indent=2)+'\n')
    print(target)
