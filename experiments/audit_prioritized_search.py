"""Audit frozen planning allocation with and without unchanged managed memory."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 d=Path(directory);m=json.loads((d/'manifest.json').read_text());r=json.loads((d/'report.json').read_text())
 assert hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 parent=ROOT/'experiments/compositional-transfer-results/manifest.json'
 assert hashlib.sha256(parent.read_bytes()).hexdigest()==m['parent_manifest_sha256']
 assert json.loads(parent.read_text())['streams']['planning']==m['streams']['planning']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==120
 summary=[];stored=[];compositions=[];families=[];paired=[]
 expected={}
 for name in ['managed-memory','transfer-manager-disabled','compositional-transfer','prioritized-search']:
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
   total=sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'];solved=sum(x['success'] for x in rr)
   summary.append({'seed':seed,'arm':arm,'solved':solved,'steps':total,'steps_per_solved':total/solved if solved else None,'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'library_size':rr[-1]['library_size'],'retired':sum(not e['active'] for e in rr[-1]['catalog']),'database_growth':rr[-1]['database_bytes']-setup['database_bytes'],'mixed_successes':sum(x['success'] and x['composed_solution'] for x in rr),'mixed_attempts':sum(a['mixed_candidates_evaluated'] for x in rr for a in x['attempts']),'validation_rejections':sum(x['validation_rejections'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'statuses':dict(Counter(a['status'] for x in rr for a in x['attempts']))})
   for family in sorted({x['family'] for x in rr}):
    xx=[x for x in rr if x['family']==family]
    families.append({'seed':seed,'arm':arm,'family':family,'solved':sum(x['success'] for x in xx),'max_call_depth':max(a['max_call_depth'] for x in xx for a in x['attempts'])})
   store=GraphStore(d/f'planning-{seed}-{arm}.sqlite3')
   try:
    lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
    for name,definition in expected.items():assert lib[name]['graph']==definition['graph'],name
    if arm=='no_memory':assert not catalog
    for entry in catalog:
     task=m['streams']['planning'][str(seed)][int(entry['name'].split('_')[-1])]
     result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'})
     assert result['accepted'],entry['name']
     stored.append({'seed':seed,'arm':arm,'name':entry['name'],'cases':len(task['audit'])})
    prior=set()
    for x in rr:
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
   a=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='managed_memory')
   b=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='no_memory')
   if a['success']!=b['success']:paired.append({'seed':seed,'task':task,'family':a['family'],'memory_wins':a['success'],'mixed_solution':a['composed_solution'],'memory_calls':a['found'],'baseline_calls':b['found']})
 r.update(summary=summary,families=families,stored_method_audit=stored,successful_compositions=compositions,paired_differences=paired)
 (d/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Generic prioritized search: planning only','','Frozen same 60 planning tasks, vocabulary, expanded length five and 450,000-step search budget. Memory rules unchanged. Both arms use the same new allocator, starting with no learned methods.','', '| Seed | Arm | Solved | Total graph steps | CPU seconds | Stored methods | Mixed successes |','|---:|---|---:|---:|---:|---:|---:|']
 for x in summary:lines.append(f"| {x['seed']} | {x['arm']} | {x['solved']}/30 | {x['steps']:,} | {x['cpu_seconds']:.2f} | {x['library_size']} | {x['mixed_successes']} |")
 lines+=['','## Direct paired differences','']
 if not paired:lines.append('None: both arms solved the same tasks.')
 for x in paired:lines.append(f"- Seed {x['seed']}, task {x['task']} ({x['family']}): {'memory' if x['memory_wins'] else 'no memory'} wins; memory calls: {x['memory_calls']}.")
 lines+=['','## Audited mixed programs','']
 if not compositions:lines.append('No successful solution combined a learned callable with other operations.')
 for x in compositions:lines.append(f"- Seed {x['seed']}, task {x['task']} ({x['family']}): {x['calls']} → {x['expanded']}.")
 lines+=['','## Family diagnostics','','| Seed | Arm | Family | Solved / 5 | Maximum evaluated call depth |','|---:|---|---|---:|---:|']
 for x in families:lines.append(f"| {x['seed']} | {x['arm']} | {x['family']} | {x['solved']}/5 | {x['max_call_depth']} |")
 lines+=['','## Integrity','',f"Task/source hashes and frozen memory definitions match. All {len(stored)} stored methods passed post-run audit ({sum(x['cases'] for x in stored)} cases). Final audit false positives: {sum(x['audit_false_positives'] for x in summary)}. Every used method predates its task. Evaluated expansions satisfy the length limit; search budgets and queue bounds were checked.",'','Logical totals include search scoring, queue work, validation, utility, retention and final audit. CPU/wall include host/storage overhead and setup; post-run diagnostic audits are separate.','', '## Frozen policy','',m['policy'],'', '## Limits','']+['- '+x for x in m['limitations']]
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'summary':summary,'paired_differences':paired,'successful_compositions':compositions},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
