"""Post-run managed-memory accounting and independent stored-program audit."""
import argparse,hashlib,json,sys
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 directory=Path(directory);r=json.loads((directory/'report.json').read_text());m=json.loads((directory/'manifest.json').read_text())
 assert hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 assert len(r['trials'])==len(m['seeds'])*60*3
 final=[];crossovers=[];checks=[];base_library_hashes=[]
 for seed in m['seeds']:
  for arm in m['arms']:
   rows=sorted([x for x in r['trials'] if x['seed']==seed and x['arm']==arm],key=lambda x:x['task'])
   assert [x['task'] for x in rows]==list(range(60))
   s=next(x for x in r['setup'] if x['seed']==seed and x['arm']==arm)
   costs=defaultdict(int)
   for row in rows:
    assert sum(row['costs'].values())==row['total_graph_steps']
    for k,v in row['costs'].items():costs[k]+=v
   final.append({'seed':seed,'split':'fresh' if seed in m['fresh_seeds'] else 'regression','arm':arm,'solved':sum(x['success'] for x in rows),'graph_steps':sum(x['total_graph_steps'] for x in rows)+s['graph_steps'],'cpu_seconds':sum(x['cpu_seconds'] for x in rows)+s['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rows)+s['wall_seconds'],'cost_breakdown':dict(costs),'audit_false_positives':sum(x['audit_false_positive'] for x in rows),'validation_rejections':sum(x['validation_rejections'] for x in rows),'library_size':rows[-1]['library_size'],'active_methods':rows[-1].get('active_methods',0),'database_growth_bytes':rows[-1]['database_bytes']-s['database_bytes']})
  managed=sorted([x for x in r['trials'] if x['seed']==seed and x['arm']=='managed'],key=lambda x:x['task'])
  for baseline in ['discard','manager_disabled']:
   comparison=sorted([x for x in r['trials'] if x['seed']==seed and x['arm']==baseline],key=lambda x:x['task'])
   a=next(x['graph_steps'] for x in r['setup'] if x['seed']==seed and x['arm']=='managed');b=next(x['graph_steps'] for x in r['setup'] if x['seed']==seed and x['arm']==baseline);sa=sb=0;valid=[]
   for x,y in zip(managed,comparison):
    a+=x['total_graph_steps'];b+=y['total_graph_steps'];sa+=x['success'];sb+=y['success'];valid.append(a<b and sa>=sb)
   first=next((i+1 for i in range(60) if all(valid[i:])),None)
   crossovers.append({'seed':seed,'baseline':baseline,'first_cumulative_advantage_persisting_to_end':first})
  store=GraphStore(directory/f'{seed}-managed.sqlite3')
  try:
   lib=store.map('knowledge.procedures');catalog=store.map('knowledge.economics')['catalog']
   base_library_hashes.append({'seed':seed,'sha256':hashlib.sha256(json.dumps({k:v['graph'] for k,v in lib.items() if not k.startswith('managed_')},sort_keys=True).encode()).hexdigest()})
   assert len({tuple(x['ops']) for x in catalog})==len(catalog)
   for entry in catalog:
    original=next(x for x in managed if x['retained'] and 'managed_'+str(x['task'])==entry['name'])
    task=m['streams'][str(seed)][original['task']]
    # Canonical stored graph, rather than only the pre-normalization candidate,
    # must pass that task's audit. This happens after the run, not as feedback.
    result,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':task['request']['predicate'],'projector':task['request']['projector']})
    checks.append({'seed':seed,'name':entry['name'],'cases':len(task['audit']),'accepted':result['accepted'],'active':entry['active'],'wins':entry['wins'],'misses':entry['misses']})
  finally:store.close()
 assert len({x['sha256'] for x in base_library_hashes})==1,base_library_hashes
 r.update(final=final,crossovers=crossovers,stored_method_audit=checks,base_library_hashes=base_library_hashes)
 (directory/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Managed-memory findings','','All six streams and all three arms are retained. No post-run policy changes or favorable-seed selection.','', '| Split | Seed | Original discard | Manager disabled | Managed | Managed steps / original | Learned / active |','|---|---:|---:|---:|---:|---:|---:|']
 for seed in m['seeds']:
  f={x['arm']:x for x in final if x['seed']==seed};mrow=f['managed'];d=f['discard']
  lines.append(f"| {mrow['split']} | {seed} | {d['solved']}/60 | {f['manager_disabled']['solved']}/60 | {mrow['solved']}/60 | {mrow['graph_steps']/d['graph_steps']:.3f} | {mrow['library_size']}/{mrow['active_methods']} |")
 lines+=['','The ratio includes canonicalization, validation, utility updates, storage graph calls, unsuccessful probes/searches and final audit. CPU/wall and physical database growth are separately reported.','', '## Cumulative crossover','', '| Seed | Comparator | First advantage maintained to end |','|---:|---|---:|']
 for x in crossovers:lines.append(f"| {x['seed']} | {x['baseline']} | {x['first_cumulative_advantage_persisting_to_end'] or 'none'} |")
 lines+=['',f"Stored canonical graphs: {sum(x['accepted'] for x in checks)}/{len(checks)} passed independent post-run audit ({sum(x['cases'] for x in checks)} cases).",'','These tests address the fixed reduction-language memory failure. Canonicalization and scalar continuation templates are supplied domain rules; they do not generalize automatically to effects or arbitrary programming. Fresh streams change examples and order within the same generator, not the domain family.','', 'REPORT.md contains the learning windows; report.json contains all trials, cost categories, CPU/wall, storage growth, retirement state and comparison summaries.']
 (directory/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
 return final

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(audit(a.output),indent=2))
