import copy
import tempfile
import unittest
from pathlib import Path

import foundation
from build_programming_curriculum import build
from build_react_curriculum import build as react_build
from javascript import handle
from preview import Application


class Translator:
    model='fixture'
    def translate(self,*args):raise AssertionError('Programming requests must not be sent to the language model.')


class ProgrammingPreviewTests(unittest.TestCase):
    def test_playground_and_lessons(self):
        with tempfile.TemporaryDirectory() as folder:
            app=Application(Translator(),Path(folder)/'memory.json')
            try:
                app.session.core.procedures.update(foundation.curriculum() | build() | react_build())
                waiting={'question':'Preserve this pending dialogue'}
                app.session.store.map('interaction.state')['waiting']=waiting
                result=app.action({'action':'javascript_run','source':'console.log([1,2].map(x => x * 2));'})
                self.assertEqual(result['execution']['result']['logs'],[[[2,4]]])
                self.assertIn('code',result['execution']['compiled_program'])
                self.assertEqual(app.session.store.map('interaction.state')['waiting'],waiting)
                result=app.action({'action':'javascript_run','source':'function f(x) { return x * 2; } f(3);','input':4})
                self.assertEqual(result['execution']['result']['value'],8)
                component='''export default function TaskList() {
  const tasks = [
    {id: 1, title: "Learn JSX", done: true},
    {id: 2, title: "Build an app", done: false},
    {id: 3, title: "Practice JavaScript", done: false}
  ];
  const remaining = tasks.filter(task => !task.done);
  return (<section><h1>My tasks</h1><p>Remaining: {remaining.length}</p>
    <ul>{remaining.map(task => (<li key={task.id}>{task.title}</li>))}</ul></section>);
}'''
                escaped='\n'.join('&#x20;'+line[1:] if line.startswith(' ') else line for line in component.splitlines()).replace('<','\\<')
                del app.session.store.map('interaction.state')['waiting']
                for pasted in (component, '```jsx\n'+component+'\n```', escaped):
                    reply=app.action({'action':'chat','message':pasted})['answer']
                    self.assertIn('JavaScript subset result:',reply)
                    self.assertIn('Build an app',reply)
                    self.assertIn('Practice JavaScript',reply)
                    self.assertIn('"children": ["Remaining: ", 2]',reply)
                with self.assertRaisesRegex(ValueError,'Supply a function input'):
                    app.action({'action':'javascript_run','source':'function f(x) { return x; }'})
                with self.assertRaises(ValueError):
                    app.action({'action':'javascript_run','source':'console.log(process.exit());'})
                self.assertIn('document tree',handle(app.session,'Teach me HTML'))
                self.assertIn('className',handle(app.session,'Teach me JSX'))
                self.assertIn('HTML → JavaScript',handle(app.session,'Teach me React'))
            finally:app.session.store.close()

    def test_react_knowledge_and_attribute_rules_are_graph_data(self):
        library=foundation.curriculum() | react_build()
        for name,expected in [('class','className'),('for','htmlFor'),('aria-label','aria-label')]:
            self.assertEqual(foundation.run(library,'jsx_attribute_name',name)[0],expected)
        lesson=foundation.run(library,'react_explain','state')[0]
        self.assertIn('previous state',lesson['explanation'])
        revised=copy.deepcopy(library)
        for node in revised['react_explain']['graph']['nodes']:
            if node['op']=='data_literal':node['value']['state']['explanation']='Revised lesson'
        self.assertEqual(foundation.run(revised,'react_explain','state')[0]['explanation'],'Revised lesson')


if __name__=='__main__':unittest.main()
