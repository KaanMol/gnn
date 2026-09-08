"""Budget-controlled whole-solution macro reuse, with graph-owned search steps.

The host meters and schedules resumable graph search, supplies fixtures, and scores
held-out outputs. It does not construct or select candidate programs.
"""
import argparse,copy,csv,hashlib,json,math,random,sys,time
from collections import defaultdict
from pathlib import Path
from statistics import median
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import foundation
from graph_runtime import execute_graph,ExecutionCache
from experiments.program_synthesis import setup,TRAINING
BASE=['synth_sum','synth_count','synth_reverse','synth_select','bench_double','bench_negate']
BUDGET_MULTIPLIERS=[0.5,1.5,4.5]
REPEATS=2
MAX_DEPTH=5
CPU_CAP=10.0
MACRO_A='bench_learned_selected_sum'
MACRO_B='bench_learned_doubled_selected_sum'
TRAIN_B={**TRAINING,'examples':[{'input':[-3,1,4],'expected':10},{'input':[-6,2],'expected':4},{'input':[0,0],'expected':0},{'input':[-9],'expected':0}]}

def search(lib,hub,request,vocabulary,budget,step_name='bench_search_step'):
 state={**copy.deepcopy(request),'vocabulary':vocabulary,'rank':0,'depth':1,'max_depth':MAX_DEPTH,'found':None,'done':False,'evaluated':0}
 steps=0;cache=ExecutionCache();cpu=time.process_time();wall=time.perf_counter();status='exhausted_space'
 while not state['done']:
  if steps>=budget:status='step_budget';break
  if time.process_time()-cpu>=CPU_CAP:status='cpu_budget';break
  meter={}
  try:
   state,_=execute_graph(lib[step_name]['graph'],state,lib,limit=budget-steps,sensors=hub,execution_cache=cache,meter=meter)
  except ValueError:
   if not meter.get('budget_exhausted'):raise
   steps+=meter['logical_steps'];status='step_budget';break
  steps+=meter['logical_steps']
 else:status='found' if state['found'] is not None else 'exhausted_space'
 return {'status':status,'found':state['found'],'candidates_evaluated':state['evaluated'],
         'search_depth':len(state['found']) if state['found'] else state['depth'],
         'graph_steps':steps,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def promote(lib,hub,name,ops,vocabulary):
 meter={};cpu=time.process_time();wall=time.perf_counter()
 result,_=execute_graph(lib['bench_promote']['graph'],{'name':name,'ops':ops,'vocabulary':vocabulary},lib,sensors=hub,limit=1000000,meter=meter)
 return result['vocabulary'],{'graph_steps':meter['logical_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def packed(domain,values,mask):
 if domain=='numbers':return values
 if domain=='products':return [{'available':ok,'price':v} for v,ok in zip(values,mask)]
 return [{'enabled':ok,'reading':v} for v,ok in zip(values,mask)]

def oracle(domain,family,items):
 values=items if domain=='numbers' else [x['price' if domain=='products' else 'reading'] for x in items]
 chosen=[x for x in values if x>0] if domain=='numbers' else [v for x,v in zip(items,values) if x['available' if domain=='products' else 'enabled']]
 if family=='selected_sum':return sum(chosen)
 if family=='selected_double_sum':return 2*sum(chosen)
 if family=='selected_negative_double_sum':return -2*sum(chosen)
 if family=='plain_sum':return sum(values)
 if family=='selected_count':return len(chosen)
 if family=='plain_double_sum':return 2*sum(values)
 if family=='maximum_control':return max(values,default=0)
 raise AssertionError(family)

def make_tasks():
 rng=random.Random(270198)
 vectors=[([-4,2,5],[True,False,True]),([-6,-1],[True,False]),([0,4,-2],[False,True,True]),([] ,[]),([7],[True]),([-3,2],[False,True])]
 families=['selected_sum','selected_double_sum','selected_negative_double_sum','plain_sum','selected_count','plain_double_sum','maximum_control']
 tasks=[]
 for domain,predicate,projector in [('numbers','synth_positive','synth_identity'),('products','synth_available','synth_price'),('readings','bench_enabled','bench_reading')]:
  train=[packed(domain,v,m) for v,m in vectors]
  excluded={json.dumps(x,sort_keys=True) for x in train}
  if domain=='numbers':excluded.update(json.dumps(x['input'],sort_keys=True) for r in [TRAINING,TRAIN_B] for x in r['examples'])
  hidden=[]
  while len(hidden)<40:
   count=rng.randint(1,12);x=packed(domain,[rng.randint(-12,15) for _ in range(count)],[bool(rng.randrange(2)) for _ in range(count)])
   key=json.dumps(x,sort_keys=True)
   if key not in excluded:excluded.add(key);hidden.append(x)
  for family in families:
   tasks.append({'id':domain+'/'+family,'domain':domain,'family':family,'request':{'predicate':predicate,'projector':projector,'examples':[{'input':x,'expected':oracle(domain,family,x)} for x in train]},'hidden':[{'input':x,'expected':oracle(domain,family,x)} for x in hidden]})
 return tasks

def run(database,output,pilot=False):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 store,lib,hub=setup(database);lib.update(json.loads((ROOT/'curriculum/reuse-benchmark.json').read_text()))
 training=[]
 for name,request,vocab in [(MACRO_A,TRAINING,BASE),(MACRO_B,TRAIN_B,None)]:
  vocab=BASE if vocab is not None else vocabulary_a
  result=search(lib,hub,request,vocab,5000000)
  assert result['status']=='found',result
  vocabulary,promotion=promote(lib,hub,name,result['found'],vocab)
  training.append({'name':name,'request':request,**result,'promotion':promotion})
  if name==MACRO_A:vocabulary_a=vocabulary
  else:vocabulary_ab=vocabulary
  print('learned',name,result['found'],'steps',result['graph_steps'],flush=True)
 assert MACRO_A in training[1]['found'],training
 if pilot:store.close();return training
 # Calibrate from training only, before constructing/revealing evaluation tasks.
 base_budget=math.ceil(training[0]['graph_steps']/50000)*50000
 budgets=[int(base_budget*x) for x in BUDGET_MULTIPLIERS]
 frozen={k:v['graph'] for k,v in lib.items()}
 digest=hashlib.sha256(json.dumps(frozen,sort_keys=True).encode()).hexdigest()
 tasks=make_tasks()
 manifest={'frozen_library_sha256':digest,'budgets':budgets,'budget_calibration':{'source':'first training task graph steps','rounded_base':base_budget,'multipliers':BUDGET_MULTIPLIERS},'repeats':REPEATS,'max_depth':MAX_DEPTH,'cpu_cap_seconds':CPU_CAP,'training':training,'tasks':tasks,'arms':{'baseline':BASE,'reuse_a':vocabulary_a,'reuse_ab':vocabulary_ab}}
 (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 rows=[];verified={};arms=manifest['arms'];order=list(arms)
 for ti,task in enumerate(tasks):
  for budget in budgets:
   for repeat in range(REPEATS):
    # Rotate/reverse execution order to reduce systematic warmup/time bias.
    run_order=order[ti%3:]+order[:ti%3]
    if repeat:run_order=run_order[::-1]
    for arm in run_order:
     result=search(lib,hub,task['request'],arms[arm],budget)
     key=(task['id'],tuple(result['found'] or []))
     if result['found'] is not None and key not in verified:
      failures=[]
      for case in task['hidden']:
       actual,_=foundation.run(lib,'synth_execute_candidate',{'ops':result['found'],'argument':{'items':case['input'],'predicate':task['request']['predicate'],'projector':task['request']['projector']}})
       if actual!=case['expected']:failures.append({'input':case['input'],'expected':case['expected'],'actual':actual})
      verified[key]=failures
     failures=verified.get(key,[])
     row={'task':task['id'],'family':task['family'],'arm':arm,'budget':budget,'repeat':repeat,**result,'hidden_checked':len(task['hidden']) if result['found'] else 0,'hidden_failures':len(failures),'success':result['status']=='found' and not failures}
     rows.append(row)
  print('evaluated',ti+1,'/',len(tasks),task['id'],flush=True)
 assert digest==hashlib.sha256(json.dumps({k:v['graph'] for k,v in lib.items()},sort_keys=True).encode()).hexdigest()
 groups=defaultdict(list)
 for row in rows:groups[(row['arm'],row['budget'])].append(row)
 summary=[]
 for (arm,budget),group in sorted(groups.items()):
  successful=[x for x in group if x['success']]
  learned=training[:0 if arm=='baseline' else 1 if arm=='reuse_a' else 2]
  setup_steps=sum(x['graph_steps']+x['promotion']['graph_steps'] for x in learned)
  summary.append({'arm':arm,'budget':budget,'trials':len(group),'successes':len(successful),'success_rate':len(successful)/len(group),'median_graph_steps':median(x['graph_steps'] for x in group),'median_cpu_seconds':median(x['cpu_seconds'] for x in group),'median_wall_seconds':median(x['wall_seconds'] for x in group),'learning_graph_steps':setup_steps,'total_graph_steps_including_learning':sum(x['graph_steps'] for x in group)+setup_steps,'hidden_false_positives':sum(x['status']=='found' and x['hidden_failures']>0 for x in group)})
 report={'frozen_library_sha256':digest,'library_unchanged_during_evaluation':True,'model_calls':0,'tasks':len(tasks),'domains':['numbers','products','readings'],'hidden_cases_per_task':40,'training':training,'summary':summary,'trials':rows,'limitations':['Fixed six supplied primitives and two learned whole-solution macros.','Predicates/projections are supplied to all arms; domain labels do not demonstrate semantic understanding.','Graph-step budgets include candidate generation, errors and nested macro calls; validation and Python overhead appear in CPU/wall measurements.','Two repetitions estimate timing noise; correlated task families are not independent evidence of broad generality.','Macro vocabulary order is fixed and appended; ordering affects search.','Learning cost is reported separately and added once per benchmark budget cohort.','Maximum-control tasks have no general solution in this candidate language.','This is a finite, hand-designed benchmark, not open-ended capability discovery.']}
 (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 with (output/'trials.csv').open('w') as f:
  writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
 lines=['# Controlled graph reuse benchmark','',f'Frozen library: `{digest}`. No model calls. {len(tasks)} tasks, two repetitions, three equal graph-step budgets.','', '| Arm | Budget | Passed / trials | Median steps | Median CPU s | Median wall s | Learning steps |','|---|---:|---:|---:|---:|---:|---:|']
 for r in summary:lines.append(f"| {r['arm']} | {r['budget']} | {r['successes']}/{r['trials']} | {r['median_graph_steps']} | {r['median_cpu_seconds']:.4f} | {r['median_wall_seconds']:.4f} | {r['learning_graph_steps']} |")
 lines+=['','The learner produced:']+[f"- `{x['name']}`: {' → '.join(x['found'])}" for x in training]
 lines+=['','Limitations:']+['- '+x for x in report['limitations']]
 (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
 store.close()
 from experiments.analyze_reuse import analyze
 analyze(output)
 return json.loads((output/'report.json').read_text())

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--output',required=True);p.add_argument('--pilot',action='store_true');a=p.parse_args()
 result=run(a.database,a.output,a.pilot)
 if not a.pilot:print(json.dumps(result['summary'],indent=2))
