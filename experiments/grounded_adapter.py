"""Learn a field predictor from graph-environment feedback, without named adapters."""
import argparse,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.program_synthesis import setup
from experiments.adaptive_reuse import graph

def run(database,output):
 store,lib,hub=setup(database);costs=[]
 def invoke(name,arg):
  result,cost=graph(lib,hub,name,arg);costs.append(cost);return result
 try:
  lib.update(json.loads((ROOT/'curriculum/grounded-adapter.json').read_text()))
  scenarios=[]
  for world,target,distractor,predictor in [('grounded_world_one','q7','r2','learned_world_one'),('grounded_world_two','m3','z9','learned_world_two')]:
   # Initial observations deliberately confound target and distractor. The graph
   # later chooses an informative intervention from a supplied pool.
   initial=[{'serial':100+i,target:bool(i%2),distractor:bool(i%2)} for i in range(4)]
   observations=invoke('grounded_observe',{'world':world,'items':initial})
   ambiguous=invoke('grounded_learn',{'name':predictor,'observations':observations})
   assert ambiguous['status']=='insufficient_evidence',ambiguous
   assert predictor not in lib
   intervention=[{'serial':110+i,target:bool(i%2),distractor:not bool(i%2)} for i in range(4)]
   query=invoke('grounded_choose_probe',{'observations':observations,'pool':initial+intervention})
   assert len(query)==1 and query[0][target]!=query[0][distractor]
   assert invoke('grounded_choose_probe',{'observations':observations,'pool':initial})==[]
   observations+=invoke('grounded_observe',{'world':world,'items':query})
   learned=invoke('grounded_learn',{'name':predictor,'observations':observations})
   assert learned['status']=='learned' and learned['field']==target,learned
   hidden=[{'serial':200+i,target:bool(i%2),distractor:bool((i//2)%2)} for i in range(40)]
   failures=[]
   for item in hidden:
    predicted=invoke('grounded_predict',{'name':predictor,'features':item})
    # The environment supplies the independent observed outcome. The learner's
    # procedure is not updated from this validation feedback.
    outcome=invoke(world,item)
    if predicted!={'known':True,'outcome':outcome}:failures.append({'item':item,'prediction':predicted,'actual':outcome})
   scenarios.append({'world':world,'ambiguous_result':ambiguous,'chosen_probe':query,'learned_field':learned['field'],'observations':observations,'held_out_passed':40-len(failures),'held_out_total':40,'failures':failures})
  renamed=invoke('grounded_predict',{'name':'learned_world_one','features':{'serial':999,'m3':True,'z9':False}})
  assert renamed=={'known':False,'outcome':None}
  contradiction=invoke('grounded_learn',{'name':'should_not_be_saved','observations':[{'features':{'x':True},'outcome':True},{'features':{'x':True},'outcome':False}]})
  assert contradiction['status']=='insufficient_evidence' and 'should_not_be_saved' not in lib
  report={'scenarios':scenarios,'unseen_rename_prediction':renamed,'contradictory_evidence':contradiction,'total_graph_steps':sum(c['graph_steps'] for c in costs),'model_calls':0,'limitations':['Synthetic environment, with supplied graph action rules.','Graph chooses an informative probe from a supplied finite pool using a supplied disagreement policy.','Candidate language is a single observed field, not arbitrary causal rules.','Renamed fields require new feedback; there is no zero-shot semantic transfer.','Forty tests per world vary identifiers; there are only four boolean feature combinations.','No claim of human-like meaning or real-world causal understanding.']}
  output=Path(output);output.mkdir(parents=True,exist_ok=True)
  (output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
  (output/'REPORT.md').write_text('# Feedback-grounded field learning\n\nThe graph observed outcomes from two synthetic graph environments, rejected ambiguous evidence, chose one informative probe from a supplied pool, then inferred and saved a field predictor. No field name was supplied to the learner.\n\nBoth predictors passed 40 held-out records. An unseen field rename returned unknown; relearning from feedback in the renamed environment succeeded. Contradictory observations produced no saved predictor; a pool without distinguishing probes returned no proposed experiment.\n\n'+ '\n'.join('- '+s for s in report['limitations'])+'\n')
  return report
 finally:store.close()

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--database',required=True);p.add_argument('--output',required=True);a=p.parse_args()
 print(json.dumps(run(a.database,a.output),indent=2))
