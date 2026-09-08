import copy
import json
import random
import shutil
import subprocess
import unittest

import foundation
from build_programming_curriculum import build
from javascript import compile_source, argument, handle
from javascript_lessons import MAXIMUM, SUM, COUNT, examples
from graph_store import GraphStore


class JavaScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.library=foundation.curriculum()|build()

    def execute(self,source,value,library=None):
        return foundation.run(library or self.library,'js_execute',{'program':compile_source(source),'argument':argument(value)})[0]

    def test_values_control_flow_and_trace(self):
        self.assertEqual(self.execute(MAXIMUM,[-8,-2,-11])['value'],-2)
        self.assertIsNone(self.execute(MAXIMUM,[])['value'])
        result=self.execute(SUM,[3,-2,9])
        self.assertEqual(result['value'],10)
        self.assertTrue(any(s['operation']=='branch' for s in result['steps']))
        self.assertEqual(result['steps'][-1]['variables']['total'],10)
        self.assertEqual(self.execute('function f(x) { let n = 0; while (n < x) { n++; if (n === 2) { continue; } if (n > 4) { break; } } return n; }',10)['value'],5)

    def test_types_bounds_and_rejections(self):
        self.assertIs(self.execute('function f(x) { return x === 1; }',True)['value'],False)
        self.assertIs(self.execute('function f(x) { return x !== null; }',None)['value'],False)
        for source,value in [
            ('function f(x) { return x + true; }',1),
            ('function f(x) { return x[-1]; }',[1]),
            ('function f(x) { return x === x; }',[1]),
            ('function f(x) { while (true) { x++; } return x; }',0),
            ('function f(x) { return x + 1; }',9007199254740991),
        ]:
            with self.subTest(source=source),self.assertRaises(ValueError):self.execute(source,value)
        for source in ['function f(x) { return process.exit(); }','function f(x) { return x / 2; }',
            'function f(x) { const y = 1; y++; return y; }','function f(x) { return 01; }',
            'function f(x) { if (true) { let y = 1; } return y; }',
            'function f(x) { for (let i = 0; i < 2; i++) { } return i; }']:
            with self.subTest(source=source),self.assertRaises(ValueError):compile_source(source)
        self.assertEqual(self.execute('function f(x) { let y = x; }',1)['value'],{'__js_type':'undefined'})

    def test_console_and_math(self):
        source='function f(x) { console.log("absolute", Math.abs(x)); console.log(); return Math.max(Math.pow(2, 3), Math.abs(x), 4); }'
        result=self.execute(source,-9)
        self.assertEqual(result['value'],9)
        self.assertEqual(result['logs'],[['absolute',9],[]])
        self.assertEqual(self.execute("function f(x) { console.log('hi ' + x); }",'there')['logs'],[['hi there']])
        for method,expected in [('abs',7),('sign',-1),('floor',-7),('ceil',-7),('round',-7),('trunc',-7)]:
            self.assertEqual(self.execute('function f(x) { return Math.'+method+'(x); }',-7)['value'],expected)
        self.assertEqual(self.execute('function f(x) { return Math.min(x, 3, -8); }',2)['value'],-8)
        script='const xs = [-3, 9]; console.log("max", Math.max(xs[0], xs[1]));'
        self.assertEqual(self.execute(script,None)['logs'],[['max',9]])
        with self.assertRaises(ValueError):compile_source('return 3;')
        for src in ['function f(x) { return Math.random(); }','function f(x) { return Math.max(); }',
                    'function f(x) { return Math.sqrt(x); }','function f(x) { console.error(x); }',
                    'function f(x) { for (return 1; x < 2; x++) { } return x; }']:
            with self.assertRaises(ValueError):compile_source(src)
        with self.assertRaises(ValueError):self.execute('function f(x) { return Math.pow(x, -1); }',2)
        lib=copy.deepcopy(self.library);del lib['js_math_binary']
        with self.assertRaisesRegex(ValueError,'Missing taught procedure'):
            self.execute('function f(x) { return Math.max(x, 2); }',3,lib)

    @unittest.skipUnless(shutil.which('node'),'Node is only a test oracle')
    def test_console_math_against_real_javascript(self):
        source='function f(x) { for (let i = 0; i < 3; i++) { console.log("n", Math.max(x, i)); } return Math.min(Math.abs(x), Math.pow(2, 3)); }'
        for value in [-12,0,5]:
            command="const d=JSON.parse(require('fs').readFileSync(0,'utf8'));const logs=[];const console={log:(...xs)=>logs.push(xs)};const value=eval('('+d.source+')')(d.value);process.stdout.write(JSON.stringify({value,logs}));"
            out=subprocess.run(['node','-e',command],input=json.dumps({'source':source,'value':value}),text=True,capture_output=True,check=True,timeout=15)
            reference=json.loads(out.stdout);actual=self.execute(source,value)
            self.assertEqual({'value':actual['value'],'logs':actual['logs']},reference)

    def test_missing_and_revised_lessons_change_execution(self):
        library=copy.deepcopy(self.library);del library['programming_expression']
        with self.assertRaisesRegex(ValueError,'Missing taught procedure'):
            self.execute('function f(x) { return x + 1; }',4,library)
        library=copy.deepcopy(self.library)
        library['programming_binary']['graph']={'input_type':'Data','output_type':'Data','nodes':[
            {'id':'value','op':'data_literal','inputs':[],'type':'Data','value':77}],'output':'value'}
        self.assertEqual(self.execute('function f(x) { return x + 1; }',4,library)['value'],77)

    def test_language_independent_representation(self):
        program={'parameter':'input','code':[{'op':'return','expression':[{'kind':'constant','value':42}]}]}
        result,_=foundation.run(self.library,'programming_execute',{'program':program,'argument':None})
        self.assertEqual(result['value'],42)

    def test_pasted_function_and_literal_call(self):
        class Session:
            def run_skill(s,name,arg,original):
                result,_=foundation.run(JavaScriptTests.library,name,arg)
                return '',{'result':result}
        self.assertIn('result: 42',handle(Session(),'function double(x) { return x * 2; }\ndouble(21);'))
        self.assertIn('Add a call',handle(Session(),'```javascript\nfunction double(x) { return x * 2; }\n```'))
        with self.assertRaises(ValueError):compile_source('function f(x) { return x; } f(process.exit());')

    def test_candidate_search_and_repair(self):
        class Session:
            def __init__(s):
                s.store=GraphStore();s.store.map('knowledge.javascript_examples').update(examples())
            def run_skill(s,name,arg,original):
                result,_=foundation.run(JavaScriptTests.library,name,arg)
                return '',{'result':result}
        session=Session()
        for task in ['maximum','minimum','sum','count_positive','product','absolute','factorial']:
            answer=handle(session,'Write JavaScript: '+json.dumps({'task':task}))
            self.assertIn('Candidate passed',answer)
        broken=MAXIMUM.replace('let best = xs[0];','let best = 0;')
        answer=handle(session,'Fix JavaScript: '+json.dumps({'source':broken,'tests':examples()['maximum']['tests']}))
        self.assertIn('let best = xs[0];',answer)

    @unittest.skipUnless(shutil.which('node'),'Node is only required as an independent test oracle')
    def test_differential_against_real_javascript(self):
        rng=random.Random(39)
        for source in [MAXIMUM,SUM,COUNT]:
            for _ in range(6):
                value=[rng.randrange(-20,21) for _ in range(rng.randrange(0,8))]
                payload=json.dumps({'source':source,'value':value})
                command="const fs=require('fs');const d=JSON.parse(fs.readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(eval('('+d.source+')')(d.value)));"
                output=subprocess.run(['node','-e',command],input=payload,text=True,capture_output=True,check=True,timeout=15)
                self.assertEqual(self.execute(source,value)['value'],json.loads(output.stdout))
