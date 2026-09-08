"""Explicit entity-name continuity lessons; Python only authors graph data."""
import copy
from graph_dsl import G


def build(library):
    suite = {}
    def save(name, g, value, description):
        suite[name] = {'graph': g.finish(value, internal=True, trace_mode='explicit',
                                       description=description),
                       'source': 'Explicit name continuity teaching: ' + description}

    # Keep the currently taught dispatcher, including any unrelated new skills.
    base = 'language_interpret_before_rename'
    suite[base] = copy.deepcopy(library.get(base, library['language_interpret']))

    row = G(); item = row.get(row.input, 'item'); old = row.get(row.input, 'context')
    same = row.either(row.eq(row.op('lower', row.get(item, 'canonical')), old),
                     row.op('contains', row.get(item, 'forms'), old, kind='Bool'))
    g = G(); policy = g.call('meaning_reference_policy', g.input)
    old = g.get(g.input, 'old'); new = g.get(g.input, 'new')
    canonical = g.call('meaning_reference', old)
    old_lower = g.op('lower', canonical); new_lower = g.op('lower', new)
    matches = g.map(policy, row.finish(same, 'Bool'), old_lower, filter=True)
    others = g.map(policy, row.finish(row.inverse(same), 'Bool'), old_lower, filter=True)
    first = g.get(matches, 0)
    forms = g.choose(g.nonempty(matches), g.get(first, 'forms'), g.data([]))
    forms = g.op('unique', g.op('concat', forms,
                 g.op('data_list', g.op('lower', old), old_lower, new_lower)))
    identity = g.choose(g.nonempty(matches),
        g.choose(g.has(first, g.data('identity')), g.get(first, 'identity'), old_lower), old_lower)
    updated = g.record(canonical=new, forms=forms, kind=g.data('entity names'),
                       identity=identity, source=g.get(g.input, 'source'))
    targets = g.map(others, row.finish(same, 'Bool'), new_lower, filter=True)
    entity = G(); name = entity.get(entity.input, 'item'); ctx = entity.get(entity.input, 'context')
    collision = entity.both(entity.eq(entity.op('lower', name), entity.get(ctx, 'new')),
        entity.inverse(entity.eq(entity.op('lower', entity.call('meaning_reference', name)), entity.get(ctx, 'old'))))
    occupied = g.map(g.get(g.input, 'entities'), entity.finish(collision, 'Bool'),
                     g.record(new=new_lower, old=old_lower), filter=True)
    safe = g.both(g.inverse(g.nonempty(targets)), g.inverse(g.nonempty(occupied)))
    safe = g.both(safe, g.inverse(g.nonempty(g.op('slice', matches, start=1))))
    rows = g.op('concat', others, g.op('data_list', updated))
    # The lesson constructs the new literal policy graph. The host only validates
    # and persists it; it does not invent aliases or rewrite arbitrary text.
    policy_graph = g.record(input_type=g.data('Data'), output_type=g.data('Data'),
        nodes=g.op('data_list', g.data({'id':'input','op':'input','inputs':[],'type':'Data'}),
            g.record(id=g.data('policy'), op=g.data('data_literal'), inputs=g.data([]),
                     type=g.data('Data'), value=rows)), output=g.data('policy'),
        internal=g.data(True), trace_mode=g.data('explicit'),
        description=g.data('Taught equivalent names. Entity renames preserve their identity and historical aliases; original evidence keeps its wording.'))
    result = g.record(entry=g.record(graph=policy_graph, source=g.get(g.input, 'source')),
        name=new, identity=identity, aliases=forms,
        text=g.textcat(g.data('I will use '), new,
                       g.data(' as my name. My existing facts stay connected, and my previous names still refer to me.')))
    save('meaning_rename_reference', g, g.op('require', safe, result,
        message='That name already identifies something else, or the current name is ambiguous. Choose a distinct name.'),
        'Keep one identity when its preferred name changes. Retain old aliases, normalize both fact endpoints, and refuse to merge a different existing entity or concept.')

    # Reusable case-preserving text capture; range selection is taught graph work.
    index = G(); i = index.get(index.input, 'item'); ctx = index.get(index.input, 'context')
    keep = index.both(index.inverse(index.lt(i, index.get(ctx, 'start'))), index.lt(i, index.get(ctx, 'stop')))
    char = G(); value = char.item(char.get(char.input, 'context'), char.get(char.input, 'item'))
    g = G(); chars = g.op('characters', g.get(g.input, 'text'))
    selected = g.map(g.op('indices', chars), index.finish(keep, 'Bool'), g.input, filter=True)
    save('identity_text_range', g, g.op('join_text', g.map(selected, char.finish(value), chars), g.data('')),
         'Capture a character range without changing the spelling or capitalization of a name.')

    g = G(); save('identity_rename_policy', g, g.data([
        {'prefix': prefix, 'suffix': suffix, 'bulk': bulk}
        for prefix, suffix, bulk in [
            ('your new name is now ', '', False), ('your name is now ', '', False),
            ('your new name is ', '', False), ('your name is ', '', False),
            ('you are now ', '', False), ('you are ', ' now', False),
            ('call yourself ', '', False), ('rename yourself to ', '', False),
            ('update all ', '', True)]
    ]), 'Explicit assistant rename forms, including updating references to a known previous assistant name. These commands never mean deleting a fact.')

    each = G(); rule = each.get(each.input, 'item'); text = each.get(each.input, 'context')
    lower = each.op('lower', text); prefix = each.get(rule, 'prefix'); suffix = each.get(rule, 'suffix')
    parts = each.op('split_text', lower, prefix)
    starts = each.both(each.eq(each.length(parts), each.data(2)), each.eq(each.get(parts, 0), each.data('')))
    ends = each.op('split_text', lower, suffix)
    ending = each.choose(each.eq(suffix, each.data('')), each.eq(text, text),
        each.both(each.eq(each.length(ends), each.data(2)), each.eq(each.item(ends, each.data(-1)), each.data(''))), kind='Bool')
    start = each.length(each.op('characters', prefix))
    stop = each.calc('subtract', each.length(each.op('characters', text)), each.length(each.op('characters', suffix)))
    captured = each.call('identity_text_range', each.record(text=text, start=start, stop=stop))
    valid = each.both(starts, each.both(ending, each.lt(start, stop)))
    found = each.choose(valid, each.op('data_list', each.record(text=captured, bulk=each.get(rule, 'bulk'))), each.data([]))
    nonempty = G(); keep = nonempty.inverse(nonempty.eq(nonempty.input, nonempty.data('')))
    g = G(); words = g.map(g.op('split_text', g.get(g.input, 'text'), g.data(' ')), nonempty.finish(keep, 'Bool'), filter=True)
    text = g.op('join_text', words, g.data(' ')); chars = g.op('characters', text)
    punctuation = g.op('contains', g.data(['.', '!', '?']), g.item(chars, g.data(-1)), kind='Bool')
    text = g.choose(g.nonempty(chars), g.choose(punctuation, g.op('join_text', g.op('slice', chars, stop=-1), g.data('')), text), text)
    matches = g.op('flatten', g.map(g.call('identity_rename_policy', g.input), each.finish(found), text))
    choice = g.get(matches, 0); captured = g.get(choice, 'text')
    parts = g.op('split_text', g.op('lower', captured), g.data(' references to '))
    old = g.get(parts, 0); start = g.calc('add', g.length(g.op('characters', old)), g.data(len(' references to ')))
    new = g.call('identity_text_range', g.record(text=captured, start=start, stop=g.length(g.op('characters', captured))))
    same_assistant = g.eq(g.op('lower', g.call('meaning_reference', old)),
                         g.op('lower', g.call('meaning_reference', g.get(g.input, 'addressee'))))
    valid_bulk = g.both(g.eq(g.length(parts), g.data(2)),
                       g.both(same_assistant, g.inverse(g.eq(g.get(parts, 1), g.data('')))))
    operation = g.data(dict(op='rename_assistant', subject='', relation='', object='',
                            negative=False, conditions=[], text=''))
    rename = g.put(operation, 'subject', g.choose(g.boolean(g.get(choice, 'bulk')), new, captured))
    clarification = g.put(g.put(operation, 'op', g.data('clarify')), 'text',
        g.data('Which existing assistant name should those references identify? I have not removed or merged any facts.'))
    selected = g.choose(g.boolean(g.get(choice, 'bulk')), g.choose(valid_bulk, rename, clarification), rename)
    save('identity_rename_interpret', g, g.choose(g.nonempty(matches),
        g.record(operations=g.op('data_list', selected)), g.data(None)),
        'Translate explicit renames without a model. A request to update references must identify the current assistant or a taught historical alias; otherwise ask for clarification.')
    g = G(); result = g.call('identity_rename_interpret', g.input)
    save('language_interpret', g, g.choose(g.eq(result, g.data(None)), g.call(base, g.input), result),
         'Use taught rename behavior before the existing taught language dispatcher.')
    return suite
