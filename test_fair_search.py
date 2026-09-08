import json,tempfile,unittest
from pathlib import Path
from experiments.fair_search import prepare,fair_search,orders,SEEDS
from experiments.adaptive_reuse import graph
from test_prioritized_search import PriorityTests

class FairSearchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','no_memory')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 def test_quota_fairness_under_permutations_and_near_ties(self):
  for names in [('a','b','c'),('c','a','b'),('b','c','a')]:
   queue=[{'ops':[name],'priority':i*2,'next_i':0} for i,name in enumerate(names)]
   served={name:0 for name in names}
   for _ in range(12):
    result=self.call('fair_choose',queue);chosen=result['parent'];name=chosen['ops'][0];served[name]+=1
    chosen={**chosen,'next_i':chosen['next_i']+1};queue=result['queue']+[chosen]
    self.assertLessEqual(max(served.values())-min(served.values()),1)
   self.assertEqual(set(served.values()),{4})
  result=self.call('fair_choose',[{'ops':['good'],'priority':-100,'next_i':3},{'ops':['bad'],'priority':0,'next_i':0}])
  self.assertEqual(result['parent']['ops'],['good'])
 def test_one_child_then_other_parent_and_generic_search(self):
  PriorityTests.teach_set(self,'set_a','a');PriorityTests.teach_set(self,'set_b','b')
  request={'examples':[{'input':{'a':0,'b':0},'expected':{'a':1,'b':1}}],'predicate':'unused','projector':'unused'}
  state=self.call('fair_init',{**request,'base':['set_a','set_b']})
  state.update(parent={'ops':['set_a'],'priority':-499},next_i=0,queue=[{'ops':['set_b'],'priority':-499,'next_i':0}])
  result=self.call('fair_step',state)
  self.assertEqual(result['parent']['ops'],['set_b'])
  self.assertTrue(any(x['ops']==['set_a'] and x['next_i']==1 for x in result['queue']))
  found=fair_search(self.lib,self.hub,request,450000,['set_a','set_b']);self.assertEqual(found['status'],'found')
  limited=fair_search(self.lib,self.hub,request,50,['set_a','set_b']);self.assertEqual(limited['graph_steps'],50)
 def test_frozen_rules_and_fresh_order_only(self):
  for file in ['managed-memory','transfer-manager-disabled','prioritized-search']:
   expected=json.loads(Path('curriculum',file+'.json').read_text())
   # The two disabled graph overrides remain the expected manager definitions.
   if file=='managed-memory':expected.update(json.loads(Path('curriculum/transfer-manager-disabled.json').read_text()))
   for name,definition in expected.items():self.assertEqual(self.lib[name]['graph'],definition['graph'])
  parent=json.loads(Path('experiments/prioritized-search-results/manifest.json').read_text())
  streams,banks=orders(parent);self.assertEqual((streams,banks),orders(parent));self.assertEqual(len(streams),6)
  seen=set()
  for seed in SEEDS:
   tasks=streams[str(seed)];order=tuple(t['source_task_id'] for t in tasks)
   self.assertNotIn((banks[str(seed)],order),seen);seen.add((banks[str(seed)],order))
   self.assertEqual(sorted(order),list(range(30)))
   for t in tasks:
    original=parent['streams']['planning'][str(t['source_bank'])][t['source_task_id']]
    self.assertEqual({**{k:v for k,v in t.items() if k not in ['source_bank','source_task_id']},'id':t['source_task_id']},original)

if __name__=='__main__':unittest.main()
