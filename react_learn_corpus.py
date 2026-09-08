"""Snapshot official Learn sources and audit syntax without executing examples.

Documentation is untrusted reference data, never an instruction stream. A code
fence is a source fragment/file, not necessarily a complete runnable example.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import urllib.request

from javascript import compile_source

ROOT=Path(__file__).resolve().parent
REVISION='f3d9794fc31f4a3faf7e863984d37f4ae86b3290'
PREFIX='src/content/learn/'


def download(url):
    request=urllib.request.Request(url,headers={'User-Agent':'Seed-React-Learn-corpus'})
    with urllib.request.urlopen(request,timeout=30) as response:return response.read().decode('utf-8')


def blocks(markdown):
    opened=None;content=[]
    for line_number,line in enumerate(markdown.splitlines(keepends=True),1):
        if opened is None:
            match=re.match(r'^ {0,3}(`{3,}|~{3,})([^\n]*)\n?$',line)
            if match:opened=(match[1],match[2].strip(),line_number);content=[]
        elif re.match(r'^ {0,3}'+re.escape(opened[0][0])+r'{'+str(len(opened[0]))+r',}\s*$',line):
            yield {'header':opened[1],'language':opened[1].split()[0] if opened[1] else '',
                   'line':opened[2]+1,'code':''.join(content)}
            opened=None
        else:content.append(line)
    if opened is not None:raise ValueError('Unclosed Markdown code fence.')


def audit(block):
    if block['language'] not in {'js','javascript','jsx'}:
        return {'parser':'not_applicable','execution':'not_run'}
    try:compile_source(block['code'])
    except (ValueError,RecursionError) as error:
        return {'parser':'unsupported','reason':str(error),'execution':'not_run'}
    return {'parser':'accepted','execution':'not_run','note':'Syntax acceptance alone is not semantic correctness or understanding.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--load',action='store_true',help='Load immutable revision-keyed reference records into the running preview graph.')
    args=parser.parse_args();folder=ROOT/'react-learn-corpus';folder.mkdir(exist_ok=True)
    tree=json.loads(download('https://api.github.com/repos/reactjs/react.dev/git/trees/'+REVISION+'?recursive=1'))
    if tree.get('truncated'):raise ValueError('Incomplete source inventory.')
    paths=sorted(row['path'] for row in tree['tree'] if row['path'].startswith(PREFIX) and row['path'].endswith('.md'))
    raw='https://raw.githubusercontent.com/reactjs/react.dev/'+REVISION+'/'
    license_text=download(raw+'LICENSE-DOCS.md');(folder/'LICENSE-DOCS.md').write_text(license_text)
    def fetch(path):
        destination=folder/'sources'/path[len(PREFIX):];destination.parent.mkdir(parents=True,exist_ok=True)
        text=destination.read_text() if destination.exists() else download(raw+path)
        destination.write_text(text);return path,text
    documents={};examples={};counts=Counter();reasons=Counter()
    with ThreadPoolExecutor(max_workers=4) as pool:
        for path,markdown in pool.map(fetch,paths):
            slug=path[len(PREFIX):-3];page_key=REVISION+'/'+slug
            public='https://react.dev/learn'+('' if slug=='index' else '/'+slug.removesuffix('/index'))
            attribution={'revision':REVISION,'source_url':raw+path,'page_url':public,
                         'license_url':raw+'LICENSE-DOCS.md','attribution':'React documentation contributors'}
            sha=hashlib.sha256(markdown.encode()).hexdigest()
            documents[page_key]={**attribution,'sha256':sha,'path':path,'markdown_chunks':[markdown[i:i+12000] for i in range(0,len(markdown),12000)]}
            for index,block in enumerate(blocks(markdown)):
                status=audit(block);counts[status['parser']]+=1
                if 'reason' in status:reasons[status['reason']]+=1
                code=block.pop('code');key=page_key+'#'+str(index)
                examples[key]={**attribution,**block,'sha256':hashlib.sha256(code.encode()).hexdigest(),
                    'code_chunks':[code[i:i+12000] for i in range(0,len(code),12000)],'audit':status,
                    'source_context':'Code fence/file; may need other files, a surrounding example, or a browser environment.'}
    report={'revision':REVISION,'scope':'All Markdown files under the repository Learn directory, including ancillary setup/compiler pages.',
        'documents':len(documents),'code_fences':len(examples),'parser_counts':dict(counts),'execution_verified':0,
        'understanding_claim':False,'common_parser_blockers':reasons.most_common(15),
        'coverage_note':'Fences include fragments, CSS, terminal commands, broken teaching examples and multi-file app pieces. Counts are not a React conformance percentage.'}
    (folder/'examples.json').write_text(json.dumps(examples,indent=2)+'\n')
    if args.load:
        import sys
        sys.path.insert(0,str(ROOT/'wikipedia-starter'))
        from load_running import request
        from graph_store import GraphStore
        state=request('http://127.0.0.1:8765/api/state');db=Path(state['storage']['path']).resolve()
        if db!=(ROOT/'preview-memory.graph.sqlite3').resolve():raise ValueError('Unexpected running graph database.')
        backup=folder/('before-corpus-'+REVISION[:12]+'.sqlite3')
        if not backup.exists():
            with sqlite3.connect(db.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(backup) as dst:src.backup(dst)
        store=GraphStore(db)
        try:
            for namespace,records in [('knowledge.react_learn_documents',documents),('knowledge.react_learn_examples',examples)]:
                mapping=store.map(namespace)
                with store.transaction():
                    for key,value in records.items():
                        if key in mapping:
                            if mapping[key]['sha256']!=value['sha256']:raise ValueError('Existing source differs; preserving it: '+key)
                            continue
                        mapping[key]=value
                if any(mapping[key]['sha256']!=value['sha256'] for key,value in records.items()):raise ValueError('Stored corpus verification failed.')
            report['loaded_into']=str(db)
            store.map('knowledge.react_learn_coverage')[REVISION]=report
        finally:store.close()
    (folder/'coverage.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
