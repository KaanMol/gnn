import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from experiments.trace_sleep import prepare,recorded_trial,partial_trial,trace_consolidate
from experiments.sleep_memory import wake_trial
from experiments.utility_router import Meter,clone
from test_prioritized_search import PriorityTests

class TraceTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub,_=prepare(Path(self.tmp.name)/'db.sqlite3')
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def call(self,n,a):return Meter(self.store,self.lib,self.hub,2000000).call(n,a,'test')
 def fixture(self):
  PriorityTests.teach_set(self,'set_a','a');PriorityTests.teach_set(self,'set_b','b')
  expected={'a':1,'b':0};examples=[{'input':{'a':0,'b':0},'expected':expected}]
  self.call('manager_retain',{'ops':['set_a','set_a'],'name':'allocated_0','base':['set_a','set_b'],'validation':examples,'predicate':'unused','projector':'unused'})
  return {'id':1,'family':'opaque','request':{'examples':examples,'predicate':'unused','projector':'unused'},'validation':examples,'audit':examples}
 def test_recording_keeps_policy_and_charges_only_storage(self):
  task=self.fixture();ss,ll,hh=clone(self.store)
  try:
   with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):
    baseline=wake_trial(ss,ll,hh,task);row=recorded_trial(self.store,self.lib,self.hub,task)
   self.assertEqual(row['attempts'],baseline['attempts'])
   extra=row['costs']['extra_wake_index']+row['costs']['extra_wake_recording']
   self.assertEqual(row['graph_steps'],baseline['graph_steps']+extra);self.assertGreater(extra,0)
   evidence=self.store.map('knowledge.sleep.experiences')['trace_1'];self.assertEqual(len(evidence['observations']),len(row['attempts'][0]['trace']))
  finally:ss.close()
 def test_positive_evidence_requires_actual_same_intervention(self):
  task=self.fixture();entry=self.store.map('knowledge.economics')['catalog'][0]
  with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):row=recorded_trial(self.store,self.lib,self.hub,task,forced=entry)
  p={'row':row,'entry':entry,'records':[]};self.assertTrue(self.call('trace_evidence',p)['factual'])
  changed=copy.deepcopy(entry);changed['ops']=['different'];self.assertFalse(self.call('trace_evidence',{**p,'entry':changed})['factual'])
  row=copy.deepcopy(row);row['attempts'][0]['selected']=None
  local={'expanded':entry['ops'],'evaluation':{'executable':True,'progress':100,'accepted':False}}
  r=self.call('trace_evidence',{'row':row,'entry':entry,'records':[local]});self.assertFalse(r['factual']);self.assertTrue(r['partial_supported'])
 def test_partial_cap_does_not_certify_failure(self):
  task=self.fixture();task['request']['examples']=[{'input':{'a':0,'b':0},'expected':{'a':9,'b':9}}]
  entry=self.store.map('knowledge.economics')['catalog'][0]
  with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):row=partial_trial(self.store,self.lib,self.hub,task,forced=entry)
  self.assertLessEqual(row['graph_steps'],75000);self.assertFalse(row['success']);self.assertTrue(row['exhaustions'])
 def test_completed_partial_matches_full_execution_exactly(self):
  task=self.fixture();entry=self.store.map('knowledge.economics')['catalog'][0];ss,ll,hh=clone(self.store)
  try:
   with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):
    a=partial_trial(self.store,self.lib,self.hub,task,forced=entry);b=recorded_trial(ss,ll,hh,task,forced=entry)
   self.assertTrue(a['success']);self.assertFalse(a['exhaustions']);self.assertEqual(a['costs'],b['costs']);self.assertEqual(a['attempts'],b['attempts'])
  finally:ss.close()
 def test_unknown_attempt_count_is_not_utility(self):
  model=[];s=self.call('trace_note_attempt',{'schedule':[],'context':'c','name':'m'});self.assertEqual(s,[{'context':'c','name':'m','count':1}]);self.assertEqual(model,[])
 def test_consolidation_keeps_unresolved_evidence_unknown(self):
  task=self.fixture();task['request']['examples']=[{'input':{'a':0,'b':0},'expected':{'a':9,'b':9}}]
  task['validation']=task['request']['examples'];task['audit']=task['request']['examples']
  with patch.dict('experiments.sleep_memory.VOCABULARIES',{'planning':['set_a','set_b']}):
   row=recorded_trial(self.store,self.lib,self.hub,task)
   evidence=copy.deepcopy(self.store.map('knowledge.sleep.experiences')['trace_1'])
   completed=[{'task':{**task,'id':i},'row':{**row,'task':i},'baseline':row,'evidence':evidence} for i in range(1,7)]
   result=trace_consolidate(self.store,self.lib,self.hub,completed,6)
  self.assertEqual(sum(x['source']=='full' for x in result['results']),1)
  self.assertTrue(any(x['source']=='UNKNOWN' for x in result['results']))
  self.assertTrue(all(x['utility'] is None for x in result['results'] if x['source']=='UNKNOWN'))
  self.assertEqual(sum(x['count'] for x in result['after']['model']),sum(x['source']!='UNKNOWN' for x in result['results']))
  self.assertEqual(result['graph_steps'],sum(result['costs'].values()))
 def test_future_prefix_rejected(self):
  with self.assertRaises(AssertionError):trace_consolidate(None,None,None,[{'task':{'id':21}}],20)

if __name__=='__main__':unittest.main()
