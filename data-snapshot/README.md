# Saved local data

Lossless gzip archives preserve the project's SQLite databases and preview-memory JSON snapshots. `manifest.json` records each original path, uncompressed size, and SHA-256 checksum. The current preview database was captured through SQLite's backup API; historical and experiment databases were archived byte-for-byte.

From a fresh clone, run:

```sh
python3 scripts/restore_data.py
```

Existing files are never overwritten. Original database paths remain ignored by Git; archived copies are tracked here to fit GitHub's per-file limit. Runtime logs, caches, and environment credentials are not included. This snapshot includes previously ignored experiment databases and knowledge data.

To update the archived snapshot deliberately, run `python3 scripts/snapshot_data.py` and commit the resulting changes. Keep prior frozen experiment outputs unchanged.
