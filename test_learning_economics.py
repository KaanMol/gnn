import json,tempfile,unittest
from pathlib import Path
from experiments.program_synthesis import setup
from experiments.adaptive_reuse import graph
from experiments.reuse_benchmark import BASE
from experiments.learning_economics import make_stream,witness,FAMILIES,trial

ROOT=Path(__file__).resolve().parent

class LearningEconomicsTests(unittest.TestCase):
 def test_stream_is_frozen_diverse_and_split(self):
  stream=make_stream(1907)
  self.assertEqual(stream,make_stream(1907));self.assertEqual(len(stream),60)
  self.assertEqual({t['role'] for t in stream},{'novel','reuse_opportunity','irrelevant','misleading'})
  seen=set()
  for task in stream:
   for split in [task['request']['examples'],task['validation'],task['audit']]:
    for case in split:
     key=json.dumps([task['domain'],case['input']],sort_keys=True)
     self.assertNotIn(key,seen);seen.add(key)
   if task['role']=='misleading':
    self.assertTrue(all((all(x>0 for x in c['input']) if task['domain']=='numbers' else all(x['available' if task['domain']=='products' else 'enabled'] for x in c['input'])) for c in task['request']['examples']))
  self.assertTrue(all(len(witness(f))<=5 for f in FAMILIES))
 def test_graph_retention_gates_persistence_and_recency(self):
  with tempfile.TemporaryDirectory() as tmp:
   store,lib,hub=setup(Path(tmp)/'db.sqlite3')
   try:
    for name in ['reuse-benchmark','adaptive-reuse','learning-economics']:lib.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
    def run(name,arg):return graph(lib,hub,name,arg)[0]
    run('economy_init',None)
    request={'ops':['synth_select','synth_sum'],'retain':True,'validated':False,'name':'learned_first','vocabulary':BASE,'validation':{'accepted':False}}
    self.assertFalse(run('economy_retain',request)['retained']);self.assertNotIn('learned_first',lib)
    request.update(validated=True,retain=False)
    self.assertFalse(run('economy_retain',request)['retained'])
    request.update(retain=True,validation={'accepted':True})
    self.assertTrue(run('economy_retain',request)['retained'])
    request['name']='duplicate';self.assertFalse(run('economy_retain',request)['retained'])
    request.update(name='alias',ops=['learned_first']);self.assertFalse(run('economy_retain',request)['retained'])
    prepared=run('economy_prepare',{'base':BASE})
    self.assertEqual(prepared['selected'],['learned_first']);self.assertEqual(prepared['vocabulary'],BASE+['learned_first'])
    self.assertEqual(prepared['prelude'][-1],['learned_first','bench_negate'])
    validation=run('economy_validate',{'ops':['learned_first'],'examples':[{'input':[-3,2],'expected':-1}],'predicate':'synth_positive','projector':'synth_identity'})
    self.assertFalse(validation['accepted'])
    refined=run('economy_refine',{'examples':[{'input':[2],'expected':2}],'validation':[{'input':[-3,2],'expected':-1}]})
    self.assertEqual(len(refined),2)
    # A previously correct selection macro is misleading for a plain sum task
    # whose first examples contain only positive values. Feedback must recover.
    task={'id':42,'phase':1,'role':'misleading','family':'sum','domain':'numbers',
      'request':{'predicate':'synth_positive','projector':'synth_identity','examples':[{'input':[i],'expected':i} for i in range(1,7)]},
      'validation':[{'input':[-i,1],'expected':1-i} for i in range(1,9)],
      'audit':[{'input':[-10,3],'expected':-7}]}
    recovered=trial(lib,hub,store,task,True)
    self.assertEqual(recovered['validation_rejections'],1)
    self.assertTrue(recovered['success']);self.assertEqual(recovered['found'],['synth_sum'])
    self.assertGreater(recovered['costs']['feedback'],0)
   finally:store.close()

if __name__=='__main__':unittest.main()
