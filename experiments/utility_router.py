"""Isolated learned utility routing. No live application state is opened."""
import argparse,copy,hashlib,json,sys,time,tempfile,random
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_runtime import execute_graph,ExecutionCache
from graph_store import GraphStore
from sensors import SensorHub
from workspace_surface import WorkspaceSurface
from experiments.shortcut_search import prepare as previous_prepare
from experiments.transfer_tasks import VOCABULARIES,stream
BUDGET=450000;SEARCH_CAP=350000
SEEDS=[210011,220009,230003,240007];ARMS=['no_memory','fixed','router']

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def prepare(path):
 store,lib,hub,cost=previous_prepare(path,'memory');lib.update(json.loads((ROOT/'curriculum/utility-router.json').read_text()))
 return store,lib,hub,cost

def connect(path):
 store=GraphStore(path);hub=SensorHub(store);hub.register_surface('workspace',WorkspaceSurface(store))
 return store,store.map('knowledge.procedures'),hub

class Meter:
 def __init__(self,store,lib,hub,budget=BUDGET):
  self.store,self.lib,self.hub,self.budget=store,lib,hub,budget;self.costs=defaultdict(int);self.cache=ExecutionCache();self.exhaustions=[]
 @property
 def spent(self):return sum(self.costs.values())
 def call(self,name,arg,category,ceiling=None):
  limit=min(self.budget,self.budget if ceiling is None else ceiling)-self.spent
  if limit<=0:return None
  meter={}
  try:
   with self.store.transaction():
    return execute_graph(self.lib[name]['graph'],arg,self.lib,limit=limit,sensors=self.hub,execution_cache=self.cache,meter=meter)[0]
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   self.exhaustions.append({'operation':name,'category':category});return None
  finally:self.costs[category]+=meter.get('logical_steps',0)

def search(m,request,arm,model,ordinal,forced=None,cap=SEARCH_CAP):
 state=m.call('shortcut_init',{**request,'base':VOCABULARIES['planning']},'initialization',cap)
 records=[];trace=[];log=[]
 if state is not None and arm!='no_memory':
  probe_end=min(cap,m.spent+45000);entries=m.call('shortcut_retrieve',None,'retrieval',probe_end)
  for entry in entries or []:
   if m.spent>=probe_end:break
   before=m.spent;probe=m.call('shortcut_probe',{'state':state,'entry':entry},'probing',min(probe_end,m.spent+15000))
   record={'name':entry['name'],'entry':copy.deepcopy(entry),'probe':probe,'probe_cost':m.spent-before,'x':None,'score':None,'activated':False,'exploration':False};records.append(record)
   if probe is None:continue
   eligible=probe['eligible'];decision={'activate':eligible,'exploration':False}
   if arm=='router':
    ordinal+=1;record['ordinal']=ordinal
    x=m.call('router_features',{'state':state,'entry':entry,'probe':probe},'router_features',cap);record['x']=x
    if x is None:break
    score=m.call('router_score',{'x':x,'model':model},'router_inference',cap);record['score']=score
    if score is None:break
    decision=m.call('router_decide',{'score':score,'updates':model['updates'],'ordinal':ordinal,'explore':True},'router_decision',cap)
    if decision is None:break
   activate=eligible and (decision['activate'] if forced is None else entry['name']==forced)
   if activate:
    updated=m.call('shortcut_inject',{'state':state,'entry':entry,'probe':probe},'injection',cap)
    if updated is None:break
    state=updated;record['activated']=True;record['exploration']=decision['exploration']
    if state['done']:break
 while state is not None and not state['done'] and m.spent<cap:
  before=m.spent;result=m.call('fair_step',state,'search',cap)
  if result is None:break
  state=result;log+=result['last_log'];trace.append({'ops':result['last'],'expanded':result['last_expanded'],'allowed':result['last_allowed'],'charged':m.spent-before,'queue':len(result['queue'])})
 return {'found':None if state is None else state['found'],'selected':[] if state is None else state['selected'],'records':records,'trace':trace,'log':log,'ordinal':ordinal}

def trial(store,lib,hub,task,arm,model,ordinal=0,forced=None):
 cpu=time.process_time();wall=time.perf_counter();m=Meter(store,lib,hub);request=copy.deepcopy(task['request']);attempts=[];logs=[];found=None;validation=None;rejections=0
 for i in range(2):
  if m.spent>=SEARCH_CAP:break
  a=search(m,request,arm,model,ordinal,forced);ordinal=a['ordinal'];attempts.append(a);found=a['found'];logs+=a['log']
  validation=m.call('economy_validate',{'ops':found,'examples':task['validation'],'predicate':'unused','projector':'unused'},'validation')
  if found is None or validation is None or validation['accepted']:break
  rejections+=1
  if i==0 and m.spent<SEARCH_CAP:
   refined=m.call('economy_refine',{'examples':request['examples'],'validation':task['validation']},'feedback',SEARCH_CAP)
   if refined is None:break
   request['examples']=refined
 retained=None
 if arm!='no_memory':
  m.call('manager_update',{'log':logs,'found':found,'validated':bool(validation and validation['accepted'])},'memory_utility')
  if validation and validation['accepted']:
   retained=m.call('manager_retain',{'ops':found,'name':'allocated_'+str(task['id']),'base':VOCABULARIES['planning'],'validation':task['validation'],'predicate':'unused','projector':'unused'},'retention')
   if retained and retained['retained']:m.call('activation_record','allocated_'+str(task['id']),'indexing')
 audit=None
 if validation and validation['accepted']:
  audit=m.call('economy_validate',{'ops':found,'examples':task['audit'],'predicate':'unused','projector':'unused'},'final_audit')
 if arm=='router':m.call('router_persist',{'model':model,'ordinal':ordinal,'task':task['id']},'router_persistence')
 success=bool(audit and audit['accepted']);used=[op for op in found or [] if op not in VOCABULARIES['planning']]
 return {'task':task['id'],'family':task['family'],'arm':arm,'success':success,'found':found,'mixed':bool(success and used and len(found)>1),'whole':bool(success and used and len(found)==1),'attempts':attempts,'ordinal':ordinal,'validation_rejections':rejections,'audit_false_positive':bool(audit and not audit['accepted']),'uncertified':bool(validation and validation['accepted'] and audit is None),'costs':dict(m.costs),'graph_steps':m.spent,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'exhaustions':m.exhaustions,'catalog':copy.deepcopy(store.map('knowledge.economics')['catalog']),'model':model}

def freeze(d):
 d=Path(d);d.mkdir(parents=True,exist_ok=True)
 if (d/'manifest.json').exists():raise ValueError('Existing frozen experiment')
 parent=ROOT/'experiments/shortcut-search-results/manifest.json';old=json.loads(parent.read_text())
 for p,h in old['source_hashes'].items():assert digest(ROOT/p)==h,p
 paths=list(old['source_hashes'])+['experiments/utility_router.py','graph-authoring/utility-router.mjs','curriculum/utility-router.json','test_utility_router.py','experiments/audit_utility_router.py']
 training=ROOT/'experiments/shortcut-search-results/report.json'
 streams={str(seed):stream('planning',seed) for seed in SEEDS}
 oldorders=[tuple(t['family'] for t in tasks) for tasks in old['streams']['planning'].values()]
 assert all(tuple(t['family'] for t in tasks) not in oldorders for tasks in streams.values())
 m={'seeds':SEEDS,'arms':ARMS,'budget':BUDGET,'search_cap':SEARCH_CAP,'streams':streams,'source_hashes':{p:digest(ROOT/p) for p in paths},'parent_manifest':digest(parent),'training_report':digest(training),'policy':{'features':['bias','exact_example_fraction','changed_leaf_agreement_fraction','expanded_length_over_five','mean_changed_leaves_over_32','prior_wins_over_wins_plus_misses_plus_one'],'feature_scale':1000,'weight_clip':4000,'learning_rate':'1/5','error_clip':2000,'threshold':100,'min_updates':5,'exploration':'one uncertain eligible proposal per twenty considered (score in [-100,100]); deterministic, frozen model in evaluation','training':'one chronological pass through single-activation outcomes of the earlier shortcut experiment; all previous-task features reconstructed from prior catalogs; no outcomes used as inputs','labels':'gained audited solve +1000; lost audited solve -2000; jointly solved normalized total charged-work saving; otherwise nonpositive overhead','cost':'450k inclusive total per task. Common 100k finalization headroom. All inference, probes, injection, search, validation, retention, utility and persistence charged. Fitting and diagnostic counterfactual runs reported separately.','updates':'training incremental after each logged task; weights and threshold frozen before evaluation, no evaluation outcome updates'},'limitations':['Four new orders and generated examples from the same planning generator; not cross-domain generalization.','Training traces were produced by the old 450k search-only budget, whereas evaluation uses an inclusive 450k task cap; label-distribution shift is explicit.','Training uses logged interventions, not counterfactual labels for rejected memories.','Identity and operation names never appear in the model features.','Counterfactual diagnostics use isolated snapshots and never update the evaluation router.']}
 dump(d/'manifest.json',m)

def verify(d):
 m=json.loads((d/'manifest.json').read_text())
 for p,h in m['source_hashes'].items():assert digest(ROOT/p)==h,p
 assert digest(ROOT/'experiments/shortcut-search-results/report.json')==m['training_report']
 return m

def train(d):
 d=Path(d);manifest=verify(d)
 if (d/'model.json').exists():raise ValueError('Already fitted')
 old=json.loads((ROOT/'experiments/shortcut-search-results/report.json').read_text());om=json.loads((ROOT/'experiments/shortcut-search-results/manifest.json').read_text())
 cpu=time.process_time();wall=time.perf_counter();store,lib,hub,setup=prepare(d/'training.sqlite3');m=Meter(store,lib,hub,10000000);model=m.call('router_zero',None,'model_init');history=[]
 try:
  for seed in om['seeds']:
   prior=[]
   for row in sorted([r for r in old['trials'] if r['seed']==seed and r['arm']=='memory'],key=lambda r:r['task']):
    active=[p for a in row['attempts'] for p in a['probes'] if p['injected']]
    if active:
     assert len(active)==1,'Single-intervention supervision required'
     p=active[0];entry=next(e for e in prior if e['name']==p['name']);task=om['streams']['planning'][str(seed)][row['task']]
     start=m.spent;state=m.call('shortcut_init',{**task['request'],'base':VOCABULARIES['planning']},'training_context')
     x=m.call('router_features',{'state':state,'entry':entry,'probe':p['probe']},'training_features');prediction=m.call('router_score',{'x':x,'model':model},'training_inference')
     baseline=next(b for b in old['trials'] if b['seed']==seed and b['task']==row['task'] and b['arm']=='no_memory')
     utility=m.call('router_utility',{'actual':{'success':row['success'],'cost':row['total_graph_steps']+m.spent-start},'baseline':{'success':baseline['success'],'cost':baseline['total_graph_steps']}},'training_label')
     before=copy.deepcopy(model);model=m.call('router_update',{'model':model,'x':x,'utility':utility},'training_update')
     m.call('router_persist',{'model':model,'seed':seed,'task':row['task']},'training_persistence')
     history.append({'seed':seed,'task':row['task'],'name':p['name'],'x':x,'prediction':prediction,'utility':utility,'before':before,'after':model,'graph_steps':m.spent-start,'actual_success':row['success'],'baseline_success':baseline['success']})
    prior=row['catalog']
  assert model and model['updates']==len(history)
  dump(d/'training.json',{'history':history,'costs':dict(m.costs),'graph_steps':m.spent+setup['graph_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'historical_trace_generation_steps':sum(r['total_graph_steps'] for r in old['trials']),'note':'Historical execution cost is reported separately and was not rerun. Update/persistence cost is charged to fitting totals, not retroactively to logged activation utility.'})
  dump(d/'model.json',{'model':model,'threshold':100,'manifest_sha256':digest(d/'manifest.json'),'training_sha256':digest(d/'training.json')})
  (d/'model.sha256').write_text(digest(d/'model.json')+'\n');print('Frozen fitted model',model,flush=True)
 finally:store.close()

def clone(store):
 other=GraphStore();store.connection.backup(other.connection);hub=SensorHub(other);hub.register_surface('workspace',WorkspaceSurface(other))
 return other,other.map('knowledge.procedures'),hub

def evaluate(d):
 harness_cpu=time.process_time();harness_wall=time.perf_counter()
 d=Path(d);manifest=verify(d);frozen=digest(d/'model.json');assert frozen==(d/'model.sha256').read_text().strip()
 model=json.loads((d/'model.json').read_text())['model']
 assert json.loads((d/'model.json').read_text())['manifest_sha256']==digest(d/'manifest.json')
 if (d/'trials.jsonl').exists():raise ValueError('Evaluation already exists')
 rows=[];setups=[];shadows=[]
 with (d/'trials.jsonl').open('w') as out,(d/'counterfactuals.jsonl').open('w') as diag:
  for seed in SEEDS:
   engines={};ordinal=0
   try:
    for arm in ARMS:
     cpu=time.process_time();wall=time.perf_counter();store,lib,hub,cost=prepare(d/f'{seed}-{arm}.sqlite3');engines[arm]=(store,lib,hub)
     setups.append({'seed':seed,'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall})
    for task in manifest['streams'][str(seed)]:
     # Deterministic rotation mitigates systematic timing order effects.
     offset=(seed+task['id'])%3;order=ARMS[offset:]+ARMS[:offset]
     for arm in order:
      store,lib,hub=engines[arm];snapshot=clone(store) if arm=='router' else None;previous_ordinal=ordinal
      row=trial(store,lib,hub,task,arm,model,ordinal if arm=='router' else 0)|{'seed':seed}
      if arm=='router':ordinal=row['ordinal']
      rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
      if snapshot:
       try:
        rejected={p['name'] for a in row['attempts'] for p in a['records'] if p['probe'] and p['probe']['eligible'] and not p['activated']}
        activated={p['name'] for a in row['attempts'] for p in a['records'] if p['activated']}
        for name in sorted(rejected-activated):
         ss,ll,hh=clone(snapshot[0])
         try:
          cf=trial(ss,ll,hh,task,'router',model,previous_ordinal,forced=name)|{'seed':seed,'forced':name}
          shadows.append(cf);diag.write(json.dumps(cf)+'\n');diag.flush()
         finally:ss.close()
       finally:snapshot[0].close()
     if (task['id']+1)%10==0:print(seed,task['id']+1,{a:sum(r['success'] for r in rows if r['seed']==seed and r['arm']==a) for a in ARMS},flush=True)
   finally:
    for store,_,_ in engines.values():store.close()
 verify(d);assert digest(d/'model.json')==frozen
 dump(d/'report.json',{'manifest_sha256':digest(d/'manifest.json'),'model_sha256':frozen,'trials':rows,'setup':setups,'counterfactuals':shadows,'harness_cpu_seconds':time.process_time()-harness_cpu,'harness_wall_seconds':time.perf_counter()-harness_wall})

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','train','evaluate']);p.add_argument('--output',required=True);a=p.parse_args()
 {'freeze':freeze,'train':train,'evaluate':evaluate}[a.phase](a.output)
