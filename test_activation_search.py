import tempfile,unittest
from pathlib import Path
from experiments.activation_search import prepare,activation_search
from experiments.adaptive_reuse import graph
from test_prioritized_search import PriorityTests

class ActivationTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','top_k')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 def retain(self,name,op,expected):
  r=self.call('manager_retain',{'ops':[op,op],'name':name,'base':['set_a','set_b'],'validation':[{'input':{'a':0,'b':0},'expected':expected}],'predicate':'unused','projector':'unused'})
  self.assertTrue(r['retained']);self.call('activation_record',name)
 def setup_methods(self):
  PriorityTests.teach_set(self,'set_a','a');PriorityTests.teach_set(self,'set_b','b')
  self.retain('method_a','set_a',{'a':1,'b':0});self.retain('method_b','set_b',{'a':0,'b':1})
  return {'examples':[{'input':{'a':0,'b':0},'expected':{'a':1,'b':0}}],'predicate':'unused','projector':'unused','base':['set_a','set_b']}
 def test_target_specific_selection_and_all_active_control(self):
  request=self.setup_methods()
  top=self.call('activation_states',{**request,'mode':'top_k'});self.assertEqual(top['active'],['method_a'])
  other=self.call('activation_states',{**request,'mode':'top_k','examples':[{'input':{'a':0,'b':0},'expected':{'a':0,'b':1}}]});self.assertEqual(other['active'],['method_b'])
  all_=self.call('activation_states',{**request,'mode':'all_active'});self.assertEqual(all_['active'],['method_a','method_b'])
  self.assertEqual(top['primitives']['vocabulary'],['set_a','set_b'])
 def test_eviction_is_task_local_and_blocks_calls(self):
  request=self.setup_methods();before=self.store.map('knowledge.activation')['index']
  state=self.call('activation_states',{**request,'mode':'top_k'})['working']
  result=self.call('activation_observe',{'stats':[{'name':'method_a','best':1000,'stalls':7}],'ops':['method_a'],'allowed':True,'score':1000})
  self.assertEqual(result['active'],[]);self.assertEqual(result['evicted'],['method_a'])
  state.update(route_stats=result['stats'],active=[],evicted=['method_a'])
  skipped=self.call('activation_step',state);self.assertFalse(skipped['last_allowed']);self.assertTrue(skipped['done'])
  self.assertEqual(self.store.map('knowledge.activation')['index'],before)
  self.assertEqual(self.call('activation_states',{**request,'mode':'top_k'})['active'],['method_a'])
 def test_full_accounting_and_primitive_fallback(self):
  request=self.setup_methods();request={**request,'examples':[{'input':{'a':0,'b':0},'expected':{'a':3,'b':0}}]}
  r=activation_search(self.lib,self.hub,request,150000,['set_a','set_b'],'top_k')
  self.assertLessEqual(r['graph_steps'],150000);self.assertEqual(r['graph_steps'],sum(r['costs'].values()))
  self.assertGreater(r['costs'].get('primitives',0),0)
  self.assertLessEqual(r['costs'].get('memory',0)+r['costs'].get('retrieval',0)+r['costs'].get('allocation',0),50000)
  self.assertTrue(all(not any(op.startswith('method_') for op in d['ops']) for d in r['diagnostics'] if d['phase']=='primitives'))

if __name__=='__main__':unittest.main()
