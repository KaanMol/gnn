import tempfile,unittest
from pathlib import Path
from experiments.adaptive_lanes import prepare,adaptive_search
from experiments.adaptive_reuse import graph
import test_activation_search as fixtures

class AdaptiveLaneTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','memory')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 retain=fixtures.ActivationTests.retain
 setup_methods=fixtures.ActivationTests.setup_methods
 def stat(self,id,spent,best=0,gains=None,costs=None,stalls=0):
  return {'id':id,'spent':spent,'best':best,'gains':gains or [],'costs':costs or [],'stalls':stalls,'live':True}
 def test_multiple_memories_and_original_only_lane(self):
  request=self.setup_methods();request['examples']=[{'input':{'a':0,'b':0},'expected':{'a':1,'b':1}}]
  result=self.call('lanes_init',{**request,'mode':'memory'})
  self.assertEqual(set(result['selected']),{'method_a','method_b'});self.assertEqual(len(result['states']),3)
  self.assertEqual(result['states'][0]['vocabulary'],['set_a','set_b'])
  for name,state in zip(result['selected'],result['states'][1:]):self.assertEqual(state['vocabulary'],[name,'set_a','set_b'])
  baseline=self.call('lanes_init',{**request,'mode':'no_memory'});self.assertEqual(len(baseline['states']),1)
 def test_floor_probes_and_borrowing_in_both_directions(self):
  stats=[self.stat(0,90000),self.stat(1,0),self.stat(2,0)]
  self.assertEqual(self.call('lanes_choose',stats),0)
  stats[0]['spent']=100000;self.assertEqual(self.call('lanes_choose',stats),1)
  stats[1]['spent']=21000;self.assertEqual(self.call('lanes_choose',stats),2)
  stats=[self.stat(0,100000,gains=[500],costs=[1000]),self.stat(1,30000,gains=[10],costs=[1000])]
  self.assertEqual(self.call('lanes_choose',stats),0) # Discovery can exceed floor.
  stats[0]['gains']=[0];stats[1]['gains']=[500]
  self.assertEqual(self.call('lanes_choose',stats),1) # Memory can exceed probe.
 def test_stalls_drop_only_memory_and_budget_is_charged(self):
  for id in [0,1]:
   s=self.stat(id,100000,best=100,stalls=7)
   r=self.call('lanes_observe',{'stat':s,'evaluation':{'matches':0,'progress':0},'charged':1000,'done':False})
   self.assertEqual(r['live'],id==0)
  request=self.setup_methods();request['examples']=[{'input':{'a':0,'b':0},'expected':{'a':2,'b':2}}]
  r=adaptive_search(self.lib,self.hub,request,160000,['set_a','set_b'],'memory')
  self.assertLessEqual(r['graph_steps'],160000);self.assertEqual(r['graph_steps'],sum(r['costs'].values()))
  self.assertEqual(sum(r['lane_spent']),r['costs'].get('execution',0))
  self.assertTrue(all(not any(op.startswith('method_') for op in z['ops']) for z in r['diagnostics'] if z['lane']==0))

if __name__=='__main__':unittest.main()
