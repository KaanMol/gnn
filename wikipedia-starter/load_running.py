"""Import Wikipedia records and curated assertions through Seed's live API.

No server restart or direct database writes. Full article text is archival data;
only the separately curated assertions are active symbolic facts.
"""
import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from graph_dsl import G
from graph_runtime import bounded_data, validate_graph
from graph_store import GraphStore

NAME = 'wikipedia_import_records'


def request(url, body=None):
    payload = None if body is None else json.dumps(body, ensure_ascii=False).encode()
    if payload is not None and len(payload) >= 1000000:
        raise ValueError('Request exceeds preview size limit.')
    req = Request(url, data=payload, headers={'Content-Type': 'application/json'})
    with urlopen(req, timeout=240) as response:
        return json.load(response)


def chunks(value, size):
    return [value[i:i+size] for i in range(0, len(value), size)]


def archive(article):
    result = {k: v for k, v in article.items() if k not in {'text','wikitext','links'}}
    result.update(format='wikipedia.article.v1',
                  text_chunks=chunks(article['text'], 12000),
                  wikitext_chunks=chunks(article['wikitext'], 12000),
                  link_chunks=chunks(article['links'], 200),
                  wikitext_sha256=hashlib.sha256(article['wikitext'].encode()).hexdigest(),
                  status='source text archived; only separately curated assertions are active facts')
    bounded_data(result)
    return result


def graph():
    body = G()
    namespace = body.get(body.input, 'namespace')
    permitted = body.either(body.eq(namespace, body.data('knowledge.wikipedia_articles')),
                           body.eq(namespace, body.data('knowledge.assertions')))
    checked = body.op('require', permitted, body.input, message='Wikipedia importer only accepts article or assertion records.')
    written = body.op('act', checked, checked, surface='workspace', action='write')
    accepted = body.get(written, 'accepted')
    g = G()
    return g.finish(g.map(g.input, body.finish(accepted)), trace_mode='explicit', internal=True,
                    description='Import source article records and curated assertions through the workspace port.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8765')
    args = parser.parse_args()
    base = args.url.rstrip('/')
    state = request(base + '/api/state')
    database = Path(state['storage']['path'])
    if database.resolve() != (HERE.parent / 'preview-memory.graph.sqlite3').resolve():
        raise ValueError('Live notebook differs from the expected project database; inspect before importing.')
    articles = [json.loads(line) for line in (HERE/'articles.jsonl').read_text().splitlines()]
    lessons = json.loads((HERE/'seed-wikipedia.json').read_text())['language']
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup = HERE / ('live-before-wikipedia-' + stamp + '.sqlite3')
    with sqlite3.connect(database.as_uri()+'?mode=ro', uri=True) as src, sqlite3.connect(backup) as dst:
        src.backup(dst)
    prior = GraphStore(backup)
    baseline = prior.map('knowledge.assertions').to_dict()
    pending, preserved = [], 0
    for article in articles:
        pending.append({'namespace':'knowledge.wikipedia_articles', 'key':article['title'], 'value':archive(article)})
    expected = []
    for lesson in lessons:
        for op in lesson['translation']['operations']:
            fact = (op['relation'].lower(), op['subject'], op['object'])
            key = (fact, op['negative'])
            expected.append(fact)
            if key in baseline:
                preserved += 1
                continue
            pending.append({'namespace':'knowledge.assertions', 'key':[list(fact),op['negative']], 'value':lesson['original']})
    lesson_graph = graph()
    validate_graph(lesson_graph, state['procedures'])
    existing = state['procedures'].get(NAME)
    if existing and existing['graph'] != lesson_graph:
        raise ValueError('A different importer already has this name.')
    if not existing:
        request(base+'/api/action', {'action':'teach_graph','name':NAME,'graph':lesson_graph})
    print('Backup:', backup, flush=True)
    batches, current = [], []
    for row in pending:
        trial = current + [row]
        if current and len(json.dumps(trial,ensure_ascii=False).encode()) > 650000:
            batches.append(current)
            current = []
        current.append(row)
    if current:
        batches.append(current)
    for i, batch in enumerate(batches, 1):
        bounded_data(batch)
        result = request(base+'/api/action', {'action':'run_skill','name':NAME,'argument':batch})
        execution = result['execution']
        if execution['status'] != 'executed' or execution['result'] != [True]*len(batch):
            raise ValueError('Import did not report all records accepted.')
        print(f'Imported batch {i}/{len(batches)} ({len(batch)} records)', flush=True)
    # Verify the actual running instance advertises the imported facts.
    state = request(base+'/api/state')
    live_facts = {tuple(f) for f in state['facts']}
    assert all(f in live_facts for f in expected)
    # Read through the live workspace skill, and compare every source byte.
    for i, article in enumerate(articles, 1):
        response = request(base+'/api/action', {'action':'run_skill','name':'workspace_read',
            'argument':{'namespace':'knowledge.wikipedia_articles','key':article['title']}})
        stored = response['execution']['result']
        assert ''.join(stored['wikitext_chunks']) == article['wikitext']
        assert ''.join(stored['text_chunks']) == article['text']
        assert [link for part in stored['link_chunks'] for link in part] == article['links']
        assert stored['revision_id'] == article['revision_id']
        if i % 10 == 0 or i == len(articles):
            print(f'Verified full article content {i}/{len(articles)}', flush=True)
    live = GraphStore(database)
    assertions = live.map('knowledge.assertions').to_dict()
    assert all(assertions[k] == v for k,v in baseline.items())
    for lesson in lessons:
        for op in lesson['translation']['operations']:
            key=((op['relation'].lower(),op['subject'],op['object']),op['negative'])
            if key not in baseline:
                assert assertions[key] == lesson['original']
    report = {'live_database':str(database),'backup':str(backup),'article_records':len(articles),
        'full_article_content_verified':True,'curated_facts_verified':len(expected),
        'preexisting_assertions_preserved':len(baseline),'existing_matching_assertions':preserved,
        'finished_at':datetime.now(timezone.utc).isoformat(),
        'limitation':'Full text is source memory, not automatic extraction of every fact.'}
    (HERE/'live-import-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
