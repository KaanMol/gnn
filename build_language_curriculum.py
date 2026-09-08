import copy
"""A taught, bounded English/Dutch grammar over generic string/list operations."""
from graph_dsl import G


def patterns():
    result = {}
    def add(name, prefix='', separator='', suffix='', slots=(), op='assert', subject='', relation='', obj='', negative=False, text=''):
        result[name] = dict(prefix=prefix, separator=separator, suffix=suffix, slots=list(slots),
            operation=dict(op=op, subject=subject, relation=relation, object=obj, negative=negative, conditions=[], text=text))
    for lang, article, neg, who, name in [('en',' a ',' is not a ','who is ','my name is '),('nl',' een ',' is geen ','wie is ','ik heet ')]:
        add(lang+'_type',separator=' is'+article,slots=['subject','object'],subject='{subject}',relation='is',obj='{object}')
        add(lang+'_not_type',separator=neg,slots=['subject','object'],subject='{subject}',relation='is',obj='{object}',negative=True)
        add(lang+'_type_question',prefix='is ',separator=article,slots=['subject','object'],op='query',subject='{subject}',relation='is',obj='{object}')
        add(lang+'_who',prefix=who,slots=['subject'],op='describe',subject='{subject}')
        add(lang+'_name',prefix=name,slots=['subject'],op='identify',subject='{subject}')
    add('en_type_an',separator=' is an ',slots=['subject','object'],subject='{subject}',relation='is',obj='{object}')
    add('en_type_question_an',prefix='is ',separator=' an ',slots=['subject','object'],op='query',subject='{subject}',relation='is',obj='{object}')
    for lang, phrases in [('en', [(' lives in ','live in'),(' likes ','like'),(' created ','created'),(' is dating ','is dating')]),('nl',[(' woont in ','live in'),(' houdt van ','like'),(' heeft gemaakt ','created'),(' heeft een relatie met ','is dating')])]:
        for i,(separator,relation) in enumerate(phrases):
            add(f'{lang}_relation_{i}',separator=separator,slots=['subject','object'],subject='{subject}',relation=relation,obj='{object}')
            add(f'{lang}_forget_{i}',prefix='forget that ' if lang=='en' else 'vergeet dat ',separator=separator,slots=['subject','object'],op='retract',subject='{subject}',relation=relation,obj='{object}')
    for lang,prefix,suffix in [('en','where does ',' live'),('nl','waar woont ','')]:
        add(lang+'_where',prefix=prefix,suffix=suffix,slots=['subject'],op='describe',subject='{subject}',relation='live in')
    for lang,prefix in [('en','who lives in '),('nl','wie woont in ')]:
        add(lang+'_incoming_location',prefix=prefix,slots=['object'],op='find',relation='live in',obj='{object}')
    for name,text,subject in [('en_self','who are you','assistant'),('en_me','who am i','speaker'),('nl_self','wie ben jij','assistant'),('nl_self2','wie ben je','assistant'),('nl_me','wie ben ik','speaker')]:
        add(name,prefix=text,op='describe',subject=subject)
    for name,text in [('en_date',"what is today's date"),('nl_date','wat is de datum vandaag')]:add(name,prefix=text,op='current_date')
    for name,text in [('en_rename','your name is '),('en_rename2','your new name is '),('nl_rename','jouw naam is '),('nl_rename2','je nieuwe naam is ')]:add(name,prefix=text,slots=['subject'],op='rename_assistant',subject='{subject}')
    for name,prefix,sep in [('en_forget_type','forget that ',' is a '),('nl_forget_type','vergeet dat ',' is een ')]:add(name,prefix=prefix,separator=sep,slots=['subject','object'],op='retract',subject='{subject}',relation='is',obj='{object}')
    return result


def build(library):
    suite={}
    def save(name,g,out,description):suite[name]={'graph':g.finish(out,trace_mode='explicit',description=description),'source':'Explicit bilingual grammar teaching: '+description}
    def read(g,namespace,key):return g.op('act',g.input,g.record(namespace=g.data(namespace),key=key),surface='workspace',action='read')
    def write(g,namespace,key,value):return g.op('act',g.input,g.record(namespace=g.data(namespace),key=key,value=value),surface='workspace',action='write')
    # Normalization is a graph lesson; preserve punctuation inside names/numbers.
    guard=G();chars=guard.input;keep=guard.choose(guard.nonempty(chars),guard.op('contains',guard.data(['.','?','!',' ','\t','\n']),guard.item(chars,guard.data(-1)),kind='Bool'),guard.eq(chars,guard.data(None)),kind='Bool')
    body=G();short=body.op('slice',body.input,stop=-1)
    g=G();chars=g.op('characters',g.op('lower',g.input));chars=g.loop(chars,guard.finish(keep,'Bool'),body.finish(short));text=g.op('join_text',chars,g.data(''))
    for a,b in [('’',"'"),('\n',' '),('\t',' ')]:text=g.op('replace_text',text,g.data(a),g.data(b))
    row=G();nonempty=row.inverse(row.eq(row.input,row.data('')))
    save('language_normalize',g,g.op('join_text',g.map(g.op('split_text',text,g.data(' ')),row.finish(nonempty,'Bool'),filter=True),g.data(' ')),'Normalize case and whitespace and remove terminal punctuation while preserving punctuation inside values.')
    g=G();save('language_policy',g,g.data({'blocked_words':['forget','vergeet','says','said','thinks','zegt','zei','denkt','if','maybe','perhaps','or','and','not','never','sometimes','als','misschien','of','en','niet','nooit','soms'], 'type_blocked_words':['in','on','under','op','onder','with','met'], 'unresolved':['who','what','wie','wat','he','she','they','it','hij','zij','ze','het','die']}),'Decline clauses and unresolved third-person references that this starting grammar cannot safely represent. Ask rather than discard a condition or assume a referent.')
    g=G();policy=g.call('language_policy',g.input);words=g.op('split_text',g.get(g.input,'text'),g.data(' '))
    row=G();bad=row.op('contains',row.get(row.input,'context'),row.get(row.input,'item'),kind='Bool')
    blocked=g.map(words,row.finish(bad,'Bool'),g.get(policy,'blocked_words'),filter=True)
    unresolved=g.op('contains',g.get(policy,'unresolved'),g.get(g.input,'text'),kind='Bool')
    save('language_slot_valid',g,g.datum(g.both(g.inverse(g.eq(g.get(g.input,'text'),g.data(''))),g.both(g.inverse(g.nonempty(blocked)),g.inverse(unresolved)))),'Reject unsupported qualifiers, compound clauses, empty slots and unresolved pronouns.')
    # Match a prefix, up to two variable phrases separated by a literal, and a suffix.
    g=G();rule=g.get(g.input,'rule');text=g.get(g.input,'text');prefix=g.get(rule,'prefix');suffix=g.get(rule,'suffix')
    pp=g.op('split_text',text,prefix);pref_ok=g.choose(g.eq(prefix,g.data('')),g.eq(text,text),g.both(g.eq(g.length(pp),g.data(2)),g.eq(g.get(pp,0),g.data(''))),kind='Bool')
    rest=g.choose(g.eq(prefix,g.data('')),text,g.choose(pref_ok,g.get(pp,1),g.data('')));sp=g.op('split_text',rest,suffix)
    suff_ok=g.choose(g.eq(suffix,g.data('')),g.eq(text,text),g.choose(g.eq(g.length(sp),g.data(2)),g.eq(g.get(sp,1),g.data('')),g.eq(text,g.data(None)),kind='Bool'),kind='Bool')
    rest=g.choose(g.eq(suffix,g.data('')),rest,g.get(sp,0));count=g.length(g.get(rule,'slots'))
    pairs=g.op('split_text',rest,g.get(rule,'separator'))
    first=g.choose(g.eq(count,g.data(2)),g.get(pairs,0),rest);second=g.choose(g.eq(count,g.data(2)),g.get(pairs,1),g.data(''))
    valid=g.both(pref_ok,suff_ok);valid=g.both(valid,g.choose(g.eq(count,g.data(0)),g.eq(rest,g.data('')),g.choose(g.eq(count,g.data(2)),g.eq(g.length(pairs),g.data(2)),g.eq(count,g.data(1)),kind='Bool'),kind='Bool'))
    slots_ok=g.choose(g.eq(count,g.data(0)),g.eq(text,text),g.both(g.boolean(g.call('language_slot_valid',g.record(text=first))),g.choose(g.eq(count,g.data(2)),g.boolean(g.call('language_slot_valid',g.record(text=second))),g.eq(text,text),kind='Bool')),kind='Bool')
    # Do not flatten “a city in NL” into a type named “city in NL”.
    type_words=g.op('split_text',second,g.data(' '));policy=g.call('language_policy',g.input)
    bad=g.map(type_words,row.finish(bad,'Bool'),g.get(policy,'type_blocked_words'),filter=True)
    slots_ok=g.both(slots_ok,g.choose(g.eq(g.get(rule,'operation','relation'),g.data('is')),g.inverse(g.nonempty(bad)),g.eq(text,text),kind='Bool'))
    binding=g.choose(g.eq(count,g.data(0)),g.data({}),g.op('set_item',g.data({}),g.get(rule,'slots',0),first))
    binding=g.choose(g.eq(count,g.data(2)),g.op('set_item',binding,g.get(rule,'slots',1),second),binding)
    save('language_match',g,g.choose(valid,g.choose(slots_ok,binding,g.data(None)),g.data(None)),'Match a taught sentence frame and retain its variable phrases. Unsupported or partial matches yield no interpretation.')
    g=G();token=g.get(g.input,'token');bindings=g.get(g.input,'bindings')
    token=g.choose(g.eq(token,g.data('{subject}')),g.get(bindings,'subject'),g.choose(g.eq(token,g.data('{object}')),g.get(bindings,'object'),token))
    body=G();entry=read(body,'skills.language_words',body.input)
    lookup=g.op('attempt',token,body=body.finish(entry))
    save('language_resolve_word',g,g.choose(g.boolean(g.get(lookup,'ok')),g.get(lookup,'result'),token),'Resolve explicitly taught aliases, including Dutch concepts and dialogue roles. Unlisted words remain unchanged.')
    g=G();op=g.get(g.input,'rule','operation');bindings=g.get(g.input,'bindings');updated=op
    for field in ['subject','object']:
        value=g.call('language_resolve_word',g.record(token=g.get(op,field),bindings=bindings));updated=g.put(updated,field,value)
    save('language_operation',g,updated,'Fill the typed operation from matched phrases using the shared bilingual vocabulary.')
    each=G();rule=each.get(each.input,'item','value');text=each.get(each.input,'context');bindings=each.call('language_match',each.record(rule=rule,text=text))
    operation=each.choose(each.eq(bindings,each.data(None)),each.data(None),each.call('language_operation',each.record(rule=rule,bindings=bindings)))
    g=G();entries=g.op('act',g.input,g.record(namespace=g.data('skills.language_patterns')),surface='workspace',action='entries');text=g.call('language_normalize',g.get(g.input,'text'))
    candidates=g.map(entries,each.finish(operation),text);validrow=G();valid=validrow.inverse(validrow.eq(validrow.input,validrow.data(None)))
    candidates=g.op('unique',g.map(candidates,validrow.finish(valid,'Bool'),filter=True))
    clarification=g.data({'op':'clarify','subject':'','relation':'','object':'','negative':False,'conditions':[],'text':'I found more than one meaning in the taught grammar. Can you rephrase? / Ik vind meerdere betekenissen. Kun je het anders formuleren?'})
    result=g.record(operations=g.choose(g.eq(g.length(candidates),g.data(1)),candidates,g.op('data_list',clarification)))
    save('language_parse',g,g.choose(g.nonempty(candidates),result,g.data(None)),'Run all taught frames. Equivalent meanings merge; conflicting meanings ask for clarification. No model participates in this parser.')
    g=G();save('language_unknown',g,g.data({'operations':[{'op':'clarify','subject':'','relation':'','object':'','negative':False,'conditions':[],'text':'I have no taught sentence pattern for that yet. Can you rephrase, or teach a pattern in Teach & inspect? / Ik ken nog geen zinspatroon hiervoor. Kun je het anders formuleren of een patroon aanleren?'}]}),'Ask for teaching when symbolic mode cannot parse a message; never silently invoke Gemma.')
    g=G();unknown=g.call('language_unknown',g.input)
    save('language_unknown_response',g,g.record(text=g.get(unknown,'operations',0,'text')),'Explain the missing grammar pattern and ask for rephrasing or teaching in both languages.')
    g=G();mode=g.get(g.input,'mode');valid=g.op('contains',g.data(['symbolic','hybrid']),mode,kind='Bool');saved=write(g,'session.language',g.data('mode'),g.op('require',valid,mode,message='Choose symbolic or hybrid language mode.'))
    save('language_mode',g,g.record(text=g.textcat(g.data('Language mode: '),g.get(saved,'after'))),'Store the language mode. Symbolic mode disables model fallback; hybrid mode can ask the existing language model after taught patterns fail.')
    g=G();saved=write(g,'skills.language_words',g.call('language_normalize',g.get(g.input,'word')),g.get(g.input,'meaning'))
    save('language_teach_word',g,g.record(text=g.data('Learned that word mapping.'),entry=g.get(saved,'after')),'Teach an explicit surface word or phrase to its shared concept or dialogue role.')
    g=G();saved=write(g,'skills.language_patterns',g.get(g.input,'id'),g.get(g.input,'rule'))
    save('language_teach_pattern',g,g.record(text=g.data('Learned that sentence pattern.'),pattern=g.get(saved,'after')),'Store a sentence frame as graph data. The generic matcher reads these records on the next request.')
    base='behavior_interpret_before_bilingual';suite[base]=copy.deepcopy(library.get(base,library['behavior_interpret']))
    g=G();text=g.call('language_normalize',g.get(g.input,'text'))
    for a,b in [('voeg het weer van vandaag toe',"add today's weather"),('voeg weer toe','add weather'),(' aan mijn dashboard',' to my dashboard'),(' aan het dashboard',' to the dashboard'),('en ververs het','and refresh it'),('ververs het','refresh it'),('ververs het weer','refresh weather'),(' elke ',' every '),(' minuten',' minutes'),(' minuut',' minute'),(' uren',' hours'),(' uur',' hours'),(' seconden',' seconds')]:text=g.op('replace_text',text,g.data(a),g.data(b))
    dashboard=g.call('dashboard_interpret',g.record(text=text))
    weather=g.op('contains',g.data(['wat is het weer','hoe is het weer','wat voor weer is het']),text,kind='Bool')
    result=g.choose(weather,g.record(kind=g.data('graph_run'),name=g.data('web_weather'),argument=g.data(None)),g.choose(g.eq(dashboard,g.data(None)),g.call(base,g.input),dashboard))
    save('behavior_interpret',g,result,'Map taught Dutch dashboard/weather commands to the same graph methods, preserving previous English behavior.')
    return suite

WORDS={'ik':'speaker','mij':'speaker','me':'speaker','i':'speaker','jij':'assistant','jou':'assistant','je':'assistant','u':'assistant','you':'assistant','mens':'human','mensen':'human','humans':'human','persoon':'person','personen':'person','stad':'city','dorp':'town','land':'country','planeet':'planet','dier':'animal','kat':'cat','hond':'dog','nederland':'the netherlands'}
