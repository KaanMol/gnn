import json,tempfile,unittest
from pathlib import Path
import foundation
from graph_dsl import G
from graph_runtime import execute_graph,ExecutionCache
from experiments.program_synthesis import setup
from experiments.reuse_benchmark import search,promote,BASE,TRAINING,MACRO_A
ROOT=Path(__file__).resolve().parent

class ReuseBenchmarkTests(unittest.TestCase):
 def test_meter_counts_nested_work_and_cached_cost(self):
  g=G();body=g.finish(g.calc('add',g.input,g.data(2)),cache_across_runs=True)
  root=G();wrapper=root.finish(root.call('added',root.input))
  lib=foundation.curriculum()|{'added':{'graph':body}}
  cache=ExecutionCache();measurements=[]
  for _ in range(2):
   meter={};result,_=execute_graph(wrapper,3,lib,execution_cache=cache,meter=meter)
   self.assertEqual(result,5);measurements.append(meter['logical_steps'])
  self.assertGreater(measurements[0],len(wrapper['nodes'])+len(body['nodes']))
  self.assertEqual(measurements[0],measurements[1])
  meter={}
  with self.assertRaisesRegex(ValueError,'budget'):execute_graph(wrapper,3,lib,limit=measurements[0]-1,execution_cache=cache,meter=meter)
  self.assertTrue(meter['budget_exhausted']);self.assertEqual(meter['logical_steps'],measurements[0]-1)
 def test_rank_generator_and_macro_execution(self):
  with tempfile.TemporaryDirectory() as tmp:
   store,lib,hub=setup(Path(tmp)/'db.sqlite3');lib.update(json.loads((ROOT/'curriculum/reuse-benchmark.json').read_text()))
   try:
    for rank,expected in [(0,[BASE[0],BASE[0]]),(1,[BASE[0],BASE[1]]),(6,[BASE[1],BASE[0]]),(35,[BASE[-1],BASE[-1]])]:
     actual=foundation.run(lib,'bench_candidate_at',{'vocabulary':BASE,'rank':rank,'depth':2})[0];self.assertEqual(actual,expected)
    found=search(lib,hub,TRAINING,BASE,5000000);self.assertEqual(found['found'],['synth_select','synth_sum'])
    vocab,cost=promote(lib,hub,MACRO_A,found['found'],BASE);self.assertEqual(vocab,BASE+[MACRO_A])
    request={'argument':{'items':[-9,4,5],'predicate':'synth_positive','projector':'synth_identity'}}
    meters=[]
    for ops in [found['found'],[MACRO_A]]:
     meter={};result,_=execute_graph(lib['synth_execute_candidate']['graph'],{'ops':ops,**request},lib,meter=meter,limit=100000)
     self.assertEqual(result,9);meters.append(meter['logical_steps'])
    self.assertGreater(meters[1],meters[0]*0.8) # Macro does not erase underlying cost.
    limited=search(lib,hub,TRAINING,vocab,50);self.assertEqual(limited['status'],'step_budget');self.assertEqual(limited['graph_steps'],50)
   finally:store.close()

if __name__=='__main__':unittest.main()
