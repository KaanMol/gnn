"""Frozen online stream: retain graph discoveries versus discard after each task.

Graph procedures own retrieval, validation, feedback refinement and retention.
The host schedules equal search allowances, supplies fixtures and audits outcomes.
"""
import argparse,copy,hashlib,json,random,sys,time
from collections import defaultdict
from pathlib import Path
from statistics import median
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.program_synthesis import setup
from experiments.adaptive_reuse import graph
from experiments.reuse_benchmark import BASE,search,packed

SEEDS=[1907,2909,3911]
SEARCH_BUDGET=450000
PHASE_LENGTH=20
SCHEMAS=[('numbers','synth_positive','synth_identity'),('products','synth_available','synth_price'),('readings','bench_enabled','bench_reading')]
# All targets except maximum have witnesses with <=5 original operations.
FAMILIES={
 'sum':(False,'sum',1),'count':(False,'count',1),
 'selected_sum':(True,'sum',1),'selected_count':(True,'count',1),
 'double_sum':(False,'sum',2),'negative_sum':(False,'sum',-1),
 'selected_double_sum':(True,'sum',2),'selected_negative_sum':(True,'sum',-1),
 'double_count':(False,'count',2),'selected_negative_count':(True,'count',-1),
 'selected_negative_double_sum':(True,'sum',-2),'selected_quad_sum':(True,'sum',4),
 'negative_double_sum':(False,'sum',-2),'selected_quad_count':(True,'count',4),
}

def expected(domain,family,items):
 values=items if domain=='numbers' else [x['price' if domain=='products' else 'reading'] for x in items]
 if family=='maximum':return max(values,default=0)
 selected,reducer,factor=FAMILIES[family]
 if selected:
  values=[v for v in values if v>0] if domain=='numbers' else [v for x,v in zip(items,values) if x['available' if domain=='products' else 'enabled']]
 return factor*(sum(values) if reducer=='sum' else len(values))

def make_stream(seed):
 rng=random.Random(seed);seen=set();stream=[]
 phases=[['selected_sum','selected_count','double_sum','negative_sum'],['selected_double_sum','selected_negative_sum','double_count','selected_negative_count'],['selected_negative_double_sum','selected_quad_sum','negative_double_sum','selected_quad_count']]
 for phase,novel in enumerate(phases):
  # Exactly 20 tasks per phase. Late phases explicitly mix helpful, irrelevant,
  # misleading and novel cases; labels never enter graph search or retrieval.
  slots=[('novel',f) for f in novel]*2
  old=phases[max(0,phase-1)]
  slots += [('reuse_opportunity',f) for f in old]
  slots += [('irrelevant','sum'),('irrelevant','count'),('irrelevant','maximum'),('irrelevant','maximum')]
  slots += [('misleading','sum'),('misleading','double_sum'),('misleading','count'),('misleading','sum')]
  rng.shuffle(slots)
  for role,family in slots:
   domain,predicate,projector=SCHEMAS[rng.randrange(len(SCHEMAS))]
   def examples(count,misleading=False):
    result=[]
    while len(result)<count:
     size=rng.randint(1,7)
     values=[rng.randint(1,9) if misleading else rng.randint(-8,11) for _ in range(size)]
     mask=[True if misleading else bool(rng.randrange(2)) for _ in values]
     items=packed(domain,values,mask);key=json.dumps([domain,items],sort_keys=True)
     if key in seen:continue
     seen.add(key);result.append({'input':items,'expected':expected(domain,family,items)})
    return result
   train=examples(6,role=='misleading');validation=examples(8);audit=examples(20)
   # A fixed distinguishing case ensures misleading examples are actually
   # challenged, rather than relying only on random validation sampling.
   if role=='misleading':
    items=packed(domain,[-1000-len(stream),2,4],[False,True,False])
    validation[0]={'input':items,'expected':expected(domain,family,items)}
   stream.append({'id':len(stream),'phase':phase,'role':role,'family':family,'domain':domain,'request':{'predicate':predicate,'projector':projector,'examples':train},'validation':validation,'audit':audit})
 return stream

def witness(family):
 if family=='maximum':return None
 selected,reducer,factor=FAMILIES[family]
 return (['synth_select'] if selected else [])+['synth_'+reducer]+(['bench_double']*(2 if abs(factor)==4 else 1 if abs(factor)==2 else 0))+(['bench_negate'] if factor<0 else [])

def trial(lib,hub,store,task,retain):
 cpu=time.process_time();wall=time.perf_counter();changes=store.connection.total_changes
 costs=defaultdict(int);attempts=[];failures=0;remaining=SEARCH_BUDGET
 prepared,cost=graph(lib,hub,'economy_prepare',{'base':BASE});costs['retrieval']+=cost['graph_steps'];remaining-=cost['graph_steps']
 request=copy.deepcopy(task['request']);request.update(prelude=prepared['prelude'],prefix_i=0)
 validation={'accepted':False};found=None
 for attempt in range(2):
  if remaining<=0:break
  result=search(lib,hub,request,prepared['vocabulary'],remaining,'adaptive_search_step')
  costs['search']+=result['graph_steps'];remaining-=result['graph_steps'];found=result['found']
  attempts.append(result)
  validation,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['validation'],'predicate':request['predicate'],'projector':request['projector']})
  costs['validation']+=cost['graph_steps']
  if found is None or validation['accepted']:break
  failures+=1
  if attempt==0 and remaining>0:
   refined,cost=graph(lib,hub,'economy_refine',{'examples':request['examples'],'validation':task['validation']})
   costs['feedback']+=cost['graph_steps'];remaining-=cost['graph_steps'];request['examples']=refined
 retained,cost=graph(lib,hub,'economy_retain',{'retain':retain,'validated':validation['accepted'],'ops':found,'name':'online_method_'+str(task['id']),'vocabulary':prepared['vocabulary'],'validation':{'examples':task['validation'],'accepted':validation['accepted']}})
 costs['retention']+=cost['graph_steps']
 # Audit happens after retention; its answers never reach the learner or change
 # what is stored. Wrong retained programs remain visible in the record.
 audit={'accepted':False}
 if validation['accepted']:
  audit,cost=graph(lib,hub,'economy_validate',{'ops':found,'examples':task['audit'],'predicate':request['predicate'],'projector':request['projector']})
  costs['audit']+=cost['graph_steps']
 catalog=store.map('knowledge.economics')['catalog']
 if not retain:assert catalog==[]
 pages=store.connection.execute('PRAGMA page_count').fetchone()[0];page_size=store.connection.execute('PRAGMA page_size').fetchone()[0]
 return {'task':task['id'],'phase':task['phase'],'role':task['role'],'family':task['family'],'domain':task['domain'],'found':found,'success':bool(validation['accepted'] and audit['accepted']),'validation_rejections':failures,'audit_false_positive':bool(validation['accepted'] and not audit['accepted']),'retained':retained['retained'],'library_size':len(catalog),'selected':prepared['selected'],'attempts':attempts,'costs':dict(costs),'total_graph_steps':sum(costs.values()),'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'sqlite_row_changes':store.connection.total_changes-changes,'database_bytes':pages*page_size,'catalog':[{k:r[k] for k in ['name','ops']} for r in catalog]}

def run(directory,seeds=SEEDS):
 directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
 manifest={'seeds':seeds,'search_budget_per_task':SEARCH_BUDGET,'max_depth':5,'max_attempts':2,'retrieval':'Four most recent methods form prefix probes; all retained names remain in exhaustive vocabulary. Supplied policy, no semantic routing.','cost_accounting':'Retrieval, search and feedback share the per-task search allowance. Validation, retention and audit are additionally metered and all included in cumulative cost. CPU/wall include database work; storage is reported in bytes, not converted into fictitious graph steps.','streams':{str(seed):make_stream(seed) for seed in seeds},'families':FAMILIES,'witnesses':{f:witness(f) for f in FAMILIES},'audit_policy':'Audit occurs after retention and is never learning feedback. Feedback validation is available for one retry.','limitations':['Finite supplied primitives and task families, with supplied schema adapters.','Recurrence is intentional; unfamiliar inputs and late families are not open-ended domains.','Three fixed seeds, not independent real-world datasets.','Recency policy is supplied; no autonomous routing algorithm discovery.','Library size may stay small; this cannot establish large-library scalability.','Timing on a shared machine is secondary to deterministic graph-step accounting.']}
 manifest['source_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['graph_runtime.py','graph_store.py','curriculum/program-synthesis.json','curriculum/reuse-benchmark.json','curriculum/adaptive-reuse.json','curriculum/learning-economics.json','experiments/learning_economics.py','experiments/reuse_benchmark.py']}
 frozen=json.dumps(manifest,sort_keys=True).encode();digest=hashlib.sha256(frozen).hexdigest()
 path=directory/'manifest.json'
 if path.exists():raise ValueError('Use a fresh output directory; frozen runs are not overwritten.')
 path.write_bytes(frozen);(directory/'manifest.sha256').write_text(digest+'\n')
 rows=[];setups=[]
 with (directory/'trials.jsonl').open('w') as journal:
  for seed in seeds:
   engines={}
   try:
    for arm in ['discard','retain']:
     cpu=time.process_time();wall=time.perf_counter()
     db=directory/f'{seed}-{arm}.sqlite3';store,lib,hub=setup(db)
     for filename in ['reuse-benchmark','adaptive-reuse','learning-economics']:
      lib.update(json.loads((ROOT/f'curriculum/{filename}.json').read_text()))
     _,cost=graph(lib,hub,'economy_init',None)
     base_bytes=store.connection.execute('PRAGMA page_count').fetchone()[0]*store.connection.execute('PRAGMA page_size').fetchone()[0]
     setups.append({'seed':seed,'arm':arm,'graph_steps':cost['graph_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'database_bytes':base_bytes})
     engines[arm]=(store,lib,hub)
    for task in manifest['streams'][str(seed)]:
     for arm in (['discard','retain'] if (task['id']+seed)%2 else ['retain','discard']):
      store,lib,hub=engines[arm];row=trial(lib,hub,store,task,arm=='retain')|{'seed':seed,'arm':arm}
      rows.append(row);journal.write(json.dumps(row)+'\n');journal.flush()
     if (task['id']+1)%10==0:
      totals={arm:sum(r['success'] for r in rows if r['seed']==seed and r['arm']==arm) for arm in engines}
      print('Seed',seed,'tasks',task['id']+1,'/ 60','solved',totals,flush=True)
   finally:
    for store,_,_ in engines.values():store.close()
 assert hashlib.sha256(path.read_bytes()).hexdigest()==digest
 report={'manifest_sha256':digest,'manifest_unchanged':True,'setup':setups,'trials':rows}
 (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 summarize(directory)
 return report

def summarize(directory):
 directory=Path(directory);report=json.loads((directory/'report.json').read_text());rows=report['trials'];manifest=json.loads((directory/'manifest.json').read_text());groups=[];crossings=[]
 for seed in manifest['seeds']:
  for arm in ['discard','retain']:
   selected=sorted([r for r in rows if r['seed']==seed and r['arm']==arm],key=lambda r:r['task'])
   setup=next(r for r in report['setup'] if r['seed']==seed and r['arm']==arm)
   for end in [20,40,60]:
    cumulative=selected[:end];window=selected[end-20:end];solved=sum(r['success'] for r in window)
    groups.append({'seed':seed,'arm':arm,'through_task':end,'cumulative_solved':sum(r['success'] for r in cumulative),'cumulative_steps':setup['graph_steps']+sum(r['total_graph_steps'] for r in cumulative),'cumulative_cpu_seconds':setup['cpu_seconds']+sum(r['cpu_seconds'] for r in cumulative),'cumulative_wall_seconds':setup['wall_seconds']+sum(r['wall_seconds'] for r in cumulative),'window_solved':solved,'window_steps_per_solved':sum(r['total_graph_steps'] for r in window)/solved if solved else None,'library_size':cumulative[-1]['library_size'],'database_growth_bytes':cumulative[-1]['database_bytes']-setup['database_bytes'],'validation_rejections':sum(r['validation_rejections'] for r in cumulative),'audit_false_positives':sum(r['audit_false_positive'] for r in cumulative)})
  a=sorted([r for r in rows if r['seed']==seed and r['arm']=='discard'],key=lambda r:r['task']);b=sorted([r for r in rows if r['seed']==seed and r['arm']=='retain'],key=lambda r:r['task'])
  ca=next(r['graph_steps'] for r in report['setup'] if r['seed']==seed and r['arm']=='discard')
  cb=next(r['graph_steps'] for r in report['setup'] if r['seed']==seed and r['arm']=='retain')
  sa=sb=0;eligible=[]
  for i,(x,y) in enumerate(zip(a,b),1):
   ca+=x['total_graph_steps'];cb+=y['total_graph_steps'];sa+=x['success'];sb+=y['success'];eligible.append(cb<ca and sb>=sa)
  crossing=next((i+1 for i in range(len(eligible)) if all(eligible[i:])),None)
  crossings.append({'seed':seed,'first_advantage_persisting_to_end':crossing,'definition':'Lower cumulative total graph steps and at least as many audit-passing tasks through every remaining prefix; not proof beyond this finite stream.'})
 roles=[]
 for arm in ['discard','retain']:
  for role in ['novel','reuse_opportunity','irrelevant','misleading']:
   selected=[r for r in rows if r['arm']==arm and r['role']==role]
   roles.append({'arm':arm,'role':role,'tasks':len(selected),'solved':sum(r['success'] for r in selected),'steps':sum(r['total_graph_steps'] for r in selected),'validation_rejections':sum(r['validation_rejections'] for r in selected),'audit_false_positives':sum(r['audit_false_positive'] for r in selected)})
 report.update(windows=groups,crossings=crossings,roles=roles)
 (directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 lines=['# Online learning economics','','Three frozen 60-task streams. All totals include graph retrieval, failed search, feedback, validation, retention and final audit. CPU/wall include SQLite work. Storage growth is reported separately.','', '| Seed | Through task | Arm | Cumulative solved | Cumulative steps | Last 20: steps / solved | Learned methods | DB growth bytes |','|---:|---:|---|---:|---:|---:|---:|---:|']
 for r in sorted(groups,key=lambda r:(r['seed'],r['through_task'],r['arm'])):
  unit='n/a' if r['window_steps_per_solved'] is None else f"{r['window_steps_per_solved']:,.0f}"
  lines.append(f"| {r['seed']} | {r['through_task']} | {r['arm']} | {r['cumulative_solved']} | {r['cumulative_steps']:,} | {unit} | {r['library_size']} | {r['database_growth_bytes']:,} |")
 lines+=['','## Task roles','', '| Arm | Role | Solved / tasks | Total steps | Validation rejections | Audit false positives |','|---|---|---:|---:|---:|---:|']
 for r in roles:lines.append(f"| {r['arm']} | {r['role']} | {r['solved']}/{r['tasks']} | {r['steps']:,} | {r['validation_rejections']} | {r['audit_false_positives']} |")
 lines+=['','## Sustained crossover','']+[f"- Seed {r['seed']}: {r['first_advantage_persisting_to_end'] or 'none'}." for r in crossings]
 lines+=['','A crossover requires lower cumulative total steps and at least as many solved tasks, maintained through the end of this finite stream. It does not establish future economics.','', 'The model starts without learned compositions. Validation may add feedback for one retry; audit happens after retention and never influences the library. Stored aliases of single calls and exactly repeated operation sequences are rejected. The four most recent methods receive prefix probes; all stored names remain in exhaustive search.','', '## Limitations','']+['- '+s for s in manifest['limitations']]
 (directory/'REPORT.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();run(a.output)
