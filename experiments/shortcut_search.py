"""Frozen primitive queue plus behaviorally probed shortcut proposals."""
import argparse,copy,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.activation_search import prepare as previous_prepare
from experiments.transfer_tasks import VOCABULARIES
ARMS=['no_memory','memory'];SEEDS=[15053,16057,17077,18089];BUDGET=450000

def prepare(database,arm):
 store,lib,hub,cost=previous_prepare(database,arm)
 lib.update(json.loads((ROOT/'curriculum/shortcut-search.json').read_text()))
 return store,lib,hub,cost

def shortcut_search(lib,hub,request,budget,vocabulary,mode):
 cache=ExecutionCache();costs=defaultdict(int);log=[];diagnostics=[];probes=[]
 cpu=time.process_time();wall=time.perf_counter();status='step_budget'
 def step(name,arg,category,cap=None):
  meter={};limit=budget-sum(costs.values())
  if cap is not None:limit=min(limit,max(0,cap))
  if limit<=0:return None
  try:return execute_graph(lib[name]['graph'],arg,lib,limit=limit,sensors=hub,execution_cache=cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   return None
  finally:costs[category]+=meter.get('logical_steps',0)
 state=step('shortcut_init',{**request,'base':vocabulary},'initialization')
 if state is not None and mode=='memory':
  before=sum(costs.values());entries=step('shortcut_retrieve',None,'probing',45000)
  for entry in entries or []:
   allowance=45000-(sum(costs.values())-before)
   if allowance<=0:break
   used=costs['probing'];probe=step('shortcut_probe',{'state':state,'entry':entry},'probing',min(15000,allowance))
   record={'name':entry['name'],'expanded':entry['ops'],'probe':probe,'charged':costs['probing']-used,'injected':False};probes.append(record)
   if probe and probe['eligible']:
    updated=step('shortcut_inject',{'state':state,'entry':entry,'probe':probe},'injection')
    if updated is None:break
    state=updated;record['injected']=True
    if state['done']:break
 if state is None:state={'done':False,'found':None,'selected':[],'evaluated':0}
 else:
  while not state['done'] and sum(costs.values())<budget:
   if time.process_time()-cpu>=10:status='cpu_budget';break
   used=costs['allocation_and_execution'];result=step('fair_step',state,'allocation_and_execution')
   if result is None:break
   state=result;log+=result['last_log']
   diagnostics.append({'ops':result['last'],'expanded':result['last_expanded'],'allowed':result['last_allowed'],'duplicate':result['last_duplicate'],'progress':result['last_evaluation']['progress'],'matches':result['last_evaluation']['matches'],'executable':result['last_evaluation']['executable'],'queue_size':len(result['queue']),'parent':result['last_parent'],'child_index':result['last_child_index'],'charged':costs['allocation_and_execution']-used})
 if state['found'] is not None:status='found'
 elif state['done']:status='exhausted_space'
 return {'status':status,'found':state['found'],'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'selected':state['selected'],'probes':probes,'candidates_evaluated':state['evaluated'],'mixed_candidates_evaluated':sum(x['allowed'] and len(x['ops'])>1 and any(op not in vocabulary for op in x['ops']) for x in diagnostics),'max_call_depth':max((len(x['ops']) for x in diagnostics if x['allowed']),default=0),'diagnostics':diagnostics,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(store,lib,hub,task,arm):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=lambda lib,hub,request,budget: shortcut_search(lib,hub,request,budget,vocabulary,arm)
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
 if arm in ['memory']:
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
 parent=ROOT/'experiments/activation-search-results/manifest.json';old=json.loads(parent.read_text())
 for p,h in old['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 paths=list(old['source_hashes'])+['experiments/shortcut_search.py','curriculum/shortcut-search.json','graph-authoring/shortcut-search.mjs','test_shortcut_search.py','experiments/audit_shortcut_search.py']
 manifest={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'streams':old['streams'],'parent_manifest_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'policy':'Unchanged fair_step with exact primitive state. Retrieve last three active retained entries, probe all current examples with generic changed-leaf agreement or exact matches above identity. Retrieval/probes together capped at 45000 steps; each probe capped at 15000. Inject only positive executable proposals into the ordinary queue and append callable vocabulary. Expanded cap five, full nested/cache charging. Rejected probes leave search state unchanged. No lanes or budget reservations.', 'limitations':['Previously evaluated task orders, not fresh-order generalization.','Initialization constructs the exact empty-memory fair state directly; fair_step is unchanged.','Probe ceiling and recent-three retrieval fixed before results; no post-run tuning.','450k covers initialization, retrieval, probes, injection, search and feedback; validation/retention/audit charged separately in total online cost.','Successful activation can change queue ordering and reduce primitive exploration; this is measured, not assumed harmless.']}
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
 if a.freeze:freeze(a.output);print('Shortcut comparison frozen.')
 else:run(a.output)
