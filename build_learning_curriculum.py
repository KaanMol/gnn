"""Author bounded induction and review behaviors as editable graph programs."""
import json
from pathlib import Path
from graph_dsl import G


def build():
    suite = {}
    def save(name, g, out, description, **meta):
        suite[name] = {'graph': g.finish(out, trace_mode='explicit', description=description, **meta),
                       'source': 'Explicit learning-behavior lesson: ' + description}
    def entries(g, namespace):
        return g.op('act', g.input, g.record(namespace=g.data(namespace)), surface='workspace', action='entries')
    def read(g, namespace, key):
        return g.op('act', g.input, g.record(namespace=g.data(namespace), key=key), surface='workspace', action='read')
    def write(g, record):
        return g.op('act', g.input, g.record(namespace=g.data('knowledge.hypotheses'), key=g.get(record,'id'), value=record), surface='workspace', action='write')
    def yes(g, v): return g.inverse(g.eq(v,g.data([])))
    def v(name): return {'var':name}

    g=G();save('learning_policy',g,g.data({
        'enabled': True, 'auto_ask': True, 'minimum_support': 2,
        'candidate_methods': ['learning_mutual_candidates','learning_inclusion_candidates'],
        'max_new_candidates': 12,
        'excluded_relations': ['is','ncbi common name','concept name','birth date'],
        'confirm': ['yes','yes.','confirm','correct'], 'reject': ['no','no.','reject'],
        'defer': ['skip','stop','cancel','later',"i don't know"]}),
        'Look for two independently witnessed examples before proposing a rule. Ask before adoption; explicit counterexamples or lost support suspend an adopted rule. Discovery is limited to the named, editable candidate methods.')

    row=G();a=row.input; assertion=row.record(fact=row.get(a,'key',0),negative=row.get(a,'key',1),source=row.get(a,'value'))
    value=G();valueout=value.get(value.input,'value')
    key=G();keyout=key.get(key.input,'key')
    g=G(); save('learning_snapshot',g,g.record(
        assertions=g.map(entries(g,'knowledge.assertions'),row.finish(assertion)),
        hypotheses=g.map(entries(g,'knowledge.hypotheses'),value.finish(valueout)),
        symmetric=g.map(entries(g,'knowledge.symmetric'),key.finish(keyout)),
        subtypes=g.map(entries(g,'knowledge.subtypes'),key.finish(keyout))),
        'Read current assertions, hypotheses and explicit declarations through the raw memory interface. Derived conclusions are not training examples.')

    # Candidate generators return generic single-premise Horn rules. Each can be
    # replaced or extended by changing the policy's candidate-method list.
    f=G();fact=f.input;rel=f.get(fact,0);ctx=None
    candidate=f.record(id=f.op('data_list',f.data('mutual'),rel),kind=f.data('mutual'),
        label=f.textcat(f.data('Is “'),rel,f.data('” always mutual?')),
        rule=f.record(when=f.op('data_list',f.op('data_list',rel,f.data(v('a')),f.data(v('b')))),
            then=f.op('data_list',rel,f.data(v('b')),f.data(v('a'))),source=f.textcat(f.data('Confirmed learned rule: '),rel,f.data(' is mutual.'))))
    filt=G();fact=filt.get(filt.input,'item');ctx=filt.get(filt.input,'context')
    reverse=filt.op('data_list',filt.get(fact,0),filt.get(fact,2),filt.get(fact,1))
    allowed=filt.both(filt.op('contains',filt.get(ctx,'positive'),reverse,kind='Bool'),filt.both(filt.inverse(filt.op('contains',filt.get(ctx,'excluded'),filt.get(fact,0),kind='Bool')),
        filt.both(filt.inverse(filt.op('contains',filt.get(ctx,'symmetric'),filt.get(fact,0),kind='Bool')),filt.inverse(filt.eq(filt.get(fact,1),filt.get(fact,2)))))
    )
    g=G();changed=g.map(g.get(g.input,'changed'),filt.finish(allowed,'Bool'),g.record(excluded=g.get(g.call('learning_policy',g.input),'excluded_relations'),symmetric=g.get(g.input,'symmetric'),positive=g.get(g.input,'positive')),filter=True)
    save('learning_mutual_candidates',g,g.op('unique',g.map(changed,f.finish(candidate))),
        'For observed relationship names not already declared mutual, propose a reversible relation pattern. A self-link is not evidence of mutuality.')

    pair=G();a=pair.get(pair.input,'context');b=pair.get(pair.input,'item','fact')
    match=pair.both(pair.eq(pair.get(b,0),pair.data('is')),pair.both(pair.eq(pair.get(a,1),pair.get(b,1)),pair.inverse(pair.eq(pair.get(a,2),pair.get(b,2)))))
    def inclusion(g,a,b):
        return g.record(id=g.op('data_list',g.data('inclusion'),a,b),kind=g.data('inclusion'),
            label=g.textcat(g.data('Is every “'),a,g.data('” also a “'),b,g.data('”?')),
            rule=g.record(when=g.op('data_list',g.op('data_list',g.data('is'),g.data(v('a')),a)),
                then=g.op('data_list',g.data('is'),g.data(v('a')),b),source=g.textcat(g.data('Confirmed learned rule: every '),a,g.data(' is a '),b,g.data('.'))))
    possibilities=pair.choose(match,pair.op('data_list',inclusion(pair,pair.get(a,2),pair.get(b,2)),inclusion(pair,pair.get(b,2),pair.get(a,2))),pair.data([]))
    seed=G();fact=seed.get(seed.input,'item');snapshot=seed.get(seed.input,'context')
    candidates=seed.choose(seed.eq(seed.get(fact,0),seed.data('is')),seed.op('flatten',seed.map(seed.get(snapshot,'positives'),pair.finish(possibilities),fact)),seed.data([]))
    undeclared=G();item=undeclared.get(undeclared.input,'item');key_=undeclared.op('slice',undeclared.get(item,'id'),start=1)
    new=undeclared.inverse(undeclared.op('contains',undeclared.get(undeclared.input,'context'),key_,kind='Bool'))
    membership=G();istype=membership.eq(membership.get(membership.input,'fact',0),membership.data('is'))
    g=G();typed=g.map(g.get(g.input,'positives'),membership.finish(istype,'Bool'),filter=True)
    context=g.put(g.input,'positives',typed)
    out=g.op('unique',g.op('flatten',g.map(g.get(g.input,'changed'),seed.finish(candidates),context)))
    save('learning_inclusion_candidates',g,g.map(out,undeclared.finish(new,'Bool'),g.get(g.input,'subtypes'),filter=True),
        'Co-occurring asserted types suggest possible inclusions in either direction. Each proposed direction must be checked separately; two labels are not automatically equivalent.')

    positive=G();pos=positive.inverse(positive.boolean(positive.get(positive.input,'negative')))
    negative=G();neg=negative.boolean(negative.get(negative.input,'negative'))
    strip=G();record=strip.record(fact=strip.get(strip.input,'fact'),source=strip.get(strip.input,'source'),premises=strip.data([]))
    raw=G();rawout=raw.get(raw.input,'fact')
    g=G();assertions=g.call('meaning_assertions',g.get(g.input,'assertions'));posrows=g.map(g.map(assertions,positive.finish(pos,'Bool'),filter=True),strip.finish(record));negrows=g.map(g.map(assertions,negative.finish(neg,'Bool'),filter=True),strip.finish(record))
    save('learning_evidence',g,g.record(positives=posrows,positive=g.map(posrows,raw.finish(rawout)),negative=g.map(negrows,raw.finish(rawout))),
        'Separate directly asserted positive and negative evidence. Missing evidence remains unknown.')

    # Evaluation uses the same generic Horn engine as ordinary inference.
    each=G();case=each.get(each.input,'item');ctx=each.get(each.input,'context');conclusion=each.get(case,'fact');premises=each.get(case,'premises')
    disputed=yes(each,each.op('difference',premises,each.op('difference',premises,each.get(ctx,'negative'))))
    support=each.op('contains',each.get(ctx,'positive'),conclusion,kind='Bool');counter=each.op('contains',each.get(ctx,'negative'),conclusion,kind='Bool')
    self_case=each.op('contains',premises,conclusion,kind='Bool')
    status=each.choose(self_case,each.data('trivial'),each.choose(disputed,each.data('contested'),each.choose(counter,each.data('counterexample'),each.choose(support,each.data('support'),each.data('unknown')))))
    # Sorting the unordered set of observations counts a mutual pair once.
    order=G();ordered=order.record(fact=order.input)
    sortedfacts=each.map(each.op('sort',each.map(each.op('unique',each.append(premises,conclusion)),order.finish(ordered)),key='fact'),raw.finish(rawout))
    checked=each.record(premises=premises,conclusion=conclusion,status=status,witness=sortedfacts)
    statusfilter=G();same=statusfilter.eq(statusfilter.get(statusfilter.input,'item','status'),statusfilter.get(statusfilter.input,'context'))
    witness=G();witnessout=witness.get(witness.input,'witness')
    g=G();evidence=g.call('learning_evidence',g.input)
    cases=g.call('horn_apply',g.record(rule=g.get(g.input,'candidate','rule'),facts=g.get(evidence,'positives')))
    checked=g.map(cases,each.finish(checked),evidence)
    support=g.map(checked,statusfilter.finish(same,'Bool'),g.data('support'),filter=True)
    counters=g.map(checked,statusfilter.finish(same,'Bool'),g.data('counterexample'),filter=True)
    contested=g.map(checked,statusfilter.finish(same,'Bool'),g.data('contested'),filter=True)
    unknown=g.map(checked,statusfilter.finish(same,'Bool'),g.data('unknown'),filter=True)
    units=g.op('unique',g.map(support,witness.finish(witnessout)))
    enough=g.inverse(g.lt(g.length(units),g.get(g.call('learning_policy',g.input),'minimum_support')))
    eligible=g.both(enough,g.both(g.eq(counters,g.data([])),g.eq(contested,g.data([]))))
    save('learning_check',g,g.record(support=support,counterexamples=counters,contested=contested,unknown=unknown,support_count=g.length(units),unknown_count=g.length(unknown),eligible=g.datum(eligible)),
        'Check a candidate against all direct observations, counting distinct witnesses. Explicit negations are counterexamples; absent conclusions are unknown. Never use this candidate’s own deductions as support.')

    g=G();candidate=g.get(g.input,'candidate');check=g.call('learning_check',g.input)
    decision=g.choose(g.has(candidate,g.data('decision')),g.get(candidate,'decision'),g.data('proposed'))
    wasactive=g.eq(decision,g.data('accepted'));eligible=g.boolean(g.get(check,'eligible'))
    decision=g.choose(g.both(wasactive,g.inverse(eligible)),g.data('needs_review'),decision)
    status=g.choose(g.eq(decision,g.data('accepted')),g.data('active'),g.choose(g.eq(decision,g.data('needs_review')),g.data('suspended'),g.choose(g.eq(decision,g.data('proposed')),g.choose(eligible,g.data('proposed'),g.data('observing')),decision)))
    record=g.put(g.put(g.put(g.put(candidate,'decision',decision),'status',status),'evidence',check),'unknown_count',g.get(check,'unknown_count'))
    save('learning_assess',g,record,'Retain review decisions, keep unconfirmed rules provisional, and suspend adopted rules when counterexamples appear or supporting observations are removed.')

    assess=G();candidate=assess.get(assess.input,'item');assertions=assess.get(assess.input,'context')
    assessment=assess.call('learning_assess',assess.record(candidate=candidate,assertions=assertions))
    active=G();isactive=active.eq(active.get(active.input,'status'),active.data('active'))
    supportwitness=G();supportout=supportwitness.get(supportwitness.input,'witness')
    rule=G();ruleout=rule.put(rule.get(rule.input,'rule'),'evidence',rule.op('unique',rule.op('flatten',rule.map(rule.op('slice',rule.get(rule.input,'evidence','support'),stop=4),supportwitness.finish(supportout)))))
    g=G();hypotheses=g.choose(g.has(g.input,g.data('hypotheses')),g.get(g.input,'hypotheses'),g.data([]))
    assessed=g.map(hypotheses,assess.finish(assessment),g.get(g.input,'assertions'))
    save('learning_active_rules',g,g.map(g.map(assessed,active.finish(isactive,'Bool'),filter=True),rule.finish(ruleout)),
        'Only confirmed rules still supported by current assertions enter inference. Recheck on rebuild, including after retraction, restart or lesson edits.')

    # Generic policy-driven discovery, bounded before expensive evaluation.
    method=G();result=method.op('invoke',method.get(method.input,'item'),method.get(method.input,'context'))
    id_=G();idout=id_.get(id_.input,'id')
    fresh=G();new=fresh.inverse(fresh.op('contains',fresh.get(fresh.input,'context'),fresh.get(fresh.input,'item','id'),kind='Bool'))
    g=G();snapshot=g.get(g.input,'snapshot');policy=g.call('learning_policy',g.input);evidence=g.call('learning_evidence',snapshot)
    changed=g.choose(g.eq(g.get(g.input,'changed'),g.data(None)),g.get(evidence,'positive'),g.get(g.input,'changed'))
    context=g.record(changed=changed,positives=g.get(evidence,'positives'),positive=g.get(evidence,'positive'),symmetric=g.get(snapshot,'symmetric'),subtypes=g.get(snapshot,'subtypes'))
    candidates=g.op('unique',g.op('flatten',g.map(g.get(policy,'candidate_methods'),method.finish(result),context)))
    existing=g.get(snapshot,'hypotheses');new=g.map(candidates,fresh.finish(new,'Bool'),g.map(existing,id_.finish(idout)),filter=True)
    # take a bounded prefix through an index predicate; the bound is taught data.
    limited=G();keep=limited.lt(limited.get(limited.input,'item'),limited.get(limited.input,'context','limit'))
    take=G();selected=take.item(take.get(take.input,'context'),take.get(take.input,'item'))
    indexes=g.map(g.op('indices',new),limited.finish(keep,'Bool'),g.record(limit=g.get(policy,'max_new_candidates')),filter=True)
    new=g.map(indexes,take.finish(selected),new)
    save('learning_discover',g,g.op('concat',existing,new),'Invoke the taught candidate generators, deduplicate proposals, retain prior decisions, and bound new candidates per pass.')

    # Persist the assessment as graph records. Writes capture before/after evidence
    # through the workspace port, so old decisions remain in attributed history.
    identical=G();sameid=identical.eq(identical.get(identical.input,'item','id'),identical.get(identical.input,'context','id'))
    persist=G();record=persist.get(persist.input,'item');prior=persist.map(persist.get(persist.input,'context'),identical.finish(sameid,'Bool'),record,filter=True)
    unchanged=persist.choose(yes(persist,prior),persist.eq(persist.item(prior,persist.data(0)),record),persist.eq(persist.data(0),persist.data(1)),kind='Bool')
    written=write(persist,record);saved=persist.choose(unchanged,record,persist.get(written,'after'))
    pending=G();h=pending.input;asked=pending.choose(pending.has(h,pending.data('asked')),pending.boolean(pending.get(h,'asked')),pending.eq(pending.data(0),pending.data(1)),kind='Bool')
    ready=pending.both(pending.inverse(asked),pending.both(pending.eq(pending.get(h,'status'),pending.data('proposed')),pending.boolean(pending.get(h,'evidence','eligible'))))
    g=G();snapshot=g.call('learning_snapshot',g.input);policy=g.call('learning_policy',g.input)
    candidates=g.call('learning_discover',g.record(snapshot=snapshot,changed=g.get(g.input,'changed')))
    assessed=g.map(candidates,assess.finish(assessment),g.get(snapshot,'assertions'))
    saved=g.map(assessed,persist.finish(saved),g.get(snapshot,'hypotheses'));pendingrows=g.op('sort',g.map(saved,pending.finish(ready,'Bool'),filter=True),key='unknown_count')
    waiting=g.op('observe',g.input,surface='dialogue')
    askallowed=g.both(g.boolean(g.get(policy,'auto_ask')),g.both(g.boolean(g.get(g.input,'ask')),g.eq(g.get(waiting,'waiting'),g.data(None))))
    review=g.op('invoke',g.data('learning_review'),g.get(g.item(pendingrows,g.data(0)),'id'))
    oldactive=G();oldyes=oldactive.eq(oldactive.get(oldactive.input,'status'),oldactive.data('active'))
    previousactive=g.map(g.map(g.get(snapshot,'hypotheses'),oldactive.finish(oldyes,'Bool'),filter=True),id_.finish(idout))
    suspended=G();h=suspended.get(suspended.input,'item');newly=suspended.both(suspended.eq(suspended.get(h,'status'),suspended.data('suspended')),suspended.op('contains',suspended.get(suspended.input,'context'),suspended.get(h,'id'),kind='Bool'))
    revisions=g.map(saved,suspended.finish(newly,'Bool'),previousactive,filter=True)
    quiet=g.choose(g.eq(g.get(g.input,'changed'),g.data(None)),g.data('Reviewed current observations. Proposals and their evidence are in Learning & hypotheses.'),g.data(''))
    notice=g.choose(yes(g,revisions),g.data('I suspended a previously confirmed rule because its observations changed or conflict with it. Its deductions have been withdrawn; you can review the evidence in Learning & hypotheses.'),quiet)
    plain=g.record(text=notice,hypotheses=saved)
    out=g.choose(g.both(askallowed,yes(g,pendingrows)),review,plain)
    save('learning_cycle',g,g.choose(g.boolean(g.get(policy,'enabled')),out,g.record(text=g.data('Pattern learning is paused in its taught policy.'))),
        'Discover patterns, reassess and store hypotheses, and ask about one eligible proposal when the dialogue is free. Proposed and rejected rules never produce deductions.')

    g=G();record=read(g,'knowledge.hypotheses',g.input);snapshot=g.call('learning_snapshot',g.input)
    assessed=g.call('learning_assess',g.record(candidate=record,assertions=g.get(snapshot,'assertions')))
    record=g.get(write(g,g.put(assessed,'asked',g.data(True))),'after')
    prompt=g.textcat(g.get(record,'label'),g.data('\nI found '),g.op('text',g.get(record,'evidence','support_count')),
        g.data(' distinct supporting examples and '),g.op('text',g.get(record,'evidence','unknown_count')),
        g.data(' cases whose conclusions are still unknown. This is a hypothesis, not a proof of a universal rule.\nReply yes to confirm, no to reject, or skip. The notebook shows the observations and counterexamples.'))
    ask=g.op('act',g.input,g.record(text=prompt,resume=g.data('learning_reply'),state=g.record(id=g.get(record,'id'),rule=g.get(record,'rule'))),surface='dialogue',action='ask')
    blocked=g.record(text=g.data('This proposal currently has too little support or conflicting evidence. Explain or correct the observations before confirming it.'))
    save('learning_review',g,g.choose(g.boolean(g.get(record,'evidence','eligible')),ask,blocked),
        'Recheck a selected proposal against current evidence before asking for a decision. Retain its exact rule with the pending question.')

    g=G();s=g.get(g.input,'state');reply=g.op('lower',g.get(g.input,'input'));policy=g.call('learning_policy',g.input)
    old=read(g,'knowledge.hypotheses',g.get(s,'id'));snapshot=g.call('learning_snapshot',g.input)
    assessed=g.call('learning_assess',g.record(candidate=old,assertions=g.get(snapshot,'assertions')))
    confirm=g.op('contains',g.get(policy,'confirm'),reply,kind='Bool');reject=g.op('contains',g.get(policy,'reject'),reply,kind='Bool');defer=g.op('contains',g.get(policy,'defer'),reply,kind='Bool')
    current=g.eq(g.get(old,'rule'),g.get(s,'rule'));eligible=g.boolean(g.get(assessed,'evidence','eligible'))
    accepted=g.both(confirm,g.both(current,eligible))
    decision=g.choose(accepted,g.data('accepted'),g.choose(reject,g.data('rejected'),g.choose(defer,g.data('deferred'),g.data('needs_review'))))
    changed=g.put(g.put(assessed,'decision',decision),'teacher_reply',g.get(g.input,'input'))
    final=g.call('learning_assess',g.record(candidate=changed,assertions=g.get(snapshot,'assertions')))
    stored=g.get(write(g,final),'after')
    message=g.choose(g.eq(g.get(stored,'decision'),g.data('accepted')),g.data('Confirmed. I can now use this general rule; new counterexamples will suspend it.'),g.choose(reject,g.data('Rejected. This pattern will not be used as a rule.'),g.choose(defer,g.data('Deferred. The hypothesis remains unconfirmed.'),g.data('I have left that rule inactive for review.'))))
    recognized=g.either(confirm,g.either(reject,defer))
    out=g.choose(recognized,g.record(text=message),g.record(text=message,language_input=g.get(g.input,'input')))
    save('learning_reply',g,out,'Interpret the teacher’s decision, verify the question still refers to the same supported rule, and store acceptance, rejection or deferral. A fuller correction returns to ordinary language teaching.')
    return suite


if __name__ == '__main__':
    target=Path(__file__).parent/'curriculum/learning.json'
    target.write_text(json.dumps(build(),indent=2)+'\n')
    print(target)
