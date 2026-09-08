"""Differential checks for generic prepared-plan optimizations."""
import unittest
import foundation
from graph_dsl import G
from graph_runtime import ExecutionCache, execute_graph, interface_binding
from javascript import source_curriculum
from build_programming_curriculum import build
from sensors import SensorHub, CanvasSurface

class PreparedIRTests(unittest.TestCase):
 def compare(self, graph, argument=None, library=None, limit=100000):
  outcomes=[]
  for optimized in (False, True):
   events=[];hub=SensorHub()
   hub.register_surface('fixture',CanvasSurface(lambda: {},{'tick':lambda arg:events.append(arg)}))
   try:
    result,trace=execute_graph(graph,argument,library,limit=limit,sensors=hub,execution_cache=ExecutionCache(optimize=optimized))
    trace=[{k:v for k,v in entry.items() if k != 'event_id'} for entry in trace]
    outcomes.append(('ok',result,trace,events))
   except (ValueError,KeyError) as error:
    outcomes.append(('error',type(error),str(error),events))
  self.assertEqual(outcomes[0],outcomes[1])
  return outcomes[0]

 def test_lazy_effects_errors_and_step_limits(self):
  g=G();effect=g.op('act',g.input,g.data({'value':1}),surface='fixture',action='tick')
  result=g.choose(g.eq(g.data(1),g.data(1)),g.data('safe'),effect)
  graph=g.finish(result,trace_mode='explicit')
  self.assertEqual(self.compare(graph)[-1],[])
  self.assertEqual(self.compare(graph,limit=2)[0],'error')
  g=G();bad=g.get(g.input,'absent');self.assertEqual(self.compare(g.finish(bad),{})[0],'error')

 def test_aggregate_bounds_remain_enforced(self):
  g=G();value=g.input
  # Sharing references must still count every occurrence toward the data budget.
  for _ in range(17):value=g.op('data_list',value,value)
  self.assertEqual(self.compare(g.finish(value),0)[0],'error')
  g=G();value=g.input
  for _ in range(65):value=g.record(value=value)
  self.assertEqual(self.compare(g.finish(value),None)[0],'error')

 def test_binding_edits_and_pure_collection_calls(self):
  lib=foundation.curriculum()
  g=G();value=g.op('as_data',g.size(g.input));graph=g.finish(value)
  self.assertEqual(self.compare(graph,[1,2,3],lib)[1],3)
  name=interface_binding('size',lib)
  replacement=G();lib[name]['graph']=replacement.finish(replacement.data('7'),interface='size')
  self.assertEqual(self.compare(graph,[1,2,3],lib)[1],7)

 def test_source_pipeline_matches_reference(self):
  lib=foundation.curriculum()|build()|source_curriculum()
  source='export default function X(){ const a=[1,2,3]; return <p>{a.map(x=>x+1)}</p>; }'
  self.compare(lib['javascript_run_source']['graph'],{'source':source,'argument':None,'has_input':False},lib,10000000)

if __name__=='__main__':unittest.main()
