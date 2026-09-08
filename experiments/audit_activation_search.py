"""Audit stored versus active memory and task-local eviction."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 d=Path(directory);m=json.loads((d/'manifest.json').read_text());r=json.loads((d/'report.json').read_text())
 assert hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 parent=ROOT/'experiments/split-search-results/manifest.json'
 assert hashlib.sha256(parent.read_bytes()).hexdigest()==m['parent_manifest_sha256']
 assert json.loads(parent.read_text())['streams']['planning']==m['streams']['planning']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==len(m['seeds'])*30*len(m['arms'])
 summary=[];stored=[];compositions=[];families=[];paired=[]
 expected={}
 for name in ['managed-memory','transfer-manager-disabled','compositional-transfer','prioritized-search','fair-search','activation-search']:
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
     if arm=='top_k':assert len(a['selected'])<=1
     if arm=='no_memory':assert not a['selected']
     if arm=='all_active':assert not a['evicted']
     if a['costs'].get('memory',0)>0:assert a['costs'].get('retrieval',0)+a['costs'].get('memory',0)+a['costs'].get('allocation',0)<=m['budget']-100000
     previous_evicted=set()
     for z in a['diagnostics']:
      if z['allowed']:assert not previous_evicted.intersection(z['ops'])
      previous_evicted=set(z['evicted'])
      if z['phase']=='primitives':assert all(not op.startswith('allocated_') for op in z['ops'])
   total=sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'];solved=sum(x['success'] for x in rr)
   summary.append({'seed':seed,'arm':arm,'solved':solved,'steps':total,'steps_per_solved':total/solved if solved else None,'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'library_size':rr[-1]['library_size'],'retired':sum(not e['active'] for e in rr[-1]['catalog']),'database_growth':rr[-1]['database_bytes']-setup['database_bytes'],'mixed_successes':sum(x['success'] and x['composed_solution'] for x in rr),'mixed_attempts':sum(a['mixed_candidates_evaluated'] for x in rr for a in x['attempts']),'evictions':sum(len(a['evicted']) for x in rr for a in x['attempts']),'retrieval_steps':sum(a['costs'].get('retrieval',0) for x in rr for a in x['attempts']),'validation_rejections':sum(x['validation_rejections'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'statuses':dict(Counter(a['status'] for x in rr for a in x['attempts']))})
   for family in sorted({x['family'] for x in rr}):
    xx=[x for x in rr if x['family']==family]
    families.append({'seed':seed,'arm':arm,'family':family,'solved':sum(x['success'] for x in xx),'max_call_depth':max(a['max_call_depth'] for x in xx for a in x['attempts'])})
   store=GraphStore(d/f'planning-{seed}-{arm}.sqlite3')
   try:
    lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
    index=store.map('knowledge.activation')['index']
    assert {e['name'] for e in index}=={e['name'] for e in catalog}
    for name,definition in expected.items():assert lib[name]['graph']==definition['graph'],name
    if arm=='no_memory':assert not catalog
    for entry in catalog:
     task=m['streams']['planning'][str(seed)][int(entry['name'].split('_')[-1])]
     metadata=next(e for e in index if e['name']==entry['name'])
     signature,_=graph(lib,None,'priority_features',entry['validation'][0])
     assert metadata['effects']==signature['features'] and metadata['length']==len(entry['ops'])
     result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'})
     assert result['accepted'],entry['name']
     stored.append({'seed':seed,'arm':arm,'name':entry['name'],'cases':len(task['audit'])})
    prior=set()
    for x in rr:
     for a in x['attempts']:
      assert set(a['selected']).issubset(prior)
      if arm=='all_active':assert set(a['selected'])==prior
     if x['found']:
      canonical,_=graph(lib,None,'manager_canonicalize',{'ops':x['found'],'catalog':catalog})
      assert len(canonical['ops'])<=5
      used=[op for op in x['found'] if op.startswith('allocated_')]
      assert all(op in prior for op in used)
      if x['success'] and x['composed_solution']:
       compositions.append({'seed':seed,'arm':arm,'task':x['task'],'family':x['family'],'calls':x['found'],'expanded':canonical['ops']})
     prior={e['name'] for e in x['catalog']}
   finally:store.close()
  for comparator in ['no_memory','all_active']:
   for task in range(30):
    a=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']=='top_k')
    b=next(x for x in rows if x['seed']==seed and x['task']==task and x['arm']==comparator)
    if a['success']!=b['success']:paired.append({'seed':seed,'task':task,'family':a['family'],'comparator':comparator,'top_k_wins':a['success'],'mixed_solution':a['composed_solution'],'top_k_calls':a['found'],'comparator_calls':b['found']})
 r.update(summary=summary,families=families,stored_method_audit=stored,successful_compositions=compositions,paired_differences=paired)
 (d/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Stored versus active memory','','Same four frozen planning orders from the stopped ratio sweep; 120 task presentations per arm. All conditions share the fair scorer/search and 450k budget. Memory treatments preserve 100k for primitive-only fallback. Top-k is top-1 retrieval plus task-local eviction; all-active keeps all retained methods active.','', '| Arm | Solved | Graph steps | CPU seconds | Mixed successes | Task-local evictions |','|---|---:|---:|---:|---:|---:|']
 for arm in m['arms']:
  ss=[x for x in summary if x['arm']==arm]
  lines.append(f"| {arm} | {sum(x['solved'] for x in ss)}/120 | {sum(x['steps'] for x in ss):,} | {sum(x['cpu_seconds'] for x in ss):.2f} | {sum(x['mixed_successes'] for x in ss)} | {sum(x['evictions'] for x in ss)} |")
 lines+=['','## Per-order results','','| Seed | Arm | Solved | Methods retained |','|---:|---|---:|---:|']
 for x in summary:lines.append(f"| {x['seed']} | {x['arm']} | {x['solved']}/30 | {x['library_size']} |")
 lines+=['','## Paired differences','']
 for comparator in ['no_memory','all_active']:
  pp=[x for x in paired if x['comparator']==comparator]
  lines.append(f"- Top-k versus {comparator}: {sum(x['top_k_wins'] for x in pp)} extra tasks, {sum(not x['top_k_wins'] for x in pp)} lost tasks.")
 lines+=['','## Audited mixed solutions','']
 if not compositions:lines.append('None.')
 for x in compositions:lines.append(f"- {x['arm']}, seed {x['seed']}, task {x['task']}: {x['calls']} → {x['expanded']}.")
 lines+=['','## Integrity','',f"Frozen hashes and retained definitions match. All {len(stored)} retained method instances passed post-run audit ({sum(x['cases'] for x in stored)} examples). Final false positives: {sum(x['audit_false_positives'] for x in summary)}. Every indexed signature matches its retained validation example, and no retained method was removed from the index. Activation uses only previously acquired methods. Top-1 bounds, eviction exclusion, original-only fallback and budget accounting were checked.",'','Totals include retrieval, search, utility updates, retention, signature indexing and final online audit, plus setup. The index is scanned linearly; this does not establish cheap retrieval at large library sizes. Global utility is used, not context-conditioned or semantic relevance.','', '## Frozen policy','',m['policy'],'', '## Limitations','']+['- '+x for x in m['limitations']]
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps({'summary':summary,'paired_differences':paired,'successful_compositions':compositions},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
