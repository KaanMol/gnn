# Wikipedia astronomy starter dataset

49 articles from the supplied Wikipedia XML export.

## Seed-compatible teaching notebook

`seed-wikipedia.json` is compatible with the project's existing `Session.load`
notebook importer. It contains 49 curated lessons with 68 assertions, covering
all 49 source articles. This is a small selection of supported facts, not a
conversion of every claim in those articles. Descriptions are stored properties;
they do not install executable physics or inference rules. The Oort cloud is
explicitly described as theorized. No numerical template fragments are taught.

Each lesson's `translation` is an `operations` object validated by `semantics.py`.
The `original` field preserves its evidence passage, revision URL, and timestamp;
the existing importer retains this as the assertion's source. `seed-evidence.jsonl`
also lists those sources beside the individual operations. Claims were explicitly
authored from the supplied article introductions; this is not an autonomous
article-reading capability. The legacy loader may label operations as user
assertions internally; the original evidence identifies Wikipedia as the source.

To open the separate notebook in the preview, run:

```sh
python3 /Users/kaan/Documents/ChatGPT/Idk/preview.py --port 8766 --memory /Users/kaan/Documents/ChatGPT/Idk/wikipedia-starter/seed-wikipedia.json
```

The preview still requires its normal Gemma connection. Port 8766 allows this
notebook to run alongside the default preview. It does not merge into the default
memory. The importer creates a sibling `seed-wikipedia.graph.sqlite3` on first
load; subsequent loads use that database. A validated standalone database is also
provided to avoid repeating the initial import. `seed-validation.json` records
the actual import, source preservation, queries, and restart checks.

The JSON file is a notebook, not input for the executable graph editor or chat
textbox. Rebuild its curated lesson records with `python3 build_lessons.py`.
Regenerating JSON does not replace a previously imported sibling database.

## Import into the running notebook

`load_running.py` uses the preview API at `http://127.0.0.1:8765`. It backs up
the active database, teaches a bounded import graph, archives all 49 complete
article records in `knowledge.wikipedia_articles`, and adds the 68 curated
assertions to `knowledge.assertions`. Existing assertions and their evidence
are preserved. This uses the running app's workspace port, so no restart is
needed. `live-import-report.json` records a completed verified import.

Article records contain `text_chunks`, `wikitext_chunks`, and `link_chunks` to
respect the runtime's per-string limits. Concatenating text chunks or flattening
link chunks recovers the corresponding original JSONL fields exactly. The
existing `workspace_read` skill can retrieve an article by title, for example:

```text
Run skill workspace_read: {"namespace":"knowledge.wikipedia_articles","key":"Earth"}
```

Full article storage does not imply that every sentence has become a symbolic
fact. The ordinary question-answering path uses the separately extracted facts;
it does not automatically search or interpret these archived article records.

## Original article extraction

- `articles.jsonl`: one JSON object per article, containing cleaned `text`, original `wikitext`, title, page ID, revision ID, timestamp, article URL, revision URL, and unique wiki link targets.
- `text/`: individual readable article files.
- `manifest.json`: source checksum and conversion counts.
- `convert.py`: reproducible converter; requires `mwparserfromhell==0.7.2`.

This is a preliminary text extraction, not a fully rendered Wikipedia dataset or an extracted knowledge graph. References, tables, galleries, and embedded files are removed from cleaned text. Unexpanded templates are explicitly marked; common conversion templates retain their positional arguments without calculating conversions. Some formulas or wiki syntax may remain. Original markup is preserved in every JSONL record for later, higher-fidelity processing. Do not treat omissions or template markers as factual statements.

Link targets include categories, files, fragments, and pages outside this sample. A hyperlink is not itself a semantic relationship or a verified claim.

Retain the original XML export and article/revision URLs for provenance and attribution. Wikipedia content remains subject to its applicable licenses; this conversion does not change them.

Reproduce:

```sh
python convert.py /path/to/Wikipedia-20260907140904.xml /path/to/output
```
