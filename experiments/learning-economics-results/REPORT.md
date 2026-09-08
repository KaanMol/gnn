# Online learning economics

Three frozen 60-task streams. All totals include graph retrieval, failed search, feedback, validation, retention and final audit. CPU/wall include SQLite work. Storage growth is reported separately.

| Seed | Through task | Arm | Cumulative solved | Cumulative steps | Last 20: steps / solved | Learned methods | DB growth bytes |
|---:|---:|---|---:|---:|---:|---:|---:|
| 1907 | 20 | discard | 18 | 5,211,397 | 289,522 | 0 | 102,400 |
| 1907 | 20 | retain | 10 | 6,502,488 | 650,248 | 7 | 667,648 |
| 1907 | 40 | discard | 30 | 11,050,954 | 486,630 | 0 | 217,088 |
| 1907 | 40 | retain | 16 | 13,883,562 | 1,230,179 | 9 | 933,888 |
| 1907 | 60 | discard | 37 | 17,646,775 | 942,260 | 0 | 286,720 |
| 1907 | 60 | retain | 22 | 21,906,246 | 1,337,114 | 12 | 1,286,144 |
| 2909 | 20 | discard | 18 | 5,141,595 | 285,644 | 0 | 114,688 |
| 2909 | 20 | retain | 11 | 6,540,459 | 594,587 | 7 | 659,456 |
| 2909 | 40 | discard | 30 | 11,035,023 | 491,119 | 0 | 208,896 |
| 2909 | 40 | retain | 17 | 14,632,555 | 1,348,683 | 12 | 1,187,840 |
| 2909 | 60 | discard | 37 | 17,638,766 | 943,392 | 0 | 299,008 |
| 2909 | 60 | retain | 23 | 22,689,613 | 1,342,843 | 14 | 1,449,984 |
| 3911 | 20 | discard | 18 | 5,180,387 | 287,799 | 0 | 114,688 |
| 3911 | 20 | retain | 10 | 6,674,575 | 667,457 | 2 | 294,912 |
| 3911 | 40 | discard | 30 | 11,060,208 | 489,985 | 0 | 217,088 |
| 3911 | 40 | retain | 19 | 13,702,001 | 780,825 | 6 | 716,800 |
| 3911 | 60 | discard | 37 | 17,646,721 | 940,930 | 0 | 307,200 |
| 3911 | 60 | retain | 24 | 21,578,749 | 1,575,350 | 9 | 1,044,480 |

## Task roles

| Arm | Role | Solved / tasks | Total steps | Validation rejections | Audit false positives |
|---|---|---:|---:|---:|---:|
| discard | novel | 30/72 | 27,959,969 | 0 | 0 |
| discard | reuse_opportunity | 27/36 | 12,401,852 | 0 | 0 |
| discard | irrelevant | 18/36 | 9,051,195 | 0 | 0 |
| discard | misleading | 36/36 | 3,519,228 | 0 | 0 |
| retain | novel | 24/72 | 26,753,605 | 0 | 0 |
| retain | reuse_opportunity | 13/36 | 13,192,061 | 0 | 0 |
| retain | irrelevant | 10/36 | 14,568,040 | 0 | 0 |
| retain | misleading | 22/36 | 11,660,884 | 5 | 0 |

## Sustained crossover

- Seed 1907: none.
- Seed 2909: none.
- Seed 3911: none.

A crossover requires lower cumulative total steps and at least as many solved tasks, maintained through the end of this finite stream. It does not establish future economics.

The model starts without learned compositions. Validation may add feedback for one retry; audit happens after retention and never influences the library. Stored aliases of single calls and exactly repeated operation sequences are rejected. The four most recent methods receive prefix probes; all stored names remain in exhaustive search.

## Limitations

- Finite supplied primitives and task families, with supplied schema adapters.
- Recurrence is intentional; unfamiliar inputs and late families are not open-ended domains.
- Three fixed seeds, not independent real-world datasets.
- Recency policy is supplied; no autonomous routing algorithm discovery.
- Library size may stay small; this cannot establish large-library scalability.
- Timing on a shared machine is secondary to deterministic graph-step accounting.
