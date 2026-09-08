import copy
import unittest
import foundation
from graph_dsl import G
from graph_runtime import ExecutionCache,EngineSurface,execute_graph
from sensors import SensorHub,CanvasSurface
from javascript import source_curriculum,display_value
from build_programming_curriculum import build

class ExecutionCacheTests(unittest.TestCase):
 def test_prepared_plans_reuse_new_inputs_and_survive_edit_undo(self):
  child=G();child_graph=child.finish(child.input)
  g=G();outer=g.finish(g.map(g.input,child_graph))
  cache=ExecutionCache()
  EngineSurface(cache,{"section":{"graph":outer}}).act("prepare",{"section":"section"})
  def run(values):return execute_graph(outer,values,execution_cache=cache)
  self.assertEqual(run([1,2])[0],[1,2])
  value,trace=run([3,4]);self.assertEqual(value,[3,4])
  self.assertEqual(trace[-1]['result']['hits'],0)
  self.assertGreater(trace[-1]['result']['prepared_plan_hits'],0)
  self.assertEqual(trace[-1]['result']['prepared_plan_misses'],0)
  original=copy.deepcopy(child_graph)
  replacement=G();child_graph.update(replacement.finish(replacement.data(9)))
  self.assertEqual(run([3,4])[0],[9,9])
  child_graph.clear();child_graph.update(original)
  self.assertEqual(run([5,6])[0],[5,6])
 def test_prepared_plan_capacity(self):
  cache=ExecutionCache(max_entries=1,max_bytes=1000)
  g=G(); graph=g.finish(g.input)
  engine=EngineSurface(cache,{'one':{'graph':graph}})
  cache.layout(graph);self.assertEqual(len(cache.plans),0)
  self.assertTrue(engine.act('prepare',{'section':'one'})['accepted'])
  self.assertTrue(engine.act('status',{'section':'one'})['warm'])
  engine.act('release',{'section':'one'})
  self.assertEqual(len(cache.plans),0)
 def test_graph_orchestrates_warm_release_and_capacity(self):
  cache=ExecutionCache();g=G();section=g.finish(g.input)
  lib={'section':{'graph':section}}
  def command(action):
   policy=G();root=policy.finish(policy.op('act',policy.input,policy.data({'section':'section'}),surface='engine',action=action))
   return execute_graph(root,None,lib,execution_cache=cache)[0]
  self.assertFalse(command('status')['warm'])
  self.assertTrue(command('prepare')['accepted'])
  self.assertTrue(command('status')['warm'])
  replacement=G();lib['section']['graph']=replacement.finish(replacement.data('changed'))
  self.assertFalse(command('status')['warm'])
  self.assertTrue(command('prepare')['accepted'])
  self.assertEqual(len(cache.plans),1)
  command('release');self.assertFalse(command('status')['warm'])
  small=ExecutionCache(max_bytes=1)
  self.assertFalse(EngineSurface(small,lib).act('prepare',{'section':'section'})['accepted'])
  self.assertEqual(small.sections,{})
 def test_shared_parent_and_nested_nodes_remain_immutable(self):
  g=G();child=g.finish(g.input)
  parent=G();outer=parent.finish(parent.map(parent.input,child))
  child['nodes'][0]=outer['nodes'][0]
  original=copy.deepcopy(outer)
  self.assertEqual(execute_graph(outer,[1,2])[0],[1,2])
  self.assertEqual(outer,original)
 def fixture(self):
  g=G();graph=g.finish(g.data({'answer':[1]}),trace_mode='explicit',cache_across_runs=True)
  root=G();rootgraph=root.finish(root.call('value',root.input),trace_mode='explicit')
  return {'value':{'graph':graph},'root':{'graph':rootgraph}}
 def test_hits_copy_and_rule_invalidation(self):
  lib=self.fixture();cache=ExecutionCache()
  run=lambda:execute_graph(lib['root']['graph'],None,lib,execution_cache=cache)
  first,_=run();first['answer'].append(99)
  result,trace=run();self.assertEqual(result,{'answer':[1]});self.assertEqual(trace[-1]['result']['hits'],1)
  lib['value']['graph']['nodes'][-1]['value']={'answer':[2]}
  result,trace=run();self.assertEqual(result,{'answer':[2]});self.assertEqual(trace[-1]['result']['hits'],0)
  del lib['value']
  with self.assertRaisesRegex(ValueError,'Missing taught procedure'):run()
 def test_effects_never_cached(self):
  count=[];hub=SensorHub();hub.register_surface('canvas',CanvasSurface(lambda: {'count':len(count)}, {'tick':lambda _:count.append(1)}))
  g=G();action=g.op('act',g.input,g.data({}),surface='canvas',action='tick')
  root=G();lib={'effect':{'graph':g.finish(action,cache_across_runs=True)},'root':{'graph':root.finish(root.call('effect',root.input))}}
  cache=ExecutionCache()
  for _ in range(2):execute_graph(lib['root']['graph'],None,lib,sensors=hub,execution_cache=cache)
  self.assertEqual(len(count),2);self.assertEqual(cache.bytes,0)
 def test_warm_cache_keeps_budget_and_capacity(self):
  lib=self.fixture();cache=ExecutionCache(max_bytes=1000,max_entries=1)
  execute_graph(lib['root']['graph'],None,lib,execution_cache=cache)
  with self.assertRaisesRegex(ValueError,'budget'):
   execute_graph(lib['root']['graph'],None,lib,limit=2,execution_cache=cache)
  cache.put(('other','null'),{'different':2},1)
  self.assertEqual(len(cache.values),1);self.assertLessEqual(cache.bytes,1000)
 def test_source_cache_and_edited_subtrees(self):
  lib=foundation.curriculum()|build()|source_curriculum();cache=ExecutionCache()
  def run(source):
   return foundation.run(lib,'javascript_run_source',{'source':source,'argument':None,'has_input':False},execution_cache=cache)
  source='export default function X(){ const n=2; return <p>{n+3}</p>; }'
  a,_=run(source);b,t=run(source)
  self.assertEqual(a,b);self.assertIn('javascript_compile_source',t[-1]['result']['procedures'])
  c,t=run(source.replace('n+3','n+4'))
  self.assertEqual(display_value(c['execution']['value'])['children'],[6])
  self.assertIn('js_source_lower_node',t[-1]['result']['procedures'])
  # An evaluator edit invalidates compiled caches too (conservative snapshot).
  lib['js_source_lower_node']['source']='Changed lesson metadata'
  _,t=run(source);self.assertNotIn('javascript_compile_source',t[-1]['result']['procedures'])

if __name__=='__main__':unittest.main()
