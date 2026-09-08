"""Author lookup behavior as portable graph lessons, never runtime Python logic."""
from graph_dsl import G


def build():
    suite = {}
    def save(name, g, out, description):
        suite[name] = {'graph': g.finish(out, trace_mode='explicit', internal=True,
                                        description=description),
                       'source': 'Explicit lookup teaching: ' + description}

    g = G()
    save('knowledge_lookup_policy', g, g.data({
        'name_relations': ['ncbi common name', 'concept name'],
        'spelling_variants': [],
        'rules': [],
        'ask_when_unknown': True,
    }), 'Declare which relations connect concept names, explicit spelling variants, and general if/then rules. Unlisted relations imply no equivalence. Names with multiple targets are not resolved.')

    # Collect naming evidence without treating arbitrary shared neighbors as synonyms.
    f = G(); row = f.get(f.input, 'item'); fact = f.get(row, 'fact')
    named = f.op('contains', f.get(f.input, 'context'), f.get(fact, 0), kind='Bool')
    positive = f.both(named, f.inverse(f.boolean(f.get(row, 'negative'))))
    n = G(); neg = n.boolean(n.get(n.input, 'negative'))
    extract = G(); raw = extract.get(extract.input, 'fact')
    g = G(); policy = g.call('knowledge_lookup_policy', g.input)
    names = g.map(g.get(g.input, 'assertions'), f.finish(positive, 'Bool'), g.get(policy, 'name_relations'), filter=True)
    negatives = g.map(g.map(g.get(g.input, 'assertions'), n.finish(neg, 'Bool'), filter=True), extract.finish(raw))

    # Each candidate link carries its original fact, not a fabricated entity claim.
    edge = G(); row = edge.get(edge.input, 'item'); fact = edge.get(row, 'fact')
    trusted = edge.inverse(edge.op('contains', edge.get(edge.input, 'context'), fact, kind='Bool'))
    link = edge.record(canonical=edge.op('lower', edge.get(fact, 1)), alias=edge.op('lower', edge.get(fact, 2)),
                       source=edge.get(row, 'source'), evidence=edge.op('data_list', fact), trusted=edge.datum(trusted))
    spelling = G(); row = spelling.input
    variant = spelling.record(canonical=spelling.op('lower', spelling.get(row, 'canonical')),
        alias=spelling.op('lower', spelling.get(row, 'variant')), source=spelling.get(row, 'source'),
        evidence=spelling.data([]), trusted=spelling.data(True))
    links = g.op('concat', g.map(names, edge.finish(link), negatives),
                 g.map(g.get(policy, 'spelling_variants'), spelling.finish(variant)))
    save('knowledge_name_links', g, links, 'Read only declared concept-name relations and explicitly taught spellings. Retain source facts; mark contradicted naming evidence unusable.')

    # Directional ambiguity checks. Multiple names for one concept are fine;
    # one alias for multiple concepts must not select any of them.
    same = G(); row = same.get(same.input, 'item'); ctx = same.get(same.input, 'context')
    match = same.eq(same.get(row, 'alias'), ctx)
    canonical = G(); value = canonical.get(canonical.input, 'canonical')
    alias = G(); value2 = alias.get(alias.input, 'alias')
    g = G(); links = g.get(g.input, 'links'); name = g.get(g.input, 'name')
    targets = g.op('unique', g.map(g.map(links, same.finish(match, 'Bool'), name, filter=True), canonical.finish(value)))
    save('knowledge_name_targets', g, targets, 'List distinct canonical meanings of a name before using it to infer membership.')

    # Bridge membership in both directions only for unambiguous, uncontested links.
    # Spelling and naming ambiguity are checked together. This also rejects a name
    # which is both a canonical concept and an alias for a different concept.
    each = G(); link = each.get(each.input, 'item'); links = each.get(each.input, 'context')
    left = each.get(link, 'alias'); right = each.get(link, 'canonical')
    meanings = each.call('knowledge_name_targets', each.record(links=links, name=left))
    right_meanings = each.call('knowledge_name_targets', each.record(links=links, name=right))
    canonical_names = each.map(links, canonical.finish(value))
    left_collision = each.both(each.op('contains', canonical_names, left, kind='Bool'), each.inverse(each.eq(left, right)))
    right_ok = each.either(each.eq(right_meanings, each.data([])), each.eq(right_meanings, each.op('data_list', right)))
    usable = each.both(each.boolean(each.get(link, 'trusted')),
        each.both(each.eq(meanings, each.op('data_list', right)), each.both(each.inverse(left_collision), right_ok)))
    def clause(start, end):
        return each.record(when=each.op('data_list', each.op('data_list', each.data('is'), each.data({'var':'member'}), start)),
            then=each.op('data_list', each.data('is'), each.data({'var':'member'}), end),
            source=each.textcat(each.data('Taught name rule: membership in '), start, each.data(' also means membership in '), end,
                                each.data('. Naming evidence: '), each.get(link, 'source')),
            evidence=each.get(link, 'evidence'))
    clauses = each.choose(usable, each.op('data_list', clause(left, right), clause(right, left)), each.data([]))
    g = G(); links = g.call('knowledge_name_links', g.input)
    save('knowledge_name_rules', g, g.op('flatten', g.map(links, each.finish(clauses), links)),
         'Compile reversible membership rules from unambiguous concept names. Preserve naming evidence; arbitrary relationships never become equivalences.')

    # Asking is an effect chosen by a stored policy, after evidence lookup.
    # A reply is handed to the existing language interface for interpretation;
    # vague agreement never manufactures an equivalence or fact.
    g = G(); status = g.call('knowledge_query', g.input); policy = g.call('knowledge_lookup_policy', g.input)
    fact = g.get(g.input, 'fact')
    question = g.textcat(g.get(g.input, 'answer'), g.data('\nCan you explain the connection between “'),
        g.get(fact, 1), g.data('” and “'), g.get(fact, 2), g.data('” for “'), g.get(fact, 0),
        g.data('”? Teach me a full statement, a concept-name relationship, or a general rule. You can also say stop.'))
    reference_question = g.call('meaning_reference_question',g.get(fact,1))
    question = g.choose(g.inverse(g.eq(reference_question,g.data(''))),reference_question,question)
    ask = g.op('act', g.input, g.record(text=question, resume=g.data('knowledge_lookup_reply'),
        state=g.record(fact=fact)), surface='dialogue', action='ask')
    allowed = g.both(g.eq(status, g.data('unknown')), g.boolean(g.get(policy, 'ask_when_unknown')))
    save('knowledge_lookup_response', g, g.choose(allowed, ask, g.record(text=g.get(g.input, 'answer'))),
         'If the evidence is unknown and asking is enabled, request an explanation and retain the question. Known and conflicting evidence keep their verdict; asking itself learns nothing.')
    g = G(); reply = g.op('lower', g.op('replace_text', g.get(g.input, 'input'), g.data(' '), g.data('')))
    stop = g.op('contains', g.data(['stop','cancel','skip',"idontknow","idon'tknow"]), reply, kind='Bool')
    vague = g.op('contains', g.data(['yes','yes.','no','no.','sure','ok','okay']), reply, kind='Bool')
    ask = g.op('act', g.input, g.record(text=g.data('What exactly should I learn? Please give the whole statement or explain the relationship; yes or no alone does not define it. You can say stop.'),
        resume=g.data('knowledge_lookup_reply'), state=g.get(g.input, 'state')), surface='dialogue', action='ask')
    out = g.choose(stop, g.record(text=g.data('Okay. I will leave that question unresolved.')),
        g.choose(vague, ask, g.record(language_input=g.get(g.input, 'input'))))
    save('knowledge_lookup_reply', g, out,
         'Leave an unanswered question unresolved, ask for a precise statement after vague agreement, or hand a full reply to the language interface for ordinary validated teaching.')
    return suite
