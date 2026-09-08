import copy,tempfile,unittest
from pathlib import Path
from experiments.utility_router import prepare,Meter,search,trial,clone
from test_activation_search import ActivationTests as Fixtures

class RouterTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,n,a):return Meter(self.store,self.lib,self.hub,1000000).call(n,a,'test')
 retain=Fixtures.retain
 setup_methods=Fixtures.setup_methods
 def test_update_learns_opposite_context_outcomes(self):
  model=self.call('router_zero',None);good=[1000,1000,1000,400,125,0];bad=[1000,0,500,400,125,0]
  for _ in range(8):
   model=self.call('router_update',{'model':model,'x':bad,'utility':-2000})
   model=self.call('router_update',{'model':model,'x':good,'utility':500})
  scores=[self.call('router_score',{'model':model,'x':x}) for x in [bad,good]]
  self.assertLess(scores[0],0);self.assertGreater(scores[1],100)
  self.assertEqual(model['updates'],16)
 def test_uncertainty_and_exploration_quota(self):
  decisions=[self.call('router_decide',{'score':0,'updates':10,'ordinal':i,'explore':True}) for i in range(1,61)]
  self.assertEqual([i+1 for i,d in enumerate(decisions) if d['activate']],[20,40,60])
  self.assertFalse(self.call('router_decide',{'score':-101,'updates':10,'ordinal':20,'explore':True})['activate'])
 def test_utility_cost_and_negative_transfer(self):
  for success,base,actualcost,basecost,sign in [(False,True,100,200,-1),(True,False,400,200,1),(True,True,100,200,1),(True,True,300,200,-1)]:
   u=self.call('router_utility',{'actual':{'success':success,'cost':actualcost},'baseline':{'success':base,'cost':basecost}})
   self.assertGreater(u*sign,0)
 def test_rejection_preserves_trace_and_catalog(self):
  q=self.setup_methods();q['base']=['set_a','set_b']
  # Use generic fair state manually because experiment binds its supplied vocabulary.
  state=self.call('shortcut_init',q);before=copy.deepcopy(self.store.map('knowledge.economics')['catalog'])
  e=before[0];probe=self.call('shortcut_probe',{'state':state,'entry':e});x=self.call('router_features',{'state':state,'entry':e,'probe':probe})
  score=self.call('router_score',{'x':x,'model':{'weights':[-4000,0,0,0,0,0],'updates':10}})
  self.assertFalse(self.call('router_decide',{'score':score,'updates':10,'ordinal':1,'explore':True})['activate'])
  self.assertEqual(before,self.store.map('knowledge.economics')['catalog'])
  self.assertEqual(x,self.call('router_features',{'state':state,'entry':{**e,'name':'arbitrary_rename','ops':['renamed','renamed']},'probe':probe}))
 def test_rejected_positive_probes_match_residual_primitive_search(self):
  from unittest.mock import patch
  q=self.setup_methods();q['examples']=[{'input':{'a':0,'b':0},'expected':{'a':1,'b':1}}]
  model={'weights':[-4000,0,0,0,0,0],'updates':10}
  before=copy.deepcopy(self.store.map('knowledge.economics')['catalog'])
  with patch.dict('experiments.utility_router.VOCABULARIES',{'planning':['set_a','set_b']}):
   m=Meter(self.store,self.lib,self.hub);r=search(m,q,'router',model,0)
   self.assertTrue(all(p['probe']['eligible'] and not p['activated'] for p in r['records']))
   overhead=sum(v for k,v in m.costs.items() if k not in ['initialization','search'])
   b=Meter(self.store,self.lib,self.hub);base=search(b,q,'no_memory',model,0,cap=350000-overhead)
   self.assertEqual(r['trace'],base['trace']);self.assertEqual(m.spent,b.spent+overhead)
  self.assertEqual(before,self.store.map('knowledge.economics')['catalog'])
 def test_inclusive_budget_and_frozen_inference(self):
  from experiments.transfer_tasks import stream
  task=stream('planning',912341)[0];model={'weights':[-4000,0,0,0,0,0],'updates':10};before=copy.deepcopy(model)
  row=trial(self.store,self.lib,self.hub,task,'router',model)
  self.assertLessEqual(row['graph_steps'],450000);self.assertEqual(sum(row['costs'].values()),row['graph_steps']);self.assertEqual(model,before)
  self.assertIn('validation',row['costs']);self.assertIn('router_persistence',row['costs'])

if __name__=='__main__':unittest.main()
