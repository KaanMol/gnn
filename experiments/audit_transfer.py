"""Post-run transfer boundary map, with no rescue or learning feedback."""
import argparse,hashlib,json,sys
from collections import defaultdict,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph

def audit(directory):
 directory=Path(directory);m=json.loads((directory/'manifest.json').read_text());r=json.loads((directory/'report.json').read_text())
 assert hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()==r['manifest_sha256']
 for p,h in m['source_hashes'].items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
 rows=r['trials'];assert len(rows)==3*2*30*4
 originals=json.loads((ROOT/'curriculum/managed-memory.json').read_text());disabled=json.loads((ROOT/'curriculum/transfer-manager-disabled.json').read_text())
 summaries=[];crossovers=[];windows=[];checks=[];compatibility=[];families=[]
 for domain in m['streams']:
  for seed in m['seeds']:
   for arm in m['arms']:
    rr=sorted([x for x in rows if x['domain']==domain and x['seed']==seed and x['arm']==arm],key=lambda x:x['task']);assert len(rr)==30
    setup=next(x for x in r['setup'] if x['domain']==domain and x['seed']==seed and x['arm']==arm)
    for x in rr:assert sum(x['costs'].values())==x['total_graph_steps']
    summaries.append({'domain':domain,'seed':seed,'arm':arm,'solved':sum(x['success'] for x in rr),'steps':sum(x['total_graph_steps'] for x in rr)+setup['graph_steps'],'cpu_seconds':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wall_seconds':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'library_size':rr[-1]['library_size'],'database_growth':rr[-1]['database_bytes']-setup['database_bytes'],'validation_rejections':sum(x['validation_rejections'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'statuses':dict(Counter(a['status'] for x in rr for a in x['attempts']))})
    for end in [10,20,30]:
     window=rr[end-10:end];solved=sum(x['success'] for x in window)
     windows.append({'domain':domain,'seed':seed,'arm':arm,'through':end,'cumulative_solved':sum(x['success'] for x in rr[:end]),'cumulative_steps':sum(x['total_graph_steps'] for x in rr[:end])+setup['graph_steps'],'last_ten_steps_per_solved':sum(x['total_graph_steps'] for x in window)/solved if solved else None})
    for family in dict.fromkeys(t['family'] for t in m['streams'][domain][str(seed)]):
     subset=[x for x in rr if x['family']==family];families.append({'domain':domain,'seed':seed,'arm':arm,'family':family,'solved':sum(x['success'] for x in subset),'tasks':len(subset)})
    store=GraphStore(directory/f'{domain}-{seed}-{arm}.sqlite3')
    try:
     lib=store.map('knowledge.procedures')
     for name,definition in originals.items():
      expected=disabled.get(name,definition) if arm in ['rules_disabled','disabled_no_memory'] else definition
      assert lib[name]['graph']==expected['graph'],(domain,seed,arm,name)
     if arm in ['exact_frozen','rules_disabled']:
      for entry in store.map('knowledge.economics')['catalog']:
       task=m['streams'][domain][str(seed)][int(entry['name'].split('_')[-1])]
       actual,_=graph(lib,None,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'})
       checks.append({'domain':domain,'seed':seed,'arm':arm,'name':entry['name'],'passed':actual['accepted'],'cases':len(task['audit'])})
     if arm=='exact_frozen':
      task=next(t for t in m['streams'][domain][str(seed)] if t['witness'] is not None and len(t['witness'])>1)
      c,_=graph(lib,None,'manager_canonicalize',{'ops':task['witness'],'catalog':[]})
      compatibility.append({'domain':domain,'seed':seed,'hardcoded_vocabulary_available':False,'example_witness':task['witness'],'canonicalizer_accepts':c['valid']})
     if arm=='discard':
      # Positive-task witnesses establish that failure is not automatically a
      # broken environment adapter. All splits checked post-run, never taught.
      for task in m['streams'][domain][str(seed)]:
       if task['witness'] is None:continue
       for case in task['request']['examples']+task['validation']+task['audit']:
        result,_=graph(lib,None,'synth_execute_candidate',{'ops':task['witness'],'argument':{'items':case['input'],'predicate':'unused','projector':'unused'}})
        assert result==case['expected'],(domain,seed,task['id'],case,result)
    finally:store.close()
   for comparator in ['discard','disabled_no_memory']:
    a=sorted([x for x in rows if x['domain']==domain and x['seed']==seed and x['arm']=='rules_disabled'],key=lambda x:x['task']);b=sorted([x for x in rows if x['domain']==domain and x['seed']==seed and x['arm']==comparator],key=lambda x:x['task'])
    ca=cb=sa=sb=0;valid=[]
    for x,y in zip(a,b):
     ca+=x['total_graph_steps'];cb+=y['total_graph_steps'];sa+=x['success'];sb+=y['success'];valid.append(ca<cb and sa>=sb)
    crossovers.append({'domain':domain,'seed':seed,'comparator':comparator,'first_advantage_maintained_to_end':next((i+1 for i in range(30) if all(valid[i:])),None)})
 boundary=[]
 for domain in m['streams']:
  totals={arm:{'solved':sum(x['solved'] for x in summaries if x['domain']==domain and x['arm']==arm),'steps':sum(x['steps'] for x in summaries if x['domain']==domain and x['arm']==arm),'cpu_seconds':sum(x['cpu_seconds'] for x in summaries if x['domain']==domain and x['arm']==arm),'audit_errors':sum(x['audit_false_positives'] for x in summaries if x['domain']==domain and x['arm']==arm)} for arm in m['arms']}
  clean=all(x['first_advantage_maintained_to_end'] is not None for x in crossovers if x['domain']==domain) and totals['rules_disabled']['audit_errors']==0
  label='cumulative compute crossover within supported subset' if clean else 'no replicated cumulative crossover'
  boundary.append({'domain':domain,'exact_frozen':'fails interface/representation: old vocabulary absent; new sequences rejected by old canonicalizer','rules_disabled':label,'totals':totals,'boundary_families':sorted({t['family'] for t in m['streams'][domain][str(m['seeds'][0])] if t['expected_boundary']})})
 r.update(summary=summaries,windows=windows,families=families,crossovers=crossovers,stored_method_audit=checks,compatibility=compatibility,boundary_map=boundary)
 (directory/'report.json').write_text(json.dumps(r,indent=2)+'\n')
 lines=['# Transfer boundary map','','The exact condition preserves the original manager and its original host vocabulary. The disabled condition changes two graph rules and binds the new vocabulary; it is explicitly not unchanged transfer. All environments and budgets were frozen before search evaluation. No rescue rules were added.','', '| Environment | Original discard | Exact frozen | Rules disabled | Disabled, no memory | Disabled steps / discard | Disabled CPU / discard |','|---|---:|---:|---:|---:|---:|---:|']
 for x in boundary:
  t=x['totals'];lines.append(f"| {x['domain']} | {t['discard']['solved']}/60 | {t['exact_frozen']['solved']}/60 | {t['rules_disabled']['solved']}/60 | {t['disabled_no_memory']['solved']}/60 | {t['rules_disabled']['steps']/t['discard']['steps']:.3f} | {t['rules_disabled']['cpu_seconds']/t['discard']['cpu_seconds']:.3f} |")
 lines+=['','## Economic crossover','', '| Environment | Seed | Comparator | First advantage lasting to task 30 |','|---|---:|---|---:|']
 for x in crossovers:lines.append(f"| {x['domain']} | {x['seed']} | {x['comparator']} | {x['first_advantage_maintained_to_end'] or 'none'} |")
 lines+=['','## Boundaries','']
 for x in boundary:lines += [f"- {x['domain']}, exact: {x['exact_frozen']}.",f"- {x['domain']}, disabled: {x['rules_disabled']}. Boundary tasks: {', '.join(x['boundary_families'])}."]
 lines+=['',f"Stored-program audits: {sum(x['passed'] for x in checks)}/{len(checks)} passed ({sum(x['cases'] for x in checks)} cases).",'','Missing-operation controls preserve an invariant no available primitive can change (digits in text, or the planning gate). Variable-shape controls require recursion/variable-length action plans that the bounded fixed-sequence search cannot express. Representable positive witnesses were verified independently after the run.','', 'Fresh computational structures still share a sequential-composition interface. Disabled mode reuses complete previously discovered programs; it does not search new hierarchical compositions through learned names. Any positive result is a transfer of bounded whole-program memory management under an explicit adapter, not a domain-agnostic engine or arbitrary-program canonicalizer.','', '## Limitations','']+['- '+x for x in m['limitations']]
 (directory/'REPORT.md').write_text('\n'.join(lines)+'\n')
 return boundary

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(audit(a.output),indent=2))
