import json
import shutil
import subprocess
import unittest
import foundation
from build_programming_curriculum import build
from build_react_curriculum import build as react_build
from javascript import compile_source, display_value


CASES=[
 'console.log([].find(x => x), [].findIndex(x => x), [].some(x => x), [].every(x => x));',
 'console.log([0,2,3].find(x => x), [0,2,3].findIndex(x => x), [0,2,3].some(x => x), [0,2,3].every(x => x));',
 'console.log([1,2].find(x => false), [1,2].findIndex(x => false), [1,2].some(x => false), [1,2].every(x => true));',
 'console.log([1,2].some(x => x === 1 ? true : Math.pow(2,-1)), [1,2].every(x => x === 1 ? false : Math.pow(2,-1)));',
 'console.log([1,2].find(x => x === 1 ? true : Math.pow(2,-1)), [1,2].findIndex(x => x === 1 ? true : Math.pow(2,-1)));',
 'console.log([1,2].map(x => [0,x].find(y => y)));',
 'console.log([3,4].find((x,i,a) => i === 1 && a.length === 2));',
 'const k="name"; const before={name:"old", active:true}; console.log({...before,[k]:"new"},before);',
 'const n=2; console.log({[n+1]:"three",["__proto__"]:7}[3]);',
 'console.log({["x"]:1, x:2, ["x"]:3}.x);',
]

class SearchReactTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lib=foundation.curriculum()|build()|react_build()
 def run_graph(self,name,value):return foundation.run(self.lib,name,value)[0]
 def test_js_search_and_computed_keys(self):
  if not shutil.which('node'):self.skipTest('Node is a test oracle only')
  script="const cases=JSON.parse(require('fs').readFileSync(0,'utf8'));const out=cases.map(s=>{const logs=[];new Function('console',s)({log:(...a)=>logs.push(a)});return logs;});process.stdout.write(JSON.stringify(out,(k,v)=>v===undefined?{__js_type:'undefined'}:v));"
  expected=json.loads(subprocess.run(['node','-e',script],input=json.dumps(CASES),text=True,capture_output=True,check=True,timeout=15).stdout)
  for source,logs in zip(CASES,expected):
   with self.subTest(source=source):
    actual=self.run_graph('js_execute',{'program':compile_source(source),'argument':None})
    self.assertEqual(display_value(actual['logs']),logs)
 def test_queue_order_and_boundaries(self):
  for updates,expected in [([],0),([{'kind':'replace','value':1}]*3,1),([{'kind':'increment','value':1}]*3,3),
      ([{'kind':'replace','value':5},{'kind':'increment','value':1}],6),
      ([{'kind':'increment','value':1},{'kind':'replace','value':5}],5)]:
   result=self.run_graph('react_state_queue',{'initial':0,'updates':updates})
   self.assertEqual(result['value'],expected);self.assertEqual(len(result['steps']),len(updates))
  for data in [{'initial':True,'updates':[]},{'initial':0,'updates':[{'kind':'unknown','value':1}]},
      {'initial':9007199254740991,'updates':[{'kind':'increment','value':1}]},
      {'initial':0,'updates':[{'kind':'replace','value':1}]*65}]:
   with self.assertRaises(ValueError):self.run_graph('react_state_queue',data)
 def test_effect_lifecycle(self):
  for phase,before,after,cleanup,expected in [
      ('mount',None,[],False,['setup']),('update',[],[],True,[]),
      ('update',['a'],['b'],True,['cleanup','setup']),('update',['a'],['b'],False,['setup']),
      ('update',None,None,True,['cleanup','setup']),('update',[1],[True],True,['cleanup','setup']),
      ('unmount',[],None,True,['cleanup']),('unmount',[],None,False,[])]:
   with self.subTest(phase=phase,before=before,after=after):
    actual=self.run_graph('react_effect_lifecycle',dict(phase=phase,previous=before,next=after,cleanup=cleanup))
    self.assertEqual(actual['actions'],expected)
  for dependencies in [[{}],[[]],[1.5],[-0.0],[2.0]]:
   with self.assertRaises(ValueError):self.run_graph('react_effect_lifecycle',dict(phase='update',previous=dependencies,next=dependencies,cleanup=True))
  with self.assertRaises(ValueError):self.run_graph('react_effect_lifecycle',dict(phase='update',previous=[],next=[1],cleanup=True))

if __name__=='__main__':unittest.main()
