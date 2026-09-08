"""Audit fixed discovery/reuse budget ratios and acquisition losses."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 d=Path(directory);m=json.loads((d/'manifest.json').read_text());r=json.loads((d/'report.json').read_text())
 assert hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 parent=ROOT/'experiments/fair-search-results/manifest.json'
 assert hashlib.sha256(parent.read_bytes()).hexdigest()==m['parent_manifest_sha256']
 from experiments.split_search import orders
 bank=ROOT/'experiments/prioritized-search-results/manifest.json'
 assert hashlib.sha256(bank.read_bytes()).hexdigest()==m['bank_manifest_sha256']
 fresh,banks=orders(json.loads(bank.read_text()))
 assert fresh==m['streams']['planning'] and banks==m['source_banks']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==len(m['seeds'])*30*len(m['conditions'])
 summary=[];stored=[];compositions=[];families=[];paired=[];plasticity=[]
 expected={}
 for name in ['managed-memory','transfer-manager-disabled','compositional-transfer','prioritized-search','fair-search','split-search']:
  expected.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
 for seed in m['seeds']:
  for percent,arm in m['conditions']:
   rr=sorted([x for x in rows if x['seed']==seed and x['arm']==arm and x['percent']==percent],key=lambda x:x['task']);assert len(rr)==30
   setup=next(x for x in r['setup'] if x['seed']==seed and x['arm']==arm and x['percent']==percent)
   for x in rr:
    assert sum(x['costs'].values())==x['total_graph_steps']
    assert sum(a['graph_steps'] for a in x['attempts'])<=m['budget']
    assert all(len(z['expanded'])<=5 for a in x['attempts'] for z in a['diagnostics'] if z['allowed'])
    assert all(z['queue_size']<=100 for a in x['attempts'] for z in a['diagnostics'])
    for attempt in x['attempts']:
     cursors={}
     assert sum(attempt['costs'].values())==attempt['graph_steps']
     for lane in ['discovery','reuse']:
      assert attempt['lane_spent'][lane]<=attempt['lane_caps'][lane]
      assert attempt['lane_spent'][lane]==sum(e['charged'] for e in attempt['lane_events'] if e['lane']==lane)
     assert sum(attempt['lane_spent'].values())+attempt['costs'].get('initialization',0)+attempt['costs'].get('scheduling',0)==attempt['graph_steps']
     if not attempt['distinct_lanes']:assert attempt['lane_spent']['reuse']==0
     for z in attempt['diagnostics']:
      key=(z['lane'],tuple(z['parent']));assert z['child_index']==cursors.get(key,0)
      cursors[key]=z['child_index']+1
      if z['lane']=='discovery':assert all(not op.startswith('allocated_') for op in z['ops'])
   total=sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'];solved=sum(x['success'] for x in rr)
   summary.append({'seed':seed,'percent':percent,'arm':arm,'solved':solved,'steps':total,'steps_per_solved':total/solved if solved else None,'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'library_size':rr[-1]['library_size'],'retired':sum(not e['active'] for e in rr[-1]['catalog']),'database_growth':rr[-1]['database_bytes']-setup['database_bytes'],'mixed_successes':sum(x['success'] and x['composed_solution'] for x in rr),'mixed_attempts':sum(a['mixed_candidates_evaluated'] for x in rr for a in x['attempts']),'near_tie_selections':sum(z['next_band_size']>1 for x in rr for a in x['attempts'] for z in a['diagnostics']),'validation_rejections':sum(x['validation_rejections'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'statuses':dict(Counter(a['status'] for x in rr for a in x['attempts']))})
   for family in sorted({x['family'] for x in rr}):
    xx=[x for x in rr if x['family']==family]
    families.append({'seed':seed,'percent':percent,'arm':arm,'family':family,'solved':sum(x['success'] for x in xx),'max_call_depth':max(a['max_call_depth'] for x in xx for a in x['attempts'])})
   store=GraphStore(d/f'planning-{seed}-{percent}-{arm}.sqlite3')
   try:
    lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
    for name,definition in expected.items():assert lib[name]['graph']==definition['graph'],name
    if arm=='no_memory':assert not catalog
    for entry in catalog:
     task=m['streams']['planning'][str(seed)][int(entry['name'].split('_')[-1])]
     result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'})
     assert result['accepted'],entry['name']
     stored.append({'seed':seed,'percent':percent,'arm':arm,'name':entry['name'],'cases':len(task['audit'])})
    prior=set();prior_entries=[]
    for x in rr:
     task=m['streams']['planning'][str(seed)][x['task']];witness=task['witness']
     known=bool(witness and any(e['ops']==witness for e in prior_entries))
     plasticity.append({'seed':seed,'percent':percent,'arm':arm,'task':x['task'],'family':x['family'],'has_prior_memory':bool(prior_entries),'target_known':known,'multi_target':bool(witness and len(witness)>1),'success':x['success'],'found_lane':next((a['found_lane'] for a in x['attempts'] if a['found'] is not None),None)})
     if x['found']:
      canonical,_=graph(lib,None,'manager_canonicalize',{'ops':x['found'],'catalog':catalog})
      assert len(canonical['ops'])<=5
      used=[op for op in x['found'] if op.startswith('allocated_')]
      assert all(op in prior for op in used)
      if x['success'] and x['composed_solution']:
       compositions.append({'seed':seed,'percent':percent,'task':x['task'],'family':x['family'],'calls':x['found'],'expanded':canonical['ops']})
     prior={e['name'] for e in x['catalog']};prior_entries=x['catalog']
   finally:store.close()
  for percent in [25,50,75]:
   for task in range(30):
    a=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='managed_memory' and x['percent']==percent)
    b=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='no_memory')
    if a['success']!=b['success']:paired.append({'seed':seed,'percent':percent,'task':task,'family':a['family'],'memory_wins':a['success'],'mixed_solution':a['composed_solution'],'memory_calls':a['found'],'baseline_calls':b['found']})
 r.update(plasticity=plasticity,summary=summary,families=families,stored_method_audit=stored,successful_compositions=compositions,paired_differences=paired)
 (d/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Fixed discovery/reuse budget sweep','','Four fresh order permutations; 120 task presentations per condition. One shared no-memory control because identical routes collapse. Splits are discovery/reuse; memory rules, scoring, fair allocation and total 450k search budget are frozen.','', '| Discovery / reuse | Solved with memory | Shared no-memory | Extra tasks | Lost tasks | Mixed successes |','|---|---:|---:|---:|---:|---:|']
 baseline=sum(x['solved'] for x in summary if x['arm']=='no_memory')
 for percent in [25,50,75]:
  ss=[x for x in summary if x['arm']=='managed_memory' and x['percent']==percent];pp=[x for x in paired if x['percent']==percent]
  lines.append(f"| {percent}/{100-percent} | {sum(x['solved'] for x in ss)}/120 | {baseline}/120 | {sum(x['memory_wins'] for x in pp)} | {sum(not x['memory_wins'] for x in pp)} | {sum(x['mixed_successes'] for x in ss)} |")
 lines+=['','## Per-order results','','| Seed | Condition | Solved | Graph steps | CPU s | Methods |','|---:|---|---:|---:|---:|---:|']
 for x in summary:lines.append(f"| {x['seed']} | {str(x['percent'])+'% discovery' if x['arm']=='managed_memory' else 'no memory'} | {x['solved']}/30 | {x['steps']:,} | {x['cpu_seconds']:.2f} | {x['library_size']} |")
 lines+=['','## Acquisition after memory exists','','A new multi-operation target here means its exact reference primitive sequence is absent from the catalog before the task. This is post-run accounting, not a semantic novelty oracle or a signal supplied to search.','', '| Discovery share | New multi-operation targets solved after prior memory | Such opportunities |','|---:|---:|---:|']
 for percent in [25,50,75]:
  pp=[x for x in plasticity if x['arm']=='managed_memory' and x['percent']==percent and x['has_prior_memory'] and x['multi_target'] and not x['target_known']]
  lines.append(f"| {percent}% | {sum(x['success'] for x in pp)} | {len(pp)} |")
 lines+=['','Opportunity denominators differ because successful acquisition removes later repetitions from the unknown-target category. Compare paired task outcomes as well.','', '## Audited mixed programs','']
 if not compositions:lines.append('None.')
 for x in compositions:lines.append(f"- {x['percent']}%, seed {x['seed']}, task {x['task']}: {x['calls']} → {x['expanded']}.")
 lines+=['','## Integrity','',f"Frozen task/source hashes and memory definitions match. All {len(stored)} retained method instances passed post-run audit ({sum(x['cases'] for x in stored)} cases). Final false positives: {sum(x['audit_false_positives'] for x in summary)}. Used methods predate their tasks. Lane caps, event charging, total search budgets, expanded length, original-only discovery and per-lane child cursors were checked.",'','Full totals include validation, utility, retention and final online audit. Shared initialization and scheduling count against total search work; lane caps are ceilings, not guaranteed delivered budgets. Repeated work across distinct lanes is charged.','', '## Policy','',m['policy'],'', '## Limitations','']+['- '+x for x in m['limitations']]
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'summary':summary,'paired_differences':paired,'successful_compositions':compositions},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
