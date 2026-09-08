"""Source-to-result acceptance tests for the exclusively graph-owned pipeline."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import foundation
from build_programming_curriculum import build
from javascript import source_curriculum,display_value
from preview import Application

TASKS='''export default function TaskList() {
  const tasks = [
    { id: 1, title: "Learn JSX", done: true },
    { id: 2, title: "Build an app", done: false },
    { id: 3, title: "Practice JavaScript", done: false }
  ];
  const remaining = tasks.filter(task => !task.done);
  return (
    <section>
      <h1>My tasks</h1>
      <p>Remaining: {remaining.length}</p>
      <ul>
        {remaining.map(task => (
          <li key={task.id}>{task.title}</li>
        ))}
      </ul>
    </section>
  );
}'''
EXPECTED={'type':'section','props':{},'children':[
 {'type':'h1','props':{},'children':['My tasks']},
 {'type':'p','props':{},'children':['Remaining: ',2]},
 {'type':'ul','props':{},'children':[[
 {'type':'li','props':{'key':2},'children':['Build an app']},
 {'type':'li','props':{'key':3},'children':['Practice JavaScript']}]]}]}

class Translator:
 model='fixture'
 def translate(self,*args):raise AssertionError('Code must not go to the language model')

class GraphSourceTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lib=foundation.curriculum()|build()|source_curriculum()
 def execute(self,source,argument=None,has_input=False):
  return foundation.run(self.lib,'javascript_run_source',{'source':source,'argument':argument,'has_input':has_input})[0]['execution']
 def test_task_list_raw_source(self):
  self.assertEqual(display_value(self.execute(TASKS)['value']),EXPECTED)
 def test_plain_javascript_and_callback_semantics(self):
  cases=[('console.log(2 + 3 * 4);',[[14]]),
   ('console.log(true || false && false, null ?? 7);',[[True,7]]),
   ('console.log([1,2,3].filter(x => x > 1).map(x => x * 2));',[[[4,6]]]),
   ('console.log([2,3].reduce((a,x) => a + x, 0));',[[5]]),
   ('console.log(false ? 1 : 3, false && Math.pow(2,-1));',[[3,False]]),
   ('const x={a:2}; console.log({...x,a:3}.a, x.a);',[[3,2]])]
  for source,expected in cases:
   with self.subTest(source=source):self.assertEqual(self.execute(source)['logs'],expected)
 def test_control_flow(self):
  cases=[('let sum=0; for(let i=0;i<5;i++){sum+=i;} console.log(sum);',[[10]]),
   ('let i=0; let sum=0; while(i<4){if(i>1){sum+=i;} i++;} console.log(sum);',[[5]]),
   ('let x=0; do{x++;}while(x<3); console.log(x);',[[3]]),
   ('let x=0; if(false){x=1;}else{x=2;} console.log(x);',[[2]])]
  for source,want in cases:
   with self.subTest(source=source):self.assertEqual(self.execute(source)['logs'],want)
  for source in ['const x=0; x++;','for(let i=0;i<2;i++){} console.log(i);']:
   with self.subTest(source=source),self.assertRaises(ValueError):self.execute(source)
 def test_learning_selects_a_general_rule(self):
  options=foundation.run(self.lib,'source_learning_character_candidates',None)[0]
  grammar={'root':{'op':'sequence','children':['digit','end'],'arity':2},'digit':{'op':'character','characters':['0','1'],'positive':True,'width':2},'end':{'op':'end'}}
  request={'grammar':grammar,'root':'root','rule':'digit','options':options,'examples':[{'source':'2','accepted':True},{'source':'x','accepted':False}],'regressions':[{'source':'7','accepted':True},{'source':'A','accepted':False},{'source':'22','accepted':False}]}
  result=foundation.run(self.lib,'source_learning_evaluate',request)[0]
  self.assertEqual(len(result['eligible']),1)
  learned=result['eligible'][0]['grammar']
  self.assertTrue(foundation.run(self.lib,'source_read_grammar',{'grammar':learned,'root':'root','source':'8'})[0]['accepted'])
  self.assertFalse(foundation.run(self.lib,'source_read_grammar',{'grammar':grammar,'root':'root','source':'8'})[0]['accepted'])
 def test_input(self):
  self.assertEqual(self.execute('function twice(x) { return x * 2; }',7,True)['value'],14)
  with self.assertRaisesRegex(ValueError,'Supply an input'):self.execute('function twice(x) { return x * 2; }')
 def test_unsupported_does_not_fall_back(self):
  for s in ['export default function X() { return <p></div>; }',
   'export default function X() { return <Counter/>; }',
   'function f(x) { return x; } f(2);',
   'while (true) { console.log(1); }',
   'const = 3;', 'const f=x=>3;', 'console.log(x=>3);', 'return 3;', 'const x=1; const x=2;', 'console.log(null ?? 1 || 2);', 'console.log(process.exit());']:
   with self.subTest(source=s),self.assertRaises(ValueError):self.execute(s)
 def test_stored_reader_is_required_and_editable(self):
  lib=copy.deepcopy(self.lib);del lib['javascript_read_source']
  with self.assertRaisesRegex(ValueError,'Missing taught procedure'):
   foundation.run(lib,'javascript_run_source',{'source':'console.log(1);','argument':None,'has_input':False})
  lib=copy.deepcopy(self.lib)
  # Changing grammar data alone changes accepted source spelling.
  table=next(n['value'] for n in lib['javascript_read_source']['graph']['nodes'] if n['op']=='data_literal' and isinstance(n['value'],dict))
  for rule in table.values():
   if rule.get('op')=='literal' and rule.get('characters')==list('const'):rule['characters']=list('fixed')
  self.assertTrue(foundation.run(lib,'javascript_read_source','fixed x=1;')[0]['accepted'])
  self.assertFalse(foundation.run(self.lib,'javascript_read_source','fixed x=1;')[0]['accepted'])
 def test_live_transport_never_calls_host_compiler(self):
  with tempfile.TemporaryDirectory() as d:
   app=Application(Translator(),Path(d)/'memory.json')
   try:
    app.session.core.procedures.update(self.lib)
    with patch('javascript.compile_source',side_effect=AssertionError('Host compilation forbidden')):
     result=app.action({'action':'javascript_run','source':'export default function X(){ return <p>{2+3}</p>; }'})
     self.assertEqual(display_value(result['execution']['result']['value'])['children'],[5])
     self.assertTrue(result['execution']['program_roots'])
     code='export default function X() {\n&#x20; return \\<p>Hi\\</p>;\n}'
     reply=app.action({'action':'chat','message':'```jsx\n'+code+'\n```'})['answer']
     self.assertIn('"children": ["Hi"]',reply)
   finally:app.session.store.close()

if __name__=='__main__':unittest.main()
