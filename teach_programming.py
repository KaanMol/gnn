"""Explicitly teach the running preview the programming starter package."""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'wikipedia-starter'))
from load_running import request
from javascript_lessons import examples, MAXIMUM
from javascript import source_curriculum, display_value
from build_programming_curriculum import build
from build_react_curriculum import build as react_lessons


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--update',action='store_true',help='Explicitly update the programming procedures while preserving stored example edits.')
    args=parser.parse_args()
    base='http://127.0.0.1:8765'
    state=request(base+'/api/state')
    db=Path(state['storage']['path'])
    assert db.resolve()==(ROOT/'preview-memory.graph.sqlite3').resolve()
    backup=ROOT/('preview-memory.before-programming-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.sqlite3')
    with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(backup) as dst:src.backup(dst)
    package=build() | react_lessons() | source_curriculum()
    collisions=set(package)&set(state['procedures'])
    if collisions and not args.update:raise ValueError('Programming procedures already present; inspect before replacing: '+str(collisions))
    response=request(base+'/api/action',{'action':'teach_graph_package','entries':package})
    print(response['answer'],flush=True)
    existing=request(base+'/api/action',{'action':'run_skill','name':'workspace_keys',
        'argument':{'namespace':'knowledge.javascript_examples'}})['execution']['result']
    added=[]
    for name,value in examples().items():
        if name in existing:continue
        response=request(base+'/api/action',{'action':'run_skill','name':'workspace_write',
            'argument':{'namespace':'knowledge.javascript_examples','key':name,'value':value}})
        assert response['execution']['result']['accepted']
        added.append(name)
    response=request(base+'/api/action',{'action':'javascript_run',
        'source':'function identity(x) { return x; }','input':-2})
    assert response['execution']['result']['value']==-2
    math=request(base+'/api/action',{'action':'javascript_run',
        'source':'const xs = [-3, 9]; console.log("max", Math.max(xs[0], xs[1]));'})
    assert math['execution']['result']['logs']==[['max',9]]
    semantics=request(base+'/api/action',{'action':'javascript_run',
        'source':'console.log(0 || 9, false ?? 4, true || false && false);'})
    assert semantics['execution']['result']['logs']==[[9,False,True]]
    data=request(base+'/api/action',{'action':'javascript_run',
        'source':'const todos = [{id: 1, done: false}]; console.log(todos.map(t => ({...t, done: !t.done})), todos);'})
    assert display_value(data['execution']['result']['logs'])==[[[{'id':1,'done':True}],[{'id':1,'done':False}]]]
    assert {tuple(f) for f in state['facts']} <= {tuple(f) for f in response['state']['facts']}
    report={'backup':str(backup),'procedures':list(package),'examples_added':added,
        'verified_result':-2,'console_math_verified':True,'graph_source_and_logical_semantics_verified':True,
        'react_data_transform_verified':True,'previous_facts_preserved':True,'taught_at':datetime.now(timezone.utc).isoformat()}
    (ROOT/'programming-teaching-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
