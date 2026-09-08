"""Boundary map for exact frozen and rules-disabled managed memory."""
import argparse,copy,hashlib,json,sys,time,types
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.program_synthesis import setup
from experiments.adaptive_reuse import graph
from experiments.managed_memory import managed_search
from experiments.reuse_benchmark import BASE,search
from experiments.transfer_tasks import VOCABULARIES,stream

ARMS=['discard','exact_frozen','rules_disabled','disabled_no_memory']
SEEDS=[7109,8111]
BUDGET=450000

def prepare(database,arm):
 store,lib,hub=setup(database)
 for name in ['reuse-benchmark','adaptive-reuse','learning-economics','managed-memory','transfer-environments']:
  lib.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
 # Reduction-specific environment operations are genuinely unavailable. The
 # exact manager retains its old vocabulary and is allowed to fail, not rescued.
 for name in BASE:del lib[name]
 if arm in ['rules_disabled','disabled_no_memory']:
  lib.update(json.loads((ROOT/'curriculum/transfer-manager-disabled.json').read_text()))
 _,cost=graph(lib,hub,'economy_init',None)
 return store,lib,hub,cost

def bound_search(vocabulary):
 # Explicit shared adapter for the disabled condition: bind the environment's
 # vocabulary, without editing any instruction in the frozen host scheduler.
 # This is NOT used in exact_frozen and is counted as a condition change.
 return types.FunctionType(managed_search.__code__,{**managed_search.__globals__,'BASE':vocabulary},name='environment_bound_search',argdefs=managed_search.__defaults__)

def trial(store,lib,hub,task,arm):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=BUDGET;attempts=[];logs=[];found=None;validation={'accepted':False};rejections=0
 vocabulary=VOCABULARIES[task['domain']];runner=managed_search if arm=='exact_frozen' else bound_search(vocabulary)
 for attempt in range(2):
  if remaining<=0:break
  if arm=='discard':
   result=search(lib,hub,request,vocabulary,remaining);result['costs']={'search':result['graph_steps']};result['log']=[]
  else:result=runner(lib,hub,request,remaining)
  attempts.append(result);logs+=result['log'];found=result['found'];remaining-=result['graph_steps']
  for k,v in result['costs'].items():costs[k]+=v
  validation,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['validation'],'predicate':'unused','projector':'unused'});costs['validation']+=cost['graph_steps']
  if found is None or validation['accepted']:break
  rejections+=1
  if attempt==0 and remaining>0:
   request['examples'],cost=graph(lib,hub,'economy_refine',{'examples':request['examples'],'validation':task['validation']});costs['feedback']+=cost['graph_steps'];remaining-=cost['graph_steps']
 retained={'retained':False}
 if arm in ['exact_frozen','rules_disabled']:
  _,cost=graph(lib,hub,'manager_update',{'log':logs,'found':found,'validated':validation['accepted']});costs['utility']+=cost['graph_steps']
  if validation['accepted']:
   retained,cost=graph(lib,hub,'manager_retain',{'ops':found,'name':'transfer_'+str(task['id']),'base':BASE if arm=='exact_frozen' else vocabulary,'validation':task['validation'],'predicate':'unused','projector':'unused'});costs['retention']+=cost['graph_steps']
 audit={'accepted':False}
 if validation['accepted']:
  audit,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['audit'],'predicate':'unused','projector':'unused'});costs['audit']+=cost['graph_steps']
 catalog=store.map('knowledge.economics')['catalog']
 if arm in ['discard','disabled_no_memory']:assert not catalog
 dbbytes=store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]
 return {'task':task['id'],'domain':task['domain'],'family':task['family'],'expected_boundary':task['expected_boundary'],'arm':arm,'found':found,'success':bool(validation['accepted'] and audit['accepted']),'validation_rejections':rejections,'audit_false_positive':bool(validation['accepted'] and not audit['accepted']),'retained':retained['retained'],'catalog':catalog,'library_size':len(catalog),'attempts':attempts,'costs':dict(costs),'total_graph_steps':sum(costs.values()),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':dbbytes,'sqlite_row_changes':store.connection.total_changes-changes}

def freeze(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 if (directory/'manifest.json').exists():raise ValueError('Frozen output directory already exists.')
 paths=['curriculum/managed-memory.json','experiments/managed_memory.py','curriculum/transfer-manager-disabled.json','curriculum/transfer-environments.json','experiments/transfer_tasks.py','experiments/transfer_test.py','graph_runtime.py','graph_store.py']
 manifest={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'max_depth':5,'max_attempts':2,'vocabularies':VOCABULARIES,'streams':{domain:{str(seed):stream(domain,seed) for seed in SEEDS} for domain in VOCABULARIES},'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},'changes':{'shared':'Data->Data environment boundary and supplied environment operations, same across arms; old reduction primitives removed.','exact_frozen':'Original manager graph definitions and original host vocabulary binding unchanged.','rules_disabled':'Only manager_canonicalize and manager_prepare graph rules replaced; host BASE binding changed to declared environment vocabulary. Ordered expansion/exact dedup, singleton method probes. No semantic simplifier or domain continuation.','disabled_no_memory':'Same disabled scheduler with no retained methods.','rescue':'None. No rule changes after evaluation.'},'limitations':['Fixed sequential composition grammar still shared across environments.','Rules-disabled condition is not exact unchanged transfer.','Environment primitives are supplied; the learner does not invent primitives or understand natural-language goals.','Text, tree zipper and simulated stateful action data are structured environments, not real-world side effects.','Retained whole solutions are probed directly; there are no continuation probes or recursive new-composition search through macro names in disabled mode.','Two seeds and 30 tasks per environment/seed; finite-stream crossover only.','Final audit never informs retention. Physical storage bytes and CPU/wall are separate from logical steps.']}
 data=json.dumps(manifest,sort_keys=True).encode();(directory/'manifest.json').write_bytes(data);(directory/'manifest.sha256').write_text(hashlib.sha256(data).hexdigest()+'\n')
 return manifest

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
      offset=(task['id']+seed)%4;order=ARMS[offset:]+ARMS[:offset]
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
 if a.freeze:freeze(a.output);print('Task streams and policies frozen.')
 else:run(a.output)
