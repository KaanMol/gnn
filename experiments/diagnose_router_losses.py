"""Post-run diagnosis requested during evaluation; never changes its policy."""
import argparse,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.utility_router import connect,clone,Meter,search,verify,digest,dump,SEARCH_CAP
from experiments.transfer_tasks import VOCABULARIES
CONSULT=['retrieval','probing','router_features','router_inference','router_decision']

def diagnose(d):
 d=Path(d);manifest=verify(d);report=json.loads((d/'report.json').read_text());model=json.loads((d/'model.json').read_text())['model'];frozen=digest(d/'model.json');rows=report['trials'];table=[];diagnostics=[]
 for row in rows:
  if row['arm']!='router':continue
  baseline=next(b for b in rows if b['arm']=='no_memory' and (b['seed'],b['task'])==(row['seed'],row['task']))
  records=[p for a in row['attempts'] for p in a['records']];activated=any(p['activated'] for p in records);consult=sum(row['costs'].get(k,0) for k in CONSULT)
  decisions=[]
  for p in records:
   decisions.append({'name':p['name'],'decision':'activate' if p['activated'] else 'probe_timeout' if p['probe'] is None else 'probe_reject' if not p['probe']['eligible'] else 'router_reject','score':p['score'],'exploration':p['exploration']})
  primitive=[z for a in row['attempts'] for z in a['trace'] if z['allowed'] and all(op in VOCABULARIES['planning'] for op in z['ops'])]
  depth=max((len(z['expanded']) for z in primitive),default=0)
  candidate_prefix=False
  if not activated and row['attempts']:
   aa=row['attempts'][0]['trace'];bb=baseline['attempts'][0]['trace'];candidate_prefix=aa==bb[:len(aa)];assert candidate_prefix
  reason='joint_failure' if not baseline['success'] and not row['success'] else 'gained_solve' if row['success'] and not baseline['success'] else 'solve_with_activation' if activated else 'true_neutral_rejection' if records else 'no_memory_considered'
  cf_solved=None
  if baseline['success'] and not row['success']:
   # Replay primitive discovery while imposing exactly the measured consultation
   # charge. The imposed amount is NOT diagnostic execution; report it separately.
   store,_,_=connect(d/f"{row['seed']}-router.sqlite3");ss,ll,hh=clone(store);store.close();m=Meter(ss,ll,hh);m.costs['imposed_consultation']=consult
   task=manifest['streams'][str(row['seed'])][row['task']];request=task['request'];attempts=[];cpu=time.process_time();wall=time.perf_counter();cf_solved=False
   try:
    for i in range(2):
     if m.spent>=SEARCH_CAP:break
     a=search(m,request,'no_memory',model,0);attempts.append(a)
     v=m.call('economy_validate',{'ops':a['found'],'examples':task['validation'],'predicate':'unused','projector':'unused'},'validation')
     if v and v['accepted']:
      audit=m.call('economy_validate',{'ops':a['found'],'examples':task['audit'],'predicate':'unused','projector':'unused'},'audit');cf_solved=bool(audit and audit['accepted']);break
     if a['found'] is None or i==1:break
     refined=m.call('economy_refine',{'examples':request['examples'],'validation':task['validation']},'feedback',SEARCH_CAP)
     if refined is None:break
     request={**request,'examples':refined}
    if not activated:
     assert attempts[0]['trace']==row['attempts'][0]['trace']
     assert not cf_solved
     reason='decision_cost_loss'
    elif cf_solved:reason='activation_loss'
    else:reason='decision_cost_sufficient_with_activation'
    diagnostics.append({'seed':row['seed'],'task':row['task'],'imposed_consultation':consult,'executed_graph_steps':m.spent-consult,'total_simulated_cost':m.spent,'cpu_seconds':time.process_time()-cpu,'wall_seconds':time.perf_counter()-wall,'solved':cf_solved,'attempts':attempts})
   finally:ss.close()
  table.append({'seed':row['seed'],'task':row['task'],'family_for_reporting_only':row['family'],'baseline_solved':baseline['success'],'decisions':decisions,'probe_steps':row['costs'].get('probing',0),'retrieval_steps':row['costs'].get('retrieval',0),'feature_steps':row['costs'].get('router_features',0),'inference_steps':row['costs'].get('router_inference',0),'decision_steps':row['costs'].get('router_decision',0),'total_consultation_steps':consult,'activated':activated,'primitive_depth':depth,'primitive_candidates':len(primitive),'baseline_primitive_depth':max((len(z['expanded']) for a in baseline['attempts'] for z in a['trace'] if z['allowed']),default=0),'final_solved':row['success'],'reason':reason,'primitive_prefix_unchanged':candidate_prefix,'paid_consultation_primitive_counterfactual_solved':cf_solved})
 assert digest(d/'model.json')==frozen
 from collections import Counter
 counts=dict(Counter(x['reason'] for x in table))
 dump(d/'loss-diagnosis.json',{'counts':counts,'tasks':table,'counterfactuals':diagnostics,'diagnostic_execution_steps':sum(x['executed_graph_steps'] for x in diagnostics),'note':'Diagnostic added after policy freeze at user request. No model/policy changes. Method and family strings appear only in reporting, never model features.'})
 lines=['# Per-task routing diagnosis','','A failed activated task is called an activation loss only if primitive search still solves after paying the same measured consultation cost. Otherwise consultation cost alone is sufficient; an additional activation effect is not identified. Rejected-memory losses have both exact trace-prefix and residual-budget replay checks.','',str(counts),'', '| Seed / task | Baseline solved | Decision | Probe | Features / inference / decision | Activated | Primitive depth | Final solved | Diagnosis |','|---|---|---|---:|---:|---|---:|---|---|']
 for x in table:
  ds=', '.join(p['decision'] for p in x['decisions']) or 'none'
  lines.append(f"| {x['seed']} / {x['task']} | {x['baseline_solved']} | {ds} | {x['probe_steps']:,} | {x['feature_steps']:,} / {x['inference_steps']:,} / {x['decision_steps']:,} | {x['activated']} | {x['primitive_depth']} | {x['final_solved']} | {x['reason']} |")
 lines+=['','Primitive depth is the maximum expanded length among executable primitive-only candidate attempts; equal depth does not imply the same candidates or amount of search.','', 'True neutral rejection means both arms audited-solved with no activation; it does not claim zero computational overhead.']
 (d/'LOSS_DIAGNOSIS.md').write_text('\n'.join(lines)+'\n');print(counts)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();diagnose(a.output)
