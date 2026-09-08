import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.sleep_memory import prepare,wake_search,consolidate
from experiments.utility_router import Meter,search
from test_activation_search import ActivationTests as Fixtures

class SleepTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,n,a):return Meter(self.store,self.lib,self.hub,2000000).call(n,a,'test')
 retain=Fixtures.retain
 setup_methods=Fixtures.setup_methods
 def test_cheap_rejection_preserves_residual_trace(self):
  q=self.setup_methods();q['examples']=[{'input':{'a':0,'b':0},'expected':{'a':2,'b':2}}]
  catalog=copy.deepcopy(self.store.map('knowledge.economics')['catalog'])
  with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):
   m=Meter(self.store,self.lib,self.hub);a=wake_search(m,q)
   self.assertIsNone(a['selected']);self.assertLessEqual(m.costs['wake_lookup'],128)
   self.assertNotIn('admitted_execution',m.costs)
   b=Meter(self.store,self.lib,self.hub);r=search(b,q,'no_memory',{'weights':[0]*6,'updates':0},0,cap=350000-m.costs['wake_lookup'])
   self.assertEqual(a['trace'],r['trace']);self.assertEqual(m.spent,b.spent+m.costs['wake_lookup'])
  self.assertEqual(catalog,self.store.map('knowledge.economics')['catalog'])
 def test_context_ignores_semantic_names_and_extra_audits(self):
  q=self.setup_methods();s=self.call('shortcut_init',q);key=self.call('sleep_context',s)
  changed=copy.deepcopy(s);changed['audit']={'future':'SECRET'}
  for e in changed['examples']:
   for f in e['features']:
    f['path']=['renamed'];f['value']=42 if isinstance(f['value'],int) else f['value']
  self.assertEqual(key,self.call('sleep_context',changed))
 def test_confidence_uses_downstream_not_local_progress(self):
  q=self.setup_methods();entry=self.store.map('knowledge.economics')['catalog'][0];s=self.call('shortcut_init',q);key=self.call('sleep_context',s);model=[]
  for i,u in enumerate([500,500]):
   model=self.call('sleep_update',{'model':model,'context':key,'name':entry['name'],'utility':u})
   self.call('sleep_publish',{'model':model,'catalog':[entry],'boundary':i})
   route=self.call('sleep_route',s);self.assertEqual(route['selected'] is not None,i==1)
  model=self.call('sleep_update',{'model':model,'context':key,'name':entry['name'],'utility':-2000})
  self.call('sleep_publish',{'model':model,'catalog':[entry],'boundary':2})
  self.assertIsNone(self.call('sleep_route',s)['selected'])
  self.assertEqual(len(self.store.map('knowledge.economics')['catalog']),2)
 def test_future_experience_rejected_and_pair_quota(self):
  with self.assertRaises(AssertionError):consolidate(None,None,None,[{'task':{'id':21}}],20)
  self.setup_methods();catalog=self.store.map('knowledge.economics')['catalog']
  pairs=self.call('sleep_pairs',{'experiences':[{'task':i,'context':'ctx'} for i in range(20)],'catalog':catalog,'model':[]})
  self.assertLessEqual(len(pairs),6);self.assertTrue(all(14<=p['task']<=19 for p in pairs))
 def test_end_to_end_sleep_charges_replay_and_preserves_methods(self):
  from test_prioritized_search import PriorityTests
  from experiments.sleep_memory import wake_trial
  from experiments.utility_router import trial
  PriorityTests.teach_set(self,'set_a','a');PriorityTests.teach_set(self,'set_b','b')
  self.retain('allocated_0','set_a',{'a':1,'b':0})
  examples=[{'input':{'a':0,'b':0},'expected':{'a':1,'b':0}}]
  completed=[]
  with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):
   for i in [1,2]:
    task={'id':i,'family':'opaque_fixture','request':{'examples':examples,'predicate':'unused','projector':'unused'},'validation':examples,'audit':examples}
    row=wake_trial(self.store,self.lib,self.hub,task)
    baseline=trial(self.store,self.lib,self.hub,task,'no_memory',{'weights':[0]*6,'updates':0})
    completed.append({'task':task,'row':row,'baseline':baseline})
   catalog=copy.deepcopy(self.store.map('knowledge.economics')['catalog'])
   result=consolidate(self.store,self.lib,self.hub,completed,2)
  self.assertEqual(len(result['results']),2);self.assertGreater(result['costs']['replay'],0)
  self.assertEqual(result['graph_steps'],sum(result['costs'].values()))
  self.assertLessEqual(result['graph_steps'],6000000)
  self.assertEqual(catalog,self.store.map('knowledge.economics')['catalog'])
  self.assertEqual(result['after']['boundary'],2)
 def test_metadata_dedup_does_not_touch_catalog(self):
  self.setup_methods();before=copy.deepcopy(self.store.map('knowledge.economics')['catalog'])
  dedup=self.call('sleep_dedup',before+[dict(before[0],name='alias')]);self.assertEqual(dedup,before)
  self.assertEqual(before,self.store.map('knowledge.economics')['catalog'])

if __name__=='__main__':unittest.main()
