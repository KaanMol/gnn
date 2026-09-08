"""React-oriented data transformations executed by taught graph procedures."""
import copy
import json
import shutil
import subprocess
import unittest

import foundation
from build_programming_curriculum import build
from javascript import argument, compile_source, display_value, handle


CASES = [
    'const name = "Kaan"; const user = {name, active: true, "score": 3, 0: "zero"}; console.log(user.name, user["score"], user[0], user.missing, typeof user);',
    'const a = {x: 1, nested: {n: 2}}; const b = {...a, x: 3}; console.log(a, b, b.nested.n);',
    'console.log({...null, ...undefined, a: 1, ...{a: 2, b: 3}, a: 4});',
    'const x = [1,2]; console.log([0,...x,3,], x);',
    'console.log([1,2,3].map(x => x * 2));',
    'console.log([0,1,2].filter(x => x));',
    'console.log([2,3,4].reduce((sum, x) => sum + x, 0));',
    'console.log([2,3].map((x, i, a, missing) => [x, i, a.length, missing]));',
    'console.log([2,3].reduce((acc, x, i, a) => acc + x + i + a.length, 0));',
    'console.log([].map(x => Math.pow(2, -1)), [].filter(x => Math.pow(2, -1)), [].reduce((a,x) => Math.pow(2, -1), 9));',
    'console.log([1,2].map(x => [3,4].map(y => x + y)));',
    'console.log([1,2].map(x => [3,4].map(x => x * 2)));',
    'let factor = 2; factor = 3; console.log([1,2].map(x => x * factor));',
    'console.log([1,2,3].filter(x => x > 1).map(x => x * 3).reduce((a,x) => a+x, 0));',
    'const todos = [{id: 1, done: false}, {id: 2, done: true}]; const next = todos.map(t => t.id === 1 ? {...t, done: !t.done} : t); console.log(todos, next, next.filter(t => t.done).map(t => t.id));',
    'console.log([1,2].map(x => { return {id: x}; }));',
    'console.log([1,2].reduce((a,x) => [...a, {id: x}], []));',
    'const user = {name: "Kaan", score: 3}; const {name, score: n} = user; console.log(name, n);',
    'const [a,b] = [3,4]; console.log(a+b);',
    'let x = 10; { const {x, y: z} = {x: 2, y: 3}; console.log(x, z); } console.log(x);',
]


class JavaScriptDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.library=foundation.curriculum() | build()

    def execute(self, source, value=None, library=None):
        return foundation.run(library or self.library,'js_execute',
            {'program':compile_source(source),'argument':argument(value)})[0]

    def test_react_state_transform_does_not_mutate_input(self):
        result=self.execute(CASES[14]);logs=display_value(result['logs'])
        self.assertFalse(logs[0][0][0]['done'])
        self.assertTrue(logs[0][1][0]['done'])
        self.assertEqual(logs[0][2],[1,2])

    def test_nested_callbacks_and_empty_arrays(self):
        self.assertEqual(self.execute(CASES[10])['logs'],[[[[4,5],[5,6]]]])
        self.assertEqual(self.execute(CASES[9])['logs'],[[[],[],9]])

    def test_explicit_boundaries(self):
        for source in ['const f = x => x + 1;', 'console.log([1].map(f));',
            'console.log([1].reduce((a,x) => a+x));',
            'console.log([1].map(x => { let y = x; return y; }));',
            'const a = {__proto__: null};', 'const x = 1; console.log({"x"});',
            'const {a,a} = {a: 1};', 'const [a,,b] = [1,2,3];',
            'const a = {x: 1}; a.x = 2;']:
            with self.subTest(source=source),self.assertRaises(ValueError):compile_source(source)
        for source in ['console.log({} === {});','console.log({}.toString);',
            'console.log({...3});','console.log([...3]);','console.log({}.map(x => x));',
            'const [a] = {0: 1};','const {a} = null;', 'const {a} = {a};',
            'console.log([1].map(x => Math.pow(2, -1)));']:
            with self.subTest(source=source),self.assertRaises(ValueError):self.execute(source)
        nested='1'
        for _ in range(9):nested='[1].map(x => '+nested+')'
        with self.assertRaisesRegex(ValueError,'eight frames'):self.execute('console.log('+nested+');')

    def test_object_input_and_chat_presentation(self):
        result=self.execute('function f(x) { return {...x, n: x.n + 1}; }',{'n':2})
        self.assertEqual(display_value(result['value']),{'n':3})
        class Session:
            def run_skill(s,name,data,original):
                value,_=foundation.run(JavaScriptDataTests.library,name,data)
                return '',{'result':value}
        text=handle(Session(),'function f(x) { return {...x, n: x.n + 1}; } f({"n": 2});')
        self.assertIn('result: {"n": 3}',text)
        # User records resembling internal tags remain ordinary object values.
        result=self.execute('function f(x) { return typeof x; }',{'__js_type':'undefined'})
        self.assertEqual(result['value'],'object')

    def test_callback_behavior_is_stored_graph_data(self):
        library=copy.deepcopy(self.library)
        del library['js_array_callback_resume']
        with self.assertRaisesRegex(ValueError,'Missing taught procedure'):
            self.execute('console.log([1].map(x => x));',library=library)
        library=copy.deepcopy(self.library)
        graph=library['js_object_get']['graph']
        graph.update(nodes=[{'id':'v','op':'data_literal','type':'Data','inputs':[],'value':77}],output='v')
        self.assertEqual(self.execute('console.log([{n: 1}].map(x => x.n));',library=library)['logs'],[[[77]]])

    def test_writing_react_data_helpers(self):
        from graph_store import GraphStore
        from javascript_lessons import examples
        class Session:
            def __init__(s):
                s.store=GraphStore();s.store.map('knowledge.javascript_examples').update(examples())
            def run_skill(s,name,data,original):
                value,_=foundation.run(JavaScriptDataTests.library,name,data)
                return '',{'result':value}
        session=Session()
        for task in ['toggle_todo','visible_todos','cart_total']:
            with self.subTest(task=task):
                self.assertIn('Candidate passed',handle(session,'Write JavaScript: '+json.dumps({'task':task})))

    @unittest.skipUnless(shutil.which('node'),'Node is only an independent test oracle')
    def test_against_javascript(self):
        oracle="""const fs=require('fs');const cases=JSON.parse(fs.readFileSync(0,'utf8'));
const out=cases.map(src=>{const logs=[];new Function('console',src)({log:(...xs)=>logs.push(xs)});return logs;});
process.stdout.write(JSON.stringify(out,(k,v)=>v===undefined?{__js_type:'undefined'}:v));"""
        reference=subprocess.run(['node','-e',oracle],input=json.dumps(CASES),text=True,capture_output=True,check=True,timeout=15)
        for source,expected in zip(CASES,json.loads(reference.stdout)):
            with self.subTest(source=source):self.assertEqual(display_value(self.execute(source)['logs']),expected)


if __name__=='__main__':unittest.main()
