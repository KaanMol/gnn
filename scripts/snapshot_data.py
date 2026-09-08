"""Archive local databases without changing experiment originals."""
import gzip, hashlib, json, pathlib, shutil, sqlite3, tempfile
root = pathlib.Path(__file__).resolve().parents[1]
out = root / 'data-snapshot'
out.mkdir(exist_ok=True)
paths = sorted(root.rglob('*.sqlite3')) + sorted(root.glob('preview-memory*.json'))
manifest = []
for path in paths:
    if '.git' in path.parts or 'data-snapshot' in path.parts:
        continue
    relative = path.relative_to(root)
    target = out / (str(relative) + '.gz')
    target.parent.mkdir(parents=True, exist_ok=True)
    source = path
    temp = None
    if relative.as_posix() == 'preview-memory.graph.sqlite3':
        temp = tempfile.NamedTemporaryFile(suffix='.sqlite3')
        with sqlite3.connect(f'file:{path}?mode=ro', uri=True) as src, sqlite3.connect(temp.name) as dst:
            src.backup(dst)
        source = pathlib.Path(temp.name)
    digest = hashlib.sha256()
    with source.open('rb') as src, target.open('wb') as raw, gzip.GzipFile(filename='', mode='wb', fileobj=raw, mtime=0, compresslevel=6) as dst:
        while block := src.read(1024 * 1024):
            digest.update(block)
            dst.write(block)
    manifest.append(dict(path=relative.as_posix(), archive=target.relative_to(out).as_posix(), bytes=source.stat().st_size, sha256=digest.hexdigest()))
    if temp: temp.close()
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(f'Archived {len(manifest)} files')
