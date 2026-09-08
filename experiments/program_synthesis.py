"""Run a bounded graph-learning experiment. Hidden tests stay outside the learner.

Python supplies fixtures and independently checks outputs; graph procedures generate,
evaluate, select, materialize and save the solution. No language model is invoked.
"""
import argparse
import json
import random
import sys
import time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import foundation
from graph_store import GraphStore
from sensors import SensorHub
from workspace_surface import WorkspaceSurface

TRAINING={'predicate':'synth_positive','projector':'synth_identity','examples':[
 {'input':[-2,3,4],'expected':7},{'input':[-7],'expected':0},
 {'input':[],'expected':0},{'input':[0,5,-3,2],'expected':7}]}
TRANSFER={'predicate':'synth_available','projector':'synth_price','examples':[
 {'input':[{'available':True,'price':5},{'available':False,'price':12}],'expected':5},
 {'input':[{'available':True,'price':-2},{'available':True,'price':6}],'expected':4},
 {'input':[],'expected':0}]}

def setup(path):
 store=GraphStore(path)
 library=store.map('knowledge.procedures')
 library.update(foundation.curriculum())
 library.update(json.loads((ROOT/'curriculum/program-synthesis.json').read_text()))
 hub=SensorHub(store);hub.register_surface('workspace',WorkspaceSurface(store))
 return store,library,hub

def run(path):
 store,library,hub=setup(path);start=time.perf_counter()
 name='learned_synth_positive_total'
 learned,trace=foundation.run(library,'synth_learn_and_store',{'name':name,'request':TRAINING},sensors=hub)
 search_seconds=time.perf_counter()-start
 ops=learned['result']['found']
 assert ops is not None
 # This data is generated after learning and never passed to search/evaluation.
 rng=random.Random(913570)
 excluded={json.dumps(case['input'],sort_keys=True) for case in TRAINING['examples']}
 hidden=[]
 while len(hidden)<100:
  xs=[rng.randint(-30,30) for _ in range(rng.randint(0,20))]
  key=json.dumps(xs,sort_keys=True)
  if key not in excluded:excluded.add(key);hidden.append(xs)
 failures=[]
 for xs in hidden:
  actual,_=foundation.run(library,name,{'items':xs,'predicate':'synth_positive','projector':'synth_identity'})
  expected=sum(x for x in xs if x>0)
  if actual!=expected:failures.append({'input':xs,'actual':actual,'expected':expected})
 transfer_check,_=foundation.run(library,'synth_evaluate_candidate',{'ops':ops,**TRANSFER})
 fresh,_=foundation.run(library,'synth_search',TRANSFER)
 excluded={json.dumps(case['input'],sort_keys=True) for case in TRANSFER['examples']}
 products=[]
 while len(products)<100:
  items=[{'available':bool(rng.randrange(2)),'price':rng.randint(-15,40)} for _ in range(rng.randint(0,16))]
  key=json.dumps(items,sort_keys=True)
  if key not in excluded:excluded.add(key);products.append(items)
 transfer_failures=[]
 for items in products:
  actual,_=foundation.run(library,name,{'items':items,'predicate':'synth_available','projector':'synth_price'})
  expected=sum(x['price'] for x in items if x['available'])
  if actual!=expected:transfer_failures.append({'input':items,'actual':actual,'expected':expected})
 # The saved executable is reused unchanged; adapters were supplied by us.
 report={'name':name,'database':str(Path(path).resolve()),'model_calls':0,
  'search_seconds':search_seconds,'searched_operations':ops,
  'candidates_evaluated':learned['result']['candidates_evaluated'],
  'training_cases':len(TRAINING['examples']),'hidden_cases':len(hidden),'hidden_failures':failures,
  'transfer_training_accepted':transfer_check['accepted'],
  'reuse_candidates_evaluated':1,'fresh_transfer_candidates_evaluated':fresh['candidates_evaluated'],
  'transfer_hidden_cases':len(products),'transfer_hidden_failures':transfer_failures,
  'learner_received_hidden_cases':False,'hidden_inputs_unique_and_disjoint_from_training':True,'learned_graph':library[name]['graph'],
  'limits':['Finite search over four supplied operations up to depth three.',
            'Predicates, projection adapters, search algorithm and arithmetic were supplied.',
            'Transfer is parameterized reuse with supplied adapters, not autonomous concept discovery.',
            'Candidate counts measure this search ordering; they are not a general efficiency claim.',
            'Held-out cases support only the tested data domain, not general intelligence.']}
 store.map('knowledge.synthesis_experiments')[name]=report
 store.close()
 if failures or transfer_failures or not transfer_check['accepted']:raise AssertionError(report)
 return report

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--database',required=True);parser.add_argument('--report',required=True);args=parser.parse_args()
 result=run(args.database);Path(args.report).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='learned_graph'},indent=2))
