import json,tempfile,unittest
from pathlib import Path
from experiments.prioritized_search import prepare,prioritized_search
from experiments.adaptive_reuse import graph

class PriorityTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3','no_memory')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,name,arg):return graph(self.lib,self.hub,name,arg)[0]
 def test_generic_changed_leaf_features_and_renaming(self):
  a=self.call('priority_features',{'input':{'constant':8,'value':0,'sequence':[]},'expected':{'constant':8,'value':1,'sequence':['a','b']}})
  self.assertEqual(a['features'],[{'path':['value'],'value':1},{'path':['sequence',0],'value':'a'},{'path':['sequence',1],'value':'b'}])
  b=self.call('priority_features',{'input':{'q':8,'r':0,'s':[]},'expected':{'q':8,'r':1,'s':['a','b']}})
  self.assertEqual([x['value'] for x in a['features']],[x['value'] for x in b['features']])
  # Runtime interpretation remains generic; the allocator has no field strings.
  source=Path('graph-authoring/prioritized-search.mjs').read_text()
  self.assertNotIn('plan_',source);self.assertNotIn('carrying',source)
 def teach_set(self,name,key):
  self.lib[name]={'graph':{'input_type':'Data','output_type':'Data','nodes':[{'id':'i','op':'input','inputs':[],'type':'Data'},{'id':'k','op':'data_literal','inputs':[],'type':'Data','value':key},{'id':'v','op':'data_literal','inputs':[],'type':'Data','value':1},{'id':'r','op':'set_item','inputs':['i','k','v'],'type':'Data'}],'output':'r','trace_mode':'explicit'}}
 def test_generic_search_and_queue_selects_deeper_candidate(self):
  self.teach_set('set_a','a');self.teach_set('set_b','b')
  request={'examples':[{'input':{'a':0,'b':0},'expected':{'a':1,'b':1}}],'predicate':'unused','projector':'unused'}
  found=prioritized_search(self.lib,self.hub,request,450000,['set_a','set_b'])
  self.assertEqual(found['status'],'found');self.assertEqual(len(found['found']),2)
  state=self.call('priority_init',{**request,'base':['set_a']})
  state['queue']=[{'ops':['set_b','set_a','set_b'],'priority':-10000000},{'ops':['set_b'],'priority':-1}]
  step=self.call('priority_step',state)
  self.assertEqual(step['parent']['ops'],['set_b','set_a','set_b'])
 def test_expanded_limit_and_duplicate_guard(self):
  self.teach_set('set_a','a')
  request={'examples':[{'input':{'a':0},'expected':{'a':2}}],'predicate':'unused','projector':'unused'}
  state=self.call('priority_init',{**request,'base':['set_a']})
  state['parent']={'ops':['macro'],'priority':0};state['catalog']=[{'name':'macro','ops':['set_a']*5}]
  step=self.call('priority_step',state)
  self.assertFalse(step['last_allowed']);self.assertEqual(len(step['last_expanded']),6);self.assertEqual(step['evaluated'],0)
  state=self.call('priority_init',{**request,'base':['set_a']});state['seen']=[['set_a']]
  step=self.call('priority_step',state)
  self.assertTrue(step['last_duplicate']);self.assertFalse(step['last_allowed'])
  limited=prioritized_search(self.lib,self.hub,request,50,['set_a'])
  self.assertEqual(limited['graph_steps'],50);self.assertEqual(limited['status'],'step_budget')

if __name__=='__main__':unittest.main()
