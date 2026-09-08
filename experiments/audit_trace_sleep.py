"""Trace consolidation evidence, matched replay ablation and lifetime audit."""
import argparse,json,sys
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.trace_sleep import verify,ARMS
from experiments.utility_router import connect,dump,digest
from experiments.adaptive_reuse import graph

def helps(x,b):return bool(x['success'] and (not b['success'] or x['graph_steps']<b['graph_steps']))
def audit(d):
 d=Path(d);m=verify(d);r=json.loads((d/'report.json').read_text());old=json.loads((ROOT/'experiments/sleep-memory-results/report.json').read_text());assert r['manifest_sha256']==digest(d/'manifest.json')
 rows=r['trials'];assert len(rows)==360;assert {(x['task'],x['arm']) for x in rows}=={(i,a) for i in range(120) for a in ARMS}
 base={x['task']:x for x in rows if x['arm']=='no_memory'};trace_rows={x['task']:x for x in rows if x['arm']=='trace'}
 summaries=[];prefix=[];decisions=[];fn=[];stored=[];lookup={}
 for arm in ARMS:
  rr=[x for x in rows if x['arm']==arm];cycles=[s for s in r['sleeps'] if s['arm']==arm];prior=set();st,lib,hub=connect(d/f'{arm}.sqlite3')
  try:
   for x in rr:
    assert x['graph_steps']==sum(x['costs'].values())<=450000 and not x['uncertified']
    active=[]
    for a in x['attempts']:
     for z in a['trace']:
      assert z['queue']<=100
      if z['allowed']:assert len(z['expanded'])<=5
     if arm!='no_memory':
      assert a['route']['boundary']==(x['task']//20)*20-1
      if a['selected']:assert a['selected']['name'] in prior;active.append(a['selected']['name'])
    if arm=='trace':
     assert x['costs'].get('extra_wake_index',0)>0 and x['costs'].get('extra_wake_recording',0)>0
     assert {e['name'] for e in x['evidence']['available']}==prior
     if not active:
      a=x['attempts'][0]['trace'];assert a==base[x['task']]['attempts'][0]['trace'][:len(a)];prefix.append(x['task'])
    if arm!='no_memory':decisions.append({'arm':arm,'task':x['task'],'names':active,'helped':bool(active and helps(x,base[x['task']])),'negative_transfer':bool(active and base[x['task']]['success'] and not x['success'])})
    if x['success']:
     for part in ['validation','audit']:
      answer,_=graph(lib,hub,'economy_validate',{'ops':x['found'],'examples':m['tasks'][x['task']][part],'predicate':'unused','projector':'unused'});assert answer['accepted']
    prior={e['name'] for e in x['catalog']}
   model=[];schedule=[]
   for s in cycles:
    assert s['available_tasks']==list(range(s['boundary']+1));assert s['graph_steps']==sum(s['costs'].values())<=6000000;assert model==s['before']['model']
    if arm=='trace':
     assert sum(z['full'] is not None for z in s['results'])<=1
     assert s['costs'].get('partial_replay',0)==sum(z['partial']['graph_steps'] for z in s['results'] if z['partial'])
     assert s['costs'].get('full_replay',0)==sum(z['full']['graph_steps'] for z in s['results'] if z['full'])
    for z in s['results']:
     p=z['pair'];assert p['task']<=s['boundary'] and int(p['entry']['name'].split('_')[-1])<=s['boundary']
     if arm=='full':
      outcome=z['replay'];utility=z['utility'];source='full';lookup[(s['boundary'],p['task'],p['entry']['name'])]=outcome['graph_steps']
     else:
      source=z['source'];outcome=z['outcome'];utility=z['utility']
      if z['partial']:assert z['partial']['graph_steps']<=75000
      if source=='partial':assert outcome['success'] and not outcome['exhaustions']
      if source=='trace':
       row=trace_rows[p['task']];assert outcome==row or {k:v for k,v in outcome.items() if k not in ['arm','bytes','evidence']}=={k:v for k,v in row.items() if k not in ['arm','bytes','evidence']}
       ev,_=graph(lib,hub,'trace_evidence',{'row':row,'entry':p['entry'],'records':row['evidence']['observations']});assert ev['factual']
      if source=='UNKNOWN':assert utility is None and outcome is None
      schedule,_=graph(lib,hub,'trace_note_attempt',{'schedule':schedule,'context':p['context'],'name':p['entry']['name']})
     if outcome is not None:
      u,_=graph(lib,hub,'router_utility',{'actual':{'success':outcome['success'],'cost':outcome['graph_steps']},'baseline':{'success':base[p['task']]['success'],'cost':base[p['task']]['graph_steps']}});assert utility==u
      model,_=graph(lib,hub,'sleep_update',{'model':model,'context':p['context'],'name':p['entry']['name'],'utility':utility})
      eligible=z['method_existed_at_wake'] and not z['selected_at_wake']
      fn.append({'arm':arm,'task':p['task'],'name':p['entry']['name'],'measurable':eligible,'useful_false_negative':bool(eligible and helps(outcome,base[p['task']]))})
    assert model==s['after']['model']
    if arm=='trace':assert schedule==s['schedule']
   for entry in st.map('knowledge.economics')['catalog']:
    task=m['tasks'][int(entry['name'].split('_')[-1])];v,_=graph(lib,hub,'economy_validate',{'ops':[entry['name']],'examples':task['audit'],'predicate':'unused','projector':'unused'});assert v['accepted'];stored.append({'arm':arm,'name':entry['name'],'cases':len(task['audit'])})
  finally:st.close()
  setup=next(x for x in r['setup'] if x['arm']==arm);wake=sum(x['graph_steps'] for x in rr)+setup['graph_steps'];sleep=sum(s['graph_steps'] for s in cycles);solved=sum(x['success'] for x in rr);events=[x for x in decisions if x['arm']==arm]
  cats=Counter()
  for x in rr:cats.update(x['costs'])
  counts=Counter(z.get('source','full') for s in cycles for z in s['results'])
  summaries.append({'arm':arm,'solved':solved,'wake_steps':wake,'sleep_steps':sleep,'lifetime_steps':wake+sleep,'cost_per_solve':(wake+sleep)/solved,'routing_steps':cats['wake_lookup'],'extra_wake_recording':cats['extra_wake_index']+cats['extra_wake_recording'],'full_replay_steps':sum(s['costs'].get('replay',s['costs'].get('full_replay',0)) for s in cycles),'partial_replay_steps':sum(s['costs'].get('partial_replay',0) for s in cycles),'evidence_counts':dict(counts),'activations':sum(len(x['names']) for x in events),'helpful_activations':sum(len(x['names'])*x['helped'] for x in events),'negative_transfer':sum(len(x['names'])*x['negative_transfer'] for x in events),'lost_primitive':sum(base[x['task']]['success'] and not x['success'] for x in rr),'whole':sum(x['whole'] for x in rr),'mixed':sum(x['mixed'] for x in rr),'audit_false_positives':sum(x['audit_false_positive'] for x in rr),'cpu_seconds':setup['cpu_seconds']+sum(x['cpu_seconds'] for x in rr)+sum(s['cpu_seconds'] for s in cycles),'wall_seconds':setup['wall_seconds']+sum(x['wall_seconds'] for x in rr)+sum(s['wall_seconds'] for s in cycles),'storage_bytes':r['final_storage'][arm],'storage_growth':r['final_storage'][arm]-setup['bytes']})
 full=next(x for x in summaries if x['arm']=='full');trace=next(x for x in summaries if x['arm']=='trace');assert full['full_replay_steps']==8683002
 oldcost=sum(s['costs']['replay'] for s in old['sleeps']);assert oldcost==8683002
 matched=[]
 for s in r['sleeps']:
  if s['arm']!='trace':continue
  for z in s['results']:
   k=(s['boundary'],z['pair']['task'],z['pair']['entry']['name'])
   matched.append({'key':k,'matched':k in lookup,'old_cost':lookup.get(k),'source':z['source'],'new_full_cost':z['full']['graph_steps'] if z['full'] else 0})
 assert len(matched)==36
 avoided=sum(z['old_cost'] for z in matched if z['matched'] and z['source']!='full')
 sleep_new=sum(s['costs'].get('trace_analysis',0)+s['costs'].get('attempt_index',0)+s['costs'].get('attempt_index_persistence',0) for s in r['sleeps'] if s['arm']=='trace')
 ablation={'old_full_replay_steps':oldcost,'new_full_replay_steps':trace['full_replay_steps'],'full_component_reduction':oldcost-trace['full_replay_steps'],'matched_pairs':sum(z['matched'] for z in matched),'avoided_matched_full_cost':avoided,'full_replays_avoided':sum(z['source']!='full' for z in matched),'partial_steps_introduced':trace['partial_replay_steps'],'trace_analysis_and_attempt_index_introduced':sleep_new,'extra_wake_recording_introduced':trace['extra_wake_recording'],'net_sleep_reduction':full['sleep_steps']-trace['sleep_steps'],'net_lifetime_reduction':full['lifetime_steps']-trace['lifetime_steps'],'pair_details':matched}
 cumulative=[];cost={a:next(x['graph_steps'] for x in r['setup'] if x['arm']==a) for a in ARMS};solves={a:0 for a in ARMS};first=None
 for i in range(120):
  for arm in ARMS:
   x=next(x for x in rows if x['task']==i and x['arm']==arm);cost[arm]+=x['graph_steps'];solves[arm]+=x['success'];cost[arm]+=sum(s['graph_steps'] for s in r['sleeps'] if s['arm']==arm and s['boundary']==i)
  cross=solves['trace']>=solves['no_memory'] and cost['trace']<cost['no_memory']
  if cross and first is None:first=i+1
  cumulative.append({'completed':i+1,'costs':dict(cost),'solved':dict(solves),'trace_repaid':cross})
 result={'summary':summaries,'ablation':ablation,'decisions':decisions,'usefulness':fn,'stored_audits':stored,'rejection_prefix_checks':prefix,'cumulative':cumulative,'first_crossover':first,'final_repaid':cumulative[-1]['trace_repaid']};dump(d/'audit.json',result)
 lines=['# Trace-assisted consolidation','','Preserved 120-task sequence; architectural comparison, not fresh evaluation.','', '| Arm | Solved | Wake | Sleep | Lifetime | Cost / solve | CPU / wall |','|---|---:|---:|---:|---:|---:|---:|']
 for x in summaries:lines.append(f"| {x['arm']} | {x['solved']}/120 | {x['wake_steps']:,} | {x['sleep_steps']:,} | {x['lifetime_steps']:,} | {x['cost_per_solve']:,.0f} | {x['cpu_seconds']:.2f} / {x['wall_seconds']:.2f} |")
 lines+=['',f"First crossover: {first}; final cost repaid: {result['final_repaid']}.",f"Old full-replay control reproduced {oldcost:,} steps. New full-replay component: {trace['full_replay_steps']:,}; partial replay: {trace['partial_replay_steps']:,}.",f"Trace analysis/attempt indexing introduced {sleep_new:,} steps; extra wake recording introduced {trace['extra_wake_recording']:,}.",f"Evidence counts: {trace['evidence_counts']}. Full replays avoided: {ablation['full_replays_avoided']}/36; matched replay pairs: {ablation['matched_pairs']}/36.",f"Activations/helpful: {trace['activations']}/{trace['helpful_activations']}; negative transfer: {trace['negative_transfer']}; lost primitive solves: {trace['lost_primitive']}; whole/mixed: {trace['whole']}/{trace['mixed']}; audit false positives: {trace['audit_false_positives']}.",'','See audit.json for the exact matched ablation, wake decisions, measured false negatives, storage, cumulative ledger and evidence provenance. UNKNOWN and unsampled opportunities are not labeled useless. All prior outputs and frozen wake/validation rules are preserved.']
 (d/'REPORT.md').write_text('\n'.join(lines)+'\n');print(json.dumps(summaries,indent=2));print('crossover',first)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();audit(a.output)
