"""Managed-memory candidate policy; independent frozen regression/fresh runs."""
import argparse,copy,hashlib,json,sys,time
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from experiments.program_synthesis import setup
from experiments.adaptive_reuse import graph
from experiments.learning_economics import trial as original_trial,SEARCH_BUDGET
from experiments.reuse_benchmark import BASE

def managed_search(lib,hub,request,budget):
 state={**copy.deepcopy(request),'vocabulary':BASE,'rank':0,'depth':1,'max_depth':5,'found':None,'done':False,'evaluated':0}
 cache=ExecutionCache();costs=defaultdict(int);log=[];selected=[];status='step_budget';cpu=time.process_time();wall=time.perf_counter()
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
  result=step('bench_search_step',state,remaining(),'search')
  if result is None:break
  state=result
 if not state['done'] and state['depth']>1 and remaining()>0:
  prepared=step('manager_prepare',{'base':BASE},remaining(),'retrieval')
  if prepared is not None:
   selected=prepared['selected'];probe_budget=min(SEARCH_BUDGET//4,remaining())
   probe_state={**request,'prelude':prepared['prelude'],'prefix_i':0,'found':None,'done':False,'evaluated':0,'log':[]}
   start=sum(costs.values())
   while probe_state['prefix_i']<len(prepared['prelude']) and not probe_state['done'] and probe_budget>sum(costs.values())-start:
    result=step('manager_probe_step',probe_state,min(remaining(),probe_budget-(sum(costs.values())-start)),'probing')
    if result is None:break
    probe_state=result;log=result['log']
   if probe_state['found'] is not None:state['found']=probe_state['found'];state['done']=True
   state['evaluated']+=probe_state['evaluated']
 # Original enumeration resumes at depth two, without repeating the base layer
 # or adding learned names to its branching factor.
 while not state['done'] and remaining()>0:
  if time.process_time()-cpu>=10:status='cpu_budget';break
  result=step('bench_search_step',state,remaining(),'search')
  if result is None:break
  state=result
 if state['found'] is not None:status='found'
 elif state['done']:status='exhausted_space'
 return {'status':status,'found':state['found'],'graph_steps':sum(costs.values()),'costs':dict(costs),'log':log,'selected':selected,'candidates_evaluated':state['evaluated'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def trial(lib,hub,store,task,retain=True):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes;costs=defaultdict(int)
 request=copy.deepcopy(task['request']);remaining=SEARCH_BUDGET;attempts=[];logs=[];validation={'accepted':False};found=None;failures=0
 for attempt in range(2):
  if remaining<=0:break
  result=managed_search(lib,hub,request,remaining);attempts.append(result);logs+=result['log'];remaining-=result['graph_steps'];found=result['found']
  for k,v in result['costs'].items():costs[k]+=v
  validation,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['validation'],'predicate':request['predicate'],'projector':request['projector']});costs['validation']+=cost['graph_steps']
  if found is None or validation['accepted']:break
  failures+=1
  if attempt==0 and remaining>0:
   request['examples'],cost=graph(lib,hub,'economy_refine',{'examples':request['examples'],'validation':task['validation']});costs['feedback']+=cost['graph_steps'];remaining-=cost['graph_steps']
 retained={'retained':False}
 if retain:
  _,cost=graph(lib,hub,'manager_update',{'log':logs,'found':found,'validated':validation['accepted']});costs['utility']+=cost['graph_steps']
  if validation['accepted']:
   retained,cost=graph(lib,hub,'manager_retain',{'ops':found,'name':'managed_'+str(task['id']),'base':BASE,'validation':task['validation'],'predicate':request['predicate'],'projector':request['projector']});costs['canonicalize_validate_retain']+=cost['graph_steps']
 audit={'accepted':False}
 if validation['accepted']:
  audit,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['audit'],'predicate':request['predicate'],'projector':request['projector']});costs['audit']+=cost['graph_steps']
 catalog=store.map('knowledge.economics')['catalog']
 if not retain:assert catalog==[]
 pages=store.connection.execute('PRAGMA page_count').fetchone()[0];size=store.connection.execute('PRAGMA page_size').fetchone()[0]
 return {'task':task['id'],'phase':task['phase'],'role':task['role'],'family':task['family'],'domain':task['domain'],'found':found,'success':bool(validation['accepted'] and audit['accepted']),'validation_rejections':failures,'audit_false_positive':bool(validation['accepted'] and not audit['accepted']),'retained':retained['retained'],'library_size':len(catalog),'active_methods':sum(r['active'] for r in catalog),'catalog':catalog,'attempts':attempts,'costs':dict(costs),'total_graph_steps':sum(costs.values()),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'sqlite_row_changes':store.connection.total_changes-changes,'database_bytes':pages*size}

def run(directory):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 if (directory/'manifest.json').exists():raise ValueError('Use a fresh output directory.')
 old=json.loads((ROOT/'experiments/learning-economics-results/manifest.json').read_text());fresh=json.loads((ROOT/'experiments/managed-memory-fresh-streams.json').read_text())
 streams={**old['streams'],**fresh['streams']};seeds=old['seeds']+fresh['seeds']
 manifest={'seeds':seeds,'regression_seeds':old['seeds'],'fresh_seeds':fresh['seeds'],'streams':streams,'arms':['discard','managed','manager_disabled'],'source_hashes':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['curriculum/managed-memory.json','experiments/managed_memory.py','graph_runtime.py','graph_store.py','experiments/learning_economics.py','experiments/reuse_benchmark.py']},'search_budget':SEARCH_BUDGET,'probe_cap':SEARCH_BUDGET//4,'policy':'Original base layer first; up to four active canonical methods with self/double/negate probes, screened on two examples; original-only exhaustive fallback. At most one feedback retry. Retire after 24 consecutive probed tasks without a validated use.','limitations':['Canonicalization is supplied and specific to the fixed pure reducer language, not arbitrary JS or effects.','New seeds use the same generator; they are held-out instances/order, not new domains.','The original negative run remains untouched.','manager_disabled uses the same scheduler with an empty catalog; it isolates retention from scheduler effects.','Graph-step totals charge management and audit; CPU/wall include SQLite and storage bytes are separate.']}
 data=json.dumps(manifest,sort_keys=True).encode();(directory/'manifest.json').write_bytes(data);digest=hashlib.sha256(data).hexdigest()
 rows=[];setups=[]
 with (directory/'trials.jsonl').open('w') as out:
  for seed in seeds:
   engines={}
   try:
    for arm in manifest['arms']:
     cpu=time.process_time();wall=time.perf_counter();store,lib,hub=setup(directory/f'{seed}-{arm}.sqlite3')
     for name in ['reuse-benchmark','adaptive-reuse','learning-economics','managed-memory']:lib.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
     _,cost=graph(lib,hub,'economy_init',None);engines[arm]=(store,lib,hub)
     setups.append({'seed':seed,'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]})
    for task in streams[str(seed)]:
     arms=manifest['arms'];offset=(task['id']+seed)%3;order=arms[offset:]+arms[:offset]
     for arm in order:
      store,lib,hub=engines[arm]
      result=original_trial(lib,hub,store,task,False) if arm=='discard' else trial(lib,hub,store,task,arm=='managed')
      row=result|{'seed':seed,'arm':arm};rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
     if (task['id']+1)%10==0:print(seed,task['id']+1,'/60',{a:sum(r['success'] for r in rows if r['seed']==seed and r['arm']==a) for a in arms},flush=True)
   finally:
    for store,_,_ in engines.values():store.close()
 assert hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()==digest
 for p,h in manifest['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 (directory/'report.json').write_text(json.dumps({'manifest_sha256':digest,'setup':setups,'trials':rows},indent=2)+'\n')
 summarize(directory)

def summarize(directory):
 directory=Path(directory);r=json.loads((directory/'report.json').read_text());m=json.loads((directory/'manifest.json').read_text());summary=[]
 for seed in m['seeds']:
  for arm in m['arms']:
   rows=sorted([x for x in r['trials'] if x['seed']==seed and x['arm']==arm],key=lambda x:x['task']);s=next(x for x in r['setup'] if x['seed']==seed and x['arm']==arm)
   for end in [20,40,60]:
    rr=rows[:end];win=rows[end-20:end];solved=sum(x['success'] for x in win)
    summary.append({'seed':seed,'split':'fresh' if seed in m['fresh_seeds'] else 'regression','arm':arm,'through':end,'solved':sum(x['success'] for x in rr),'graph_steps':sum(x['total_graph_steps'] for x in rr)+s['graph_steps'],'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+s['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+s['wall_seconds'],'window_steps_per_solved':sum(x['total_graph_steps'] for x in win)/solved if solved else None,'library_size':rr[-1]['library_size'],'database_growth':rr[-1]['database_bytes']-s['database_bytes'],'audit_false_positives':sum(x['audit_false_positive'] for x in rr)})
 r['summary']=summary;(directory/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Managed memory comparison','','Frozen regression streams and three fresh seeds; all management, validation and audit costs charged.','', '| Seed | Split | Arm | Through | Solved | Total steps | CPU s | Methods |','|---:|---|---|---:|---:|---:|---:|---:|']
 for x in summary:lines.append(f"| {x['seed']} | {x['split']} | {x['arm']} | {x['through']} | {x['solved']} | {x['graph_steps']:,} | {x['cpu_seconds']:.2f} | {x['library_size']} |")
 lines+=['','## Limitations','']+['- '+x for x in m['limitations']]
 (directory/'REPORT.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
