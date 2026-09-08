"""Convert a Wikipedia XML export. Requires mwparserfromhell==0.7.2."""
import hashlib
import html
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import quote

import mwparserfromhell as mw


def clean(raw):
    code = mw.parse(raw)
    # Remove non-prose elements; preserve their original representation separately.
    for tag in list(code.filter_tags(recursive=True)):
        if str(tag.tag).lower() in {'ref', 'references', 'table', 'gallery', 'timeline', 'score', 'imagemap'}:
            try:
                code.remove(tag)
            except ValueError:
                pass
    for link in list(code.filter_wikilinks(recursive=True)):
        if str(link.title).strip().lower().startswith(('file:', 'image:', 'category:')):
            try:
                code.remove(link)
            except ValueError:
                pass
    # Do not silently erase inline quantities or qualifications in templates.
    # This is a readable fallback, not MediaWiki template execution.
    for template in list(code.filter_templates(recursive=False)):
        name = str(template.name).strip()
        args = [str(p.value).strip() for p in template.params if str(p.name).strip().isdigit()]
        if name.lower() in {'convert', 'cvt'}:
            replacement = ' '.join(args)
        elif name.lower() in {'nowrap', 'nobr', 'math', 'mvar'} and args:
            replacement = args[0]
        else:
            replacement = '[template omitted: ' + name + ']'
        code.replace(template, replacement)
    text = html.unescape(code.strip_code(normalize=True, collapse=True))
    text = re.sub(r'(?m)^[ \t]*[*#:;]+[ \t]*', '', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' *\n *', '\n', text)
    return re.sub(r'\n{3,}', '\n\n', text).strip()


def main(source, output):
    source, output = Path(source), Path(output)
    output.mkdir(parents=True, exist_ok=True)
    (output / 'text').mkdir(exist_ok=True)
    root = ET.parse(source).getroot()
    ns = {'m': root.tag.split('}')[0].lstrip('{')}
    records = []
    for page in root.findall('m:page', ns):
        title = page.findtext('m:title', namespaces=ns)
        rev = page.find('m:revision', ns)
        raw = rev.findtext('m:text', default='', namespaces=ns)
        links = sorted({str(x.title).strip() for x in mw.parse(raw).filter_wikilinks()})
        revision_id = rev.findtext('m:id', namespaces=ns)
        record = {
            'title': title,
            'page_id': page.findtext('m:id', namespaces=ns),
            'revision_id': revision_id,
            'timestamp': rev.findtext('m:timestamp', namespaces=ns),
            'url': 'https://en.wikipedia.org/wiki/' + quote(title.replace(' ', '_'), safe=''),
            'revision_url': 'https://en.wikipedia.org/w/index.php?oldid=' + revision_id,
            'links': links,
            'text': clean(raw),
            'wikitext': raw,
        }
        records.append(record)
        filename = re.sub(r'[^\w .()-]', '_', title) + '.txt'
        (output / 'text' / filename).write_text(title + '\n\n' + record['text'] + '\n', encoding='utf-8')
    with (output / 'articles.jsonl').open('w', encoding='utf-8') as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    summary = {
        'source_file': source.name,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'articles': len(records),
        'text_characters': sum(len(r['text']) for r in records),
        'unique_link_targets': len({link for r in records for link in r['links']}),
        'empty_articles': [r['title'] for r in records if not r['text']],
        'parser': 'mwparserfromhell ' + mw.__version__,
    }
    (output / 'manifest.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
