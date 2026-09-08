"""Post-run integrity, expressibility and search-pollution analysis."""
import argparse,hashlib,json,sys
from collections import defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from graph_store import GraphStore
from experiments.adaptive_reuse import graph
from experiments.learning_economics import witness,expected

def audit(directory):
 directory=Path(directory);manifest=json.loads((directory/'manifest.json').read_text());report=json.loads((directory/'report.json').read_text())
 assert hashlib.sha256((directory/'manifest.json').read_bytes()).hexdigest()==report['manifest_sha256']
 rows=report['trials'];assert len(rows)==len(manifest['seeds'])*120
 witnesses=[];growth=[];source_changes=[];misleading_fixtures=[]
 for path,digest in manifest['source_sha256'].items():
  if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:source_changes.append(path)
 assert not source_changes,source_changes
 for seed in manifest['seeds']:
  store=GraphStore(directory/f'{seed}-discard.sqlite3')
  try:
   lib=store.map('knowledge.procedures');checked=set()
   for task in manifest['streams'][str(seed)]:
    if task['role']=='misleading':
     alternative={'sum':'selected_sum','count':'selected_count','double_sum':'selected_double_sum'}[task['family']]
     assert all(expected(task['domain'],alternative,c['input'])==c['expected'] for c in task['request']['examples'])
     assert any(expected(task['domain'],alternative,c['input'])!=c['expected'] for c in task['validation'])
     misleading_fixtures.append({'seed':seed,'task':task['id'],'plausible_wrong_family':alternative})
    key=(task['domain'],task['family']);ops=witness(task['family'])
    if ops is None or key in checked:continue
    checked.add(key);assert len(ops)<=manifest['max_depth']
    # One complete task per family/schema/seed. Post-run witnesses do not
    # contribute to discovery, retention or the claimed learning cost.
    for case in task['request']['examples']+task['validation']+task['audit']:
     value,_=graph(lib,None,'synth_execute_candidate',{'ops':ops,'argument':{'items':case['input'],'predicate':task['request']['predicate'],'projector':task['request']['projector']}})
     assert value==case['expected'],(task['id'],case,value)
    witnesses.append({'seed':seed,'domain':task['domain'],'family':task['family'],'cases':34,'ops':ops})
  finally:store.close()
  final=next(r for r in rows if r['seed']==seed and r['arm']=='retain' and r['task']==59)
  definitions={r['name']:r['ops'] for r in final['catalog']}
  def expand(ops,seen=()):
   result=[]
   for op in ops:
    if op in definitions:
     assert op not in seen,'Cyclic learned composition'
     result+=expand(definitions[op],seen+(op,))
    else:result.append(op)
   return result
  # Independent finite behavioral fingerprint, used ONLY for reporting. It is
  # not an equivalence proof and is never used to improve the frozen policy.
  store=GraphStore(directory/f'{seed}-retain.sqlite3')
  try:
   lib=store.map('knowledge.procedures');fingerprints=defaultdict(list);methods=[]
   probes=[[],[-4],[0],[2],[-4,2,5],[1,1],[-3,-2,4,9]]
   for name in ['synth_sum','synth_count']+list(definitions):
    outputs=[]
    for items in probes:
     result,_=graph(lib,None,'economy_validate',{'ops':[name],'examples':[{'input':items,'expected':None}],'predicate':'synth_positive','projector':'synth_identity'})
     execution=result['cases'][0]['execution'];outputs.append(execution)
    # Execution trace/debug data is deliberately excluded from the fingerprint.
    signature=json.dumps([{'ok':r['ok'],'result':r.get('result')} for r in outputs],sort_keys=True)
    fingerprints[signature].append(name)
    if name in definitions:methods.append({'name':name,'ops':definitions[name],'expanded_ops':expand([name])})
   duplicates=[v for v in fingerprints.values() if len(v)>1]
   growth.append({'seed':seed,'final_library_size':len(definitions),'methods':methods,'same_outputs_on_seven_numeric_probes':duplicates,'note':'Finite observational overlap only; not global equivalence or a learning signal.'})
  finally:store.close()
 actual_misleading=[{'seed':r['seed'],'task':r['task'],'first_candidate':r['attempts'][0]['found']} for r in rows if r['arm']=='retain' and r['role']=='misleading' and r['validation_rejections']>0 and any(op.startswith('online_method_') for op in (r['attempts'][0]['found'] or []))]
 audit_result={'manifest_and_sources_unchanged':True,'witness_tasks':len(witnesses),'witness_cases':sum(r['cases'] for r in witnesses),'witnesses':witnesses,'library_analysis':growth,'constructed_misleading_fixtures':misleading_fixtures,'realized_misleading_learned_candidates':actual_misleading}
 (directory/'audit.json').write_text(json.dumps(audit_result,indent=2)+'\n')
 # Aggregate the same frozen trials; never select favorable seeds or omit audit
 # failures from the denominator.
 totals=[]
 for arm in ['discard','retain']:
  selected=[r for r in rows if r['arm']==arm];setups=[r for r in report['setup'] if r['arm']==arm]
  totals.append({'arm':arm,'tasks':len(selected),'solved':sum(r['success'] for r in selected),'graph_steps':sum(r['total_graph_steps'] for r in selected)+sum(r['graph_steps'] for r in setups),'cpu_seconds':sum(r['cpu_seconds'] for r in selected)+sum(r['cpu_seconds'] for r in setups),'wall_seconds':sum(r['wall_seconds'] for r in selected)+sum(r['wall_seconds'] for r in setups),'validation_rejections':sum(r['validation_rejections'] for r in selected),'audit_false_positives':sum(r['audit_false_positive'] for r in selected),'sqlite_row_changes':sum(r['sqlite_row_changes'] for r in selected)})
 report['aggregate']=totals;(directory/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 lines=['# Long-run findings','','These are the results of the frozen policy, including unsuccessful searches and all validation/audit costs. No tuning was done after inspecting the stream.','', '| Arm | Solved / 180 | Total graph steps | Total CPU s | Validation rejections | Audit false positives |','|---|---:|---:|---:|---:|---:|']
 for r in totals:lines.append(f"| {r['arm']} | {r['solved']} | {r['graph_steps']:,} | {r['cpu_seconds']:.2f} | {r['validation_rejections']} | {r['audit_false_positives']} |")
 lines+=['','Final library sizes: '+', '.join(f"seed {r['seed']}: {r['final_library_size']}" for r in growth)+'.','',f"Post-run original-operation witnesses passed {audit_result['witness_tasks']} complete task samples / {audit_result['witness_cases']} cases. The manifest and source hashes are unchanged.",f"There are {len(misleading_fixtures)} constructed misleading fixtures: a selected-items method fits all initial examples but disagrees with validation. Actual learned candidates reaching that trap: {len(actual_misleading)}. Constructing a trap does not guarantee the learner acquires and selects the tempting method.",'','The audit.json file expands every retained composition and groups methods with matching outputs on seven numeric probes. These groups identify possible redundancy, not proven semantic equivalence. The learner never received these post-run diagnostics.','', 'See REPORT.md for cumulative and last-window costs at tasks 20, 40 and 60, task-role breakdowns and sustained crossover checks. Every search attempt, storage footprint and retained method is recorded in report.json and trials.jsonl.']
 (directory/'FINDINGS.md').write_text('\n'.join(lines)+'\n')
 return totals

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();print(json.dumps(audit(a.output),indent=2))
