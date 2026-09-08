"""Frozen shortcut comparison integrity and paired attribution audit."""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph
from experiments.shortcut_search import shortcut_search
from experiments.transfer_tasks import VOCABULARIES

def audit(d):
 d=Path(d);m=json.loads((d/'manifest.json').read_text());r=json.loads((d/'report.json').read_text())
 assert hashlib.sha256((d/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 parent=ROOT/'experiments/activation-search-results/manifest.json'
 assert hashlib.sha256(parent.read_bytes()).hexdigest()==m['parent_manifest_sha256']
 assert json.loads(parent.read_text())['streams']==m['streams']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==240
 summary=[];pairs=[];stored=[];attribution=[]
 for seed in m['seeds']:
  for arm in m['arms']:
   rr=sorted([x for x in rows if x['seed']==seed and x['arm']==arm],key=lambda x:x['task']);assert len(rr)==30
   prior=set()
   for x in rr:
    assert sum(x['costs'].values())==x['total_graph_steps']
    assert sum(a['graph_steps'] for a in x['attempts'])+x['costs'].get('feedback',0)<=450000
    for a in x['attempts']:
     assert sum(a['costs'].values())==a['graph_steps']
     assert set(a['selected']).issubset(prior)
     assert a['selected']==[p['name'] for p in a['probes'] if p['injected']]
     assert a['costs'].get('probing',0)<=45000
     assert len(a['probes'])<=3
     for p in a['probes']:
      assert p['name'] in prior and p['charged']<=15000
      if p['injected']:assert p['probe']['eligible'] and p['probe']['evaluation']['executable'] and len(p['expanded'])<=5
     if not a['selected']:assert a['costs'].get('injection',0)==0
     for z in a['diagnostics']:
      assert z['queue_size']<=100
      if z['allowed']:assert len(z['expanded'])<=5
      assert all(op in VOCABULARIES['planning'] or op in a['selected'] for op in z['ops'])
    prior={e['name'] for e in x['catalog']}
   setup=next(x for x in r['setup'] if x['arm']==arm and x['seed']==seed)
   summary.append({'seed':seed,'arm':arm,'solved':sum(x['success'] for x in rr),'steps':sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'],'cpu':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'mixed':sum(x['success'] and x['composed_solution'] for x in rr),'whole':sum(x['success'] and bool(x['found']) and len(x['found'])==1 and x['found'][0] not in VOCABULARIES['planning'] for x in rr),'probed':sum(len(a['probes']) for x in rr for a in x['attempts']),'injected':sum(len(a['selected']) for x in rr for a in x['attempts']),'timeouts':sum(p['probe'] is None for x in rr for a in x['attempts'] for p in a['probes']),'false_positives':sum(x['audit_false_positive'] for x in rr)})
   store=GraphStore(d/f'planning-{seed}-{arm}.sqlite3')
   try:
    lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
    for file in ['fair-search','shortcut-search']:
     for name,definition in json.loads((ROOT/f'curriculum/{file}.json').read_text()).items():assert lib[name]['graph']==definition['graph']
    for entry in catalog:
     task=m['streams']['planning'][str(seed)][int(entry['name'].split('_')[-1])]
     result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'});assert result['accepted']
     stored.append({'seed':seed,'name':entry['name'],'cases':len(task['audit'])})
    # Trace injected calls in gains against the matched no-memory arm.
    if arm=='memory':
     for x in rr:
      baseline=next(b for b in rows if b['seed']==seed and b['task']==x['task'] and b['arm']=='no_memory')
      if x['success']!=baseline['success']:
       pairs.append({'seed':seed,'task':x['task'],'family':x['family'],'memory_wins':x['success'],'calls':x['found'],'mixed':x['composed_solution']})
      if x['success'] and not baseline['success']:
       used=[op for op in x['found'] if op not in VOCABULARIES['planning']]
       assert all(op in {n for a in x['attempts'] for n in a['selected']} for op in used)
       attribution.append({'seed':seed,'task':x['task'],'direct_injected_call':bool(used),'calls':x['found'],'mixed':x['composed_solution']})
   finally:store.close()
 r.update(summary=summary,paired_differences=pairs,stored_method_audit=stored,attribution=attribution)
 (d/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Probed shortcut injection','','Previously evaluated four planning orders; 120 tasks per arm. Same frozen fair expansion, 450k search budget, exact validation and final audit.','', '| Arm | Solved | Total graph steps | CPU seconds | Mixed | Whole reuse |','|---|---:|---:|---:|---:|---:|']
 for arm in m['arms']:
  ss=[x for x in summary if x['arm']==arm];lines.append(f"| {arm} | {sum(x['solved'] for x in ss)}/120 | {sum(x['steps'] for x in ss):,} | {sum(x['cpu'] for x in ss):.2f} | {sum(x['mixed'] for x in ss)} | {sum(x['whole'] for x in ss)} |")
 lines+=['','Per-order results:']+[f"- {x['seed']} {x['arm']}: {x['solved']}/30; {x['probed']} probes, {x['injected']} injections, {x['timeouts']} probe timeouts." for x in summary]
 lines+=['',f"Paired gains: {sum(x['memory_wins'] for x in pairs)}; losses: {sum(not x['memory_wins'] for x in pairs)}.",f"Additional tasks whose successful program directly uses an injected call: {sum(x['direct_injected_call'] for x in attribution)}.",f"Final false positives: {sum(x['false_positives'] for x in summary)}. Retained methods: {len(stored)} audited on {sum(x['cases'] for x in stored)} cases.",'','Attribution is a trace plus matched-arm comparison, not a separate ablation of memory history. Pure primitive wins, if any, are not counted as directly caused by injected calls.','', 'Policy:',m['policy'],'','Limitations:']+['- '+x for x in m['limitations']]
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps({'summary':summary,'paired':pairs,'attribution':attribution},indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
