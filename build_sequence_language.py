"""Taught clause templates for common linked commands; no native parser at runtime."""
from graph_dsl import G


def build():
    suite = {}
    def save(name, g, out, description):
        suite[name] = {'graph': g.finish(out, internal=True, trace_mode='explicit', description=description),
                       'source': 'Explicit sequence language lesson: ' + description}
    templates = []
    def add(prefix, method, argument, capture='none', suffix='', provides=''):
        templates.append(dict(prefix=prefix, suffix=suffix, capture=capture, method=method,
                              argument=argument, provides=provides))
    previous, literal = {'var': 'previous'}, {'var': 'literal'}
    for prefix in ['start with ', 'begin with ', 'take ']:
        add(prefix, 'sequence_value', {'value': literal}, 'number')
    for verb, method in [('add', 'add'), ('subtract', 'subtract')]:
        for suffix in ['', ' to it', ' to that', ' to the result'] if verb == 'add' else ['', ' from it', ' from that', ' from the result']:
            add(verb+' ', 'sequence_'+method, {'left':previous,'right':literal}, 'number', suffix)
    for verb, method in [('multiply', 'multiply'), ('divide', 'divide')]:
        for reference in ['', 'it ', 'that ', 'the result ']:
            add(verb+' '+reference+'by ', 'sequence_'+method, {'left':previous,'right':literal}, 'number')
    for word, factor in [('double', 2), ('triple', 3)]:
        for reference in ['it', 'that', 'the result']:
            add(word+' '+reference, 'sequence_multiply', {'left':previous,'right':factor})
    for phrase in ['tell me the result', 'show me the result', 'report the result', 'tell me the answer', 'show the result']:
        add(phrase, 'sequence_report', {'value':previous})
    for prefix, preposition in [('run ', ' on '), ('apply ', ' to ')]:
        for reference in ['that', 'it', 'the result']:
            add(prefix, literal, previous, 'text', preposition+reference)
    add('get my birth date', 'sequence_birth_date', {'subject':{'var':'speaker'}}, provides='birth')
    add('get ', 'sequence_birth_date', {'subject':literal}, 'text', "'s birth date", 'birth')
    for phrase in ["get today's date", 'get today', 'read today', "read today's date"]:
        add(phrase, 'sequence_today', None, provides='today')
    for phrase in ['find the next birthday', 'find my next birthday', 'find the next yearly occurrence']:
        add(phrase, 'sequence_next_annual', {'anchor':{'var':'birth'},'from':{'var':'today'}}, provides='next_date')
    for phrase in ['calculate how many days are left', 'count the days left', 'calculate the days remaining']:
        add(phrase, 'sequence_days_between', {'start':{'var':'today'},'end':{'var':'next_date'}})
    g=G();save('sequence_clause_policy',g,g.data(templates),
        'Teach reusable clause shapes, literal captures, prior-result references and named date roles. These templates select taught methods; they contain no computed answers.')

    nonempty=G();keep=nonempty.inverse(nonempty.eq(nonempty.input,nonempty.data('')))
    g=G();words=g.map(g.op('split_text',g.op('lower',g.input),g.data(' ')),nonempty.finish(keep,'Bool'),filter=True)
    text=g.op('join_text',words,g.data(' '));chars=g.op('characters',text)
    ending=g.op('contains',g.data(['.',',',';','?','!']),g.item(chars,g.data(-1)),kind='Bool')
    clean=g.choose(g.nonempty(chars),g.choose(ending,g.op('join_text',g.op('slice',chars,stop=-1),g.data('')),text),text)
    save('sequence_clean_clause',g,clean,'Normalize clause whitespace/case and one terminal punctuation mark while preserving decimal points inside numbers.')

    each=G();rule=each.get(each.input,'item');text=each.get(each.input,'context')
    parts=each.op('split_text',text,each.get(rule,'prefix'))
    starts=each.both(each.eq(each.length(parts),each.data(2)),each.eq(each.get(parts,0),each.data('')))
    tail=each.get(parts,1);suffix=each.get(rule,'suffix');end=each.op('split_text',tail,suffix)
    ending=each.choose(each.eq(suffix,each.data('')),each.eq(text,text),
        each.both(each.eq(each.length(end),each.data(2)),each.eq(each.item(end,each.data(-1)),each.data(''))),kind='Bool')
    captured=each.choose(each.eq(suffix,each.data('')),tail,each.get(end,0))
    valid=each.choose(each.eq(each.get(rule,'capture'),each.data('none')),each.eq(text,each.get(rule,'prefix')),
        each.choose(starts,each.both(ending,each.inverse(each.eq(captured,each.data('')))),each.eq(text,each.data('')),kind='Bool'),kind='Bool')
    out=each.record(rule=rule,literal=each.choose(each.eq(each.get(rule,'capture'),each.data('none')),each.data(''),captured))
    g=G();matches=g.op('flatten',g.map(g.call('sequence_clause_policy',g.input),
        each.finish(each.choose(valid,each.op('data_list',out),each.data([]))),g.input))
    # Longer suffix templates are tried before the no-suffix version, so the
    # number reader never receives "3 to that" as a numeric literal.
    save('sequence_clause_matches',g,matches,'Collect recognized clause forms; the compiler tries numeric captures without accepting a partial sentence.')

    candidate=G();row=candidate.get(candidate.input,'item');ctx=candidate.get(candidate.input,'context');rule=candidate.get(row,'rule')
    parse=G();r=parse.get(parse.input,'row');literal=parse.get(r,'literal');rule2=parse.get(r,'rule')
    value=parse.choose(parse.eq(parse.get(rule2,'capture'),parse.data('number')),parse.op('as_data',parse.num(literal)),literal)
    bindings=parse.put(parse.get(parse.input,'refs'),'literal',value)
    argument=parse.call('pattern_substitute',parse.record(template=parse.get(rule2,'argument'),bindings=bindings))
    method=parse.call('pattern_substitute',parse.record(template=parse.get(rule2,'method'),bindings=bindings))
    parsed=parse.record(method=method,argument=argument,provides=parse.get(rule2,'provides'))
    attempted=candidate.op('attempt',candidate.record(row=row,refs=ctx),body=parse.finish(parsed))
    selected=candidate.choose(candidate.boolean(candidate.get(attempted,'ok')),candidate.op('data_list',candidate.get(attempted,'result')),candidate.data([]))
    guard=G();again=guard.both(guard.nonempty(guard.get(guard.input,'pending')),guard.boolean(guard.get(guard.input,'ok')))
    body=G();s=body.input;clause=body.call('sequence_clean_clause',body.get(s,'pending',0))
    options=body.op('flatten',body.map(body.call('sequence_clause_matches',clause),candidate.finish(selected),body.get(s,'refs')))
    found=body.nonempty(options);chosen=body.get(options,0);identifier=body.textcat(body.data('s'),body.op('text',body.calc('add',body.length(body.get(s,'steps')),body.data(1))))
    reference=body.record(var=identifier);refs=body.put(body.get(s,'refs'),'previous',reference)
    refs=body.choose(body.eq(body.get(chosen,'provides'),body.data('')),refs,
        body.op('set_item',refs,body.get(chosen,'provides'),reference))
    step=body.record(id=identifier,method=body.get(chosen,'method'),argument=body.get(chosen,'argument'))
    updated=body.record(pending=body.op('slice',body.get(s,'pending'),start=1),ok=body.datum(found),
        refs=body.choose(found,refs,body.get(s,'refs')),steps=body.choose(found,body.append(body.get(s,'steps'),step),body.get(s,'steps')))
    g=G();text=g.op('lower',g.input)
    for before,after in [('’',"'"),('sequence: ',''),(' and then ',' then '),(',then ',' then '),(';then ',' then '),('\nthen ',' then '),(' and afterwards ',' then '),(' afterwards ',' then '),(' followed by ',' then ')]:
        text=g.op('replace_text',text,g.data(before),g.data(after))
    initial={key:{'var':key} for key in ['previous','literal','speaker','assistant','birth','today','next_date']}
    loop=g.loop(g.record(pending=g.op('split_text',text,g.data(' then ')),refs=g.data(initial),steps=g.data([]),ok=g.data(True)),guard.finish(again,'Bool'),body.finish(updated))
    save('sequence_interpret',g,g.choose(g.boolean(g.get(loop,'ok')),g.get(loop,'steps'),g.data(None)),
        'Compile an entirely recognized sequence into linked steps. Any unmatched clause returns no plan, allowing the language interface to interpret the whole request instead of dropping a step.')

    row=G();value=row.get(row.input,'value')
    needed=row.eq(value,row.data({'var':'previous'}))
    g=G();save('sequence_needs_initial',g,g.datum(g.nonempty(g.map(g.call('tree_nodes',g.input),row.finish(needed,'Bool'),filter=True))),
        'Identify a sequence that uses the previous result before establishing an initial value.')
    g=G();text=g.call('sequence_clean_clause',g.input)
    text=g.op('replace_text',text,g.data('start with '),g.data(''))
    save('sequence_initial_reply',g,g.op('as_data',g.num(text)),
        'Read a supplied numeric starting value with the taught number reader after an initial-reference clarification.')
    return suite
