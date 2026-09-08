# Reference lessons for Seed

This expansion prepares 862 sourced assertions beyond the astronomy starter:

| Subject | Assertions | Coverage |
| --- | ---: | --- |
| Chemistry | 354 | All 118 elements: element membership, atomic number, chemical symbol |
| Geography | 428 | World Bank region and nonempty listed-capital fields for 217 country/economy records |
| Biology | 56 | NCBI names, ranks, classes, and families for 15 taxa |
| Computing | 24 | Python built-in types, mutability, and Boolean operator behavior |

## Sources and interpretation

- [PubChem periodic table](https://pubchem.ncbi.nlm.nih.gov/periodic-table/), downloaded through its periodic-table JSON endpoint.
- [World Bank country API](https://datahelpdesk.worldbank.org/knowledgebase/articles/898590-country-api-queries), excluding aggregate records. Six records have no listed capital; no capital was invented. A World Bank region is an economic/reporting grouping, not a continent. Its capital field is stored as `world bank listed capital`, without claiming it fully describes multiple capitals or constitutional status.
- [NCBI Taxonomy](https://www.ncbi.nlm.nih.gov/taxonomy), downloaded as XML. Classification predicates explicitly identify NCBI; classifications can change and this database is not a definitive nomenclatural authority. A common name is not treated as a unique entity identifier.
- [Python built-in types documentation](https://docs.python.org/3/library/stdtypes.html), paraphrased into short properties. These are reference facts, not executable Python skills.

Each assertion retains its source URL, retrieval timestamp, and supporting source fields or authored paraphrase. Source snapshots and their checksums are included. No LLM was used to infer missing fields. This set does not teach causal science, general reasoning, or every fact in these sources.

## Files

- `lessons.json`: all assertions and evidence.
- `seed-reference-notebook.json`: standalone notebook format accepted by the existing legacy loader.
- `build_lessons.py`: reproducible authoring from saved source data.
- `staging-validation.json`: tests on a copy of the existing notebook.
- `import_live.py`: existing-knowledge-preserving live import, using the previously taught workspace importer.
- `live-import-report.json`: completed live verification, counts, and backup path.

The initial staged rebuild with the expanded knowledge took about 34 seconds;
direct taught query calls took roughly 0.06–0.24 seconds. Those timings are for
this machine and test, not guarantees for chat or future larger datasets. Further
growth should address rebuild costs first.

Testing also found an existing case-insensitive entity-resolution ambiguity
between `Moon` and `moon`. The source records and exact-label graph queries are
correct; ambiguous natural-language lookup remains a separate interface issue.

After import, try asking what it knows about `Carbon`, `France`, `Homo sapiens`,
or `Python list`. Chat still relies on the existing Gemma translator; direct
structured graph-query validation is recorded separately from that translator.
