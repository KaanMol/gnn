"""Load validated reference assertions through the running notebook's API."""
import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'wikipedia-starter'))
from load_running import request, NAME
from graph_store import GraphStore
from graph_runtime import bounded_data


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify-existing',type=Path,help='Verify an already persisted import against its original backup without repeating writes.')
    args=parser.parse_args()
    validation=json.loads((HERE/'staging-validation.json').read_text())
    assert validation['unknown_not_invented'] and all(q['passed'] for q in validation['queries'])
    base='http://127.0.0.1:8765'
    before=request(base+'/api/state')
    database=Path(before['storage']['path'])
    assert database.resolve()==(HERE.parent/'preview-memory.graph.sqlite3').resolve()
    assert NAME in before['procedures']
    backup=args.verify_existing or HERE/('live-before-expansion-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.sqlite3')
    if args.verify_existing:
        assert backup.is_file()
    else:
        with sqlite3.connect(database.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(backup) as dst:
            src.backup(dst)
    previous=GraphStore(backup).map('knowledge.assertions').to_dict()
    lessons=json.loads((HERE/'lessons.json').read_text())
    records, expected=[],[]
    for row in lessons:
        op=row['translation']['operations'][0]
        fact=(op['relation'],op['subject'],op['object'])
        key=(fact,False)
        expected.append(fact)
        if key in previous:
            continue
        if (fact,True) in previous:
            raise ValueError('Existing negative assertion requires explicit reconciliation: '+str(fact))
        records.append({'namespace':'knowledge.assertions','key':[list(fact),False],'value':row['original']})
    bounded_data(records)
    print('Backup:',backup,flush=True)
    if args.verify_existing:
        print('Verifying persisted import without repeating writes...',flush=True)
        state=before
    else:
        print('Importing',len(records),'new assertions through the live workspace port...',flush=True)
        response=request(base+'/api/action',{'action':'run_skill','name':NAME,'argument':records})
        assert response['execution']['status']=='executed'
        assert response['execution']['result']==[True]*len(records)
        state=response['state']
    facts={tuple(f) for f in state['facts']}
    assert all(f in facts for f in expected)
    assert state['reasoning_error'] is None
    live=GraphStore(database)
    stored=live.map('knowledge.assertions').to_dict()
    assert all(stored[k]==v for k,v in previous.items())
    for row in records:
        key=(tuple(row['key'][0]),False)
        assert stored[key]==row['value']
    # Execute a taught query against the actual live evidence. This avoids
    # testing Gemma's translation instead of the graph's knowledge.
    evidence=live.map('knowledge.facts').to_dict()
    negatives=live.map('knowledge.negatives').to_dict()
    def evidence_rows(mapping):
        return [{'fact':list(f),'source':source,'premises':[list(p) for p in premises]}
                for f,(source,premises) in mapping.items()]
    base_argument={'facts':evidence_rows(evidence),'negatives':evidence_rows(negatives)}
    checks=[]
    for q in validation['queries']:
        argument={**base_argument,'fact':[q['relation'],q['subject'],q['object']],'negative':False}
        result=request(base+'/api/action',{'action':'run_skill','name':'knowledge_query','argument':argument})
        assert result['execution']['result']=='yes'
        checks.append({'subject':q['subject'],'relation':q['relation'],'object':q['object'],'result':'yes'})
        print('Live query passed:',q['subject'],q['relation'],flush=True)
    report={'loaded_at':datetime.now(timezone.utc).isoformat(),'new_assertions':len(records),
        'domain_counts':json.loads((HERE/'manifest.json').read_text())['domains'],
        'live_facts':len(facts),'preserved_assertions':len(previous),'all_sources_preserved':True,
        'queries':checks,'backup':str(backup),'database':str(database)}
    (HERE/'live-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
