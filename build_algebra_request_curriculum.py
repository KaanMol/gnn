"""Author explicit equation-request phrasing as stored graph rules."""
from graph_dsl import G


def build():
 g=G();text=g.input;parts=g.op('split_text',text,g.data(':'));head=g.op('lower',g.get(parts,0))
 nonempty=G();words=g.map(g.op('split_text',head,g.data(' ')),nonempty.finish(nonempty.inverse(nonempty.eq(nonempty.input,nonempty.data(''))),'Bool'),filter=True)
 count=g.length(words);first=g.choose(g.nonempty(words),g.get(words,0),g.data(''))
 variable=g.choose(g.nonempty(words),g.item(words,g.data(-1)),g.data(''));letters=g.op('characters',g.data('abcdefghijklmnopqrstuvwxyz'))
 named=g.both(g.op('contains',letters,variable,kind='Bool'),g.either(g.eq(count,g.data(2)),g.choose(g.eq(count,g.data(3)),g.eq(g.get(words,1),g.data('for')),g.eq(g.data(0),g.data(1)),kind='Bool')))
 recognized=g.both(g.eq(g.length(parts),g.data(2)),g.both(g.eq(first,g.data('solve')),g.either(g.eq(count,g.data(1)),named)))
 operation=g.record(op=g.data('solve_math'),subject=g.data(''),relation=g.data(''),object=g.data(''),negative=g.data(False),conditions=g.data([]),text=g.get(parts,1))
 result=g.choose(recognized,g.record(operations=g.op('data_list',operation)),g.data(None))
 return {'algebra_request_interpret':{'graph':g.finish(result,internal=True,trace_mode='explicit'),'source':'Taught request forms: Solve: equation, Solve x: equation, Solve for x: equation. One-letter variable labels are accepted; the algebra reader validates the equation.'}}
