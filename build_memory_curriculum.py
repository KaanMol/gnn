"""Author inspectable policies for selecting, correcting and explaining evidence."""
from graph_dsl import G


def build():
    suite = {}
    def save(name, g, out, description):
        suite[name] = {'graph': g.finish(out, trace_mode='explicit', description=description),
                       'source': 'Foundational memory teaching: ' + description}
    g=G(); save('memory_policy',g,g.data({'functional_relations':['birth date']}),
        'A newly asserted value of a declared functional relation replaces older positive values for that subject.')
    f=G(); fact=f.get(f.get(f.input,'item'),'fact'); ctx=f.get(f.input,'context')
    yes=f.both(f.eq(f.item(fact,f.data(0)),f.data('is')),f.eq(f.item(fact,f.data(2)),f.get(ctx,'concept')))
    g=G(); selected=g.map(g.get(g.input,'facts'),f.finish(yes,'Bool'),g.input,filter=True)
    extract=G(); fact=extract.get(extract.input,'fact')
    negative=g.map(g.get(g.input,'negatives'),extract.finish(fact))
    filt=G(); yes=filt.op('contains',filt.get(filt.input,'context'),filt.get(filt.get(filt.input,'item'),'fact'),kind='Bool')
    entity=G(); subject=entity.item(entity.get(entity.input,'fact'),entity.data(1))
    conflicts=g.map(selected,filt.finish(yes,'Bool'),negative,filter=True)
    good=g.map(selected,filt.finish(filt.inverse(yes),'Bool'),negative,filter=True)
    save('count_known',g,g.record(matches=g.op('unique',g.map(good,entity.finish(subject))),conflicts=g.op('unique',g.map(conflicts,entity.finish(subject)))),
         'Select known members of a concept and separate contradictory membership evidence.')
    f=G(); old=f.get(f.input,'item'); new=f.get(f.input,'context'); fact=f.get(old,'fact')
    yes=f.both(f.inverse(f.boolean(f.get(old,'negative'))),f.both(f.eq(f.item(fact,f.data(0)),f.get(new,'relation')),
        f.both(f.eq(f.op('lower',f.item(fact,f.data(1))),f.op('lower',f.get(new,'subject'))),f.inverse(f.eq(f.item(fact,f.data(2)),f.get(new,'object'))))))
    g=G(); new=g.get(g.input,'new'); functional=g.op('contains',g.get(g.call('memory_policy',g.input),'functional_relations'),g.get(new,'relation'),kind='Bool')
    replaced=g.choose(functional,g.map(g.get(g.input,'assertions'),f.finish(yes,'Bool'),new,filter=True),g.data([]))
    save('memory_superseded',g,g.map(replaced,extract.finish(extract.get(extract.input,'fact'))),
         'Find previous assertions superseded by a new value according to the taught functional-relation policy.')
    # Proof traversal is iterative and cycle-aware, independent of any relation.
    f=G(); same=f.eq(f.get(f.get(f.input,'item'),'fact'),f.get(f.input,'context'))
    child=G(); item=child.get(child.input,'item'); depth=child.get(child.input,'context'); row=child.record(fact=item,depth=depth)
    guard=G(); run=guard.nonempty(guard.get(guard.input,'pending'))
    body=G(); s=body.input; pending=body.get(s,'pending'); current=body.item(pending,body.data(0)); fact=body.get(current,'fact'); seen=body.get(s,'seen')
    matches=body.map(body.get(s,'facts'),f.finish(same,'Bool'),fact,filter=True)
    fresh=body.both(body.inverse(body.op('contains',seen,fact,kind='Bool')),body.nonempty(matches))
    proof=body.item(matches,body.data(0)); depth=body.get(current,'depth')
    children=body.map(body.get(proof,'premises'),child.finish(row),body.calc('add',depth,body.data(1)))
    entry=body.record(fact=fact,source=body.get(proof,'source'),depth=depth)
    rest=body.op('slice',pending,start=1)
    out=body.record(pending=body.choose(fresh,body.op('concat',children,rest),rest),facts=body.get(s,'facts'),seen=body.choose(fresh,body.append(seen,fact),seen),result=body.choose(fresh,body.append(body.get(s,'result'),entry),body.get(s,'result')))
    g=G(); loop=g.loop(g.record(pending=g.op('data_list',g.record(fact=g.get(g.input,'fact'),depth=g.data(0))),facts=g.get(g.input,'facts'),seen=g.data([]),result=g.data([])),guard.finish(run,'Bool'),body.finish(out))
    save('knowledge_explain',g,g.get(loop,'result'),'Traverse stored premises in proof order, retaining sources and avoiding cycles.')
    return suite
