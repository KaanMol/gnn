"""Teacher-authored identity correction rules; runtime decisions are graph data."""
from graph_dsl import G


def build(library):
 suite={}
 def save(name,g,value):
  suite[name]={'graph':g.finish(value,internal=True,trace_mode='explicit',memoize=True),'source':'Explicit reference-disambiguation and truthful clarification lessons.'}
 # Scope both endpoints. Old rows retain their original subject-only meaning.
 match=G();scope=match.get(match.input,'item');ctx=match.get(match.input,'context');row=match.get(ctx,'row');endpoint=match.get(ctx,'endpoint')
 ep=match.choose(match.has(scope,match.data('endpoint')),match.get(scope,'endpoint'),match.data(1))
 same=match.eq(match.op('lower',match.item(match.get(row,'fact'),endpoint)),match.op('lower',match.get(scope,'name')))
 source=match.op('split_text',match.get(row,'source'),match.get(scope,'source_contains'))
 ok=match.both(match.eq(ep,endpoint),match.both(same,match.nonempty(match.op('slice',source,start=1))))
 target=G();g=G();scopes=g.get(g.call('meaning_policy',g.input),'source_scopes')
 found=g.map(g.map(scopes,match.finish(ok,'Bool'),g.input,filter=True),target.finish(target.get(target.input,'scope')))
 choices=g.op('unique',found);old=g.item(g.get(g.input,'row','fact'),g.get(g.input,'endpoint'))
 value=g.choose(g.eq(g.length(choices),g.data(1)),g.get(choices,0),old)
 save('meaning_scoped_endpoint',g,value)
 row=G();a=row.input;fact=row.get(a,'fact')
 first=row.call('meaning_scoped_endpoint',row.record(row=a,endpoint=row.data(1)))
 second=row.choose(row.eq(row.get(fact,0),row.data('is')),row.get(fact,2),row.call('meaning_scoped_endpoint',row.record(row=a,endpoint=row.data(2))))
 interpreted=row.call('meaning_fact',row.op('data_list',row.get(fact,0),first,second))
 g=G();save('meaning_assertions',g,g.map(g.input,row.finish(row.put(a,'fact',interpreted))))
 g=G();fact=g.input
 first=g.call('meaning_reference_question',g.get(fact,1))
 second=g.choose(g.eq(g.get(fact,0),g.data('is')),g.data(''),g.call('meaning_reference_question',g.get(fact,2)))
 save('meaning_fact_reference_question',g,g.choose(g.eq(first,g.data('')),second,first))
 # Explicit relation-role teaching; no entity names or countries hard-coded.
 g=G();save('meaning_person_city_roles',g,g.data([
  {'relation':r,'endpoint':endpoint,'sense':sense}
  for r,endpoint,sense in [('has sister',2,'person'),('has brother',2,'person'),('sister of',1,'person'),('brother of',1,'person'),('world bank listed capital',2,'city'),('capital of',1,'city')]]))
 role=G();rule=role.get(role.input,'item');ctx=role.get(role.input,'context');a=role.get(ctx,'row');f=role.get(a,'fact');name=role.get(ctx,'name')
 valid=role.both(role.eq(role.get(f,0),role.get(rule,'relation')),role.eq(role.op('lower',role.item(f,role.get(rule,'endpoint'))),role.op('lower',name)))
 entry=role.record(name=name,scope=role.textcat(name,role.data(' ('),role.get(rule,'sense'),role.data(')')),source_contains=role.get(a,'source'),endpoint=role.get(rule,'endpoint'))
 selected=role.choose(valid,role.op('data_list',entry),role.data([]))
 each=G();entries=each.op('flatten',each.map(each.call('meaning_person_city_roles',each.input),role.finish(selected),each.record(row=each.get(each.input,'item'),name=each.get(each.input,'context'))))
 g=G();name=g.get(g.input,'name');rows=g.op('unique',g.op('flatten',g.map(g.get(g.input,'assertions'),each.finish(entries),name)))
 scope=G();labels=g.op('unique',g.map(rows,scope.finish(scope.get(scope.input,'scope'))))
 enough=g.both(g.op('contains',labels,g.textcat(name,g.data(' (person)')),kind='Bool'),g.op('contains',labels,g.textcat(name,g.data(' (city)')),kind='Bool'))
 policy=g.call('meaning_policy',g.input)
 updated=g.put(policy,'source_scopes',g.op('unique',g.op('concat',g.get(policy,'source_scopes'),rows)))
 graph=g.record(input_type=g.data('Data'),output_type=g.data('Data'),nodes=g.op('data_list',g.data({'id':'input','op':'input','inputs':[],'type':'Data'}),g.record(id=g.data('policy'),op=g.data('data_literal'),inputs=g.data([]),type=g.data('Data'),value=updated)),output=g.data('policy'),internal=g.data(True),trace_mode=g.data('explicit'))
 result=g.record(entry=g.record(graph=graph,source=g.get(g.input,'source')),text=g.textcat(g.data('Saved separate references for '),name,g.data(' (person) and '),name,g.data(' (city). The family and geography evidence remains intact.')))
 save('meaning_separate_person_city',g,g.op('require',enough,result,message='I need identifiable family and city evidence before I can safely separate these references. No correction was saved.'))
 # A model clarification is never evidence that an operation succeeded.
 g=G()
 fixed=g.data("I couldn't resolve that meaning into a supported operation, so I haven't changed memory. Please specify the fact or connection to correct.")
 save('dialogue_clarification_response',g,fixed)
 # Recognize this explicit correction pattern through graph string operations.
 g=G();text=g.get(g.input,'text');lower=g.op('lower',g.op('replace_text',text,g.data('’'),g.data("'")))
 parts=g.op('split_text',lower,g.data(" as a person's name, not the city"));prefix=g.get(parts,0)
 start=g.op('split_text',prefix,g.data('i meant '))
 valid=g.both(g.eq(g.length(parts),g.data(2)),g.both(g.eq(g.length(start),g.data(2)),g.eq(g.get(start,0),g.data(''))))
 name=g.call('identity_text_range',g.record(text=text,start=g.data(8),stop=g.length(g.op('characters',prefix))))
 op=g.record(op=g.data('separate_person_city'),subject=name,relation=g.data(''),object=g.data(''),negative=g.data(False),conditions=g.data([]),text=g.data(''))
 save('meaning_correction_interpret',g,g.choose(valid,g.record(operations=g.op('data_list',op)),g.data(None)))
 return suite
