"""Summarize frozen benchmark results without rerunning or selecting search trials."""
import json,sys
from collections import defaultdict
from pathlib import Path
from statistics import mean,median

def analyze(directory):
 directory=Path(directory);path=directory/'report.json';report=json.loads(path.read_text());rows=report['trials'];training=report['training']
 groups=defaultdict(list)
 for row in rows:groups[(row['arm'],row['budget'])].append(row)
 summary=[]
 for (arm,budget),group in sorted(groups.items()):
  taskrows=defaultdict(list)
  for row in group:taskrows[row['task']].append(row)
  stable=all(len({(r['status'],tuple(r['found'] or []),r['graph_steps']) for r in results})==1 for results in taskrows.values())
  learned=training[:0 if arm=='baseline' else 1 if arm=='reuse_a' else 2]
  setup_steps=sum(x['graph_steps']+x['promotion']['graph_steps'] for x in learned)
  setup_cpu=sum(x['cpu_seconds']+x['promotion']['cpu_seconds'] for x in learned)
  setup_wall=sum(x['wall_seconds']+x['promotion']['wall_seconds'] for x in learned)
  solved=[x for x in group if x['success']]
  macro_defs={x['name']:x['found'] for x in training}
  def expanded(ops):
   return [primitive for op in ops for primitive in (expanded(macro_defs[op]) if op in macro_defs else [op])]
  direct={name:0 for name in macro_defs};nested={name:0 for name in macro_defs}
  def dependencies(ops):
   out=set()
   for op in ops:
    if op in macro_defs:out.add(op);out.update(dependencies(macro_defs[op]))
   return out
  for x in solved:
   if x['repeat']!=0:continue
   for name in direct:direct[name]+=name in x['found']
   for name in dependencies(x['found']):nested[name]+=1
  r={'arm':arm,'budget':budget,'tasks':len(taskrows),'tasks_passed_both_repeats':sum(all(x['success'] for x in results) for results in taskrows.values()),
     'repeated_search_outcomes_identical':stable,'trials':len(group),'successes':sum(x['success'] for x in group),
     'median_graph_steps':median(x['graph_steps'] for x in group),'median_cpu_seconds':median(x['cpu_seconds'] for x in group),'median_wall_seconds':median(x['wall_seconds'] for x in group),
     'median_steps_to_first_solution':median(x['graph_steps'] for x in solved) if solved else None,
     'median_candidates_to_first_solution':median(x['candidates_evaluated'] for x in solved) if solved else None,
     'median_candidates_all_trials':median(x['candidates_evaluated'] for x in group),
     'median_solution_search_depth':median(len(x['found']) for x in solved) if solved else None,
     'median_solution_expanded_primitive_length':median(len(expanded(x['found'])) for x in solved) if solved else None,
     'direct_macro_use_tasks':direct,'nested_macro_use_tasks':nested,
     'learning_graph_steps':setup_steps,'learning_cpu_seconds':setup_cpu,'learning_wall_seconds':setup_wall,
     'average_search_steps_for_21_tasks':sum(mean(x['graph_steps'] for x in results) for results in taskrows.values()),
     'average_search_cpu_for_21_tasks':sum(mean(x['cpu_seconds'] for x in results) for results in taskrows.values()),
     'average_search_wall_for_21_tasks':sum(mean(x['wall_seconds'] for x in results) for results in taskrows.values()),
     'hidden_false_positives':sum(x['status']=='found' and x['hidden_failures']>0 for x in group)}
  # Repetitions are independent replicas, not extra opportunities to amortize training.
  r['average_total_steps_for_21_tasks_including_learning']=r['average_search_steps_for_21_tasks']+setup_steps
  r['average_total_cpu_for_21_tasks_including_learning']=r['average_search_cpu_for_21_tasks']+setup_cpu
  r['average_total_wall_for_21_tasks_including_learning']=r['average_search_wall_for_21_tasks']+setup_wall
  summary.append(r)
 report['summary']=summary
 report['cost_accounting']='Average the two evaluation repetitions; add learning/promotion cost once to each 21-task evaluation cohort, not once across both repetitions.'
 report['limitations']=[x for x in report['limitations'] if not x.startswith('Learning cost is reported')]
 accounting_limit='Learning cost is included once per independent 21-task cohort; repetitions do not double amortization opportunities.'
 if accounting_limit not in report['limitations']:report['limitations'].append(accounting_limit)
 family_rows=[]
 for budget in sorted({r['budget'] for r in rows}):
  for family in dict.fromkeys(r['family'] for r in rows):
   record={'budget':budget,'family':family}
   for arm in ['baseline','reuse_a','reuse_ab']:
    selected=[r for r in rows if r['budget']==budget and r['family']==family and r['arm']==arm and r['repeat']==0]
    record[arm]={'successes':sum(r['success'] for r in selected),'tasks':len(selected),'average_steps':mean(r['graph_steps'] for r in selected),'found':[r['found'] for r in selected]}
   family_rows.append(record)
 report['families']=family_rows
 paired=[]
 for budget in sorted({r['budget'] for r in rows}):
  baseline={r['task']:r for r in rows if r['budget']==budget and r['arm']=='baseline' and r['repeat']==0 and r['success']}
  for arm in ['reuse_a','reuse_ab']:
   reuse={r['task']:r for r in rows if r['budget']==budget and r['arm']==arm and r['repeat']==0 and r['success']}
   common=sorted(set(baseline)&set(reuse))
   paired.append({'budget':budget,'arm':arm,'jointly_solved_tasks':len(common),
    'median_step_ratio_reuse_over_baseline':median(reuse[k]['graph_steps']/baseline[k]['graph_steps'] for k in common) if common else None,
    'median_cpu_ratio_reuse_over_baseline':median(reuse[k]['cpu_seconds']/baseline[k]['cpu_seconds'] for k in common) if common else None,
    'only_reuse_solved':sorted(set(reuse)-set(baseline)),'only_baseline_solved':sorted(set(baseline)-set(reuse))})
 report['paired_comparisons']=paired
 lines=['# Controlled graph reuse benchmark','',f"{report['tasks']} tasks across three supplied input schemas; two repetitions per condition. No model calls.",'',
 '| Condition | Step budget per task | Tasks passed / 21 | Median CPU s | Search steps, 21 tasks | Steps including learning |',
 '|---|---:|---:|---:|---:|---:|']
 for r in sorted(summary,key=lambda x:(x['budget'],x['arm'])):
  lines.append(f"| {r['arm']} | {r['budget']:,} | {r['tasks_passed_both_repeats']}/21 | {r['median_cpu_seconds']:.4f} | {r['average_search_steps_for_21_tasks']:,.0f} | {r['average_total_steps_for_21_tasks_including_learning']:,.0f} |")
 lines+=['','Learned on separate training tasks:']+[f"- `{x['name']}` = {' → '.join(x['found'])}; discovery cost {x['graph_steps']:,} graph steps." for x in training]
 lines+=['','The frozen library hash is `'+report['frozen_library_sha256']+'`. The baseline has the same supplied operations and adapters; only reuse conditions may select learned macros. Calls inside macros remain metered. All conditions allow depth five.','',
 '| Budget | Task family | Original only | Reuse A | Reuse A+B |','|---:|---|---:|---:|---:|']
 for r in family_rows:lines.append(f"| {r['budget']:,} | {r['family']} | {r['baseline']['successes']}/3 | {r['reuse_a']['successes']}/3 | {r['reuse_ab']['successes']}/3 |")
 lines+=['','Steps and candidates below are conditional on finding a solution; conditions may solve different task subsets. The JSON report also includes paired comparisons on jointly solved tasks.','',
 '| Condition | Budget | Median steps to solution | Median candidates to solution | Direct learned-method use |',
 '|---|---:|---:|---:|---|']
 for r in sorted(summary,key=lambda x:(x['budget'],x['arm'])):
  lines.append(f"| {r['arm']} | {r['budget']:,} | {r['median_steps_to_first_solution']} | {r['median_candidates_to_first_solution']} | {r['direct_macro_use_tasks']} |")
 lines+=['','Paired comparisons below use only tasks solved by both conditions. Ratios above 1 mean reuse cost more graph steps.','',
 '| Reuse condition | Budget | Jointly solved tasks | Median step ratio to baseline |',
 '|---|---:|---:|---:|']
 for r in paired:lines.append(f"| {r['arm']} | {r['budget']:,} | {r['jointly_solved_tasks']} | {r['median_step_ratio_reuse_over_baseline']:.3f} |")
 lines+=['','Learned-method use including nested calls (unique solved tasks):','',
 '| Condition | Budget | A including nested use | B including nested use |','|---|---:|---:|---:|']
 for r in sorted(summary,key=lambda x:(x['budget'],x['arm'])):
  counts=r['nested_macro_use_tasks']
  lines.append(f"| {r['arm']} | {r['budget']:,} | {counts[training[0]['name']]} | {counts[training[1]['name']]} |")
 witness_path=directory/'expressibility.json'
 if witness_path.exists():
  witness=json.loads(witness_path.read_text());report['expressibility_verification']=witness
  lines+=['',f"Post-search baseline witness checks passed for all {witness['tasks_passed']} non-control tasks ({witness['cases_passed']} training/held-out cases). Witnesses use at most four original operations and were never supplied to the learner. See expressibility.json."]
 lines+=['',report['cost_accounting'],'','Limitations:']+['- '+x for x in report['limitations']]
 path.write_text(json.dumps(report,indent=2)+'\n');(directory/'REPORT.md').write_text('\n'.join(lines)+'\n')
 return summary

if __name__=='__main__':print(json.dumps(analyze(sys.argv[1]),indent=2))
