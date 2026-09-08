"""Frozen sleep experiment integrity and lifetime economics."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.sleep_memory import verify,ARMS,INTERVAL,SLEEP_CAP
from experiments.utility_router import connect,dump,digest
from experiments.adaptive_reuse import graph

def helped(x,b):return bool(x['success'] and (not b['success'] or x['graph_steps']<b['graph_steps']))
def audit(d):
 d=Path(d);m=verify(d);r=json.loads((d/'report.json').read_text());assert r['manifest_sha256']==digest(d/'manifest.json')
 rows=r['trials'];sleeps=r['sleeps'];assert len(rows)==360 and len(sleeps)==6
 assert {(x['task'],x['arm']) for x in rows}=={(i,a) for i in range(120) for a in ARMS}
 baseline={x['task']:x for x in rows if x['arm']=='no_memory'};wake={x['task']:x for x in rows if x['arm']=='sleep'}
 ss,ll,hh=connect(d/'sleep.sqlite3');replayed=[];model=[]
 try:
  for cycle in sleeps:
   boundary=cycle['boundary'];assert cycle['available_tasks']==list(range(boundary+1));assert (boundary+1)%INTERVAL==0
   assert cycle['before']['model']==model and cycle['graph_steps']==sum(cycle['costs'].values())<=SLEEP_CAP
   assert len(cycle['results'])<=6
   for result in cycle['results']:
    pair=result['pair'];assert pair['task']<=boundary and int(pair['entry']['name'].split('_')[-1])<=boundary
    replay=result['replay'];assert replay['graph_steps']==sum(replay['costs'].values())<=450000
    b=baseline[pair['task']]
    utility,_=graph(ll,hh,'router_utility',{'actual':{'success':replay['success'],'cost':replay['graph_steps']},'baseline':{'success':b['success'],'cost':b['graph_steps']}});assert utility==result['utility']
    model,_=graph(ll,hh,'sleep_update',{'model':model,'context':pair['context'],'name':pair['entry']['name'],'utility':utility})
    replayed.append({'boundary':boundary,'task':pair['task'],'name':pair['entry']['name'],'utility':utility,'useful_false_negative':bool(result['method_existed_at_wake'] and not result['selected_at_wake'] and helped(replay,b)),'false_negative_measurable':result['method_existed_at_wake'] and not result['selected_at_wake']})
   assert model==cycle['after']['model'];assert cycle['after']['boundary']==boundary
   for key,entry in cycle['after']['table'].items():
    stats=next(x for x in model if x['context']==key and x['name']==entry['name'])
    assert stats['positive']>=2 and stats['lost']==0 and stats['total']>50*stats['count']
    assert entry in cycle['catalog']
  assert ss.map('knowledge.sleep')['state']==sleeps[-1]['after']
 finally:ss.close()
 summary=[];prefix=[];decisions=[];audited=[];pairs=[]
 for arm in ARMS:
  rr=sorted([x for x in rows if x['arm']==arm],key=lambda x:x['task']);prior=set();store,lib,hub=connect(d/f'{arm}.sqlite3')
  try:
   expected={}
   for file in ['managed-memory','transfer-manager-disabled','compositional-transfer','prioritized-search','fair-search','activation-search','shortcut-search','utility-router','sleep-memory']:expected.update(json.loads((ROOT/f'curriculum/{file}.json').read_text()))
   for name,definition in expected.items():assert lib[name]['graph']==definition['graph'],name
   for x in rr:
    assert x['graph_steps']==sum(x['costs'].values())<=450000 and not x['uncertified']
    activated=[]
    for a in x['attempts']:
     for z in a['trace']:
      if z['allowed']:assert len(z['expanded'])<=5
      assert z['queue']<=100
     if arm=='sleep':
      route=a['route'];assert route is not None and route['boundary']==(x['task']//20)*20-1
      if a['selected']:
       assert a['selected']['name'] in prior;assert int(a['selected']['name'].split('_')[-1])<=route['boundary']
       activated.append(a['selected']['name'])
      assert 'probing' not in x['costs'] and 'router_features' not in x['costs']
     elif arm=='online':activated += [p['name'] for p in a['records'] if p['activated']]
    assert set(activated).issubset(prior)
    b=baseline[x['task']]
    if arm=='sleep':
     decisions.append({'task':x['task'],'context':x['context'],'names':activated,'lookup_steps':x['costs'].get('wake_lookup',0),'helped':bool(activated and helped(x,b)),'negative_transfer':bool(activated and b['success'] and not x['success']),'lost_after_rejection':bool(not activated and b['success'] and not x['success'])})
     if not activated:
      a=x['attempts'][0]['trace'];assert a==b['attempts'][0]['trace'][:len(a)];prefix.append(x['task'])
    if arm!='no_memory' and x['success']!=b['success']:pairs.append({'task':x['task'],'arm':arm,'gained':x['success'],'calls':x['found']})
    if x['success']:
     task=m['tasks'][x['task']]
     for key in ['validation','audit']:
      result,_=graph(lib,hub,'economy_validate',{'ops':x['found'],'examples':task[key],'predicate':'unused','projector':'unused'});assert result['accepted']
    prior={e['name'] for e in x['catalog']}
   for e in store.map('knowledge.economics')['catalog']:
    task=m['tasks'][int(e['name'].split('_')[-1])];result,_=graph(lib,hub,'economy_validate',{'ops':[e['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'});assert result['accepted'];audited.append({'arm':arm,'name':e['name'],'cases':len(task['audit'])})
  finally:store.close()
  setup=next(x for x in r['setup'] if x['arm']==arm);wake_steps=sum(x['graph_steps'] for x in rr)+setup['graph_steps'];sleep_steps=sum(x['graph_steps'] for x in sleeps) if arm=='sleep' else 0;inherited=m['online_inherited_steps'] if arm=='online' else 0;solved=sum(x['success'] for x in rr)
  if arm=='sleep':acts=sum(len(x['names']) for x in decisions);helpful=sum(len(x['names'])*x['helped'] for x in decisions);negative=sum(len(x['names'])*x['negative_transfer'] for x in decisions)
  else:
   events=[(x,p) for x in rr for a in x['attempts'] for p in a.get('records',[]) if p['activated']];acts=len(events);helpful=sum(helped(x,baseline[x['task']]) for x,p in events);negative=sum(baseline[x['task']]['success'] and not x['success'] for x,p in events)
  summary.append({'arm':arm,'solved':solved,'wake_steps':wake_steps,'sleep_steps':sleep_steps,'inherited_steps':inherited,'lifetime_steps':wake_steps+sleep_steps+inherited,'cost_per_solved':(wake_steps+sleep_steps+inherited)/solved if solved else None,'wake_cpu':sum(x['cpu_seconds'] for x in rr)+setup['cpu_seconds'],'wake_wall':sum(x['wall_seconds'] for x in rr)+setup['wall_seconds'],'sleep_cpu':sum(x['cpu_seconds'] for x in sleeps) if arm=='sleep' else 0,'sleep_wall':sum(x['wall_seconds'] for x in sleeps) if arm=='sleep' else 0,'activations':acts,'helpful_activations':helpful,'activation_precision':helpful/acts if acts else None,'negative_transfer_activations':negative,'lost_primitive':sum(baseline[x['task']]['success'] and not x['success'] for x in rr),'whole':sum(x['whole'] for x in rr),'mixed':sum(x['mixed'] for x in rr),'library_size':len(rr[-1]['catalog']),'storage_bytes':r['final_storage'][arm],'storage_growth':r['final_storage'][arm]-setup['bytes'],'audit_false_positives':sum(x['audit_false_positive'] for x in rr)})
 cumulative=[];first=None
 totals={a:next(x['graph_steps'] for x in r['setup'] if x['arm']==a)+(m['online_inherited_steps'] if a=='online' else 0) for a in ARMS};solved={a:0 for a in ARMS}
 for task in range(120):
  for arm in ARMS:
   x=next(x for x in rows if x['task']==task and x['arm']==arm);totals[arm]+=x['graph_steps'];solved[arm]+=x['success']
  totals['sleep']+=sum(x['graph_steps'] for x in sleeps if x['boundary']==task)
  cross=solved['sleep']>=solved['no_memory'] and totals['sleep']<totals['no_memory']
  if cross and first is None:first=task+1
  cumulative.append({'completed':task+1,'costs':dict(totals),'solved':dict(solved),'sleep_repaid':cross})
 result={'summary':summary,'wake_decisions':decisions,'usefulness_replays':replayed,'useful_false_negatives':sum(x['useful_false_negative'] for x in replayed),'measured_rejected_pairs':sum(x['false_negative_measurable'] for x in replayed),'unchanged_rejection_prefixes':prefix,'paired_differences':pairs,'stored_audits':audited,'cumulative':cumulative,'first_crossover':first,'final_repaid':cumulative[-1]['sleep_repaid']}
 dump(d/'audit.json',result)
 lines=['# Sleep consolidation results','','One 120-task sequence, six fixed sleep phases. All sleep work is included.','', '| Arm | Solved | Wake steps | Sleep steps | Inherited steps | Lifetime steps | Cost / solve | Whole / mixed |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for x in summary:lines.append(f"| {x['arm']} | {x['solved']}/120 | {x['wake_steps']:,} | {x['sleep_steps']:,} | {x['inherited_steps']:,} | {x['lifetime_steps']:,} | {x['cost_per_solved']:,.0f} | {x['whole']} / {x['mixed']} |")
 lines+=['','| Arm | Wake CPU / wall | Sleep CPU / wall | Activations / helpful | Negative transfer | Lost primitive | Library | DB growth |','|---|---:|---:|---:|---:|---:|---:|---:|']
 for x in summary:lines.append(f"| {x['arm']} | {x['wake_cpu']:.2f} / {x['wake_wall']:.2f} | {x['sleep_cpu']:.2f} / {x['sleep_wall']:.2f} | {x['activations']} / {x['helpful_activations']} | {x['negative_transfer_activations']} | {x['lost_primitive']} | {x['library_size']} | {x['storage_growth']:,} bytes |")
 lines+=['',f"First cumulative crossover: {first}. Final consolidation cost repaid: {result['final_repaid']}.",f"Observed useful-memory false negatives: {result['useful_false_negatives']} / {result['measured_rejected_pairs']} replayed rejected pairs whose methods existed at wake. Remaining opportunities are unmeasured, not negative.",f"Rejected-wake primitive-prefix checks: {len(prefix)}. Lost primitive tasks after rejection: {sum(x['lost_after_rejection'] for x in decisions)}.",f"Stored audit: {len(audited)} methods on {sum(x['cases'] for x in audited)} cases. Final false positives: {sum(x['audit_false_positives'] for x in summary)}.",'','Historical acquisition and fitting cost is included for the inherited online router. Wake/sleep CPU columns describe this run; inherited historical CPU is reported separately in FINDINGS.md. Cold sleep learning receives no prior model or utility table.','', 'No future-task data was passed to consolidation. Tables are frozen between sleep boundaries. Thresholds, streams and budgets were frozen before results. See audit.json for every wake decision, cumulative trajectory, usefulness replay and paired outcome.']
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summary,indent=2));print('first crossover',first)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
