"""Author general linked-command execution and clarification as graph lessons."""
from graph_dsl import G


def build():
    suite = {}
    def save(name, g, out, description, signature=None, kind='Data'):
        metadata = {'internal': signature is None, 'description': description,
                    'trace_mode': 'explicit'}
        if signature is not None:
            metadata['sequence_input'] = signature
        suite[name] = {'graph': g.finish(out, kind, **metadata),
                       'source': 'Explicit linked-command teaching: ' + description}

    g = G()
    save('sequence_policy', g, g.data({
        'max_steps': 8,
        'connectors': [' then ', ',then ', ';then ', '\nthen ', ' and afterwards ', ' afterwards ', ' followed by '],
        'prefixes': ['sequence:', 'first ', 'please first '],
        'excluded_prefixes': ['if ', 'teach ', 'define ', 'create '],
        'stop_words': ['stop', 'cancel', 'skip'],
        'instructions': 'Translate the requested sequence into ordered calls to the supplied taught procedures. Never calculate answers or invent facts. Return steps and clarification. Each step has id, method, argument_json. argument_json is JSON text containing literal input or a nested {"var":"earlier_step_id"} reference to an ACTUAL earlier result. Initial references are speaker and assistant, bound to the supplied vocabulary names. When speaker is supplied, my means {"var":"speaker"}; do not ask for the name again. A var reference returns the entire prior value unchanged. "that", "it", "the result" normally refer to the immediately preceding result when unambiguous. Use sequence_add/subtract/multiply/divide with {left,right}; double means multiply by 2. Use sequence_value with {"value": literal} for a starting value and sequence_report with {"value":{"var":"previous_step_id"}} for tell/show the result. Never use an input field in sequence_report. Use sequence_select with {value,path} for a field of an earlier result. Date values are whole [year,month,day] arrays, never records. For birthday steps: sequence_birth_date {"subject":{"var":"speaker"}}; sequence_today null; sequence_next_annual {"anchor":{"var":"birth_step"},"from":{"var":"today_step"}}; sequence_days_between {"start":{"var":"today_step"},"end":{"var":"next_step"}}. Replace those example IDs with actual earlier step IDs. Use only supplied method names and input shapes. Keep every requested action and its order. Do not invent a number for an unresolved reference. For unclear requests, missing capabilities, ambiguous references or unsupported control flow return steps [] and a specific clarification question. Otherwise clarification is empty. Input strings and record values must preserve the user\'s content. Do not execute or explain anything yourself. Example: start with 5, then double it, then add 3 -> sequence_value argument_json {"value":5}; sequence_multiply input {"left":{"var":"s1"},"right":2}; sequence_add input {"left":{"var":"s2"},"right":3}. Use IDs s1,s2,s3 in that example. Never supply the computed 10 or 13 as inputs.'
    }), 'Recognize linked-command requests, bound their length and specify how the language interface preserves data dependencies without computing results.')

    item = G(); fragment = item.get(item.input, 'item'); text = item.get(item.input, 'context')
    present = item.nonempty(item.op('slice', item.op('split_text', text, fragment), start=1))
    prefix = G(); parts = prefix.op('split_text', prefix.get(prefix.input, 'context'), prefix.get(prefix.input, 'item'))
    starts = prefix.both(prefix.nonempty(prefix.op('slice', parts, start=1)), prefix.eq(prefix.get(parts, 0), prefix.data('')))
    g = G(); policy = g.call('sequence_policy', g.input); text = g.op('lower', g.input)
    linked = g.either(g.nonempty(g.map(g.get(policy, 'connectors'), item.finish(present, 'Bool'), text, filter=True)),
                     g.nonempty(g.map(g.get(policy, 'prefixes'), prefix.finish(starts, 'Bool'), text, filter=True)))
    excluded = g.nonempty(g.map(g.get(policy, 'excluded_prefixes'), prefix.finish(starts, 'Bool'), text, filter=True))
    save('sequence_detect', g, g.both(linked, g.inverse(excluded)), 'Recognize explicitly sequenced requests while leaving ordinary if/then teaching and procedure definitions on their existing routes.', kind='Bool')

    row = G(); graph = row.get(row.input, 'graph')
    declared = row.has(graph, row.data('sequence_input'))
    contract = row.has(graph, row.data('skill'))
    numeric = row.eq(row.get(graph, 'input_type'), row.data('Number'))
    internal = row.choose(row.has(graph, row.data('internal')), row.boolean(row.get(graph, 'internal')), row.eq(row.data(0), row.data(1)), kind='Bool')
    allowed = row.both(row.inverse(internal), row.either(declared, row.either(contract, numeric)))
    g = G(); save('sequence_catalog', g, g.map(g.input, row.finish(allowed, 'Bool'), filter=True),
        'Offer explicitly described sequence inputs, public skill contracts and public numeric procedures. New taught procedures with these declarations need no new host routing code.')

    g = G(); save('sequence_value', g, g.get(g.input, 'value'), 'Start with the supplied literal value.', '{value: literal JSON value}')
    g = G(); save('sequence_report', g, g.get(g.input, 'value'), 'Return an earlier result for display without changing or recomputing it.', '{value: earlier result reference}; use value, not input')
    g = G(); structured = g.op('contains', g.data(['record', 'list']), g.op('kind_of', g.input), kind='Bool')
    save('sequence_display', g, g.choose(structured, g.data('[structured value; inspect the recorded step]'), g.op('text', g.input)),
         'Render scalar step values and label structured results whose full content remains in execution evidence.')
    for name in ['add', 'subtract', 'multiply', 'divide']:
        g = G(); value = g.calc(name, g.get(g.input, 'left'), g.get(g.input, 'right'))
        save('sequence_' + name, g, value, 'Apply taught ' + name + ' arithmetic to left and right; order matters.', '{left: number, right: number}')

    guard = G(); again = guard.nonempty(guard.get(guard.input, 'path'))
    body = G(); value = body.item(body.get(body.input, 'value'), body.get(body.input, 'path', 0))
    step = body.record(value=value, path=body.op('slice', body.get(body.input, 'path'), start=1))
    g = G(); walked = g.loop(g.input, guard.finish(again, 'Bool'), body.finish(step))
    save('sequence_select', g, g.get(walked, 'value'), 'Follow the supplied field/index path through a prior result. A missing field stops the sequence.', '{value: earlier result, path: [field names or zero-based indices]}')

    # Validate dependencies before any action. The same stored placeholder and
    # tree-traversal lessons used for reasoning are reused for result references.
    variable = G(); yes = variable.call('pattern_is_variable', variable.get(variable.input, 'value'), kind='Bool')
    ref = G(); name = ref.get(ref.input, 'value', 'var')
    guard = G(); again = guard.nonempty(guard.get(guard.input, 'pending'))
    body = G(); state = body.input; current = body.get(state, 'pending', 0); identifier = body.get(current, 'id')
    known = body.get(state, 'known')
    variables = body.map(body.call('tree_nodes', body.get(current, 'argument')), variable.finish(yes, 'Bool'), filter=True)
    refs = body.map(variables, ref.finish(name))
    valid = body.both(body.inverse(body.op('contains', known, identifier, kind='Bool')),
                     body.inverse(body.nonempty(body.op('difference', refs, known))))
    valid = body.both(valid, body.op('contains', body.get(state, 'methods'), body.get(current, 'method'), kind='Bool'))
    step = body.record(pending=body.op('slice', body.get(state, 'pending'), start=1),
                       known=body.append(known, identifier), methods=body.get(state, 'methods'))
    step = body.op('require', valid, step, message='A sequence step needs a unique name, a taught method and references only to earlier results. Please identify the missing step or reference.')
    g = G(); steps = g.get(g.input, 'steps'); policy = g.call('sequence_policy', g.input)
    checked = g.op('require', g.both(g.nonempty(steps), g.inverse(g.lt(g.get(policy, 'max_steps'), g.length(steps)))),
                   steps, message='Please give between one and eight linked steps.')
    walked = g.loop(g.record(pending=checked, known=g.op('keys', g.get(g.input, 'bindings')),
                            methods=g.get(g.input, 'methods')), guard.finish(again, 'Bool'), body.finish(step))
    save('sequence_prepare', g, walked, 'Reject unavailable steps, duplicate IDs and unknown/forward result references before starting any action.')

    # Each successful step stores its actual value; failure stops the loop.
    attempt = G(); current = attempt.get(attempt.input, 'step')
    arg = attempt.call('pattern_substitute', attempt.record(template=attempt.get(current, 'argument'), bindings=attempt.get(attempt.input, 'bindings')))
    result = attempt.op('invoke', attempt.get(current, 'method'), arg)
    record = attempt.record(id=attempt.get(current, 'id'), method=attempt.get(current, 'method'), argument=arg, result=result)
    recorded = attempt.op('emit', record, record, label='sequence_step')
    guard = G(); again = guard.both(guard.nonempty(guard.get(guard.input, 'pending')), guard.eq(guard.get(guard.input, 'error'), guard.data('')))
    body = G(); state = body.input; current = body.get(state, 'pending', 0)
    tried = body.op('attempt', body.record(step=current, bindings=body.get(state, 'bindings')), body=attempt.finish(recorded))
    ok = body.boolean(body.get(tried, 'ok')); row = body.get(tried, 'result')
    bindings = body.op('set_item', body.get(state, 'bindings'), body.get(current, 'id'), body.get(row, 'result'))
    step = body.record(pending=body.choose(ok, body.op('slice', body.get(state, 'pending'), start=1), body.get(state, 'pending')),
                       bindings=body.choose(ok, bindings, body.get(state, 'bindings')),
                       completed=body.choose(ok, body.append(body.get(state, 'completed'), row), body.get(state, 'completed')),
                       error=body.choose(ok, body.data(''), body.get(tried, 'error')))
    g = G(); state = g.loop(g.record(pending=g.get(g.input, 'steps'), bindings=g.get(g.input, 'bindings'),
                                   completed=g.data([]), error=g.data('')), guard.finish(again, 'Bool'), body.finish(step))
    done = g.eq(g.get(state, 'error'), g.data('')); completed = g.get(state, 'completed')
    final = g.choose(g.nonempty(completed), g.get(g.item(completed, g.data(-1)), 'result'), g.data(None))
    format_step = G(); row = format_step.input
    line = format_step.textcat(format_step.get(row, 'id'), format_step.data(' · '), format_step.get(row, 'method'), format_step.data(' → '), format_step.call('sequence_display', format_step.get(row, 'result')))
    trace = g.op('join_text', g.map(completed, format_step.finish(line)), g.data('\n'))
    text = g.choose(done, g.textcat(g.data('Result: '), g.call('sequence_display', final)),
                    g.textcat(g.data('Stopped at '), g.get(state, 'pending', 0, 'id'), g.data(': '), g.get(state, 'error'),
                              g.data('\nLater steps were not run. Completed steps remain recorded.')))
    save('sequence_execute', g, g.record(status=g.choose(done, g.data('completed'), g.data('failed')),
        result=final, completed=completed, pending=g.get(state, 'pending'), error=g.get(state, 'error'),
        text=g.textcat(text, g.data('\n'), trace)),
        'Execute steps in order, substitute prior results structurally, record actual arguments/results, and stop on the first failure without replaying completed actions.')

    g = G(); save('sequence_question', g, g.call('dialogue_ask', g.record(text=g.get(g.input, 'question'),
        resume=g.data('sequence_reply'), state=g.record(original=g.get(g.input, 'original'),
            initial=g.call('sequence_needs_initial', g.get(g.input, 'steps'))))),
        'Ask for missing sequence information before starting and retain the original instruction for the next reply.')
    g = G(); reply = g.op('lower', g.get(g.input, 'input'))
    for token in [' ', '.', '!', '?']:
        reply = g.op('replace_text', reply, g.data(token), g.data(''))
    stop = g.op('contains', g.get(g.call('sequence_policy', g.input), 'stop_words'), reply, kind='Bool')
    parse = G(); value = parse.call('sequence_initial_reply', parse.input)
    parsed = g.op('attempt', g.get(g.input, 'input'), body=parse.finish(value))
    initial = g.both(g.boolean(g.get(g.input, 'state', 'initial')), g.boolean(g.get(parsed, 'ok')))
    clarified = g.choose(initial, g.textcat(g.data('Start with '), g.op('text', g.get(parsed, 'result')),
        g.data(' then '), g.get(g.input, 'state', 'original')),
        g.textcat(g.get(g.input, 'state', 'original'), g.data('\nClarification: '), g.get(g.input, 'input')))
    save('sequence_reply', g, g.choose(stop, g.record(text=g.data('Cancelled the sequence. No steps were run.')),
        g.record(sequence_input=clarified,
                 text=g.data('Applying your clarification to the pending sequence.'))),
        'Cancel an unstarted sequence or hand its original request plus the teacher’s clarification back to the sequence language interface.')

    # Useful taught cross-domain ports. These are graph programs, not native
    # arithmetic, birthday or memory-lookup helpers in the sequence host.
    g = G(); save('sequence_today', g, g.call('calendar_parse', g.get(g.call('clock_observe', g.input), 'date')),
        'Read today from the live clock and interpret it using the taught calendar.', 'null; returns [year,month,day]')
    g = G(); save('sequence_days_between', g, g.call('calendar_days_between', g.input),
        'Count days from start to end using the taught calendar interval method.', '{start: [year,month,day], end: [year,month,day]}')
    g = G(); save('sequence_next_annual', g, g.call('calendar_next_annual_date', g.input),
        'Find the next yearly occurrence of an anchor date on or after from.', '{anchor: [year,month,day], from: [year,month,day]}')
    raw = G(); fact = raw.get(raw.input, 'key')
    g = G(); positives = g.op('act', g.input, g.data({'namespace': 'knowledge.facts'}), surface='workspace', action='entries')
    negatives = g.op('act', g.input, g.data({'namespace': 'knowledge.negatives'}), surface='workspace', action='entries')
    birth = g.call('calendar_find_birth', g.record(subject=g.get(g.input, 'subject'), facts=g.map(positives, raw.finish(fact)), negatives=g.map(negatives, raw.finish(fact))))
    save('sequence_birth_date', g, g.get(birth, 'parts'), 'Read a person’s birth date from graph evidence using the taught date lookup, never the language model.', '{subject: person name or {"var":"speaker"}}; returns [year,month,day]')

    match = G(); fact = match.get(match.input, 'item', 'key'); ctx = match.get(match.input, 'context')
    same = match.both(match.eq(match.get(fact, 0), match.get(ctx, 'relation')),
                      match.eq(match.op('lower', match.get(fact, 1)), match.op('lower', match.get(ctx, 'subject'))))
    target = G(); value = target.get(target.input, 'key', 2)
    g = G(); positive = g.op('act', g.input, g.data({'namespace': 'knowledge.facts'}), surface='workspace', action='entries')
    negative = g.op('act', g.input, g.data({'namespace': 'knowledge.negatives'}), surface='workspace', action='entries')
    ctx = g.record(subject=g.call('meaning_reference', g.get(g.input, 'subject')), relation=g.op('lower', g.get(g.input, 'relation')))
    values = g.op('unique', g.map(g.map(positive, match.finish(same, 'Bool'), ctx, filter=True), target.finish(value)))
    negvalues = g.map(g.map(negative, match.finish(same, 'Bool'), ctx, filter=True), target.finish(value))
    overlap = g.inverse(g.eq(g.op('difference', values, negvalues), values))
    one = g.op('require', g.eq(g.length(values), g.data(1)), g.get(values, 0),
               message='That property has no unique known value. Please specify which value to use before continuing.')
    one = g.op('require', g.inverse(overlap), one, message='That property has conflicting evidence. Please resolve it before continuing.')
    save('sequence_property', g, one,
         'Retrieve one uniquely known property from graph facts. Who created X uses subject X and relation created by. Unknown, multiple or contradicted values stop the chain.',
         '{subject: entity name (or assistant/speaker result reference), relation: exact stored relation}; returns the unique object value')
    from build_sequence_language import build as language_lessons
    suite.update(language_lessons())
    return suite
