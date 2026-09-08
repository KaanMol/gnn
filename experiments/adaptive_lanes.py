"""Adaptive probes and borrowing across primitive and retrieved-memory lanes."""
import argparse,copy,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.adaptive_reuse import graph
from experiments.activation_search import prepare as previous_prepare
from experiments.transfer_tasks import VOCABULARIES
ARMS=['no_memory','memory']
SEEDS=[15053,16057,17077,18089]
BUDGET=450000

def prepare(database,arm):
 store,lib,hub,cost=previous_prepare(database,arm)
 lib.update(json.loads((ROOT/'curriculum/adaptive-lanes.json').read_text()))
 return store,lib,hub,cost

def adaptive_search(lib,hub,request,budget,vocabulary,mode):
 cache=ExecutionCache();costs=defaultdict(int);log=[];diagnostics=[];events=[]
 cpu=time.process_time();wall=time.perf_counter();status='step_budget';found=None;found_lane=None;selected=[];ranking=[];stats=[];lane_spent=[]
 def remaining():return budget-sum(costs.values())
 def step(name,arg,category,limit=None):
  meter={}
  try:return execute_graph(lib[name]['graph'],arg,lib,limit=remaining() if limit is None else min(limit,remaining()),sensors=hub,execution_cache=cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   return None
  finally:costs[category]+=meter.get('logical_steps',0)
 # Preserve the existing primitive opportunity if metadata retrieval overruns.
 limit=budget if mode=='no_memory' else max(0,budget-100000)
 initialized=step('lanes_init',{**request,'base':vocabulary,'mode':mode},'initialization',limit) if limit else None
 if initialized is None and remaining()>0:
  primitive=step('activation_primitive_init',{**request,'base':vocabulary},'fallback_init')
  if primitive is not None:initialized={'states':[primitive],'selected':[],'ranking':[]}
 if initialized is not None and remaining()>0:
  states=initialized['states'];selected=initialized['selected'];ranking=initialized['ranking'];lane_spent=[0]*len(states)
  stats=step('lanes_stats',states,'routing')
  if stats is None:stats=[]
  while remaining()>0 and stats and any(x['live'] for x in stats):
   if time.process_time()-cpu>=10:status='cpu_budget';break
   lane=step('lanes_choose',stats,'routing')
   if lane is None or remaining()<=0:break
   before=costs['execution'];result=step('fair_step',states[lane],'execution');charged=costs['execution']-before;lane_spent[lane]+=charged
   events.append({'lane':lane,'charged':charged,'completed':result is not None,'before_stat':copy.deepcopy(stats[lane])})
   if result is None:break
   states[lane]=result;log+=result['last_log']
   diagnostics.append({'lane':lane,'ops':result['last'],'expanded':result['last_expanded'],'allowed':result['last_allowed'],'progress':result['last_evaluation']['progress'],'matches':result['last_evaluation']['matches'],'executable':result['last_evaluation']['executable'],'queue_size':len(result['queue']),'parent':result['last_parent'],'child_index':result['last_child_index']})
   if result['found'] is not None:found=result['found'];found_lane=lane;status='found';break
   if remaining()<=0:break
   observed=step('lanes_observe',{'stat':stats[lane],'evaluation':result['last_evaluation'],'charged':charged,'done':result['done']},'routing')
   if observed is None:break
   stats[lane]=observed;events[-1]['after_stat']=copy.deepcopy(observed)
  if found is None and stats and not any(x['live'] for x in stats):status='exhausted_lanes'
 return {'status':status,'found':found,'found_lane':found_lane,'selected':selected,'ranking':ranking,'lane_spent':lane_spent,'lane_stats':stats,'events':events,'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'diagnostics':diagnostics,'candidates_evaluated':sum(x['allowed'] for x in diagnostics),'mixed_candidates_evaluated':sum(x['allowed'] and len(x['ops'])>1 and any(op not in vocabulary for op in x['ops']) for x in diagnostics),'max_call_depth':max((len(x['ops']) for x in diagnostics if x['allowed']),default=0),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(store,lib,hub,task,arm):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=lambda lib,hub,request,budget: adaptive_search(lib,hub,request,budget,vocabulary,arm)
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
 paths=list(old['source_hashes'])+['experiments/adaptive_lanes.py','curriculum/adaptive-lanes.json','graph-authoring/adaptive-lanes.mjs']
 manifest={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'streams':old['streams'],'parent_manifest_sha256':hashlib.sha256(parent.read_bytes()).hexdigest(),'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'policy':'Same relevance scores, widen to top four compatible positive-overlap memories. Independent fair-search lane per memory (that callable plus primitives), and a primitive-only lane. Primitive lane receives 100k execution steps first unless it solves/exhausts sooner. Then each live lane gets a 20k probe target, checked at completed-transition boundaries; these are opportunities, not caps. Remaining work goes to the highest recent positive agreement gain / execution cost, measured over four transitions; least total execution spent breaks ties. Drop memory lanes after eight non-improving transitions once probe target is reached; never stall-drop the primitive lane. No fixed lane caps or permanent partitions. Retrieval, routing, duplicated work and nested cached work all count toward total 450k.','limitations':['Same four previously evaluated planning orders; not held-out confirmation or cross-domain evidence.','Independent lanes may repeat primitive work; all repetitions charged.','Initial floor is execution work, so shared retrieval/routing add overhead. A solution can end the task before other probes occur.','Probe target can overshoot by one completed transition. No promise of useful learning from a fixed probe allowance.','Recent gain is heuristic and can favor misleading intermediate agreement. No semantic/action-specific routing.','Only two arms: effect of this whole adaptive policy with memory, not separate ablations of probes, borrowing or stall thresholds.','Memory manager, signature index, scorer, validation and task data unchanged. No further heuristic tuning after freezing.']}
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
 if a.freeze:freeze(a.output);print('Adaptive-lane comparison frozen.')
 else:run(a.output)
