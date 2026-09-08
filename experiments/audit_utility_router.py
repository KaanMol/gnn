"""Audit frozen utility routing, held-out solves, and diagnostic interventions."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.utility_router import verify,digest,connect,dump,ARMS,SEEDS
from experiments.adaptive_reuse import graph
from experiments.transfer_tasks import VOCABULARIES

def helped(a,b):return bool(a['success'] and (not b['success'] or a['graph_steps']<b['graph_steps']))

def audit(d):
 d=Path(d);manifest=verify(d);r=json.loads((d/'report.json').read_text());frozen=json.loads((d/'model.json').read_text());model=frozen['model']
 assert r['model_sha256']==digest(d/'model.json')==(d/'model.sha256').read_text().strip()
 assert r['manifest_sha256']==digest(d/'manifest.json')==frozen['manifest_sha256']
 training=json.loads((d/'training.json').read_text());assert digest(d/'training.json')==frozen['training_sha256']
 history=training['history'];assert len(history)==model['updates']
 ss,ll,hh=connect(d/'training.sqlite3')
 try:
  current,_=graph(ll,hh,'router_zero',None)
  regression=[]
  for h in history:
   assert h['before']==current
   prediction,_=graph(ll,hh,'router_score',{'model':current,'x':h['x']});assert prediction==h['prediction']
   current,_=graph(ll,hh,'router_update',{'model':current,'x':h['x'],'utility':h['utility']});assert current==h['after']
   if not h['actual_success'] and h['baseline_success']:
    score,_=graph(ll,hh,'router_score',{'model':model,'x':h['x']})
    regression.append({'seed':h['seed'],'task':h['task'],'utility':h['utility'],'score_before':h['prediction'],'frozen_score':score,'suppressed':score<=100})
  assert current==model
 finally:ss.close()
 rows=r['trials'];assert len(rows)==360
 expected={(seed,arm,t) for seed in SEEDS for arm in ARMS for t in range(30)}
 assert {(x['seed'],x['arm'],x['task']) for x in rows}==expected
 summaries=[];prefix_checks=[];precision=[];counterfactuals=[];stored=[];pairs=[]
 for seed in SEEDS:
  baseline={x['task']:x for x in rows if x['seed']==seed and x['arm']=='no_memory'}
  for arm in ARMS:
   rr=sorted([x for x in rows if x['seed']==seed and x['arm']==arm],key=lambda x:x['task']);prior=set();act=useful=negative=0
   store,lib,hub=connect(d/f'{seed}-{arm}.sqlite3')
   try:
    expected_graphs={}
    for file in ['managed-memory','transfer-manager-disabled','compositional-transfer','prioritized-search','fair-search','activation-search','shortcut-search','utility-router']:
     expected_graphs.update(json.loads((ROOT/f'curriculum/{file}.json').read_text()))
    for name,definition in expected_graphs.items():assert lib[name]['graph']==definition['graph'],name
    for x in rr:
     assert x['graph_steps']==sum(x['costs'].values()) and x['graph_steps']<=450000
     assert not x['uncertified'];assert x['model']==model
     for a in x['attempts']:
      assert set(a['selected']).issubset(prior)
      assert a['selected']==[p['name'] for p in a['records'] if p['activated']]
      for p in a['records']:
       assert p['name'] in prior
       if p['activated']:assert p['probe']['eligible']
       if p['x'] is not None:
        assert len(p['x'])==6 and all(isinstance(v,int) and 0<=v<=1000 for v in p['x'])
        score,_=graph(lib,hub,'router_score',{'x':p['x'],'model':model});assert score==p['score']
        decision,_=graph(lib,hub,'router_decide',{'score':score,'updates':model['updates'],'ordinal':p['ordinal'],'explore':True})
        # A selected decision can fail to inject only when its graph budget ends.
        if p['activated']:assert decision['activate']
      for z in a['trace']:
       if z['allowed']:assert len(z['expanded'])<=5
       assert z['queue']<=100 and z['charged']>0
     b=baseline[x['task']];activated=[p for a in x['attempts'] for p in a['records'] if p['activated']]
     act+=len(activated);useful+=len(activated)*helped(x,b);negative+=len(activated)*bool(b['success'] and not x['success'])
     if activated:precision.append({'seed':seed,'task':x['task'],'arm':arm,'names':[p['name'] for p in activated],'helped':helped(x,b),'lost_solve':bool(b['success'] and not x['success']),'extra_cost':x['graph_steps']-b['graph_steps'],'credit':'task-level shared if multiple activations'})
     if arm!='no_memory' and x['success']!=b['success']:pairs.append({'seed':seed,'task':x['task'],'arm':arm,'gained':x['success'],'found':x['found']})
     if arm!='no_memory' and not x['attempts'][0]['selected']:
      trace=x['attempts'][0]['trace'];assert trace==b['attempts'][0]['trace'][:len(trace)],(seed,arm,x['task'])
      prefix_checks.append({'seed':seed,'task':x['task'],'arm':arm,'candidates':len(trace)})
     if x['success']:
      task=manifest['streams'][str(seed)][x['task']]
      validation,_=graph(lib,hub,'economy_validate',{'ops':x['found'],'examples':task['validation'],'predicate':'unused','projector':'unused'})
      audit_result,_=graph(lib,hub,'economy_validate',{'ops':x['found'],'examples':task['audit'],'predicate':'unused','projector':'unused'})
      assert validation['accepted'] and audit_result['accepted']
     prior={e['name'] for e in x['catalog']}
    catalog=store.map('knowledge.economics')['catalog']
    for e in catalog:
     task=manifest['streams'][str(seed)][int(e['name'].split('_')[-1])]
     answer,_=graph(lib,hub,'economy_validate',{'ops':[e['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'});assert answer['accepted']
     stored.append({'seed':seed,'arm':arm,'name':e['name'],'cases':len(task['audit'])})
   finally:store.close()
   setup=next(x for x in r['setup'] if x['seed']==seed and x['arm']==arm);solved=sum(x['success'] for x in rr);steps=sum(x['graph_steps'] for x in rr)+setup['graph_steps']
   summaries.append({'seed':seed,'arm':arm,'solved':solved,'steps':steps,'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'cost_per_solved':steps/solved if solved else None,'activations':act,'helpful_activations':useful,'activation_precision':useful/act if act else None,'negative_transfer_activations':negative,'mixed':sum(x['mixed'] for x in rr),'whole':sum(x['whole'] for x in rr),'primitive_tasks_lost':sum(baseline[x['task']]['success'] and not x['success'] for x in rr),'gained':sum(x['success'] and not baseline[x['task']]['success'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'exploration':sum(p['activated'] and p['exploration'] for x in rr for a in x['attempts'] for p in a['records'])})
 for cf in r['counterfactuals']:
  assert cf['graph_steps']==sum(cf['costs'].values())<=450000 and cf['model']==model
  baseline=next(x for x in rows if x['seed']==cf['seed'] and x['task']==cf['task'] and x['arm']=='no_memory')
  actual=next(x for x in rows if x['seed']==cf['seed'] and x['task']==cf['task'] and x['arm']=='router')
  assert cf['forced'] in {p['name'] for a in actual['attempts'] for p in a['records'] if p['probe'] and p['probe']['eligible'] and not p['activated']}
  counterfactuals.append({'seed':cf['seed'],'task':cf['task'],'name':cf['forced'],'useful_false_negative':helped(cf,baseline),'would_lose_primitive_solve':bool(baseline['success'] and not cf['success']),'actually_forced':any(p['activated'] and p['name']==cf['forced'] for a in cf['attempts'] for p in a['records'])})
 report={'summary':summaries,'activation_outcomes':precision,'counterfactual_outcomes':counterfactuals,'negative_training_regression':regression,'unchanged_primitive_prefixes':prefix_checks,'stored_method_audit':stored,'paired_differences':pairs,'training_graph_steps':training['graph_steps'],'counterfactual_graph_steps':sum(x['graph_steps'] for x in r['counterfactuals']),'counterfactual_cpu_seconds':sum(x['cpu_seconds'] for x in r['counterfactuals']),'counterfactual_wall_seconds':sum(x['wall_seconds'] for x in r['counterfactuals'])}
 dump(d/'audit.json',report)
 lines=['# Learned utility routing','','Four evaluation orders excluded from fitting; same planning generator. Model and policy frozen before evaluation.','', '| Arm | Solved | Steps | CPU / wall seconds | Cost / solved | Activations | Helpful | Lost primitive tasks | Mixed / whole |','|---|---:|---:|---:|---:|---:|---:|---:|---:|']
 for arm in ARMS:
  s=[x for x in summaries if x['arm']==arm];total=lambda k:sum(x[k] for x in s);solved=total('solved')
  lines.append(f"| {arm} | {solved}/120 | {total('steps'):,} | {total('cpu_seconds'):.2f} / {total('wall_seconds'):.2f} | {total('steps')/solved:,.0f} | {total('activations')} | {total('helpful_activations')} | {total('primitive_tasks_lost')} | {total('mixed')} / {total('whole')} |")
 lines+=['','Per-order results:']+[f"- {s['seed']} {s['arm']}: {s['solved']}/30, gained {s['gained']}, lost {s['primitive_tasks_lost']}." for s in summaries]
 lines+=['',f"Useful-memory false negatives: {sum(x['useful_false_negative'] for x in counterfactuals)} / {len(counterfactuals)} probe-positive rejected methods tested in isolated snapshots. Unfinished probes are not labeled useful or useless.",f"Historical negative-transfer regression: frozen model suppresses {sum(x['suppressed'] for x in regression)} / {len(regression)} previously harmful contexts. This is fitting-set diagnostics, not held-out evidence.",f"Unactivated primitive trace prefix checks: {len(prefix_checks)}. Retained audits: {len(stored)} methods, {sum(x['cases'] for x in stored)} cases.",f"Fitting overhead: {training['graph_steps']:,} graph steps. Diagnostic counterfactual overhead: {report['counterfactual_graph_steps']:,} graph steps. These are separate from the arm totals above.",'','See audit.json for activation precision, negative-transfer counts, exploration, model regression, paired outcomes and counterfactual details. Training history and frozen parameters are in training.json and model.json.','', 'All 450k task caps include validation, audit, retention and router persistence. A common 100k finalization allowance reduces the search cap to 350k, so raw solved counts are not directly comparable with earlier search-only-budget experiments.','', 'No evaluation outcomes updated the model. Activation credit is downstream task-level utility against the matched baseline; if multiple methods activate, this does not identify individual causal credit.']
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(report['summary'],indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
