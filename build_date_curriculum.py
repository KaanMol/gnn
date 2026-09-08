"""Taught calendar interpretation and clock-interface use."""
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description,kind='Data',**metadata):
        suite[name]={'graph':g.finish(out,kind,trace_mode='explicit',description=description,**metadata),'source':'Foundational calendar teaching: '+description}
    names=['january','february','march','april','may','june','july','august','september','october','november','december']
    months={name:i+1 for i,name in enumerate(names)}; months.update({name[:3]:i+1 for i,name in enumerate(names)})
    g=G(); save('calendar_vocabulary',g,g.data({'months':months,'ignored':['','the','of','on'],'suffixes':['','st','nd','rd','th'],
        'birth_relations':['birth date','date of birth','born on','was born on','birthday','birthdate','born'],
        'month_lengths':[31,28,31,30,31,30,31,31,30,31,30,31], 'birth_fields':{'birth.year':0,'birth.month':1,'birth.day':2}}),
        'Month names, ordinal endings, birth-relation vocabulary, month lengths and date-part bindings are taught data.')
    g=G(); a=g.get(g.input,'a'); b=g.get(g.input,'b')
    save('integer_modulo',g,g.calc('subtract',a,g.calc('multiply',g.calc('floor',g.calc('divide',a,b)),b)),'Compute the remainder by subtracting the divisor times the floored quotient.')
    digit=G(); yes=digit.op('contains',digit.data(list('0123456789')),digit.input,kind='Bool')
    nondigit=G(); no=nondigit.inverse(nondigit.op('contains',nondigit.data(list('0123456789')),nondigit.input,kind='Bool'))
    g=G(); chars=g.op('characters',g.input); digits=g.op('join_text',g.map(chars,digit.finish(yes,'Bool'),filter=True),g.data('')); suffix=g.op('join_text',g.map(chars,nondigit.finish(no,'Bool'),filter=True),g.data(''))
    valid=g.both(g.nonempty(digits),g.both(g.eq(g.textcat(digits,suffix),g.input),g.op('contains',g.get(g.call('calendar_vocabulary',g.input),'suffixes'),suffix,kind='Bool')))
    checked=g.op('require',valid,digits,message='Please give a complete birth date with an ordinary day, month and year.')
    save('calendar_integer',g,g.op('as_data',g.num(checked)),'Read a nonnegative integer optionally followed by a taught ordinal ending.')
    g=G(); parts=g.input; y=g.item(parts,g.data(0)); m=g.item(parts,g.data(1)); d=g.item(parts,g.data(2))
    leap=g.either(g.eq(g.call('integer_modulo',g.record(a=y,b=g.data(400))),g.data(0)),g.both(g.eq(g.call('integer_modulo',g.record(a=y,b=g.data(4))),g.data(0)),g.inverse(g.eq(g.call('integer_modulo',g.record(a=y,b=g.data(100))),g.data(0)))))
    bounds=g.both(g.both(g.lt(g.data(0),y),g.lt(y,g.data(10000))),g.both(g.lt(g.data(0),m),g.lt(m,g.data(13))))
    checked=g.op('require',bounds,parts,message='Please give a complete valid birth date.')
    normal=g.item(g.get(g.call('calendar_vocabulary',g.input),'month_lengths'),g.calc('subtract',g.item(checked,g.data(1)),g.data(1)))
    limit=g.choose(g.both(g.eq(m,g.data(2)),leap),g.data(29),normal)
    valid=g.both(g.lt(g.data(0),d),g.inverse(g.lt(limit,d)))
    save('calendar_validate',g,g.op('require',valid,checked,message='Please give a complete valid birth date; that day is outside the taught month length.'),'Validate calendar ranges and the Gregorian leap-year rule using the taught vocabulary and arithmetic.')
    filt=G(); token=filt.get(filt.input,'item'); ignored=filt.get(filt.input,'context'); yes=filt.inverse(filt.op('contains',ignored,token,kind='Bool'))
    g=G(); text=g.op('lower',g.input)
    for old,new in [('-', ' '),(',', ''),('\t',' '),('\n',' ')]:
        text=g.op('replace_text',text,g.data(old),g.data(new))
    vocabulary=g.call('calendar_vocabulary',g.input); tokens=g.map(g.op('split_text',text,g.data(' ')),filt.finish(yes,'Bool'),g.get(vocabulary,'ignored'),filter=True)
    tokens=g.op('require',g.eq(g.length(tokens),g.data(3)),tokens,message='Please give a complete birth date, such as 24 February 2000 or 2000-02-24.')
    a=g.item(tokens,g.data(0)); b=g.item(tokens,g.data(1)); c=g.item(tokens,g.data(2)); months=g.get(vocabulary,'months')
    namedmiddle=g.op('data_list',g.call('calendar_integer',c),g.item(months,b),g.call('calendar_integer',a))
    namedfirst=g.op('data_list',g.call('calendar_integer',c),g.item(months,a),g.call('calendar_integer',b))
    iso=g.op('require',g.eq(g.length(a),g.data(4)),g.op('data_list',g.call('calendar_integer',a),g.call('calendar_integer',b),g.call('calendar_integer',c)),message='Use a named month or the unambiguous YYYY-MM-DD format.')
    parts=g.choose(g.has(months,b),namedmiddle,g.choose(g.has(months,a),namedfirst,iso))
    save('calendar_parse',g,g.call('calendar_validate',parts),'Interpret taught month names, ordinal numbers and year-first numeric date text; validate the resulting calendar parts.')
    g=G(); texts=[]
    for i,width in [(0,4),(1,2),(2,2)]:
        text=g.textcat(g.data('0'*width),g.op('text',g.item(g.input,g.data(i))))
        texts.append(g.op('join_text',g.op('slice',g.op('characters',text),start=-width),g.data('')))
    save('calendar_format',g,g.op('join_text',g.op('data_list',*texts),g.data('-')),'Format validated date parts as a padded year-month-day string.')
    g=G(); a=g.get(g.input,'a'); b=g.get(g.input,'b'); comparison=g.eq(g.data(0),g.data(1))
    for i in (2,1,0):
        left=g.item(a,g.data(i)); right=g.item(b,g.data(i)); comparison=g.choose(g.eq(left,right),comparison,g.lt(left,right),kind='Bool')
    save('calendar_before',g,comparison,'Compare calendar dates lexicographically by year, month and day.','Bool')
    filt=G(); fact=filt.get(filt.input,'item'); ctx=filt.get(filt.input,'context')
    match=filt.both(filt.eq(filt.op('lower',filt.item(fact,filt.data(1))),filt.op('lower',filt.get(ctx,'subject'))),filt.op('contains',filt.get(ctx,'relations'),filt.op('lower',filt.item(fact,filt.data(0))),kind='Bool'))
    conflict=G(); yes=conflict.op('contains',conflict.get(conflict.input,'context'),conflict.get(conflict.input,'item'),kind='Bool')
    parse=G(); parts=parse.call('calendar_parse',parse.item(parse.input,parse.data(2)))
    g=G(); vocabulary=g.call('calendar_vocabulary',g.input); ctx=g.record(subject=g.get(g.input,'subject'),relations=g.get(vocabulary,'birth_relations'))
    matches=g.map(g.get(g.input,'facts'),filt.finish(match,'Bool'),ctx,filter=True)
    matches=g.op('require',g.nonempty(matches),matches,message="I don't know that person's complete birth date yet. Tell me when they were born.")
    matches=g.op('require',g.inverse(g.nonempty(g.map(matches,conflict.finish(yes,'Bool'),g.get(g.input,'negatives'),filter=True))),matches,message='The birth date has conflicting evidence. Please correct it first.')
    dates=g.op('unique',g.map(matches,parse.finish(parts)))
    dates=g.op('require',g.eq(g.length(dates),g.data(1)),dates,message='I have multiple birth dates for that person. Which one should I keep?')
    save('calendar_find_birth',g,g.record(parts=g.item(dates,g.data(0)),facts=matches),'Find birth facts using taught relation vocabulary, reject conflicts, and interpret consistent dates with the taught calendar methods.')
    field=G(); name=field.get(field.input,'item'); ctx=field.get(field.input,'context'); idx=field.item(field.get(ctx,'bindings'),name)
    part=field.item(field.get(ctx,'parts'),idx)
    g=G(); values=g.map(g.get(g.input,'fields'),field.finish(part),g.record(parts=g.get(g.input,'parts'),bindings=g.get(g.call('calendar_vocabulary',g.input),'birth_fields')))
    save('calendar_bind_input',g,values,'Connect named date-part input fields to their taught positions in a birth-date representation.')
    g=G(); save('clock_observe',g,g.op('observe',g.input,surface='clock'),'Observe the raw local clock port using its taught interface binding.')
    g=G(); observation=g.call('clock_observe',g.input); parts=g.call('calendar_parse',g.get(observation,'date'))
    parts=g.op('emit',parts,observation,label='current_date')
    save('clock_calendar',g,g.op('as_numbers',parts,kind='List[Number]'),'Read the raw clock interface and interpret its date string using taught calendar knowledge.','List[Number]',interface='current_date')
    return suite
