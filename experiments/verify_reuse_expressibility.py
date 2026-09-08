"""Post-search baseline witnesses. These programs are never supplied to search."""
import argparse, hashlib, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import foundation
from graph_store import GraphStore

WITNESSES={
 'selected_sum':['synth_select','synth_sum'],
 'selected_double_sum':['synth_select','synth_sum','bench_double'],
 'selected_negative_double_sum':['synth_select','synth_sum','bench_double','bench_negate'],
 'plain_sum':['synth_sum'],
 'selected_count':['synth_select','synth_count'],
 'plain_double_sum':['synth_sum','bench_double'],
}

def verify(database,directory):
 directory=Path(directory)
 manifest=json.loads((directory/'manifest.json').read_text())
 store=GraphStore(database)
 try:
  lib=store.map('knowledge.procedures')
  digest=hashlib.sha256(json.dumps({k:v['graph'] for k,v in lib.items()},sort_keys=True).encode()).hexdigest()
  assert digest==manifest['frozen_library_sha256']
  results=[]
  for task in manifest['tasks']:
   if task['family'] not in WITNESSES:continue
   ops=WITNESSES[task['family']]
   assert len(ops)<=manifest['max_depth'] and set(ops)<=set(manifest['arms']['baseline'])
   cases=task['request']['examples']+task['hidden']
   for case in cases:
    actual,_=foundation.run(lib,'synth_execute_candidate',{'ops':ops,'argument':{'items':case['input'],'predicate':task['request']['predicate'],'projector':task['request']['projector']}})
    assert actual==case['expected'],(task['id'],case,actual)
   results.append({'task':task['id'],'ops':ops,'cases_passed':len(cases)})
  result={'purpose':'Post-search expressibility verification, not discovered programs or search input. Maximum controls intentionally excluded.','tasks_passed':len(results),'cases_passed':sum(r['cases_passed'] for r in results),'results':results}
  (directory/'expressibility.json').write_text(json.dumps(result,indent=2)+'\n')
  return result
 finally:store.close()

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--database',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
 result=verify(args.database,args.output)
 print(json.dumps({k:v for k,v in result.items() if k!='results'},indent=2))
