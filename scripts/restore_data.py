"""Restore archived data; never overwrite existing files. Run from a fresh clone."""
import gzip, hashlib, json, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
folder = root / 'data-snapshot'
for entry in json.loads((folder / 'manifest.json').read_text()):
    target = root / entry['path']
    if target.exists():
        print('Keeping existing', entry['path'])
        continue
    data = gzip.decompress((folder / entry['archive']).read_bytes())
    if len(data) != entry['bytes'] or hashlib.sha256(data).hexdigest() != entry['sha256']:
        raise ValueError('Invalid archive: ' + entry['path'])
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as output:
        output.write(data)
    print('Restored', entry['path'])
