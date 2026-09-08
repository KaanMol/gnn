import unittest
import foundation
from build_programming_curriculum import build
from javascript import source_curriculum,argument,display_value
from graph_runtime import ExecutionCache

class WorkbenchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.lib=foundation.curriculum()|build()|source_curriculum()
 def run_graph(self,name,value):return foundation.run(self.lib,name,value,execution_cache=ExecutionCache())[0]
 def test_callback_return_blocks(self):
  source='function prices(xs) { return xs.filter(x => { return x.active; }).map(x => { return x.price * x.quantity; }).reduce((a, x) => { return a + x; }, 0); }'
  result=self.run_graph('javascript_run_source',{'source':source,'argument':argument([{'active':True,'price':3,'quantity':4},{'active':False,'price':99,'quantity':1}]),'has_input':True})
  self.assertEqual(display_value(result['execution']['value']),12)
  result=self.run_graph('javascript_run_source',{'source':'function f(xs){return xs.map(x=>{return;});}','argument':[1],'has_input':True})
  self.assertEqual(result['execution']['value'],[{'__js_type':'undefined'}])
 def test_unsupported_callback_statements_reject(self):
  with self.assertRaisesRegex(ValueError,'exactly one return'):
   self.run_graph('javascript_compile_source','function f(xs){return xs.map(x=>{const y=x+1;return y;});}')
 def spec(self):
  return {'pipeline':[{'operation':'filter','expression':'x.active'},{'operation':'map','expression':'x.price * x.quantity'}],'finish':'sum','tests':[{'input':argument([]),'expected':0},{'input':argument([{'active':True,'price':5,'quantity':3},{'active':False,'price':100,'quantity':1}]),'expected':15}]}
 def test_compose_and_verify(self):
  result=self.run_graph('javascript_write_pipeline',self.spec())
  self.assertEqual(result['tests_passed'],2)
  self.assertIn('.filter(x => (x.active)).map(x => (x.price * x.quantity))',result['source'])
  # Unseen input validates useful behavior beyond the two synthesis examples.
  executed=self.run_graph('javascript_run_source',{'source':result['source'],'argument':argument([{'active':True,'price':7,'quantity':2}]),'has_input':True})
  self.assertEqual(executed['execution']['value'],14)
 def test_false_spec_and_empty_tests_reject(self):
  spec=self.spec();spec['tests'][1]['expected']=99
  with self.assertRaisesRegex(ValueError,'did not pass'):self.run_graph('javascript_write_pipeline',spec)
  spec['tests']=[]
  with self.assertRaisesRegex(ValueError,'1–12'):self.run_graph('javascript_write_pipeline',spec)
 def test_analyze_without_input_or_execution(self):
  result=self.run_graph('javascript_analyze_source','function summarize(xs){ const count=xs.length; if(count>0){return count;} return 0; }')
  self.assertEqual(result['parameter'],'xs')
  ops=[x['operation'] for x in result['statements']]
  self.assertIn('branch',ops);self.assertIn('assign',ops)
  self.assertTrue(any(x['binding']=='count' for x in result['statements']))

if __name__=='__main__':unittest.main()
