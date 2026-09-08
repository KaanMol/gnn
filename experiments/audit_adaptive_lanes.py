"""Audit adaptive memory probes, lane borrowing and unchanged task semantics."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 d=Path(directory);m=json.loads((d/'manifest.json').read_text());r=json.loads((d/'report.json').read_text())
 assert hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 parent=ROOT/'experiments/activation-search-results/manifest.json'
 assert hashlib.sha256(parent.read_bytes()).hexdigest()==m['parent_manifest_sha256']
 assert json.loads(parent.read_text())['streams']['planning']==m['streams']['planning']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==len(m['seeds'])*30*len(m['arms'])
 summary=[];stored=[];compositions=[];families=[];paired=[]
 expected={}
 for name in ['managed-memory','transfer-manager-disabled','compositional-transfer','prioritized-search','fair-search','activation-search','adaptive-lanes']:
  expected.update(json.loads((ROOT/f'curriculum/{name}.json').read_text()))
 for seed in m['seeds']:
  for arm in m['arms']:
   rr=sorted([x for x in rows if x['seed']==seed and x['arm']==arm],key=lambda x:x['task']);assert len(rr)==30
   setup=next(x for x in r['setup'] if x['seed']==seed and x['arm']==arm)
   for x in rr:
    assert sum(x['costs'].values())==x['total_graph_steps']
    assert sum(a['graph_steps'] for a in x['attempts'])<=m['budget']
    assert all(len(z['expanded'])<=5 for a in x['attempts'] for z in a['diagnostics'] if z['allowed'])
    assert all(z['queue_size']<=100 for a in x['attempts'] for z in a['diagnostics'])
    for a in x['attempts']:
     assert sum(a['costs'].values())==a['graph_steps']
     assert sum(a['lane_spent'])==a['costs'].get('execution',0)
     assert len(a['selected'])<=4
     if arm=='no_memory':assert not a['selected']
     replay=[{'id':i,'spent':0,'best':0,'gains':[],'costs':[],'stalls':0,'live':True} for i in range(len(a['lane_spent']))]
     actual_spent=[0]*len(replay)
     for e in a['events']:
      active=[z for z in replay if z['live']]
      if replay[0]['live'] and replay[0]['spent']<100000:chosen=0
      else:
       pending=[z for z in active if z['spent']<20000]
       chosen=min(pending,key=lambda z:(z['spent'],z['id']))['id'] if pending else min(active,key=lambda z:(-(sum(z['gains'])*1000000//(sum(z['costs'])+1)),z['spent'],z['id']))['id']
      assert e['lane']==chosen and e['before_stat']==replay[chosen]
      if chosen>0:assert actual_spent[0]>=100000 or not replay[0]['live']
      actual_spent[chosen]+=e['charged']
      if 'after_stat' in e:
       assert e['after_stat']['spent']==replay[chosen]['spent']+e['charged']
       replay[chosen]=e['after_stat']
     assert actual_spent==a['lane_spent']
     cursors={}
     for z in a['diagnostics']:
      key=(z['lane'],tuple(z['parent']));assert z['child_index']==cursors.get(key,0);cursors[key]=z['child_index']+1
      learned=[op for op in z['ops'] if op.startswith('allocated_')]
      if z['lane']==0:assert not learned
      else:assert all(op==a['selected'][z['lane']-1] for op in learned)
   total=sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'];solved=sum(x['success'] for x in rr)
   summary.append({'seed':seed,'arm':arm,'solved':solved,'steps':total,'steps_per_solved':total/solved if solved else None,'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'library_size':rr[-1]['library_size'],'retired':sum(not e['active'] for e in rr[-1]['catalog']),'database_growth':rr[-1]['database_bytes']-setup['database_bytes'],'mixed_successes':sum(x['success'] and x['composed_solution'] for x in rr),'mixed_attempts':sum(a['mixed_candidates_evaluated'] for x in rr for a in x['attempts']),'primitive_execution':sum(a['lane_spent'][0] if a['lane_spent'] else 0 for x in rr for a in x['attempts']),'memory_execution':sum(sum(a['lane_spent'][1:]) for x in rr for a in x['attempts']),'memory_borrow_events':sum(e['lane']>0 and e['before_stat']['spent']>=20000 for x in rr for a in x['attempts'] for e in a['events']),'primitive_borrow_events':sum(e['lane']==0 and e['before_stat']['spent']>=100000 for x in rr for a in x['attempts'] for e in a['events']),'stopped_memory_lanes':sum(sum(not z['live'] for z in a['lane_stats'][1:]) for x in rr for a in x['attempts']),'validation_rejections':sum(x['validation_rejections'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'statuses':dict(Counter(a['status'] for x in rr for a in x['attempts']))})
   for family in sorted({x['family'] for x in rr}):
    xx=[x for x in rr if x['family']==family]
    families.append({'seed':seed,'arm':arm,'family':family,'solved':sum(x['success'] for x in xx),'max_call_depth':max(a['max_call_depth'] for x in xx for a in x['attempts'])})
   store=GraphStore(d/f'planning-{seed}-{arm}.sqlite3')
   try:
    lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
    index=store.map('knowledge.activation')['index'];assert {e['name'] for e in index}=={e['name'] for e in catalog}
    for name,definition in expected.items():assert lib[name]['graph']==definition['graph'],name
    if arm=='no_memory':assert not catalog
    for entry in catalog:
     task=m['streams']['planning'][str(seed)][int(entry['name'].split('_')[-1])]
     result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'})
     assert result['accepted'],entry['name']
     stored.append({'seed':seed,'arm':arm,'name':entry['name'],'cases':len(task['audit'])})
    prior=set()
    for x in rr:
     for a in x['attempts']:assert set(a['selected']).issubset(prior)
     if x['found']:
      canonical,_=graph(lib,None,'manager_canonicalize',{'ops':x['found'],'catalog':catalog})
      assert len(canonical['ops'])<=5
      used=[op for op in x['found'] if op.startswith('allocated_')]
      assert all(op in prior for op in used)
      if x['success'] and x['composed_solution']:
       compositions.append({'seed':seed,'task':x['task'],'family':x['family'],'calls':x['found'],'expanded':canonical['ops']})
     prior={e['name'] for e in x['catalog']}
   finally:store.close()
  for task in range(30):
   a=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='memory')
   b=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='no_memory')
   if a['success']!=b['success']:paired.append({'seed':seed,'task':task,'family':a['family'],'memory_wins':a['success'],'mixed_solution':a['composed_solution'],'memory_calls':a['found'],'baseline_calls':b['found']})
 r.update(summary=summary,families=families,stored_method_audit=stored,successful_compositions=compositions,paired_differences=paired)
 (d/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Adaptive probes and borrowing','','Same four frozen planning orders; 120 task presentations per arm, 450k total search steps. Same scorer, memory manager, task examples, validation and nested charging. Up to four retrieved methods receive independent fair-search lanes alongside the primitive lane.','', '| Arm | Solved | Total graph steps | CPU seconds | Mixed successes |','|---|---:|---:|---:|---:|']
 for arm in m['arms']:
  ss=[x for x in summary if x['arm']==arm]
  lines.append(f"| {arm} | {sum(x['solved'] for x in ss)}/120 | {sum(x['steps'] for x in ss):,} | {sum(x['cpu_seconds'] for x in ss):.2f} | {sum(x['mixed_successes'] for x in ss)} |")
 lines+=['','## Per-order outcomes','','| Seed | Arm | Solved | Methods | Memory transitions beyond probe | Primitive transitions beyond floor |','|---:|---|---:|---:|---:|---:|']
 for x in summary:lines.append(f"| {x['seed']} | {x['arm']} | {x['solved']}/30 | {x['library_size']} | {x['memory_borrow_events']} | {x['primitive_borrow_events']} |")
 lines+=['','These counts require that a lane already exceeded its initial allowance before receiving another transition. They do not mistake one-transition probe overshoot for adaptive borrowing.','', '## Paired task differences','',f"Memory gained {sum(x['memory_wins'] for x in paired)} tasks and lost {sum(not x['memory_wins'] for x in paired)} against the same adaptive allocator without memory.",'', '## Audited mixed programs','']
 if not compositions:lines.append('None.')
 for x in compositions:lines.append(f"- Seed {x['seed']}, task {x['task']}: {x['calls']} → {x['expanded']}.")
 lines+=['','## Integrity','',f"Frozen source/task hashes match. All {len(stored)} retained method instances passed audit ({sum(x['cases'] for x in stored)} held-out examples). Final false positives: {sum(x['audit_false_positives'] for x in summary)}. The lane scheduler was independently replayed from event records. Selected methods predate use, primitive-floor precedence and lane vocabularies match policy, and execution/routing/total costs were checked.",'','Total costs include retrieval, routing, duplicated lane work, retention, indexing, utility and online validation/audit. Post-run diagnostic audits are separate. No permanent memory deletion or new task teaching occurred.','', '## Frozen policy','',m['policy'],'', '## Limitations','']+['- '+x for x in m['limitations']]
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'summary':summary,'paired_differences':paired,'successful_compositions':compositions},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
