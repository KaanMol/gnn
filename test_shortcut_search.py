import tempfile,unittest,copy
from pathlib import Path
from experiments.shortcut_search import prepare,shortcut_search
from experiments.adaptive_reuse import graph
from test_activation_search import ActivationTests

class ShortcutTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','memory')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 retain=ActivationTests.retain
 setup_methods=ActivationTests.setup_methods
 def test_primitive_state_matches_frozen_initializer(self):
  request={'base':['plan_east','plan_west'],'examples':[{'input':{'x':0},'expected':{'x':1}}],'predicate':'unused','projector':'unused'}
  self.assertEqual(self.call('shortcut_init',request),self.call('fair_init',request))
 def test_failed_probes_preserve_exact_primitive_trace_and_cost(self):
  request=self.setup_methods();request['examples']=[{'input':{'a':0,'b':0},'expected':{'a':2,'b':2}}]
  catalog=copy.deepcopy(self.store.map('knowledge.economics')['catalog'])
  r=shortcut_search(self.lib,self.hub,request,450000,request['base'],'memory')
  self.assertEqual(len(r['probes']),2);self.assertTrue(all(not p['probe']['eligible'] for p in r['probes']))
  self.assertEqual(r['selected'],[]);self.assertEqual(r['costs'].get('injection',0),0)
  reduced=shortcut_search(self.lib,self.hub,request,450000-r['costs']['probing'],request['base'],'no_memory')
  full=shortcut_search(self.lib,self.hub,request,450000,request['base'],'no_memory')
  self.assertEqual(r['diagnostics'],reduced['diagnostics'])
  self.assertEqual(r['diagnostics'],full['diagnostics'][:len(r['diagnostics'])])
  self.assertEqual(r['graph_steps'],reduced['graph_steps']+r['costs']['probing'])
  self.assertEqual(catalog,self.store.map('knowledge.economics')['catalog'])
 def test_injection_progress_composition_and_length(self):
  request=self.setup_methods();request['examples']=[{'input':{'a':0,'b':0},'expected':{'a':1,'b':1}}]
  state=self.call('shortcut_init',request)
  entries=self.call('shortcut_retrieve',None)
  for entry in entries:
   probe=self.call('shortcut_probe',{'state':state,'entry':entry});self.assertTrue(probe['eligible'])
   state=self.call('shortcut_inject',{'state':state,'entry':entry,'probe':probe})
  self.assertEqual(len(state['queue']),2);self.assertEqual(state['vocabulary'][:2],request['base'])
  for extension in ['set_b','method_b']:
   s=copy.deepcopy(state);s['parent']={'ops':['method_a'],'priority':0};s['next_i']=s['vocabulary'].index(extension)
   result=self.call('fair_step',s);self.assertEqual(result['found'],['method_a',extension])
   self.assertLessEqual(len(result['last_expanded']),5)
  s=copy.deepcopy(state);s['parent']={'ops':['method_a','method_b'],'priority':0};s['next_i']=s['vocabulary'].index('method_a')
  result=self.call('fair_step',s);self.assertEqual(len(result['last_expanded']),6);self.assertFalse(result['last_allowed'])
 def test_whole_reuse_and_global_cap(self):
  request=self.setup_methods()
  r=shortcut_search(self.lib,self.hub,request,450000,request['base'],'memory')
  self.assertEqual(r['found'],['method_a']);self.assertTrue(r['probes'][0]['injected'])
  self.assertLessEqual(r['graph_steps'],450000);self.assertEqual(sum(r['costs'].values()),r['graph_steps'])
  self.assertGreater(r['costs']['injection'],0);self.assertGreater(r['costs']['probing'],0)

if __name__=='__main__':unittest.main()
