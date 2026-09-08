"""Independent reporting of the frozen generic composition follow-up."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 d=Path(directory);m=json.loads((d/'manifest.json').read_text());r=json.loads((d/'report.json').read_text())
 assert hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 parent=ROOT/'experiments/transfer-results/manifest.json'
 assert hashlib.sha256(parent.read_bytes()).hexdigest()==m['parent_manifest_sha256']
 assert json.loads(parent.read_text())['streams']==m['streams']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==540
 summaries=[];checks=[];compositions=[];families=[];crossovers=[]
 expected=json.loads((ROOT/'curriculum/managed-memory.json').read_text())|json.loads((ROOT/'curriculum/transfer-manager-disabled.json').read_text())|json.loads((ROOT/'curriculum/compositional-transfer.json').read_text())
 for domain in m['streams']:
  for seed in m['seeds']:
   for arm in m['arms']:
    rr=sorted([x for x in rows if x['domain']==domain and x['seed']==seed and x['arm']==arm],key=lambda x:x['task']);assert len(rr)==30
    setup=next(x for x in r['setup'] if x['domain']==domain and x['seed']==seed and x['arm']==arm)
    for x in rr:assert sum(x['costs'].values())==x['total_graph_steps']
    summaries.append({'domain':domain,'seed':seed,'arm':arm,'solved':sum(x['success'] for x in rr),'steps':sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'],'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'library_size':rr[-1]['library_size'],'retired':sum(not x['active'] for x in rr[-1]['catalog']),'database_growth':rr[-1]['database_bytes']-setup['database_bytes'],'mixed_successes':sum(x['success'] and x['composed_solution'] for x in rr),'mixed_attempts':sum(a['mixed_candidates_evaluated'] for x in rr for a in x['attempts']),'overlength_rejections':sum(a['overlength_rejections'] for x in rr for a in x['attempts']),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'statuses':dict(Counter(a['status'] for x in rr for a in x['attempts']))})
    for family in dict.fromkeys(t['family'] for t in m['streams'][domain][str(seed)]):
     subset=[x for x in rr if x['family']==family];families.append({'domain':domain,'seed':seed,'arm':arm,'family':family,'solved':sum(x['success'] for x in subset),'tasks':len(subset)})
    store=GraphStore(d/f'{domain}-{seed}-{arm}.sqlite3')
    try:
     lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
     for name,definition in expected.items():assert lib[name]['graph']==definition['graph'],name
     for entry in catalog:
      t=m['streams'][domain][str(seed)][int(entry['name'].split('_')[-1])]
      result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':t['audit'],'predicate':'unused','projector':'unused'})
      assert result['accepted'],entry['name']
      checks.append({'domain':domain,'seed':seed,'arm':arm,'name':entry['name'],'cases':len(t['audit']),'passed':True})
     prior=set()
     for x in rr:
      if x['found']:
       c,_=graph(lib,None,'manager_canonicalize',{'ops':x['found'],'catalog':catalog})
       assert len(c['ops'])<=m['max_depth']
       used=[op for op in x['found'] if op.startswith('composed_')]
       assert all(op in prior for op in used),(x['task'],used,prior)
       if x['success'] and x['composed_solution']:
        compositions.append({'domain':domain,'seed':seed,'arm':arm,'task':x['task'],'family':x['family'],'calls':x['found'],'expanded':c['ops']})
      prior={e['name'] for e in x['catalog']}
    finally:store.close()
   for comparator in ['no_memory','whole_program']:
    a=sorted([x for x in rows if x['domain']==domain and x['seed']==seed and x['arm']=='compositional'],key=lambda x:x['task'])
    b=sorted([x for x in rows if x['domain']==domain and x['seed']==seed and x['arm']==comparator],key=lambda x:x['task'])
    for metric in ['total_graph_steps','cpu_seconds']:
     key='graph_steps' if metric=='total_graph_steps' else metric
     ca=next(x[key] for x in r['setup'] if x['domain']==domain and x['seed']==seed and x['arm']=='compositional')
     cb=next(x[key] for x in r['setup'] if x['domain']==domain and x['seed']==seed and x['arm']==comparator)
     sa=sb=0;valid=[]
     for x,y in zip(a,b):
      ca+=x[metric];cb+=y[metric];sa+=x['success'];sb+=y['success'];valid.append(ca<cb and sa>=sb)
     crossovers.append({'domain':domain,'seed':seed,'comparator':comparator,'metric':metric,'first_advantage_maintained_to_end':next((i+1 for i in range(30) if all(valid[i:])),None)})
 r.update(summary=summaries,families=families,stored_method_audit=checks,successful_compositions=compositions,crossovers=crossovers)
 (d/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Generic compositional reuse: frozen follow-up','','Same previously evaluated text/tree/planning tasks; 450,000 search graph steps, expanded length at most five, empty initial learned libraries. All three conditions use the same expanded-length guard. This is an architectural follow-up, not a fresh held-out confirmation.','', '| Environment | No memory | Whole-program | Compositional | Successful mixed programs | Composition steps / no memory | Composition CPU / no memory |','|---|---:|---:|---:|---:|---:|---:|']
 for domain in m['streams']:
  totals={a:{k:sum(x[k] for x in summaries if x['domain']==domain and x['arm']==a) for k in ['solved','steps','cpu_seconds','mixed_successes','library_size']} for a in m['arms']}
  n,w,c=[totals[a] for a in m['arms']]
  lines.append(f"| {domain} | {n['solved']}/60 | {w['solved']}/60 | {c['solved']}/60 | {c['mixed_successes']} | {c['steps']/n['steps']:.3f} | {c['cpu_seconds']/n['cpu_seconds']:.3f} |")
 lines+=['','## Per-stream diagnostics','','| Environment | Seed | Arm | Solved | Methods | Mixed candidates evaluated | Over-length rejected |','|---|---:|---|---:|---:|---:|---:|']
 for x in summaries:lines.append(f"| {x['domain']} | {x['seed']} | {x['arm']} | {x['solved']}/30 | {x['library_size']} | {x['mixed_attempts']} | {x['overlength_rejections']} |")
 lines+=['','## Successful compositions','']
 if not compositions:lines.append('None. Generic composability was implemented and exercised, but this run did not produce an audited mixed-program solution.')
 for x in compositions:lines.append(f"- {x['domain']} seed {x['seed']} task {x['task']}: {x['calls']} → {x['expanded']}")
 lines+=['','## Integrity and interpretation','',f"Frozen source and task hashes match. All {len(checks)} stored-method audits passed ({sum(x['cases'] for x in checks)} examples). Final false positives: {sum(x['audit_false_positives'] for x in summaries)}.",'','If text/tree acquire no multi-operation methods, their outcomes remain acquisition/search failures, not evidence against compositional transfer. A tie in planning shows this particular generic composition/search policy was insufficient at this budget; it does not establish impossibility, necessity, or a unique cause. Generic composition mechanics were tested with isolated fixtures, never seeded into benchmark libraries.','', 'The previous study used a different candidate evaluator without the new expanded-length guard. Its historical 30/60 planning result is context; the primary causal comparisons are the freshly rerun matched controls here.','', '## Limitations','']+['- '+x for x in m['limitations']]
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n')
 print(json.dumps(summaries,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
