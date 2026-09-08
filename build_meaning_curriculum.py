"""Author explicit phrase and reference-meaning lessons as graph programs."""
import json
from pathlib import Path
from graph_dsl import G


def build():
    suite={}
    def save(name,g,out,description):
        suite[name]={'graph':g.finish(out,trace_mode='explicit',internal=True,memoize=True,description=description),
                     'source':'Explicit meaning lesson: '+description}
    def nonempty(g,x): return g.inverse(g.eq(x,g.data([])))
    def only(g,x): return g.both(nonempty(g,x),g.eq(g.op('slice',x,start=1),g.data([])))
    modifiers=[]
    for word in ['red','blue','green','yellow','black','white']:
        modifiers.append({'word':word,'relation':'color','value':word,
                          'heads':['ball','car','flower','object'],'predicative':True})
    for word in ['female','male']:
        modifiers.append({'word':word,'relation':'gender association','value':word,
                          'heads':['name'],'predicative':False})
    g=G();save('meaning_policy',g,g.data({'modifiers':modifiers,'name_heads':['name'],
        'name_suffix':' (name)','source_scopes':[],
        'description_relation':'described as'}),
        'Taught adjective meanings and allowed noun heads. A modifier applies to its head, not automatically to a bearer of that name. Unknown phrases stay intact; source-scoped references are explicit teaching data.')

    # Recognize only supplied adjective/head combinations. This deliberately does
    # not strip the first word of every phrase (fake gun/former president, etc.).
    head=G();h=head.get(head.input,'item');m=head.get(head.input,'context');phrase=head.textcat(head.get(m,'word'),head.data(' '),h)
    row=head.record(phrase=phrase,head=h,relation=head.get(m,'relation'),value=head.get(m,'value'))
    modifier=G();rows=modifier.map(modifier.get(modifier.input,'heads'),head.finish(row),modifier.input)
    matches=G();match=matches.eq(matches.get(matches.input,'item','phrase'),matches.get(matches.input,'context'))
    g=G();phrase=g.op('lower',g.input);policy=g.call('meaning_policy',g.input)
    choices=g.map(g.op('flatten',g.map(g.get(policy,'modifiers'),modifier.finish(rows))),matches.finish(match,'Bool'),phrase,filter=True)
    unknown=g.record(phrase=phrase,head=phrase,relation=g.data(''),value=g.data(''))
    save('meaning_phrase',g,g.choose(only(g,choices),g.item(choices,g.data(0)),unknown),
        'Interpret an explicitly taught modifier/head combination; preserve opaque compound nouns and untaught adjectives without guessing their structure.')

    g=G();fact=g.input;rel=g.get(fact,0);subject=g.get(fact,1);obj=g.get(fact,2);policy=g.call('meaning_policy',g.input)
    phrase=g.call('meaning_phrase',obj);isname=g.op('contains',g.get(policy,'name_heads'),g.get(phrase,'head'),kind='Bool')
    suffix=g.get(policy,'name_suffix');parts=g.op('split_text',subject,suffix)
    scoped=g.choose(g.both(nonempty(g,g.op('slice',parts,start=1)),g.eq(g.item(parts,g.data(-1)),g.data(''))),subject,g.textcat(subject,suffix))
    named=g.op('data_list',rel,scoped,obj)
    adjective=G();m=adjective.get(adjective.input,'item');word=adjective.get(adjective.input,'context')
    pred=adjective.both(adjective.boolean(adjective.get(m,'predicative')),adjective.eq(adjective.get(m,'word'),word))
    descriptions=g.map(g.get(policy,'modifiers'),adjective.finish(pred,'Bool'),g.op('lower',obj),filter=True)
    d=g.item(descriptions,g.data(0));attributed=g.op('data_list',g.get(d,'relation'),subject,g.get(d,'value'))
    out=g.choose(g.eq(rel,g.data('is')),g.choose(isname,named,fact),
        g.choose(g.eq(rel,g.get(policy,'description_relation')),g.choose(only(g,descriptions),attributed,fact),fact))
    save('meaning_fact',g,out,
        'Separate a name expression from the entity bearing it, idempotently. Map explicitly taught predicate adjectives to property relations; leave other descriptions as descriptions.')

    # A source-qualified reference restores distinctions an import flattened.
    # Both the labels and the evidence selectors are editable policy data.
    binding=G();scope=binding.get(binding.input,'item');row=binding.get(binding.input,'context');fact=binding.get(row,'fact')
    same=binding.eq(binding.op('lower',binding.get(fact,1)),binding.op('lower',binding.get(scope,'name')))
    textparts=binding.op('split_text',binding.get(row,'source'),binding.get(scope,'source_contains'))
    matches=binding.both(same,nonempty(binding,binding.op('slice',textparts,start=1)))
    target=G();value=target.get(target.input,'scope')
    row=G();a=row.get(row.input,'item');policy=row.get(row.input,'context')
    scopes=row.op('unique',row.map(row.map(row.get(policy,'source_scopes'),binding.finish(matches,'Bool'),a,filter=True),target.finish(value)))
    fact=row.get(a,'fact');scoped=row.op('set_item',fact,row.data(1),row.item(scopes,row.data(0)))
    interpreted=row.call('meaning_fact',row.choose(only(row,scopes),scoped,fact))
    record=row.put(a,'fact',interpreted)
    g=G();save('meaning_assertions',g,g.map(g.input,row.finish(record),g.call('meaning_policy',g.input)),
        'Interpret stored assertions using supplied phrase rules and unambiguous source-scoping lessons. Preserve original sources and negation; historical raw assertions remain available.')

    # Phrase entailments are deductions, not extra independent training examples.
    each=G();a=each.input;fact=each.get(a,'fact');phrase=each.call('meaning_phrase',each.get(fact,2))
    compound=each.inverse(each.eq(each.get(phrase,'relation'),each.data('')))
    variable=each.data({'var':'entity'});when=each.op('data_list',each.op('data_list',each.data('is'),variable,each.get(phrase,'phrase')))
    source=each.textcat(each.data('Taught phrase meaning: “'),each.get(phrase,'phrase'),each.data('” describes a '),each.get(phrase,'head'),each.data('; its modifier belongs to that noun.'))
    headrule=each.record(when=when,then=each.op('data_list',each.data('is'),variable,each.get(phrase,'head')),source=source)
    propertyrule=each.record(when=when,then=each.op('data_list',each.get(phrase,'relation'),variable,each.get(phrase,'value')),source=source)
    out=each.choose(each.eq(each.get(fact,0),each.data('is')),
        each.choose(compound,each.op('data_list',headrule,propertyrule),each.data([])),each.data([]))
    g=G();save('meaning_rules',g,g.op('unique',g.op('flatten',g.map(g.get(g.input,'assertions'),each.finish(out)))),
        'Compile noun membership and modifier properties as supported graph deductions. A negative compound assertion does not imply a negative noun or property.')

    binding=G();b=binding.get(binding.input,'item');name=binding.get(binding.input,'context')
    same=binding.eq(binding.op('lower',binding.get(b,'name')),binding.op('lower',name))
    scope=G();target=scope.get(scope.input,'scope')
    g=G();choices=g.op('unique',g.map(g.map(g.get(g.call('meaning_policy',g.input),'source_scopes'),binding.finish(same,'Bool'),g.input,filter=True),scope.finish(target)))
    question=g.textcat(g.data('“'),g.input,g.data('” has separate meanings in my notebook: '),g.op('join_text',choices,g.data(' or ')),g.data('. Which one do you mean? Please use its full label in your question.'))
    save('meaning_reference_question',g,g.choose(nonempty(g,g.op('slice',choices,start=1)),question,g.data('')),
        'Ask which source-qualified entity a shared name refers to instead of mixing their properties.')

    each=G();raw=each.get(each.input,'item');ctx=each.get(each.input,'context')
    normal=each.item(each.call('meaning_assertions',each.op('data_list',raw)),each.data(0))
    same=each.both(each.eq(each.get(normal,'fact'),each.get(ctx,'fact')),each.eq(each.get(normal,'negative'),each.get(ctx,'negative')))
    key=each.op('data_list',each.get(raw,'fact'),each.get(raw,'negative'))
    selected=each.choose(same,each.op('data_list',key),each.data([]))
    g=G();save('meaning_retraction_keys',g,g.op('flatten',g.map(g.get(g.input,'assertions'),each.finish(selected),g.input)),
        'Find the original stored keys behind an interpreted assertion so corrections can retract scoped legacy evidence without losing its provenance.')
    return suite


if __name__=='__main__':
    target=Path(__file__).parent/'curriculum/meaning.json'
    target.write_text(json.dumps(build(),indent=2)+'\n')
    print(target)
