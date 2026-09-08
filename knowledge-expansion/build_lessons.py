"""Create source-backed, atomic lessons from downloaded public reference data."""
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from semantics import operation, validate


def build():
    lessons = []
    retrieved = datetime.now(timezone.utc).isoformat()

    def add(domain, subject, relation, obj, url, evidence):
        if not obj:
            return
        op = operation('assert', subject.strip(), relation.lower(), obj.strip())
        assert all(0 < len(op[k]) <= 160 for k in ('subject','relation','object'))
        proposal = {'operations':[op]}
        validate(proposal)
        source = f'{domain} reference lesson. Source: {url}\nRetrieved: {retrieved}\nEvidence: {evidence}'
        lessons.append({'domain':domain, 'original':source, 'translation':proposal,
                        'source_url':url, 'evidence':evidence})

    table = json.loads((HERE/'pubchem-elements.json').read_text())['Table']
    columns = table['Columns']['Column']
    for row in table['Row']:
        e = dict(zip(columns,row['Cell']))
        url = 'https://pubchem.ncbi.nlm.nih.gov/element/' + e['AtomicNumber']
        evidence = json.dumps({k:e[k] for k in ['AtomicNumber','Symbol','Name']})
        for relation, value in [('is','chemical element'),('atomic number',e['AtomicNumber']),('chemical symbol',e['Symbol'])]:
            add('Chemistry',e['Name'],relation,value,url,evidence)
    assert len(table['Row']) == 118

    metadata, countries = json.loads((HERE/'worldbank-countries.json').read_text())
    assert metadata['pages'] == 1 and len(countries) == metadata['total']
    for country in countries:
        if country['region']['id'] == 'NA':
            continue  # Aggregates are not country/economy records.
        url = 'https://api.worldbank.org/v2/country/' + country['id'] + '?format=json'
        # Attribution is part of the predicate: do not imply that a single API
        # capital field completely describes constitutional/administrative status.
        evidence = json.dumps({k:country[k] for k in ['id','name','capitalCity','region']},ensure_ascii=False)
        add('Geography',country['name'],'World Bank listed capital',country['capitalCity'],url,evidence)
        add('Geography',country['name'],'World Bank region',country['region']['value'],url,evidence)

    for taxon in ET.parse(HERE/'ncbi-taxonomy.xml').getroot().findall('Taxon'):
        name = taxon.findtext('ScientificName')
        url = 'https://www.ncbi.nlm.nih.gov/Taxonomy/Browser/wwwtax.cgi?id=' + taxon.findtext('TaxId')
        common = taxon.findtext('OtherNames/GenbankCommonName')
        rows = [('NCBI taxonomic rank',taxon.findtext('Rank')),('NCBI common name',common)]
        for parent in taxon.findall('LineageEx/Taxon'):
            rank = parent.findtext('Rank')
            if rank in {'class','family'}:
                rows.append(('NCBI taxonomic '+rank,parent.findtext('ScientificName')))
        evidence = json.dumps({'scientific_name':name, 'classification':dict(rows)},ensure_ascii=False)
        for relation,value in rows:
            add('Biology',name,relation,value,url,evidence)

    url = 'https://docs.python.org/3/library/stdtypes.html'
    properties = {
        'Python int': [('description','integer numeric type'),('precision','unlimited, subject to available memory')],
        'Python float': [('description','floating-point numeric type')],
        'Python complex': [('description','numeric type with real and imaginary components')],
        'Python bool': [('subclass of','Python int')],
        'Python list': [('description','mutable sequence'),('mutability','mutable')],
        'Python tuple': [('description','immutable sequence'),('mutability','immutable')],
        'Python str': [('description','immutable sequence of Unicode code points'),('mutability','immutable')],
        'Python range': [('description','immutable sequence of numbers'),('mutability','immutable')],
        'Python dict': [('description','mutable mapping'),('key requirement','hashable')],
        'Python set': [('description','unordered collection of distinct hashable objects'),('mutability','mutable')],
        'Python frozenset': [('mutability','immutable')],
        'Python bytes': [('description','immutable sequence of bytes')],
        'Python bytearray': [('description','mutable sequence of bytes')],
        'Python and': [('evaluation','short-circuit'),('result','one of its operands')],
        'Python or': [('evaluation','short-circuit'),('result','one of its operands')],
    }
    for name, rows in properties.items():
        for relation,value in rows:
            add('Computing',name,relation,value,url,f'Authored paraphrase of built-in types documentation: {name}: {value}.')

    keys = [(r['translation']['operations'][0]['subject'],r['translation']['operations'][0]['relation'],r['translation']['operations'][0]['object']) for r in lessons]
    assert len(keys) == len(set(keys))
    (HERE/'lessons.json').write_text(json.dumps(lessons,ensure_ascii=False,indent=2)+'\n')
    notebook = {'sensors':[], 'language':[{k:r[k] for k in ['original','translation']} |
                {'source':'reference-expansion','interpretation':r['domain']+' lesson','answer':'Prepared sourced assertion.'}
                for r in lessons]}
    (HERE/'seed-reference-notebook.json').write_text(json.dumps(notebook,ensure_ascii=False,indent=2)+'\n')
    manifest={'prepared_at':retrieved,'assertions':len(lessons),'domains':dict(Counter(r['domain'] for r in lessons)),
              'source_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                [HERE/'pubchem-elements.json',HERE/'worldbank-countries.json',HERE/'ncbi-taxonomy.xml']}}
    (HERE/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(manifest,indent=2))


if __name__ == '__main__':
    build()
