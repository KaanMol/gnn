"""Separate calibration/evaluation for graph-owned evidence and prefix reuse.

Python provides fixtures, timing and independent output checks. It does not pick
programs or decide which learned methods survive the graph's evidence policy.
"""
import argparse,copy,hashlib,json,random,sys,time
from collections import Counter
from pathlib import Path
from statistics import median
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import foundation
from graph_runtime import execute_graph
from experiments.program_synthesis import setup,TRAINING
from experiments.reuse_benchmark import BASE,MACRO_A,MACRO_B,TRAIN_B,search,promote,make_tasks,packed,oracle

BUDGETS=[150000,450000,1350000]
REPEATS=2

def graph(lib,hub,name,arg):
 meter={};cpu=time.process_time();wall=time.perf_counter()
 result,_=execute_graph(lib[name]['graph'],arg,lib,sensors=hub,limit=10000000,meter=meter)
 return result,{'graph_steps':meter['logical_steps'],'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall}

def check(lib,task,result):
 failures=[];verification_steps=0
 if result['found'] is not None:
  for case in task['hidden']:
   actual,cost=graph(lib,None,'synth_execute_candidate',{'ops':result['found'],'argument':{'items':case['input'],'predicate':task['request']['predicate'],'projector':task['request']['projector']}})
   verification_steps+=cost['graph_steps']
   if actual!=case['expected']:failures.append({'case':case,'actual':actual})
 return result|{'success':result['status']=='found' and not failures,'hidden_failures':failures,'verification_graph_steps':verification_steps}

def tasks():
 # New fixture values, held-out from macro training, evidence calibration and the
 # earlier benchmark. Repeated families across schemas remain correlated.
 template=make_tasks();rng=random.Random(890173)
 excluded={json.dumps(c['input'],sort_keys=True) for t in template for c in t['request']['examples']+t['hidden']}
 excluded.update(json.dumps(c['input'],sort_keys=True) for r in [TRAINING,TRAIN_B] for c in r['examples'])
 for task in template:
  examples=[]
  while len(examples)<46:
   n=rng.randint(1,10);items=packed(task['domain'],[rng.randint(-14,17) for _ in range(n)],[bool(rng.randrange(2)) for _ in range(n)])
   key=json.dumps(items,sort_keys=True)
   if key in excluded:continue
   excluded.add(key);examples.append({'input':items,'expected':oracle(task['domain'],task['family'],items)})
  task['request']['examples']=examples[:6];task['hidden']=examples[6:]
 return template

def run(database,output):
 output=Path(output);output.mkdir(parents=True,exist_ok=True)
 store,lib,hub=setup(database)
 try:
  for filename in ['reuse-benchmark','adaptive-reuse']:
   lib.update(json.loads((ROOT/f'curriculum/{filename}.json').read_text()))
  training=[];vocab=BASE
  for name,request in [(MACRO_A,TRAINING),(MACRO_B,TRAIN_B)]:
   result=search(lib,hub,request,vocab,5000000)
   assert result['status']=='found',result
   vocab,cost=promote(lib,hub,name,result['found'],vocab)
   training.append({'name':name,**result,'promotion':cost})
  assert MACRO_A in training[1]['found']
  evidence=[{'name':n,'trials':0,'utility':0,'evidence':[]} for n in [MACRO_A,MACRO_B]]
  calibration=[];updates=[]
  for task in make_tasks():
   if task['domain']!='numbers' or task['family'] in ['selected_negative_double_sum','maximum_control']:continue
   baseline=check(lib,task,search(lib,hub,task['request'],BASE,450000))
   calibration.append({'task':task['id'],'arm':'baseline',**baseline})
   for i,record in enumerate(evidence):
    trial=check(lib,task,search(lib,hub,task['request'],BASE+[record['name']],450000))
    calibration.append({'task':task['id'],'arm':record['name'],**trial})
    evidence[i],cost=graph(lib,hub,'adaptive_record',{'record':record,'baseline':{'success':baseline['success'],'graph_steps':baseline['graph_steps']},'trial':{'success':trial['success'],'graph_steps':trial['graph_steps']},'budget':450000})
    updates.append(cost)
  _,cost=graph(lib,hub,'adaptive_save_evidence',evidence);updates.append(cost)
  print('Calibration evidence:',json.dumps([{k:v for k,v in r.items() if k!='evidence'} for r in evidence]),flush=True)
  evaluation=tasks()
  digest=hashlib.sha256(json.dumps({k:v['graph'] for k,v in lib.items()},sort_keys=True).encode()).hexdigest()
  arms=['baseline','fixed_ab','evidence','evidence_prefix']
  manifest={'training':training,'calibration':calibration,'evidence':evidence,'evidence_update_costs':updates,'tasks':evaluation,'budgets':BUDGETS,'repeats':REPEATS,'max_depth':5,'arms':arms,'frozen_library_sha256':digest,'policy':'Positive aggregate paired budget utility; prefix arm tests each retained macro alone and with every base operation, then exhaustive fallback. Policy is supplied, evidence and programs are learned. No target-specific ranking.'}
  (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
  rows=[];verified={}
  for ti,task in enumerate(evaluation):
   for budget in BUDGETS:
    for repeat in range(REPEATS):
     order=arms[ti%4:]+arms[:ti%4]
     if repeat:order=order[::-1]
     for arm in order:
      request=copy.deepcopy(task['request']);prep={'graph_steps':0,'cpu_seconds':0,'wall_seconds':0}
      vocabulary=BASE if arm=='baseline' else vocab;step='bench_search_step';selected=[]
      if arm.startswith('evidence'):
       prepared,prep=graph(lib,hub,'adaptive_prepare',{'base':BASE,'evidence':evidence,'extend':arm=='evidence_prefix'})
       vocabulary=prepared['vocabulary'];selected=prepared['selected']
       request.update(prelude=prepared['prelude'],prefix_i=0);step='adaptive_search_step'
      assert prep['graph_steps']<budget
      result=search(lib,hub,request,vocabulary,budget-prep['graph_steps'],step_name=step)
      for key in prep:result[key]+=prep[key]
      cachekey=(task['id'],tuple(result['found'] or []))
      if cachekey not in verified:verified[cachekey]=check(lib,task,result)['hidden_failures']
      failures=verified[cachekey]
      row={'task':task['id'],'family':task['family'],'arm':arm,'budget':budget,'repeat':repeat,**result,'selected':selected,'hidden_checked':40 if result['found'] else 0,'hidden_failures':len(failures),'success':result['status']=='found' and not failures}
      rows.append(row)
   print('Evaluated',ti+1,'/ 21',task['id'],flush=True)
  assert digest==hashlib.sha256(json.dumps({k:v['graph'] for k,v in lib.items()},sort_keys=True).encode()).hexdigest()
  learned_cost=sum(t['graph_steps']+t['promotion']['graph_steps'] for t in training)
  calibration_cost=sum(t['graph_steps']+t['verification_graph_steps'] for t in calibration)+sum(t['graph_steps'] for t in updates)
  summary=[]
  for budget in BUDGETS:
   for arm in arms:
    group=[r for r in rows if r['arm']==arm and r['budget']==budget];solved=[r for r in group if r['success']]
    overhead=0 if arm=='baseline' else learned_cost+(calibration_cost if arm.startswith('evidence') else 0)
    summary.append({'arm':arm,'budget':budget,'tasks_solved':sum(all(r['success'] for r in group if r['task']==t['id']) for t in evaluation),'median_steps_to_solution':median(r['graph_steps'] for r in solved) if solved else None,'median_candidates_to_solution':median(r['candidates_evaluated'] for r in solved) if solved else None,'search_steps_per_cohort':sum(r['graph_steps'] for r in group)/REPEATS,'steps_including_learning_and_calibration':sum(r['graph_steps'] for r in group)/REPEATS+overhead,'median_cpu_seconds':median(r['cpu_seconds'] for r in group),'median_wall_seconds':median(r['wall_seconds'] for r in group),'successful_programs':[{'task':r['task'],'ops':r['found']} for r in solved if r['repeat']==0]})
  report={'summary':summary,'trials':rows,'learning_steps':learned_cost,'calibration_steps':calibration_cost,'evidence':evidence,'library_unchanged':True,'statuses':dict(Counter(r['status'] for r in rows)),'hidden_false_positives':sum(r['hidden_failures']>0 for r in rows),'model_calls':0}
  (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  lines=['# Evidence-guided graph reuse','','All methods and search decisions execute as graph data. The search policy itself is supplied, not independently invented. Calibration uses five numeric task families; evaluation uses new inputs across three supplied schemas. The negate composition is excluded from calibration.','', '| Budget | Arm | Solved / 21 | Median steps to solution | Median candidates | Total steps including learning/calibration |','|---:|---|---:|---:|---:|---:|']
  for r in summary:lines.append(f"| {r['budget']:,} | {r['arm']} | {r['tasks_solved']} | {r['median_steps_to_solution']} | {r['median_candidates_to_solution']} | {r['steps_including_learning_and_calibration']:,.0f} |")
  lines+=['',f'Learning cost: {learned_cost:,} graph steps. Additional calibration/update cost: {calibration_cost:,}. Costs are added once per independent 21-task cohort. Trial budgets include policy preparation and all nested candidate execution. Hidden verification is outside the search budget for every arm.','', 'Limitations: global aggregate utility, not contextual understanding; hand-supplied prefix exploration; only whole-solution abstractions; correlated schemas/families; fixed ordering; two repetitions; finite generated tests. Negative controls are intentionally not generally expressible. Conditional solution medians compare different solved subsets. See report.json for every program, timing and candidate count.']
  (output/'REPORT.md').write_text('\n'.join(lines)+'\n')
  return report
 finally:store.close()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--database',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
 result=run(args.database,args.output)
 print(json.dumps([{k:v for k,v in r.items() if k!='successful_programs'} for r in result['summary']],indent=2))
