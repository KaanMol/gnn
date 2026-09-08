"""Frozen wake/sleep consolidation with all lifetime compute charged."""
import argparse,copy,json,sys,time
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.utility_router import Meter,prepare as previous_prepare,trial as online_trial,clone,connect,digest,dump
from experiments.transfer_tasks import stream,VOCABULARIES
BUDGET=450000;SEARCH_CAP=350000;SLEEP_CAP=6000000;INTERVAL=20
SEEDS=[410009,420001,430007,440009];ARMS=['no_memory','online','sleep']

def prepare(path):
 store,lib,hub,cost=previous_prepare(path);lib.update(json.loads((ROOT/'curriculum/sleep-memory.json').read_text()))
 m=Meter(store,lib,hub);m.call('sleep_init',None,'sleep_init');cost['graph_steps']+=m.spent
 return store,lib,hub,cost

def wake_search(m,request,forced=None):
 state=m.call('shortcut_init',{**request,'base':VOCABULARIES['planning']},'initialization',SEARCH_CAP);route=None;selected=None;injected=False;trace=[];logs=[]
 if state is not None:
  route=m.call('sleep_route',state,'wake_lookup',SEARCH_CAP)
  selected=forced if forced is not None else (route['selected'] if route else None)
  if selected:
   result=m.call('sleep_execute_admitted',{'state':state,'entry':selected},'admitted_execution',SEARCH_CAP)
   if result and result['eligible']:
    updated=m.call('shortcut_inject',{'state':state,'entry':selected,'probe':result},'injection',SEARCH_CAP)
    if updated is not None:state=updated;injected=True
  while not state['done'] and m.spent<SEARCH_CAP:
   before=m.spent;result=m.call('fair_step',state,'search',SEARCH_CAP)
   if result is None:break
   state=result;logs+=state['last_log'];trace.append({'ops':state['last'],'expanded':state['last_expanded'],'allowed':state['last_allowed'],'charged':m.spent-before,'queue':len(state['queue'])})
 return {'found':state['found'] if state else None,'route':route,'selected':selected,'injected':injected,'trace':trace,'log':logs}

def wake_trial(store,lib,hub,task,forced=None):
 cpu=time.process_time();wall=time.perf_counter();m=Meter(store,lib,hub);request=copy.deepcopy(task['request']);attempts=[];logs=[];found=None;validation=None;rejections=0
 for i in range(2):
  if m.spent>=SEARCH_CAP:break
  a=wake_search(m,request,forced);attempts.append(a);found=a['found'];logs+=a['log']
  validation=m.call('economy_validate',{'ops':found,'examples':task['validation'],'predicate':'unused','projector':'unused'},'validation')
  if found is None or validation is None or validation['accepted']:break
  rejections+=1
  if i==0 and m.spent<SEARCH_CAP:
   refined=m.call('economy_refine',{'examples':request['examples'],'validation':task['validation']},'feedback',SEARCH_CAP)
   if refined is None:break
   request['examples']=refined
 m.call('manager_update',{'log':logs,'found':found,'validated':bool(validation and validation['accepted'])},'memory_utility')
 if validation and validation['accepted']:
  retained=m.call('manager_retain',{'ops':found,'name':'allocated_'+str(task['id']),'base':VOCABULARIES['planning'],'validation':task['validation'],'predicate':'unused','projector':'unused'},'retention')
  if retained and retained['retained']:m.call('activation_record','allocated_'+str(task['id']),'indexing')
 audit=None
 if validation and validation['accepted']:audit=m.call('economy_validate',{'ops':found,'examples':task['audit'],'predicate':'unused','projector':'unused'},'final_audit')
 success=bool(audit and audit['accepted']);used=[op for op in found or [] if op not in VOCABULARIES['planning']]
 # Persist completed evidence only. Audit answers for future tasks never enter it.
 m.call('sleep_log',{'key':str(task['id']),'value':{'task':task,'attempts':attempts,'success':success,'costs_before_logging':dict(m.costs)}},'experience_persistence')
 return {'task':task['id'],'family':task['family'],'arm':'sleep','success':success,'found':found,'mixed':bool(success and used and len(found)>1),'whole':bool(success and used and len(found)==1),'attempts':attempts,'validation_rejections':rejections,'audit_false_positive':bool(audit and not audit['accepted']),'uncertified':bool(validation and validation['accepted'] and audit is None),'costs':dict(m.costs),'graph_steps':m.spent,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'exhaustions':m.exhaustions,'catalog':copy.deepcopy(store.map('knowledge.economics')['catalog']),'context':attempts[0]['route']['context'] if attempts and attempts[0]['route'] else None}

def consolidate(store,lib,hub,completed,boundary):
 # API deliberately has no full task stream. Only completed evidence is accepted.
 assert completed and max(x['task']['id'] for x in completed)<=boundary
 cpu=time.process_time();wall=time.perf_counter();m=Meter(store,lib,hub,SLEEP_CAP)
 old=copy.deepcopy(store.map('knowledge.sleep')['state']);catalog=copy.deepcopy(store.map('knowledge.economics')['catalog']);model=old['model']
 for entry in catalog:assert int(entry['name'].split('_')[-1])<=boundary
 pairs=m.call('sleep_pairs',{'experiences':[{'task':x['task']['id'],'context':x['row']['context']} for x in completed if x['row']['context'] is not None],'catalog':catalog,'model':model},'replay_selection')
 results=[]
 for pair in pairs or []:
  if m.spent+550000>SLEEP_CAP-1000000:break
  experience=next(x for x in completed if x['task']['id']==pair['task']);assert experience['task']['id']<=boundary
  ss,ll,hh=clone(store)
  try:replay=wake_trial(ss,ll,hh,experience['task'],forced=pair['entry'])
  finally:ss.close()
  m.costs['replay']+=replay['graph_steps']
  baseline=experience['baseline'];utility=m.call('router_utility',{'actual':{'success':replay['success'],'cost':replay['graph_steps']},'baseline':{'success':baseline['success'],'cost':baseline['graph_steps']}},'downstream_utility')
  assert utility is not None
  updated=m.call('sleep_update',{'model':model,'context':pair['context'],'name':pair['entry']['name'],'utility':utility},'model_update')
  assert updated is not None;model=updated
  at_wake=int(pair['entry']['name'].split('_')[-1])<experience['task']['id']
  selected_at_wake=any(a['selected'] and a['selected']['name']==pair['entry']['name'] for a in experience['row']['attempts'])
  results.append({'pair':pair,'utility':utility,'replay':replay,'baseline_success':baseline['success'],'baseline_cost':baseline['graph_steps'],'method_existed_at_wake':at_wake,'selected_at_wake':selected_at_wake})
 published=m.call('sleep_publish',{'model':model,'catalog':catalog,'boundary':boundary},'consolidation_index_persistence');assert published is not None
 assert store.map('knowledge.economics')['catalog']==catalog,'Consolidation must not delete or edit retained methods'
 assert m.spent<=SLEEP_CAP
 return {'boundary':boundary,'available_tasks':[x['task']['id'] for x in completed],'pairs':pairs,'results':results,'before':old,'after':copy.deepcopy(store.map('knowledge.sleep')['state']),'costs':dict(m.costs),'graph_steps':m.spent,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'catalog':catalog}

def freeze(d):
 d=Path(d);d.mkdir(parents=True,exist_ok=True)
 if (d/'manifest.json').exists():raise ValueError('Existing frozen output')
 parent=ROOT/'experiments/utility-router-results/manifest.json';old=json.loads(parent.read_text())
 for p,h in old['source_hashes'].items():assert digest(ROOT/p)==h,p
 tasks=[]
 for seed in SEEDS:
  for task in stream('planning',seed):task['source_seed']=seed;task['source_task']=task['id'];task['id']=len(tasks);tasks.append(task)
 paths=list(old['source_hashes'])+['experiments/sleep_memory.py','graph-authoring/sleep-memory.mjs','curriculum/sleep-memory.json','test_sleep_memory.py','experiments/audit_sleep_memory.py']
 training=json.loads((ROOT/'experiments/utility-router-results/training.json').read_text());prior_report=json.loads((ROOT/'experiments/shortcut-search-results/report.json').read_text())
 dump(d/'manifest.json',{'tasks':tasks,'arms':ARMS,'budget':BUDGET,'search_cap':SEARCH_CAP,'sleep_interval':INTERVAL,'sleep_cap':SLEEP_CAP,'replay_quota':6,'source_hashes':{p:digest(ROOT/p) for p in paths},'online_model_sha256':digest(ROOT/'experiments/utility-router-results/model.json'),'online_training_sha256':digest(ROOT/'experiments/utility-router-results/training.json'),'online_inherited_steps':training['graph_steps']+training['historical_trace_generation_steps']+sum(x['graph_steps'] for x in prior_report['setup']),'policy':'120 consecutive tasks; sleep after every 20 including final boundary. Six least-observed pairs from last six completed tasks and up to three exact-deduplicated retained methods. Tabular context/method utility sum and positive/lost/irrelevant counts. Publish only entries with at least two positive outcomes, mean utility >50 milli-utility, and no lost baseline solve. Highest mean wins per context. Context is input/output root kinds and ordered kinds of changed scalar leaves in the first current example, already enriched by the primitive initializer. No scalar values, field paths, action names, family labels or method execution in the wake key. No wake fitting. One selected method executes only after routing. All nested/cache work charged.','limitations':['Same generator family, not broad generalization.','Coarse structural keys may alias distinct tasks; evidence count is not a calibrated confidence bound.','Six replay interventions per sleep; usefulness false negatives measured only among replayed pairs whose methods already existed at wake. Unmeasured pairs stay unknown.','Common 350k search cap with 100k finalization headroom within inclusive 450k task budget.','Final sleep is charged even though it has no later wake tasks in the measured lifetime.','Historical training and trace acquisition for inherited online baseline charged as an initial lifetime cost; current-run totals also reported.','No policy or threshold tuning after evaluation.']})

def verify(d):
 m=json.loads((d/'manifest.json').read_text())
 for p,h in m['source_hashes'].items():assert digest(ROOT/p)==h,p
 assert digest(ROOT/'experiments/utility-router-results/model.json')==m['online_model_sha256']
 assert digest(ROOT/'experiments/utility-router-results/training.json')==m['online_training_sha256']
 return m

def run(d):
 d=Path(d);manifest=verify(d)
 if (d/'trials.jsonl').exists():raise ValueError('Run exists')
 model=json.loads((ROOT/'experiments/utility-router-results/model.json').read_text())['model'];engines={};setups=[];rows=[];sleeps=[];completed=[];ordinal=0;cpu=time.process_time();wall=time.perf_counter()
 with (d/'trials.jsonl').open('w') as out,(d/'sleeps.jsonl').open('w') as sout:
  try:
   for arm in ARMS:
    startcpu=time.process_time();startwall=time.perf_counter();store,lib,hub,cost=prepare(d/f'{arm}.sqlite3');engines[arm]=(store,lib,hub)
    setups.append({'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-startcpu,'wall_seconds':time.perf_counter()-startwall,'bytes':store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]})
   for task in manifest['tasks']:
    current={};offset=task['id']%3
    for arm in ARMS[offset:]+ARMS[:offset]:
     store,lib,hub=engines[arm]
     if arm=='sleep':row=wake_trial(store,lib,hub,task)
     else:
      row=online_trial(store,lib,hub,task,'no_memory' if arm=='no_memory' else 'router',model,ordinal if arm=='online' else 0);row['arm']=arm
      if arm=='online':ordinal=row['ordinal']
     row['bytes']=store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]
     current[arm]=row;rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
    completed.append({'task':copy.deepcopy(task),'row':current['sleep'],'baseline':current['no_memory']})
    if (task['id']+1)%INTERVAL==0:
     result=consolidate(*engines['sleep'],completed,task['id']);sleeps.append(result);sout.write(json.dumps(result)+'\n');sout.flush()
     print('boundary',task['id']+1,'solves',{a:sum(r['success'] for r in rows if r['arm']==a) for a in ARMS},'sleep steps',result['graph_steps'],'routes',len(result['after']['table']),flush=True)
   verify(d)
   dump(d/'report.json',{'manifest_sha256':digest(d/'manifest.json'),'setup':setups,'trials':rows,'sleeps':sleeps,'harness_cpu_seconds':time.process_time()-cpu,'harness_wall_seconds':time.perf_counter()-wall,'final_storage':{a:store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0] for a,(store,_,_) in engines.items()}})
  finally:
   for store,_,_ in engines.values():store.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','run']);p.add_argument('--output',required=True);a=p.parse_args();{'freeze':freeze,'run':run}[a.phase](a.output)
