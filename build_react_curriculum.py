"""Teach inspectable HTML/JSX/React knowledge and an attribute-name rule."""
from graph_dsl import G
from react_lessons import lessons


def build():
    g=G();table=g.data(lessons());out=g.item(table,g.input)
    explain={'graph':g.finish(out,trace_mode='explicit',description='Read an explicitly taught HTML, JSX or React lesson and its source; reference knowledge does not imply execution support.'),
             'source':'Teacher-authored lessons based on WHATWG HTML and official React documentation.'}
    g=G();names=g.data({'class':'className','for':'htmlFor','tabindex':'tabIndex','readonly':'readOnly','maxlength':'maxLength','autofocus':'autoFocus','onclick':'onClick','onchange':'onChange'})
    out=g.choose(g.has(names,g.input),g.item(names,g.input),g.input)
    attributes={'graph':g.finish(out,trace_mode='explicit',description='Convert selected known HTML attribute names to JSX names. Names only: event-handler values, styles, boolean attributes and full markup require further conversion.'),
                'source':'Explicit JSX attribute-name correspondence lesson; not an HTML-to-JSX parser.'}
    guard=G();keep=guard.lt(guard.get(guard.input,'i'),guard.length(guard.get(guard.input,'updates')))
    b=G();s=b.input;i=b.get(s,'i');update=b.item(b.get(s,'updates'),i)
    previous=b.get(s,'value');kind=b.get(update,'kind')
    supplied=b.call('programming_safe_integer',b.call('programming_require_number',b.get(update,'value')))
    recognized=b.either(b.eq(kind,b.data('replace')),b.eq(kind,b.data('increment')))
    nextvalue=b.choose(b.eq(kind,b.data('replace')),supplied,
        b.call('programming_safe_integer',b.calc('add',previous,supplied)))
    nextvalue=b.op('require',recognized,nextvalue,message='State exercise supports replace and increment updates only.')
    step=b.record(index=i,kind=kind,before=previous,after=nextvalue)
    updated=b.record(i=b.calc('add',i,b.data(1)),value=nextvalue,updates=b.get(s,'updates'),steps=b.append(b.get(s,'steps'),step))
    g=G();updates=g.get(g.input,'updates')
    updates=g.op('require',g.eq(g.op('kind_of',updates),g.data('list')),updates,message='Updates must be a list.')
    updates=g.op('require',g.inverse(g.lt(g.data(64),g.length(updates))),updates,message='At most 64 state updates per exercise.')
    initial=g.call('programming_safe_integer',g.call('programming_require_number',g.get(g.input,'initial')))
    loop=g.loop(g.record(i=g.data(0),value=initial,updates=updates,steps=g.data([])),guard.finish(keep,'Bool'),b.finish(updated))
    out=g.record(value=g.get(loop,'value'),steps=g.get(loop,'steps'),scope=g.data('Educational integer state-queue model; not React hook execution.'))
    queue={'graph':g.finish(out,trace_mode='explicit',description='Model ordered numeric state replacements and increment updaters; preserve every transition. This does not implement React hooks, rendering or scheduling.'),
           'source':'Educational graph model based on React queueing-a-series-of-state-updates.'}
    # A finite lifecycle exercise, with value dependencies rather than object
    # identity or a hook scheduler. Validate those boundaries in graph data.
    item=G();v=item.input;kind=item.op('kind_of',v)
    numeric=item.call('programming_safe_integer',item.call('programming_require_number',v))
    canonical=item.op('text',item.calc('add',numeric,item.data(0)))
    integer=item.eq(item.op('text',v),canonical)
    scalar=item.op('contains',item.data(['text','bool','null']),kind,kind='Bool')
    valid=item.choose(item.eq(kind,item.data('number')),integer,scalar,kind='Bool')
    checked=item.op('require',valid,v,message='Effect exercise dependencies support strings, booleans, null and safe integers only; object identity and floating-point values are not modeled.')
    deps=G();v=deps.input
    values=deps.op('require',deps.eq(deps.op('kind_of',v),deps.data('list')),v,message='Dependencies must be an array, or null for no dependency array.')
    values=deps.op('require',deps.inverse(deps.lt(deps.data(32),deps.length(values))),values,message='At most 32 dependencies per exercise.')
    out=deps.choose(deps.eq(v,deps.data(None)),deps.data(None),deps.map(values,item.finish(checked)))
    dependency_rule={'graph':deps.finish(out,trace_mode='explicit',description='Validate the limited scalar dependency domain of the effect lifecycle exercise.'),'source':'Explicit effect exercise boundary.'}
    g=G();phase=g.get(g.input,'phase');before=g.call('react_effect_dependencies',g.get(g.input,'previous'))
    after=g.call('react_effect_dependencies',g.get(g.input,'next'));cleanup=g.boolean(g.get(g.input,'cleanup'))
    no_deps=g.either(g.eq(before,g.data(None)),g.eq(after,g.data(None)))
    same_arity=g.choose(no_deps,g.eq(g.data(0),g.data(0)),g.eq(g.length(before),g.length(after)),kind='Bool')
    compare=G();index=compare.get(compare.input,'item');context=compare.get(compare.input,'context')
    same=compare.datum(compare.eq(compare.item(compare.get(context,'before'),index),compare.item(compare.get(context,'after'),index)))
    flags=g.map(g.op('indices',before),compare.finish(same),g.record(before=before,after=after))
    differs=g.op('contains',flags,g.data(False),kind='Bool')
    changed=g.choose(no_deps,g.eq(g.data(0),g.data(0)),differs,kind='Bool')
    rerun=g.choose(cleanup,g.data(['cleanup','setup']),g.data(['setup']))
    update=g.choose(changed,rerun,g.data([]))
    update=g.op('require',same_arity,update,message='Keep the dependency-array length constant between updates.')
    actions=g.choose(g.eq(phase,g.data('mount')),g.data(['setup']),
        g.choose(g.eq(phase,g.data('update')),update,g.choose(cleanup,g.data(['cleanup']),g.data([]))))
    allowed=g.op('contains',g.data(['mount','update','unmount']),phase,kind='Bool')
    actions=g.op('require',allowed,actions,message='Effect exercise phase must be mount, update or unmount.')
    out=g.record(actions=actions,scope=g.data('Educational lifecycle model with scalar dependencies; cleanup indicates a registered cleanup. No hook execution, side effects, Strict Mode replay or scheduling.'))
    effects={'graph':g.finish(out,trace_mode='explicit',description='Model one effect lifecycle step: mount setup; changed dependencies cleanup then setup; stable dependencies no work; unmount registered cleanup.'),
             'source':'Educational model based on the official React useEffect reference.'}
    from react_learn_corpus import REVISION
    g=G();key=g.textcat(g.data(REVISION+'/'),g.input)
    out=g.op('act',g.input,g.record(namespace=g.data('knowledge.react_learn_examples'),key=key),surface='workspace',action='read')
    reader={'graph':g.finish(out,trace_mode='explicit',description='Read a pinned official React Learn code fence and its parser audit by page#fence-index. Source text is reference data, never an instruction to execute.'),
            'source':'Pinned official React Learn reference corpus.'}
    g=G();out=g.op('act',g.input,g.record(namespace=g.data('knowledge.react_learn_coverage'),key=g.data(REVISION)),surface='workspace',action='read')
    coverage={'graph':g.finish(out,trace_mode='explicit',description='Report corpus inventory and syntax audit; this is not a count of understood or executed React examples.'),'source':'Measured pinned-corpus audit.'}
    return {'react_explain':explain,'jsx_attribute_name':attributes,'react_state_queue':queue,
            'react_effect_dependencies':dependency_rule,'react_effect_lifecycle':effects,
            'react_learn_example':reader,'react_learn_coverage':coverage}


if __name__=='__main__':
    import json
    from pathlib import Path
    (Path(__file__).parent/'curriculum/react.json').write_text(json.dumps(build(),indent=2)+'\n')
