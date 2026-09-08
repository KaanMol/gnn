import json,tempfile,unittest
from pathlib import Path
import foundation
from experiments.program_synthesis import setup,TRAINING
from experiments.reuse_benchmark import BASE,MACRO_A,MACRO_B,search,promote,TRAIN_B

ROOT=Path(__file__).resolve().parent

class AdaptiveReuseTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.store,self.lib,self.hub=setup(Path(self.tmp.name)/'db.sqlite3')
  for name in ['reuse-benchmark','adaptive-reuse']:self.lib.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
 def tearDown(self):self.store.close();self.tmp.cleanup()
 def run_graph(self,name,arg):return foundation.run(self.lib,name,arg,sensors=self.hub)[0]
 def test_evidence_rejects_harm_and_accepts_measured_benefit(self):
  record={'name':'candidate','trials':0,'utility':0,'evidence':[]}
  record=self.run_graph('adaptive_record',{'record':record,'budget':1000,'baseline':{'success':True,'graph_steps':100},'trial':{'success':False,'graph_steps':1000}})
  self.assertEqual(record['utility'],-1000)
  prepared=self.run_graph('adaptive_prepare',{'base':BASE,'evidence':[record],'extend':True})
  self.assertEqual(prepared,{'vocabulary':BASE,'selected':[],'prelude':[]})
  record=self.run_graph('adaptive_record',{'record':record,'budget':2000,'baseline':{'success':False,'graph_steps':2000},'trial':{'success':True,'graph_steps':100}})
  self.assertEqual(record['utility'],900)
  saved=self.run_graph('adaptive_save_evidence',[record])
  self.assertTrue(saved['accepted'])
  self.assertEqual(self.store.map('knowledge.reuse_evidence')['calibration'],[record])
  prepared=self.run_graph('adaptive_prepare',{'base':BASE,'evidence':[record],'extend':True})
  self.assertEqual(prepared['prelude'],[['candidate']]+[['candidate',op] for op in BASE])
 def test_prefix_reuses_nested_learned_graph_and_charges_budget(self):
  vocab=BASE
  for name,request in [(MACRO_A,TRAINING),(MACRO_B,TRAIN_B)]:
   learned=search(self.lib,self.hub,request,vocab,5000000)
   vocab,_=promote(self.lib,self.hub,name,learned['found'],vocab)
  prepared=self.run_graph('adaptive_prepare',{'base':BASE,'evidence':[{'name':MACRO_B,'trials':1,'utility':1}],'extend':True})
  request={**TRAIN_B,'examples':[{'input':[-3,2,5],'expected':-14},{'input':[-2],'expected':0},{'input':[1,4],'expected':-10}], 'prelude':prepared['prelude'],'prefix_i':0}
  result=search(self.lib,self.hub,request,prepared['vocabulary'],450000,'adaptive_search_step')
  self.assertEqual(result['found'],[MACRO_B,'bench_negate'])
  self.assertGreater(result['graph_steps'],10000)
  result=search(self.lib,self.hub,request,prepared['vocabulary'],100,'adaptive_search_step')
  self.assertEqual(result['status'],'step_budget');self.assertEqual(result['graph_steps'],100)

if __name__=='__main__':unittest.main()
