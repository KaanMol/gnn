"""Generic callable reuse, isolated from the completed whole-program study."""
import argparse,copy,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.transfer_test import prepare as original_prepare
from experiments.transfer_tasks import VOCABULARIES
ARMS=['no_memory','whole_program','compositional']
SEEDS=[7109,8111]
BUDGET=450000
SEARCH_BUDGET=BUDGET

def prepare(database,arm):
 store,lib,hub,cost=original_prepare(database,'rules_disabled')
 lib.update(json.loads((ROOT/'curriculum/compositional-transfer.json').read_text()))
 return store,lib,hub,cost

def generic_search(lib,hub,request,budget,vocabulary,compose=False):
 state={**copy.deepcopy(request),'vocabulary':vocabulary,'catalog':[],'rank':0,'depth':1,'max_depth':5,'found':None,'done':False,'evaluated':0}
 cache=ExecutionCache();costs=defaultdict(int);log=[];selected=[];mixed_attempts=0;overlength=0;status='step_budget';cpu=time.process_time();wall=time.perf_counter()
 def step(name,arg,limit,category):
  meter={}
  try:return execute_graph(lib[name]['graph'],arg,lib,limit=limit,sensors=hub,execution_cache=cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   return None
  finally:costs[category]+=meter['logical_steps']
 def remaining():return budget-sum(costs.values())
 # Finish the original one-instruction layer first. These exact same candidates
 # and evaluations are charged to the original baseline, too.
 while state['depth']==1 and not state['done'] and remaining()>0:
  result=step('composition_search_step',state,remaining(),'search')
  if result is None:break
  state=result;log+=result['last_log']
  overlength+=not result['last_evaluation']['allowed']
  mixed_attempts+=bool(result['last_evaluation']['allowed'] and len(result['last'])>1 and any(op not in vocabulary for op in result['last']))
 if not state['done'] and state['depth']>1 and remaining()>0:
  prepared=step('composition_prepare',{'base':vocabulary,'compose':compose},remaining(),'retrieval')
  if prepared is not None:
   state['catalog']=prepared['catalog'];state['vocabulary']=prepared['vocabulary']
   selected=prepared['selected'];probe_budget=min(SEARCH_BUDGET//4,remaining())
   probe_state={**request,'prelude':prepared['prelude'],'prefix_i':0,'found':None,'done':False,'evaluated':0,'log':[]}
   start=sum(costs.values())
   while probe_state['prefix_i']<len(prepared['prelude']) and not probe_state['done'] and probe_budget>sum(costs.values())-start:
    result=step('manager_probe_step',probe_state,min(remaining(),probe_budget-(sum(costs.values())-start)),'probing')
    if result is None:break
    probe_state=result;log=result['log']
   if probe_state['found'] is not None:state['found']=probe_state['found'];state['done']=True
   state['evaluated']+=probe_state['evaluated']
 # Enumerate the chosen alphabet at depth two onward. All arms use the same
 # expanded-length guard; only compositional mode includes learned callables.
 while not state['done'] and remaining()>0:
  if time.process_time()-cpu>=10:status='cpu_budget';break
  result=step('composition_search_step',state,remaining(),'search')
  if result is None:break
  state=result;log+=result['last_log']
  overlength+=not result['last_evaluation']['allowed']
  mixed_attempts+=bool(result['last_evaluation']['allowed'] and len(result['last'])>1 and any(op not in vocabulary for op in result['last']))
 if state['found'] is not None:status='found'
 elif state['done']:status='exhausted_space'
 return {'status':status,'found':state['found'],'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'selected':selected,'mixed_candidates_evaluated':mixed_attempts,'overlength_rejections':overlength,'search_depth':state['depth'],'candidates_evaluated':state['evaluated'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(store,lib,hub,task,arm):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=lambda lib,hub,request,budget: generic_search(lib,hub,request,budget,vocabulary,arm=='compositional')
 for attempt in range(2):
  if remaining<=0:break
  result=runner(lib,hub,request,remaining)
  attempts.append(result);logs+=result['log'];found=result['found'];remaining-=result['graph_steps']
  for k,v in result['costs'].items():costs[k]+=v
  validation,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['validation'],'predicate':'unused','projector':'unused'});costs['validation']+=cost['graph_steps']
  if found is None or validation['accepted']:break
  rejections+=1
  if attempt==0 and remaining>0:
   request['examples'],cost=graph(lib,hub,'economy_refine',{'examples':request['examples'],'validation':task['validation']});costs['feedback']+=cost['graph_steps'];remaining-=cost['graph_steps']
 retained={'retained':False}
 if arm in ['whole_program','compositional']:
  _,cost=graph(lib,hub,'manager_update',{'log':logs,'found':found,'validated':validation['accepted']});costs['utility']+=cost['graph_steps']
  if validation['accepted']:
   retained,cost=graph(lib,hub,'manager_retain',{'ops':found,'name':'composed_'+str(task['id']),'base':vocabulary,'validation':task['validation'],'predicate':'unused','projector':'unused'});costs['retention']+=cost['graph_steps']
 audit={'accepted':False}
 if validation['accepted']:
  audit,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['audit'],'predicate':'unused','projector':'unused'});costs['audit']+=cost['graph_steps']
 catalog=store.map('knowledge.economics')['catalog']
 if arm in ['no_memory']:assert not catalog
 dbbytes=store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]
 return {'task':task['id'],'domain':task['domain'],'family':task['family'],'expected_boundary':task['expected_boundary'],'arm':arm,'found':found,'success':bool(validation['accepted'] and audit['accepted']),'composed_solution':bool(found and len(found)>1 and any(op not in vocabulary for op in found)),'validation_rejections':rejections,'audit_false_positive':bool(validation['accepted'] and not audit['accepted']),'retained':retained['retained'],'catalog':catalog,'library_size':len(catalog),'attempts':attempts,'costs':dict(costs),'total_graph_steps':sum(costs.values()),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':dbbytes,'sqlite_row_changes':store.connection.total_changes-changes}

def freeze(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 if (directory/'manifest.json').exists():raise ValueError('Frozen output directory already exists.')
 previous=ROOT/'experiments/transfer-results/manifest.json'
 old=json.loads(previous.read_text())
 paths=list(old['source_hashes'])+['experiments/compositional_transfer.py','curriculum/compositional-transfer.json','experiments/reuse_benchmark.py','experiments/adaptive_reuse.py','curriculum/reuse-benchmark.json','curriculum/learning-economics.json','graph-authoring/compositional-transfer.mjs']
 manifest={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'streams':old['streams'],'parent_manifest_sha256':hashlib.sha256(previous.read_bytes()).hexdigest(),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'policy':'Same base singleton layer and whole-method probes in all arms. Then breadth-first rank enumeration over the chosen alphabet. Compositional mode prepends up to four active recent learned callables to originals; whole-program mode searches originals only. Exact expanded sequence length <=5, full nested execution costs, no environment continuation templates. Every attempted callable receives utility accounting. Retained definitions are flattened after canonical validation.','limitations':['Same previously evaluated tasks: this is a controlled architectural follow-up, not held-out confirmatory evidence.','Text/tree may not acquire multi-operation methods within this budget, preventing an informative reuse test.','Shared fixed-sequence Data-to-Data interface and supplied environment primitives.','Generic callable composition is newly supplied search machinery, not invented by the learner.','Expanded length checks and management are charged. CPU/wall and storage reported separately.','No seeded methods in the benchmark; test fixtures are isolated.','Two seeds per environment; no post-run rescue.']}
 data=json.dumps(manifest,sort_keys=True).encode();(directory/'manifest.json').write_bytes(data);(directory/'manifest.sha256').write_text(hashlib.sha256(data).hexdigest()+'\n')

def run(directory):
 directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());digest=hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()
 if (directory/'trials.jsonl').exists():raise ValueError('Refusing to overwrite an existing run.')
 rows=[];setups=[]
 with (directory/'trials.jsonl').open('w') as out:
  for domain in manifest['streams']:
   for seed in SEEDS:
    engines={}
    try:
     for arm in ARMS:
      cpu=time.process_time();wall=time.perf_counter();store,lib,hub,cost=prepare(directory/f'{domain}-{seed}-{arm}.sqlite3',arm);engines[arm]=(store,lib,hub)
      setups.append({'domain':domain,'seed':seed,'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]})
     for task in manifest['streams'][domain][str(seed)]:
      offset=(task['id']+seed)%len(ARMS);order=ARMS[offset:]+ARMS[:offset]
      for arm in order:
       store,lib,hub=engines[arm];row=trial(store,lib,hub,task,arm)|{'seed':seed};rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
      if (task['id']+1)%10==0:print(domain,seed,task['id']+1,'/30',{a:sum(r['success'] for r in rows if r['domain']==domain and r['seed']==seed and r['arm']==a) for a in ARMS},flush=True)
    finally:
     for store,_,_ in engines.values():store.close()
 assert hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()==digest
 for p,h in manifest['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 (directory/'report.json').write_text(json.dumps({'manifest_sha256':digest,'trials':rows,'setup':setups},indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
 if a.freeze:freeze(a.output);print('Generic composition experiment frozen.')
 else:run(a.output)
