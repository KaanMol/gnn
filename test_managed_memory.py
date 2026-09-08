import json,tempfile,unittest
from pathlib import Path
from experiments.program_synthesis import setup
from experiments.adaptive_reuse import graph
from experiments.reuse_benchmark import BASE
from experiments.managed_memory import managed_search

ROOT=Path(__file__).resolve().parent
class ManagedMemoryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub=setup(Path(self.tmp.name)/'db.sqlite3')
  for name in ['reuse-benchmark','adaptive-reuse','learning-economics','managed-memory']:self.lib.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
  self.run_graph('economy_init',None)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def run_graph(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 def test_canonicalization_parity_and_fail_closed(self):
  for prefix in [['synth_sum'],['synth_select','synth_count'],['synth_select','synth_sum']]:
   for suffix in [[],['bench_negate']*2,['bench_negate','bench_double','bench_negate'],['bench_double','bench_negate','bench_double']]:
    ops=prefix+suffix;canonical=self.run_graph('manager_canonicalize',{'ops':ops,'catalog':[]})
    self.assertTrue(canonical['valid'])
    for items in [[],[-2,1,4],[-6], [0,2]]:
     arg={'items':items,'predicate':'synth_positive','projector':'synth_identity'}
     before=self.run_graph('synth_execute_candidate',{'ops':ops,'argument':arg})
     after=self.run_graph('synth_execute_candidate',{'ops':canonical['ops'],'argument':arg})
     self.assertEqual(before,after)
  for ops in [['bench_negate','synth_sum'],['synth_sum','synth_select'],['unknown'],['synth_reverse','synth_sum']]:
   self.assertFalse(self.run_graph('manager_canonicalize',{'ops':ops,'catalog':[]})['valid'])
 def test_deduplication_retirement_and_dependencies(self):
  def retain(name,ops):return self.run_graph('manager_retain',{'name':name,'ops':ops,'base':BASE,'validation':[{'input':[-2,1,4],'expected':10}],'predicate':'synth_positive','projector':'synth_identity'})
  self.assertTrue(retain('first',['synth_select','synth_sum','bench_double'])['retained'])
  self.assertFalse(retain('duplicate',['first','bench_negate','bench_negate'])['retained'])
  self.assertEqual(len(self.store.map('knowledge.economics')['catalog']),1)
  for _ in range(24):self.run_graph('manager_update',{'log':[{'ops':['first'],'accepted':False}],'found':None,'validated':False})
  self.assertEqual(self.run_graph('manager_prepare',{'base':BASE})['selected'],[])
  self.assertIn('first',self.lib)
  self.assertEqual(self.run_graph('synth_execute_candidate',{'ops':['first'],'argument':{'items':[2],'predicate':'synth_positive','projector':'synth_identity'}}),4)
 def test_base_fallback_budget_and_actual_macro_reuse(self):
  self.run_graph('manager_retain',{'name':'selected_sum','ops':['synth_select','synth_sum'],'base':BASE,'validation':[{'input':[-2,1,4],'expected':5}],'predicate':'synth_positive','projector':'synth_identity'})
  request={'predicate':'synth_positive','projector':'synth_identity','examples':[{'input':[-2,1,4],'expected':10},{'input':[2,3],'expected':10},{'input':[-3],'expected':0}]}
  result=managed_search(self.lib,self.hub,request,450000)
  self.assertEqual(result['found'],['selected_sum','bench_double'])
  self.assertGreater(result['costs']['probing'],0)
  tiny=managed_search(self.lib,self.hub,request,20)
  self.assertEqual(tiny['graph_steps'],20);self.assertEqual(tiny['status'],'step_budget')

if __name__=='__main__':unittest.main()
