import json,tempfile,unittest
from pathlib import Path
from experiments.adaptive_reuse import graph
from experiments.transfer_test import prepare,bound_search
from experiments.transfer_tasks import stream,execute,TARGETS,VOCABULARIES
from experiments.managed_memory import managed_search

class TransferTests(unittest.TestCase):
 def test_primitive_oracle_and_order_preservation(self):
  with tempfile.TemporaryDirectory() as tmp:
   store,lib,hub,_=prepare(Path(tmp)/'db.sqlite3','rules_disabled')
   try:
    for domain in VOCABULARIES:
     for task in stream(domain,7109):
      if task['witness'] is None:continue
      for case in task['request']['examples'][:1]:
       actual,_=graph(lib,hub,'synth_execute_candidate',{'ops':task['witness'],'argument':{'items':case['input'],'predicate':'unused','projector':'unused'}})
       self.assertEqual(actual,case['expected'])
    c,_=graph(lib,hub,'manager_canonicalize',{'ops':['plan_east','plan_west'],'catalog':[]})
    self.assertEqual(c,{'valid':True,'ops':['plan_east','plan_west']})
    start={'x':0,'energy':6,'carrying':False,'gate':False,'log':[]}
    self.assertNotEqual(execute(c['ops'],start),start) # Round trip has effects.
    self.assertIs(bound_search(VOCABULARIES['tree']).__code__,managed_search.__code__)
   finally:store.close()
 def test_frozen_rejects_new_language_and_disabled_retains(self):
  with tempfile.TemporaryDirectory() as tmp:
   for arm in ['exact_frozen','rules_disabled']:
    store,lib,hub,_=prepare(Path(tmp)/(arm+'.sqlite3'),arm)
    try:
     ops=['text_split','text_clean','text_join']
     c,_=graph(lib,hub,'manager_canonicalize',{'ops':ops,'catalog':[]})
     self.assertEqual(c['valid'],arm=='rules_disabled')
     r,_=graph(lib,hub,'manager_retain',{'ops':ops,'name':'normalize','base':VOCABULARIES['text'],'validation':[{'input':' A  B ','expected':'A B'}],'predicate':'unused','projector':'unused'})
     self.assertEqual(r['retained'],arm=='rules_disabled')
     if arm=='rules_disabled':
      p,_=graph(lib,hub,'manager_prepare',{'base':VOCABULARIES['text']})
      self.assertEqual(p['prelude'],[['normalize']])
     self.assertFalse(any(n in lib for n in ['synth_sum','bench_double','bench_negate']))
    finally:store.close()
 def test_stream_split_and_planning_boundary(self):
  for domain in VOCABULARIES:
   tasks=stream(domain,8111);self.assertEqual(tasks,stream(domain,8111));seen=set()
   for t in tasks:
    for case in t['request']['examples']+t['validation']+t['audit']:
     key=json.dumps(case['input'],sort_keys=True);self.assertNotIn(key,seen);seen.add(key)
    if t['family']=='reach_goal':self.assertGreater(len({c['input']['x'] for c in t['request']['examples']}),1)

if __name__=='__main__':unittest.main()
