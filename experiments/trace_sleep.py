"""Trace-first consolidation, unchanged wake algorithms and utility thresholds."""
import argparse,copy,json,sys,time,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.sleep_memory import prepare as previous_prepare,wake_trial,consolidate,INTERVAL,SLEEP_CAP
from experiments.utility_router import Meter,trial as primitive_trial,clone,digest,dump
ARMS=['no_memory','full','trace'];PARTIAL_CAP=75000

def prepare(path):
 store,lib,hub,cost=previous_prepare(path);lib.update(json.loads((ROOT/'curriculum/trace-sleep.json').read_text()))
 return store,lib,hub,cost

class RecordingMeter(Meter):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.observations=[];self.available=super().call('trace_availability',None,'extra_wake_index')
 def call(self,name,arg,category,ceiling=None):
  result=super().call(name,arg,category,ceiling)
  if name=='fair_step' and result is not None:
   self.observations.append({'ops':result['last'],'expanded':result['last_expanded'],'evaluation':result['last_evaluation'],'parent':result['last_parent'],'next_parent':result['parent'],'next_i':result['next_i'],'duplicate':result['last_duplicate']})
  if name=='sleep_log':
   super().call('sleep_log',{'key':'trace_'+arg['key'],'value':{'available':self.available,'observations':self.observations}},'extra_wake_recording')
  return result

class PartialMeter(RecordingMeter):
 def __init__(self,*args,**kw):
  super().__init__(*args,**kw);self.budget=PARTIAL_CAP

# Only the meter/recorder binding differs. Search, signatures, activation,
# validation and retention bodies remain the exact frozen function objects.
def bound_trial(meter):return types.FunctionType(wake_trial.__code__,{**wake_trial.__globals__,'Meter':meter},argdefs=wake_trial.__defaults__)
recorded_trial=bound_trial(RecordingMeter);partial_trial=bound_trial(PartialMeter)

def trace_consolidate(store,lib,hub,completed,boundary):
 assert completed and max(x['task']['id'] for x in completed)<=boundary
 cpu=time.process_time();wall=time.perf_counter();m=Meter(store,lib,hub,SLEEP_CAP)
 old=copy.deepcopy(store.map('knowledge.sleep')['state']);catalog=copy.deepcopy(store.map('knowledge.economics')['catalog']);model=old['model']
 schedule=copy.deepcopy(store.map('knowledge.trace_sleep').get('schedule',[]))
 pairs=m.call('sleep_pairs',{'experiences':[{'task':x['task']['id'],'context':x['row']['context']} for x in completed if x['row']['context'] is not None],'catalog':catalog,'model':schedule},'replay_selection')
 results=[];fallback_used=False
 for pair in pairs or []:
  assert pair['task']<=boundary and int(pair['entry']['name'].split('_')[-1])<=boundary
  experience=next(x for x in completed if x['task']['id']==pair['task']);row=experience['row'];baseline=experience['baseline']
  records=experience['evidence']['observations']
  evidence=m.call('trace_evidence',{'row':row,'entry':pair['entry'],'records':records},'trace_analysis')
  source='UNKNOWN';outcome=None;partial=None;full=None
  if evidence['factual']:
   outcome=row;source='trace'
  elif evidence['partial_supported']:
   ss,ll,hh=clone(store)
   try:partial=partial_trial(ss,ll,hh,experience['task'],forced=pair['entry'])
   finally:ss.close()
   m.costs['partial_replay']+=partial['graph_steps']
   # A bounded failure is censored. Only a completed audited solve proves utility.
   if partial['success'] and not partial['exhaustions']:
    outcome=partial;source='partial'
  if outcome is None and not fallback_used:
   fallback_used=True;ss,ll,hh=clone(store)
   try:full=recorded_trial(ss,ll,hh,experience['task'],forced=pair['entry'])
   finally:ss.close()
   m.costs['full_replay']+=full['graph_steps'];outcome=full;source='full'
  utility=None
  if outcome is not None:
   utility=m.call('router_utility',{'actual':{'success':outcome['success'],'cost':outcome['graph_steps']},'baseline':{'success':baseline['success'],'cost':baseline['graph_steps']}},'downstream_utility')
   assert utility is not None
   model=m.call('sleep_update',{'model':model,'context':pair['context'],'name':pair['entry']['name'],'utility':utility},'model_update');assert model is not None
  schedule=m.call('trace_note_attempt',{'schedule':schedule,'context':pair['context'],'name':pair['entry']['name']},'attempt_index');assert schedule is not None
  results.append({'pair':pair,'evidence':evidence,'source':source,'utility':utility,'partial':partial,'full':full,'outcome':outcome,'method_existed_at_wake':int(pair['entry']['name'].split('_')[-1])<experience['task']['id'],'selected_at_wake':any(a['selected'] and a['selected']['name']==pair['entry']['name'] for a in row['attempts'])})
 assert m.call('sleep_publish',{'model':model,'catalog':catalog,'boundary':boundary},'consolidation_index_persistence') is not None
 assert m.call('trace_schedule_persist',schedule,'attempt_index_persistence') is not None
 assert store.map('knowledge.economics')['catalog']==catalog
 assert m.spent<=SLEEP_CAP
 return {'boundary':boundary,'available_tasks':[x['task']['id'] for x in completed],'pairs':pairs,'results':results,'before':old,'after':copy.deepcopy(store.map('knowledge.sleep')['state']),'schedule':schedule,'costs':dict(m.costs),'graph_steps':m.spent,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'catalog':catalog}

def freeze(d):
 d=Path(d);d.mkdir(parents=True,exist_ok=True)
 if (d/'manifest.json').exists():raise ValueError('Frozen directory exists')
 parent=ROOT/'experiments/sleep-memory-results/manifest.json';old=json.loads(parent.read_text())
 for p,h in old['source_hashes'].items():assert digest(ROOT/p)==h,p
 paths=list(old['source_hashes'])+['experiments/trace_sleep.py','graph-authoring/trace-sleep.mjs','curriculum/trace-sleep.json','test_trace_sleep.py','experiments/audit_trace_sleep.py']
 dump(d/'manifest.json',{'tasks':old['tasks'],'arms':ARMS,'parent_manifest_sha256':digest(parent),'parent_report_sha256':digest(ROOT/'experiments/sleep-memory-results/report.json'),'source_hashes':{p:digest(ROOT/p) for p in paths},'partial_cap':PARTIAL_CAP,'full_fallbacks_per_sleep':1,'sleep_interval':20,'sleep_cap':SLEEP_CAP,'task_budget':450000,'search_cap':350000,'policy':'Same wake functions and routing signatures/thresholds. Record existing fair-step evaluation and frontier summaries and stored method availability; no extra semantic execution. Factual same-method single-activation completed wake outcome can directly supply utility. Otherwise an executable matching expanded candidate in stored traces permits a 75k total bounded wake-style replay. Only an audited solve without any budget exhaustion resolves that partial replay. All incomplete cases remain UNKNOWN. At most one full fallback per sleep, first unresolved pair. Attempt counts advance for UNKNOWN separately from utility statistics to preserve fair investigation. Same pair selector, interval, utility model and publication threshold. No cache-hit charge discount.','limitations':['Previously evaluated preserved 120-task sequence; architectural comparison, not fresh evaluation or generalization.','Recorded frontier/evaluation summaries are reused, not unavailable per-example program outputs. No claim of arbitrary cached-state continuation.','Factual wake utility includes actual recording cost and is not asserted numerically identical to a later forced replay.','UNKNOWN observations are not zero-utility labels and do not contribute confidence.','False negatives are measured on resolved replay/observed interventions only; UNKNOWN and unsampled pairs remain unmeasured.','Extra wake recording and sleep analysis are charged; physical serialization/clone cost appears in CPU/wall and persistent storage.','No policy tuning after evaluation.']})

def verify(d):
 m=json.loads((d/'manifest.json').read_text())
 for p,h in m['source_hashes'].items():assert digest(ROOT/p)==h,p
 assert digest(ROOT/'experiments/sleep-memory-results/report.json')==m['parent_report_sha256']
 return m

def run(d):
 d=Path(d);manifest=verify(d)
 if (d/'trials.jsonl').exists():raise ValueError('Run exists')
 engines={};setups=[];rows=[];cycles=[];completed={'full':[],'trace':[]};cpu=time.process_time();wall=time.perf_counter()
 with (d/'trials.jsonl').open('w') as out,(d/'sleeps.jsonl').open('w') as sout:
  try:
   for arm in ARMS:
    c=time.process_time();w=time.perf_counter();store,lib,hub,cost=prepare(d/f'{arm}.sqlite3');engines[arm]=(store,lib,hub)
    setups.append({'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-c,'wall_seconds':time.perf_counter()-w,'bytes':store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]})
   for task in manifest['tasks']:
    current={};offset=task['id']%3
    for arm in ARMS[offset:]+ARMS[:offset]:
     store,lib,hub=engines[arm]
     if arm=='no_memory':row=primitive_trial(store,lib,hub,task,'no_memory',{'weights':[0]*6,'updates':0})
     else:row=(wake_trial if arm=='full' else recorded_trial)(store,lib,hub,task)
     row['arm']=arm;row['bytes']=store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]
     if arm=='trace':row['evidence']=copy.deepcopy(store.map('knowledge.sleep.experiences')['trace_'+str(task['id'])])
     current[arm]=row;rows.append(row);out.write(json.dumps(row)+'\n');out.flush()
    for arm in ['full','trace']:completed[arm].append({'task':copy.deepcopy(task),'row':current[arm],'baseline':current['no_memory'],'evidence':current[arm].get('evidence')})
    if (task['id']+1)%INTERVAL==0:
     for arm in ['full','trace']:
      result=(consolidate if arm=='full' else trace_consolidate)(*engines[arm],completed[arm],task['id']);result['arm']=arm;cycles.append(result);sout.write(json.dumps(result)+'\n');sout.flush()
     print('boundary',task['id']+1,'solves',{a:sum(x['success'] for x in rows if x['arm']==a) for a in ARMS},'sleep',{a:sum(s['graph_steps'] for s in cycles if s['arm']==a) for a in ['full','trace']},flush=True)
   verify(d);dump(d/'report.json',{'manifest_sha256':digest(d/'manifest.json'),'setup':setups,'trials':rows,'sleeps':cycles,'harness_cpu_seconds':time.process_time()-cpu,'harness_wall_seconds':time.perf_counter()-wall,'final_storage':{a:st.connection.execute('PRAGMA page_count').fetchone()[0]*st.connection.execute('PRAGMA page_size').fetchone()[0] for a,(st,_,_) in engines.items()}})
  finally:
   for st,_,_ in engines.values():st.close()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('phase',choices=['freeze','run']);p.add_argument('--output',required=True);a=p.parse_args();{'freeze':freeze,'run':run}[a.phase](a.output)
