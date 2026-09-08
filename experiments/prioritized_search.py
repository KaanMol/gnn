"""Planning-only controlled best-first allocation experiment."""
import argparse,copy,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.compositional_transfer import prepare as previous_prepare
from experiments.transfer_tasks import VOCABULARIES
ARMS=['no_memory','managed_memory']
SEEDS=[7109,8111]
BUDGET=450000

def prepare(database,arm):
 store,lib,hub,cost=previous_prepare(database,'compositional')
 lib.update(json.loads((ROOT/'curriculum/prioritized-search.json').read_text()))
 return store,lib,hub,cost

def prioritized_search(lib,hub,request,budget,vocabulary):
 cache=ExecutionCache();costs=defaultdict(int);log=[];diagnostics=[]
 cpu=time.process_time();wall=time.perf_counter();status='step_budget'
 def step(name,arg,category):
  meter={}
  try:return execute_graph(lib[name]['graph'],arg,lib,limit=budget-sum(costs.values()),sensors=hub,execution_cache=cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   return None
  finally:costs[category]+=meter.get('logical_steps',0)
 state=step('priority_init',{**request,'base':vocabulary},'initialization')
 if state is None:state={'done':False,'found':None,'selected':[],'evaluated':0}
 else:
  while not state['done'] and sum(costs.values())<budget:
   if time.process_time()-cpu>=10:status='cpu_budget';break
   result=step('priority_step',state,'allocation_and_execution')
   if result is None:break
   state=result;log+=result['last_log']
   diagnostics.append({'ops':result['last'],'expanded':result['last_expanded'],'allowed':result['last_allowed'],'duplicate':result['last_duplicate'],'progress':result['last_evaluation']['progress'],'matches':result['last_evaluation']['matches'],'executable':result['last_evaluation']['executable'],'queue_size':len(result['queue'])})
 if state['found'] is not None:status='found'
 elif state['done']:status='exhausted_space'
 return {'status':status,'found':state['found'],'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'selected':state['selected'],'candidates_evaluated':state['evaluated'],'mixed_candidates_evaluated':sum(x['allowed'] and len(x['ops'])>1 and any(op not in vocabulary for op in x['ops']) for x in diagnostics),'max_call_depth':max((len(x['ops']) for x in diagnostics if x['allowed']),default=0),'diagnostics':diagnostics,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(store,lib,hub,task,arm):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=lambda lib,hub,request,budget: prioritized_search(lib,hub,request,budget,vocabulary)
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
 if arm in ['managed_memory']:
  _,cost=graph(lib,hub,'manager_update',{'log':logs,'found':found,'validated':validation['accepted']});costs['utility']+=cost['graph_steps']
  if validation['accepted']:
   retained,cost=graph(lib,hub,'manager_retain',{'ops':found,'name':'allocated_'+str(task['id']),'base':vocabulary,'validation':task['validation'],'predicate':'unused','projector':'unused'});costs['retention']+=cost['graph_steps']
 audit={'accepted':False}
 if validation['accepted']:
  audit,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['audit'],'predicate':'unused','projector':'unused'});costs['audit']+=cost['graph_steps']
 catalog=store.map('knowledge.economics')['catalog']
 if arm in ['no_memory']:assert not catalog
 dbbytes=store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]
 return {'task':task['id'],'domain':task['domain'],'family':task['family'],'expected_boundary':task['expected_boundary'],'arm':arm,'found':found,'success':bool(validation['accepted'] and audit['accepted']),'composed_solution':bool(found and len(found)>1 and any(op not in vocabulary for op in found)),'validation_rejections':rejections,'audit_false_positive':bool(validation['accepted'] and not audit['accepted']),'retained':retained['retained'],'catalog':catalog,'library_size':len(catalog),'attempts':attempts,'costs':dict(costs),'total_graph_steps':sum(costs.values()),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':dbbytes,'sqlite_row_changes':store.connection.total_changes-changes}

def freeze(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 if (directory/'manifest.json').exists():raise ValueError('Frozen output already exists.')
 parent=ROOT/'experiments/compositional-transfer-results/manifest.json'
 old=json.loads(parent.read_text())
 # Preserve every previously frozen dependency, including all memory rules.
 for p,h in old['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 paths=list(old['source_hashes'])+['experiments/prioritized_search.py','curriculum/prioritized-search.json','graph-authoring/prioritized-search.mjs']
 manifest={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'streams':{'planning':old['streams']['planning']},'parent_manifest_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'policy':'Best-first queue capped at 100 partial programs. Complete all children of the selected parent, then choose lowest priority. Integer priority = expanded primitive length - 1000000 * full training-example matches - floor(1000 * sum of per-example fractions of changed target scalar leaves already matched). Scalar target leaves equal to input at the same path are excluded from heuristic only. Full output equality remains acceptance. Exact expanded-sequence dedup; failed executable prefixes pruned; successful prefixes below expanded length five queued. All callables use the same expansion rule. Up to four recent active methods selected by unchanged memory manager. No whole-program probe phase.','limitations':['Planning only, two previously evaluated streams: architectural diagnostic, not fresh confirmation or cross-domain transfer evidence.','Heuristic is newly supplied generic search machinery. No planning action or field names occur in allocator rules.','Partial scoring ignores unchanged target leaves and empty containers; full equality still validates solutions.','Priority is heuristic, not an admissible remaining-cost estimate. Beam truncation may discard useful candidates.','All scoring, canonicalization, queue and execution graph work is charged; host CPU, wall time and storage are separately reported.','Memory canonicalization, retention, routing and utility rules unchanged. No seeded learned methods.','No post-freeze tuning; text/tree untouched.']}
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
 if a.freeze:freeze(a.output);print('Planning allocator experiment frozen.')
 else:run(a.output)
