"""Frozen discovery/reuse budget sweep on new planning orders."""
import argparse,copy,hashlib,json,sys,time,random
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.fair_search import prepare as previous_prepare
from experiments.transfer_tasks import VOCABULARIES
SEEDS=[15053,16057,17077,18089]
BUDGET=450000
CONDITIONS=[(50,'no_memory'),(25,'managed_memory'),(50,'managed_memory'),(75,'managed_memory')]

def prepare(database,arm):
 store,lib,hub,cost=previous_prepare(database,arm)
 lib.update(json.loads((ROOT/'curriculum/split-search.json').read_text()))
 return store,lib,hub,cost

def split_search(lib,hub,request,budget,vocabulary,percent):
 cache=ExecutionCache();costs=defaultdict(int);log=[];diagnostics=[];events=[]
 cpu=time.process_time();wall=time.perf_counter();status='step_budget';found=None;found_lane=None
 spent={'discovery':0,'reuse':0};caps={'discovery':0,'reuse':0};selected=[];distinct=False
 def remaining():return budget-sum(costs.values())
 def step(name,arg,category,limit=None):
  meter={}
  try:return execute_graph(lib[name]['graph'],arg,lib,limit=remaining() if limit is None else min(limit,remaining()),sensors=hub,execution_cache=cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   return None
  finally:costs[category]+=meter.get('logical_steps',0)
 initial=step('split_init',{**request,'base':vocabulary},'initialization')
 if initial is not None and remaining()>0:
  selected=initial['selected'];distinct=initial['distinct']
  config=step('split_caps',{'remaining':remaining(),'percent':percent,'distinct':distinct},'scheduling')
  if config is not None:
   caps=config;states={key:initial[key] for key in spent};active={key:caps[key]>0 for key in spent}
   while remaining()>0 and any(active.values()):
    if time.process_time()-cpu>=10:status='cpu_budget';break
    lane=step('split_choose',{'discovery_active':active['discovery'],'reuse_active':active['reuse'],'discovery_spent':spent['discovery'],'reuse_spent':spent['reuse'],'discovery_cap':caps['discovery'],'reuse_cap':caps['reuse']},'scheduling')
    if lane is None or remaining()<=0:break
    before=costs[lane];result=step('fair_step',states[lane],lane,caps[lane]-spent[lane]);charged=costs[lane]-before;spent[lane]+=charged
    events.append({'lane':lane,'charged':charged,'completed':result is not None})
    if result is None:active[lane]=False;continue
    states[lane]=result;log+=result['last_log']
    diagnostics.append({'lane':lane,'ops':result['last'],'expanded':result['last_expanded'],'allowed':result['last_allowed'],'duplicate':result['last_duplicate'],'progress':result['last_evaluation']['progress'],'matches':result['last_evaluation']['matches'],'executable':result['last_evaluation']['executable'],'queue_size':len(result['queue']),'parent':result['last_parent'],'child_index':result['last_child_index'],'next_band_size':result['last_band_size']})
    if result['found'] is not None:found=result['found'];found_lane=lane;status='found';break
    active[lane]=not result['done'] and spent[lane]<caps[lane]
   if found is None and not any(active.values()):status='lane_budgets_or_exhausted_space'
 return {'status':status,'found':found,'found_lane':found_lane,'distinct_lanes':distinct,'lane_caps':caps,'lane_spent':spent,'lane_events':events,'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'selected':selected,'candidates_evaluated':sum(x['allowed'] for x in diagnostics),'mixed_candidates_evaluated':sum(x['allowed'] and len(x['ops'])>1 and any(op not in vocabulary for op in x['ops']) for x in diagnostics),'max_call_depth':max((len(x['ops']) for x in diagnostics if x['allowed']),default=0),'diagnostics':diagnostics,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(store,lib,hub,task,arm,percent):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=lambda lib,hub,request,budget: split_search(lib,hub,request,budget,vocabulary,percent)
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

def orders(parent):
 streams={};banks={}
 for index,seed in enumerate(SEEDS):
  bank=parent['seeds'][index%len(parent['seeds'])];tasks=parent['streams']['planning'][str(bank)]
  rng=random.Random(seed);permutation=[]
  for start in range(0,len(tasks),6):
   block=list(range(start,start+6));rng.shuffle(block);permutation+=block
  assert permutation!=list(range(30))
  reordered=[]
  for new_id,source in enumerate(permutation):
   task=copy.deepcopy(tasks[source]);task.update(id=new_id,source_task_id=source,source_bank=bank);reordered.append(task)
  streams[str(seed)]=reordered;banks[str(seed)]=bank
 return streams,banks

def freeze(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 if (directory/'manifest.json').exists():raise ValueError('Frozen output already exists.')
 parent=ROOT/'experiments/fair-search-results/manifest.json';old=json.loads(parent.read_text())
 bank=ROOT/'experiments/prioritized-search-results/manifest.json'
 for p,h in old['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 paths=list(old['source_hashes'])+['experiments/split_search.py','curriculum/split-search.json','graph-authoring/split-search.mjs']
 streams,banks=orders(json.loads(bank.read_text()))
 manifest={'seeds':SEEDS,'conditions':CONDITIONS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'streams':{'planning':streams},'source_banks':banks,'parent_manifest_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'bank_manifest_sha256':hashlib.sha256(bank.read_bytes()).hexdigest(),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'policy':'Discovery shares 25/50/75 percent, complement assigned to memory-assisted search. Two independent fair-search frontiers; originals only in discovery, unchanged selected learned vocabulary plus originals in reuse. Interleave one graph transition from the lane with the smaller used fraction of its reserved cap. Distinct-lane caps are computed from budget remaining after shared initialization. Scheduling work is additionally charged to the total 450k budget, so caps are ceilings, not guaranteed delivered work. No cross-lane budget borrowing. Identical vocabularies collapse to one full-budget frontier; hence one shared no-memory control suffices for all ratios. Repeated candidate work across distinct lanes remains charged, including cache hits. Scoring, fairness, memory rules and primitive semantics unchanged.','limitations':['Four fresh order permutations of two existing banks; no fresh examples, new task families or cross-domain evidence.','Ratios are discovery/reuse. Shared initialization and scheduling costs count in total; actual lane spending is recorded.','Hard reservations can leave unusable quota when a frontier exhausts; fixed policy is not automatically beneficial.','A transition interrupted by a lane cap is charged and that lane stops; partial instruction progress is not resumed.','Identical no-memory routes collapse, so the no-memory baseline is shared across ratios, not three independent repeats.','No seeded memory, no post-freeze tuning, no changes to text/tree or abstraction features.']}
 data=json.dumps(manifest,sort_keys=True).encode();(directory/'manifest.json').write_bytes(data);(directory/'manifest.sha256').write_text(hashlib.sha256(data).hexdigest()+'\n')

def run(directory):
 directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());digest=hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()
 if (directory/'trials.jsonl').exists():raise ValueError('Refusing to overwrite an existing run.')
 rows=[];setups=[]
 with (directory/'trials.jsonl').open('w') as out:
  for seed in SEEDS:
   engines={}
   try:
    for percent,arm in CONDITIONS:
     cpu=time.process_time();wall=time.perf_counter();store,lib,hub,cost=prepare(directory/f'planning-{seed}-{percent}-{arm}.sqlite3',arm);engines[percent,arm]=(store,lib,hub)
     setups.append({'domain':'planning','seed':seed,'percent':percent,'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]})
    for task in manifest['streams']['planning'][str(seed)]:
     offset=(task['id']+seed)%len(CONDITIONS);order=CONDITIONS[offset:]+CONDITIONS[:offset]
     for percent,arm in order:
      store,lib,hub=engines[percent,arm];row=trial(store,lib,hub,task,arm,percent)|{'seed':seed,'percent':percent};rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
     if (task['id']+1)%10==0:print(seed,task['id']+1,'/30',{str(p)+':'+a:sum(r['success'] for r in rows if r['seed']==seed and r['arm']==a and r['percent']==p) for p,a in CONDITIONS},flush=True)
   finally:
    for store,_,_ in engines.values():store.close()
 assert hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()==digest
 for p,h in manifest['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 (directory/'report.json').write_text(json.dumps({'manifest_sha256':digest,'trials':rows,'setup':setups},indent=2)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--freeze',action='store_true');a=p.parse_args()
 if a.freeze:freeze(a.output);print('Four fresh planning orders and three budget ratios frozen.')
 else:run(a.output)
