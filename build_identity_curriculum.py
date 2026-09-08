"""Author removable dialogue-reference and relationship-language graph lessons."""
import copy

from graph_dsl import G


def build(library):
    suite = {}

    def save(name, g, output, description):
        suite[name] = {'graph': g.finish(output, internal=True, trace_mode='explicit',
                                       description=description),
                       'source': 'Explicit dialogue teaching: ' + description}

    # Preserve the previously taught meaning and language methods on first install.
    # Rebuilding this package must not wrap its own dispatcher recursively.
    for name in ('meaning_fact', 'language_interpret'):
        base = name + '_before_identity'
        suite[base] = copy.deepcopy(library[base] if base in library else library[name])

    g = G()
    save('meaning_reference_policy', g, g.data([
        {'canonical': 'human', 'forms': ['human', 'humans'],
         'kind': 'concept word forms',
         'source': 'Explicit teaching: humans is the plural name of the human concept. A relation to this concept does not by itself assert that relation to every individual human.'}
    ]), 'Declare the labels that refer to the same concept node. This table teaches human/humans explicitly; no suffix-stripping heuristic is used.')
    match = G(); row = match.get(match.input, 'item')
    yes = match.op('contains', match.get(row, 'forms'), match.get(match.input, 'context'), kind='Bool')
    target = G(); canonical = target.get(target.input, 'canonical')
    g = G(); matches = g.map(g.call('meaning_reference_policy', g.input), match.finish(yes, 'Bool'),
                            g.op('lower', g.input), filter=True)
    targets = g.op('unique', g.map(matches, target.finish(canonical)))
    save('meaning_reference', g, g.choose(g.eq(g.length(targets), g.data(1)),
                                        g.item(targets, g.data(0)), g.input),
         'Resolve only uniquely taught label forms to their shared concept. Unknown or ambiguous names remain unchanged, including Homo sapiens and unrelated proper names.')

    g = G()
    save('dialogue_reference_policy', g, g.data({
        'aliases': {'you': 'addressee', 'your': 'addressee', 'yourself': 'addressee',
                    'assistant': 'addressee', 'addressee': 'addressee',
                    'i': 'speaker', 'me': 'speaker', 'my': 'speaker',
                    'myself': 'speaker', 'speaker': 'speaker'},
        'subject_operations': ['assert', 'retract', 'query', 'describe', 'date_procedure'],
        'object_operations': ['assert', 'retract', 'query', 'find'],
        'membership_relation': 'is',
        'self_prefix': 'I am ',
        'unknown_description': "I haven't learned that yet. You can teach me.",
    }), 'Resolve dialogue roles from the current speaker and addressee. Names of procedures, new names and category labels are not dialogue references.')

    g = G(); policy = g.call('dialogue_reference_policy', g.input)
    text = g.get(g.input, 'text'); lower = g.op('lower', text)
    aliases = g.get(policy, 'aliases'); context = g.get(g.input, 'context')
    role = g.item(aliases, lower)
    value = g.choose(g.has(aliases, lower), g.item(context, role), text)
    # Explicit names and role references converge without merging other entities.
    for role_name in ('speaker', 'addressee'):
        name = g.get(context, role_name)
        valid = g.inverse(g.eq(name, g.data(None)))
        same = g.eq(lower, g.op('lower', name))
        value = g.choose(g.both(valid, same), name, value)
    value = g.op('require', g.inverse(g.eq(value, g.data(None))), value,
                 message='What name should I use for that dialogue participant?')
    save('dialogue_reference', g, value,
         'Bind a dialogue reference to the current participant, including either participant’s explicit name. Missing participants require clarification.')

    g = G()
    save('relationship_language_policy', g, g.data([
        {'relation': relation, 'canonical': 'created by', 'reverse': reverse}
        for relation, reverse in [('created by', False), ('was created by', False),
                                  ('create', True), ('created', True), ('creator of', True)]
    ]), 'Teach the active/passive meanings of creation: A created B and A is creator of B mean B created by A. This supplies no creator facts.')

    match = G(); row = match.get(match.input, 'item')
    yes = match.eq(match.get(row, 'relation'), match.get(match.input, 'context'))
    g = G(); fact = g.call('meaning_fact_before_identity', g.input)
    fact = g.op('data_list', g.get(fact, 0), g.call('meaning_reference', g.get(fact, 1)),
                g.call('meaning_reference', g.get(fact, 2)))
    choices = g.map(g.call('relationship_language_policy', g.input), match.finish(yes, 'Bool'),
                    g.get(fact, 0), filter=True)
    rule = g.item(choices, g.data(0)); reverse = g.boolean(g.get(rule, 'reverse'))
    normalized = g.op('data_list', g.get(rule, 'canonical'),
                      g.choose(reverse, g.get(fact, 2), g.get(fact, 1)),
                      g.choose(reverse, g.get(fact, 1), g.get(fact, 2)))
    save('meaning_fact', g, g.choose(g.eq(g.length(choices), g.data(1)), normalized, fact),
         'Normalize only uniquely taught relationship forms after existing phrase interpretation. The same normalization applies to positive and negative assertions and queries.')

    g = G(); item = g.get(g.input, 'operation'); context = g.get(g.input, 'context')
    policy = g.call('dialogue_reference_policy', g.input); kind = g.get(item, 'op')
    subject = g.get(item, 'subject'); obj = g.get(item, 'object')
    for field, value in [('subject', subject), ('object', obj)]:
        enabled = g.op('contains', g.get(policy, field + '_operations'), kind, kind='Bool')
        if field == 'object':
            enabled = g.both(enabled, g.inverse(g.eq(g.get(item, 'relation'), g.get(policy, 'membership_relation'))))
        reference = g.call('dialogue_reference', g.record(text=value, context=context))
        item = g.put(item, field, g.choose(enabled, reference, value))
    save('dialogue_resolve_operation', g, item,
         'Resolve subject and object references only in fields that denote participants; preserve concept filters, category values, new names and executable skill identifiers.')

    g = G(); policy = g.call('dialogue_reference_policy', g.input)
    facts = g.get(g.input, 'description')
    prefix = g.textcat(g.get(policy, 'self_prefix'), g.get(g.input, 'name'), g.data('.'))
    answer = g.choose(g.eq(facts, g.get(policy, 'unknown_description')), prefix,
                      g.textcat(prefix, g.data('\n'), facts))
    save('dialogue_self_description', g, answer,
         'State the current assistant name and include its ordinary retrieved knowledge. Do not replace learned self-facts with a fixed biography.')

    templates = []
    for prefix in ['who created ', 'who made ', 'who is the creator of ']:
        templates.append({'prefix': prefix, 'suffix': '', 'op': 'describe',
                          'capture': 'subject', 'subject': '', 'object': '', 'relation': 'created by'})
    templates.append({'prefix': 'who is ', 'suffix': ' creator', 'op': 'describe',
                      'capture': 'subject', 'subject': '', 'object': '', 'relation': 'created by'})
    for prefix in ['who did ', 'what did ']:
        templates.append({'prefix': prefix, 'suffix': ' create', 'op': 'find',
                          'capture': 'object', 'subject': '', 'object': '', 'relation': 'created by'})
    templates.append({'prefix': '', 'suffix': ' is your creator', 'op': 'assert',
                      'capture': 'object', 'subject': 'assistant', 'object': '', 'relation': 'created by'})
    g = G()
    save('dialogue_question_policy', g, g.data(templates),
         'Teach creation-question forms and which participant to retrieve. These templates contain no entity names or answers; add other forms by teaching this table.')

    nonempty = G(); keep = nonempty.inverse(nonempty.eq(nonempty.input, nonempty.data('')))
    each = G(); template = each.get(each.input, 'item'); text = each.get(each.input, 'context')
    prefix = each.get(template, 'prefix'); suffix = each.get(template, 'suffix')
    left = each.op('split_text', text, prefix)
    prefix_ok = each.choose(each.eq(prefix, each.data('')), each.eq(text, text),
        each.both(each.eq(each.length(left), each.data(2)), each.eq(each.get(left, 0), each.data(''))), kind='Bool')
    tail = each.choose(each.eq(prefix, each.data('')), text, each.get(left, 1))
    right = each.op('split_text', tail, suffix)
    suffix_ok = each.choose(each.eq(suffix, each.data('')), each.eq(text, text),
        each.both(each.eq(each.length(right), each.data(2)), each.eq(each.item(right, each.data(-1)), each.data(''))), kind='Bool')
    captured = each.choose(each.eq(suffix, each.data('')), tail, each.get(right, 0))
    valid = each.both(suffix_ok, each.inverse(each.eq(captured, each.data(''))))
    op = each.record(op=each.get(template, 'op'), subject=each.get(template, 'subject'),
                     relation=each.get(template, 'relation'), object=each.get(template, 'object'),
                     negative=each.data(False), conditions=each.data([]), text=each.data(''))
    op = each.op('set_item', op, each.get(template, 'capture'), captured)
    found = each.choose(prefix_ok, each.choose(valid, each.op('data_list', op), each.data([])), each.data([]))
    g = G(); text = g.op('lower', g.get(g.input, 'text'))
    for before, after in [('’', "'"), ('?', ''), ('!', '')]:
        text = g.op('replace_text', text, g.data(before), g.data(after))
    text = g.op('join_text', g.map(g.op('split_text', text, g.data(' ')), nonempty.finish(keep, 'Bool'), filter=True), g.data(' '))
    matches = g.op('flatten', g.map(g.call('dialogue_question_policy', g.input), each.finish(found), text))
    save('dialogue_interpret', g, g.choose(g.nonempty(matches),
        g.record(operations=g.op('data_list', g.item(matches, g.data(0)))), g.data(None)),
        'Match taught relationship question forms, retaining the known participant and correct lookup direction. Unmatched wording goes to the existing language interface.')
    g = G(); interpreted = g.call('dialogue_interpret', g.input)
    save('language_interpret', g, g.choose(g.eq(interpreted, g.data(None)),
        g.call('language_interpret_before_identity', g.input), interpreted),
        'Try taught dialogue questions before the previously taught language methods, preserving calendar interpretation and the ordinary language fallback.')
    return suite
