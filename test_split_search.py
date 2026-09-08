import tempfile,unittest
from pathlib import Path
from experiments.split_search import prepare,split_search
from experiments.adaptive_reuse import graph
from test_prioritized_search import PriorityTests

class SplitSearchTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','no_memory')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 def test_graph_caps_and_weighted_selection(self):
  for p in [25,50,75]:
   caps=self.call('split_caps',{'remaining':10000,'percent':p,'distinct':True})
   self.assertEqual(caps,{'discovery':100*p,'reuse':100*(100-p)})
   self.assertEqual(self.call('split_caps',{'remaining':10000,'percent':p,'distinct':False}),{'discovery':10000,'reuse':0})
  args={'discovery_active':True,'reuse_active':True,'discovery_cap':2500,'reuse_cap':7500,'discovery_spent':1000,'reuse_spent':1000}
  self.assertEqual(self.call('split_choose',args),'reuse')
  self.assertEqual(self.call('split_choose',{**args,'reuse_active':False}),'discovery')
 def test_identical_frontiers_collapse_at_every_ratio(self):
  PriorityTests.teach_set(self,'set_a','a')
  request={'examples':[{'input':{'a':0},'expected':{'a':1}}],'predicate':'unused','projector':'unused'}
  outcomes=[split_search(self.lib,self.hub,request,30000,['set_a'],p) for p in [25,50,75]]
  for r in outcomes:
   self.assertFalse(r['distinct_lanes']);self.assertEqual(r['found'],['set_a']);self.assertEqual(r['lane_spent']['reuse'],0)
  self.assertEqual(len({r['graph_steps'] for r in outcomes}),1)
 def test_distinct_lane_budgets_and_total_charge(self):
  PriorityTests.teach_set(self,'set_a','a')
  retained=self.call('manager_retain',{'ops':['set_a','set_a'],'name':'fixture_macro','base':['set_a'],'validation':[{'input':{'a':0},'expected':{'a':1}}],'predicate':'unused','projector':'unused'})
  self.assertTrue(retained['retained'])
  request={'examples':[{'input':{'a':0},'expected':{'a':2}}],'predicate':'unused','projector':'unused'}
  for p in [25,50,75]:
   r=split_search(self.lib,self.hub,request,12000,['set_a'],p)
   self.assertTrue(r['distinct_lanes']);self.assertLessEqual(r['graph_steps'],12000)
   self.assertEqual(r['graph_steps'],sum(r['costs'].values()))
   for lane in ['discovery','reuse']:
    self.assertLessEqual(r['lane_spent'][lane],r['lane_caps'][lane])
    self.assertEqual(r['lane_spent'][lane],sum(e['charged'] for e in r['lane_events'] if e['lane']==lane))
   self.assertTrue(all('fixture_macro' not in z['ops'] for z in r['diagnostics'] if z['lane']=='discovery'))
  limited=split_search(self.lib,self.hub,request,50,['set_a'],25)
  self.assertEqual(limited['graph_steps'],50)

if __name__=='__main__':unittest.main()
