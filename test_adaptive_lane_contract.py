import tempfile,unittest
from pathlib import Path
from experiments.adaptive_lanes import prepare,adaptive_search
from experiments.adaptive_reuse import graph
import test_activation_search as fixtures

class AdaptiveContractTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','memory')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 retain=fixtures.ActivationTests.retain
 setup_methods=fixtures.ActivationTests.setup_methods
 def test_actual_memory_probes_borrowing_and_duplicate_charges(self):
  request=self.setup_methods();request['examples']=[{'input':{'a':0,'b':0},'expected':{'a':2,'b':2}}]
  catalog=self.store.map('knowledge.economics')['catalog'];index=self.store.map('knowledge.activation')['index']
  r=adaptive_search(self.lib,self.hub,request,450000,['set_a','set_b'],'memory')
  self.assertEqual(set(r['selected']),{'method_a','method_b'})
  self.assertTrue({0,1,2}.issubset({e['lane'] for e in r['events']}))
  self.assertTrue(any(e['lane']>0 and e['before_stat']['spent']>=20000 for e in r['events']))
  ended=set()
  for e in r['events']:
   self.assertNotIn(e['lane'],ended)
   if 'after_stat' in e and not e['after_stat']['live']:ended.add(e['lane'])
  self.assertEqual(self.store.map('knowledge.economics')['catalog'],catalog)
  self.assertEqual(self.store.map('knowledge.activation')['index'],index)
  groups={}
  completed=[e for e in r['events'] if e['completed']]
  self.assertEqual(len(completed),len(r['diagnostics']))
  for e,z in zip(completed,r['diagnostics']):
   if z['allowed']:groups.setdefault(tuple(z['expanded']),[]).append((z['lane'],e['charged']))
  duplicated=[values for values in groups.values() if len({lane for lane,cost in values})>1]
  self.assertTrue(duplicated)
  self.assertTrue(all(cost>0 for values in duplicated for lane,cost in values))
  self.assertEqual(sum(e['charged'] for e in r['events']),r['costs']['execution'])
  self.assertEqual(sum(r['costs'].values()),r['graph_steps']);self.assertLessEqual(r['graph_steps'],450000)
 def test_primitive_borrows_in_actual_search(self):
  request=self.setup_methods();request['examples']=[{'input':{'a':0,'b':0},'expected':{'a':2,'b':2}}]
  r=adaptive_search(self.lib,self.hub,request,450000,['set_a','set_b'],'no_memory')
  self.assertTrue(any(e['lane']==0 and e['before_stat']['spent']>=100000 for e in r['events']))
  self.assertLessEqual(r['graph_steps'],450000)
 def test_stall_transition_stops_selection_but_preserves_retention(self):
  self.setup_methods()
  catalog=self.store.map('knowledge.economics')['catalog'];index=self.store.map('knowledge.activation')['index']
  # Seed the boundary explicitly: the full-budget fixture does not reach it.
  primitive={'id':0,'spent':110000,'best':0,'gains':[0],'costs':[1000],'stalls':0,'live':True}
  memory={'id':1,'spent':21000,'best':1000,'gains':[0],'costs':[1000],'stalls':7,'live':True}
  stopped=self.call('lanes_observe',{'stat':memory,'evaluation':{'matches':0,'progress':0},'charged':1000,'done':False})
  self.assertFalse(stopped['live'])
  for _ in range(3):
   self.assertEqual(self.call('lanes_choose',[primitive,stopped]),0)
   primitive['spent']+=1000
  self.assertEqual(self.store.map('knowledge.economics')['catalog'],catalog)
  self.assertEqual(self.store.map('knowledge.activation')['index'],index)
 def test_progress_winner_executes_beyond_its_initial_allowance(self):
  request=self.setup_methods()
  initialized=self.call('lanes_init',{**request,'mode':'memory'})
  for winner in [0,1]:
   stats=[{'id':i,'spent':110000 if i==0 else 30000,'best':0,'gains':[500 if i==winner else 0],'costs':[1000],'stalls':0,'live':True} for i in range(len(initialized['states']))]
   chosen=self.call('lanes_choose',stats);self.assertEqual(chosen,winner)
   result,cost=graph(self.lib,self.hub,'fair_step',initialized['states'][chosen])
   self.assertGreater(cost['graph_steps'],0)
   updated=self.call('lanes_observe',{'stat':stats[chosen],'evaluation':result['last_evaluation'],'charged':cost['graph_steps'],'done':result['done']})
   self.assertGreater(updated['spent'],stats[chosen]['spent'])
 def test_actual_lane_rejects_expanded_length_six(self):
  request=self.setup_methods();state=self.call('lanes_init',{**request,'mode':'memory'})['states'][1]
  name=state['vocabulary'][0];state['parent']={'ops':[name,name],'priority':0};state['next_i']=0
  result=self.call('fair_step',state)
  self.assertEqual(len(result['last_expanded']),6);self.assertFalse(result['last_allowed'])
  self.assertFalse(result['last_evaluation']['executable'])

if __name__=='__main__':unittest.main()
