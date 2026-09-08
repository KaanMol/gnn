"""Stored versus active memory, isolated three-arm planning experiment."""
import argparse,copy,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.fair_search import prepare as previous_prepare
from experiments.transfer_tasks import VOCABULARIES
ARMS=['no_memory','all_active','top_k']
SEEDS=[15053,16057,17077,18089]
BUDGET=450000

def prepare(database,arm):
 store,lib,hub,cost=previous_prepare(database,arm)
 lib.update(json.loads((ROOT/'curriculum/activation-search.json').read_text()))
 _,extra=graph(lib,hub,'activation_index_init',None)
 cost['graph_steps']+=extra['graph_steps']
 return store,lib,hub,cost

def activation_search(lib,hub,request,budget,vocabulary,mode):
 cache=ExecutionCache();costs=defaultdict(int);log=[];diagnostics=[]
 cpu=time.process_time();wall=time.perf_counter();status='step_budget';found=None;found_phase=None;selected=[];ranking=[];evicted=[]
 def remaining():return budget-sum(costs.values())
 def step(name,arg,category,limit=None):
  meter={}
  try:return execute_graph(lib[name]['graph'],arg,lib,limit=remaining() if limit is None else min(limit,remaining()),sensors=hub,execution_cache=cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   return None
  finally:costs[category]+=meter.get('logical_steps',0)
 cap=step('activation_cap',remaining(),'allocation')
 initialized=None
 if cap is not None and remaining()>0:
  limit=remaining() if mode=='no_memory' else max(0,min(cap['cap'],remaining()-cap['floor']))
  if limit>0:initialized=step('activation_states',{**request,'base':vocabulary,'mode':mode},'retrieval',limit)
 if initialized is not None:selected=initialized['active'];ranking=initialized['ranking']
 for phase in ['memory','primitives']:
  if found is not None or remaining()<=0:break
  if phase=='memory':
   if not selected:continue
   cap=step('activation_cap',remaining(),'allocation')
   if cap is None:break
   limit=max(0,min(cap['cap'],remaining()-cap['floor']))
   if not limit:continue
   state=initialized['working'];name='activation_step'
  else:
   state=initialized['primitives'] if initialized is not None else step('activation_primitive_init',{**request,'base':vocabulary},'fallback_init')
   if state is None:break
   limit=remaining();name='fair_step'
  start=sum(costs.values())
  while not state['done'] and remaining()>0 and sum(costs.values())-start<limit:
   if time.process_time()-cpu>=10:status='cpu_budget';break
   result=step(name,state,phase,limit-(sum(costs.values())-start))
   if result is None:break
   state=result;log+=result['last_log']
   if phase=='memory':evicted=result['evicted']
   diagnostics.append({'phase':phase,'ops':result['last'],'expanded':result['last_expanded'],'allowed':result['last_allowed'],'progress':result['last_evaluation']['progress'],'executable':result['last_evaluation']['executable'],'queue_size':len(result['queue']),'parent':result['last_parent'],'child_index':result['last_child_index'],'evicted':list(evicted),'active':result.get('active',[])})
   if result['found'] is not None:found=result['found'];found_phase=phase;status='found';break
  if status=='cpu_budget':break
 return {'status':status,'found':found,'found_phase':found_phase,'selected':selected,'ranking':ranking,'evicted':evicted,'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'diagnostics':diagnostics,'candidates_evaluated':sum(x['allowed'] for x in diagnostics),'mixed_candidates_evaluated':sum(x['allowed'] and len(x['ops'])>1 and any(op not in vocabulary for op in x['ops']) for x in diagnostics),'max_call_depth':max((len(x['ops']) for x in diagnostics if x['allowed']),default=0),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(store,lib,hub,task,arm):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=lambda lib,hub,request,budget: activation_search(lib,hub,request,budget,vocabulary,arm)
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
 if arm in ['all_active','top_k']:
  _,cost=graph(lib,hub,'manager_update',{'log':logs,'found':found,'validated':validation['accepted']});costs['utility']+=cost['graph_steps']
  if validation['accepted']:
   retained,cost=graph(lib,hub,'manager_retain',{'ops':found,'name':'allocated_'+str(task['id']),'base':vocabulary,'validation':task['validation'],'predicate':'unused','projector':'unused'});costs['retention']+=cost['graph_steps']
   if retained['retained']:
    _,cost=graph(lib,hub,'activation_record','allocated_'+str(task['id']));costs['indexing']+=cost['graph_steps']
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
 parent=ROOT/'experiments/split-search-results/manifest.json';old=json.loads(parent.read_text())
 for p,h in old['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 paths=list(old['source_hashes'])+['experiments/activation_search.py','curriculum/activation-search.json','graph-authoring/activation-search.mjs']
 manifest={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'streams':old['streams'],'parent_manifest_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'policy':'Three arms: no retention; all retained methods active without eviction; top-1 input-compatible method with positive stored-effect overlap plus task-local eviction after eight non-improving attempted uses. Rank uses changed-leaf path/type/value overlap, output-kind agreement, expanded length and global wins/misses. Effect signatures indexed once upon retention in both memory arms. First training example supplies the retrieval target signature; full training and independent validation/audit govern acceptance. Memory-guided phase and retrieval must preserve 100k remaining steps for original-only fallback initialization/search; unused memory budget falls through to fallback. No deletion from long-term catalog/index. Both memory arms share retention and primitive fallback.','limitations':['Same four partially evaluated orders from the stopped sweep, not fresh confirmatory data. That sweep remains stopped.','Top-k plus eviction is a combined treatment; there is no separate ablation isolating either component.','Index scan is linear in retained methods; no large-library scaling claim.','Global wins/misses are used; context-conditioned utility and semantic/LLM routing are not implemented.','Signatures use one stored validation example and one current training example, so retrieval can be misleading.','Eight non-improving candidate attempts is a supplied policy, not learned.','Memory phase and fallback use separate frontiers; repeated work is fully charged. A fallback floor is not a guarantee of solving every new target.','No app migration, text/tree, abstraction extraction or adaptive borrowing experiment.']}
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
 if a.freeze:freeze(a.output);print('Stored/active memory comparison frozen.')
 else:run(a.output)
