import tempfile
import unittest
from pathlib import Path
import foundation
from graph_store import GraphStore
from experiments.program_synthesis import setup,TRAINING

class ProgramSynthesisTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'memory.sqlite3'
  self.store,self.lib,self.hub=setup(self.path)
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def run_graph(self,name,arg):return foundation.run(self.lib,name,arg,sensors=self.hub)[0]
 def test_generates_compositions_and_changes_solution_with_examples(self):
  candidates=self.run_graph('synth_generate_candidates',None)
  self.assertEqual(len(candidates),84)
  request={**TRAINING,'examples':[{'input':[-1,2,8],'expected':2},{'input':[-2],'expected':0},{'input':[],'expected':0}]}
  result=self.run_graph('synth_search',request)
  self.assertEqual(result['found'],['synth_select','synth_count'])
 def test_contradictory_examples_do_not_learn(self):
  request={**TRAINING,'examples':[{'input':[1],'expected':1},{'input':[1],'expected':2}]}
  result=self.run_graph('synth_search',request)
  self.assertIsNone(result['found']);self.assertEqual(result['candidates_evaluated'],84)
  with self.assertRaisesRegex(ValueError,'No candidate'):
   self.run_graph('synth_learn_and_store',{'name':'bad_learning','request':request})
  self.assertNotIn('bad_learning',self.lib)
 def test_empty_examples_and_unsafe_adapters_reject(self):
  with self.assertRaisesRegex(ValueError,'1–12'):self.run_graph('synth_search',{**TRAINING,'examples':[]})
  with self.assertRaisesRegex(ValueError,'taught adapters'):
   self.run_graph('synth_init',{'items':[],'predicate':'synth_learn_and_store','projector':'synth_price'})
 def test_persistence_and_no_overwrite(self):
  request={'name':'learned_demo','request':TRAINING}
  self.run_graph('synth_learn_and_store',request);original=self.lib['learned_demo']
  with self.assertRaisesRegex(ValueError,'already exists'):self.run_graph('synth_learn_and_store',request)
  self.assertEqual(self.lib['learned_demo'],original)
  reopened=GraphStore(self.path)
  try:
   self.assertEqual(foundation.run(reopened.map('knowledge.procedures'),'learned_demo',{'items':[-9,4,6],'predicate':'synth_positive','projector':'synth_identity'})[0],10)
  finally:reopened.close()

if __name__=='__main__':unittest.main()
