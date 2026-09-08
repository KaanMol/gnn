"""Behavioral regression cases for the graph's abstract operations and scopes.

Node supplies independent expected values only in differential tests. These are
project tests, not a claim to have run the official Test262 harness.
"""
import copy
import json
import shutil
import subprocess
import unittest

import foundation
from build_programming_curriculum import build
from javascript import compile_source


CASES = [
    'console.log(Boolean(), Boolean(0), Boolean(1), Boolean(""), Boolean("0"), Boolean([]), Boolean(null), Boolean(undefined));',
    'console.log(!0, !1, !"", ![], !!null, !!"yes");',
    'console.log(typeof 3, typeof "hi", typeof null, typeof undefined, typeof true, typeof [], void 3);',
    'console.log(0 && Math.pow(2, -1), 1 || Math.pow(2, -1), false ?? Math.pow(2, -1));',
    'console.log(0 || 7, 2 && 8, null ?? 4, undefined ?? 5, "" ?? 6);',
    'console.log(0 ? Math.pow(2, -1) : 9, [] ? 3 : Math.pow(2, -1));',
    'console.log(1 ? 2 ? 3 : 4 : 5, 0 ? 1 : 0 ? 2 : 3, (null ?? 2) || 3, null ?? (0 || 7));',
    'let x = 1; if (x) { console.log("yes"); } else { console.log("no"); } if ("") { console.log("bad"); } else if ([]) { console.log("array"); }',
    'let x = 2; { let x = 7; x++; console.log(x); } console.log(x);',
    'let x; console.log(x); x = 4; console.log(x);',
    'let i = 9; for (let i = 0; i < 2; i++) { let k = i * 3; console.log(i, k); } console.log(i);',
    'let i = 0; do { i++; if (i === 2) { continue; } console.log(i); if (i === 3) { break; } } while (i < 5);',
    'let i = 0; while (i < 2) { let x; console.log(x); x = 3; i++; }',
    'let xs = []; console.log(xs && 5, xs || 4, xs ?? 3);',
]


class JavaScriptSemanticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.library=foundation.curriculum() | build()

    def execute(self, source, library=None):
        return foundation.run(library or self.library,'js_execute',
            {'program':compile_source(source),'argument':None})[0]

    def test_short_circuit_values_and_precedence(self):
        result=self.execute(CASES[3])
        self.assertEqual(result['logs'],[[0,1,False]])
        self.assertEqual(self.execute(CASES[6])['logs'],[[3,3,2,7]])
        for source in ['console.log(null ?? 1 || 2);','console.log(1 && null ?? 2);',
                       'console.log(null ?? 1 && 2);','console.log(1 || null ?? 2);']:
            with self.subTest(source=source),self.assertRaises(ValueError):compile_source(source)

    def test_temporal_dead_zone_and_lexical_errors(self):
        for source in [
            'console.log(x); let x = 1;',
            'let x = x;',
            'x = 1; let x;',
            'let x = 1; { console.log(x); let x = 2; }',
            'let x = 1; { console.log(typeof x); let x = 2; }',
            'let i = 0; while (i < 2) { if (i) { console.log(x); } let x = 3; i++; }',
        ]:
            with self.subTest(source=source),self.assertRaisesRegex(ValueError,'ReferenceError'):
                self.execute(source)
        for source in ['let x = 1; let x = 2;','const x;',
                       'let undefined = 2;','let Boolean = 3;',
                       '{ let x = 1; } console.log(x);',
                       'function f(x) { let x = 2; return x; }']:
            with self.subTest(source=source),self.assertRaises(ValueError):compile_source(source)

    def test_semantics_are_revisable_graphs(self):
        source='if (1) { console.log("yes"); } else { console.log("no"); }'
        self.assertEqual(self.execute(source)['logs'],[['yes']])
        library=copy.deepcopy(self.library)
        library['js_to_boolean']['graph']={'input_type':'Data','output_type':'Data',
            'nodes':[{'id':'v','op':'data_literal','inputs':[],'type':'Data','value':False}], 'output':'v'}
        self.assertEqual(self.execute(source,library)['logs'],[['no']])
        del library['js_read_binding']
        with self.assertRaisesRegex(ValueError,'Missing taught procedure'):self.execute(source,library)

    @unittest.skipUnless(shutil.which('node'),'Node is only a test oracle')
    def test_against_javascript(self):
        oracle="""const fs=require('fs');const src=JSON.parse(fs.readFileSync(0,'utf8'));
const logs=[];const capture={log:(...xs)=>logs.push(xs)};
new Function('console',src)(capture);
process.stdout.write(JSON.stringify(logs,(k,v)=>v===undefined?{__js_type:'undefined'}:v));"""
        for source in CASES:
            with self.subTest(source=source):
                result=subprocess.run(['node','-e',oracle],input=json.dumps(source),text=True,
                    capture_output=True,check=True,timeout=15)
                self.assertEqual(self.execute(source)['logs'],json.loads(result.stdout))


if __name__=='__main__':unittest.main()
