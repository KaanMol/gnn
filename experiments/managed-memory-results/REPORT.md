# Managed memory comparison

Frozen regression streams and three fresh seeds; all management, validation and audit costs charged.

| Seed | Split | Arm | Through | Solved | Total steps | CPU s | Methods |
|---:|---|---|---:|---:|---:|---:|---:|
| 1907 | regression | discard | 20 | 18 | 5,211,397 | 16.80 | 0 |
| 1907 | regression | discard | 40 | 30 | 11,050,954 | 35.77 | 0 |
| 1907 | regression | discard | 60 | 37 | 17,646,775 | 56.89 | 0 |
| 1907 | regression | managed | 20 | 14 | 4,818,869 | 16.84 | 3 |
| 1907 | regression | managed | 40 | 28 | 9,359,513 | 33.20 | 6 |
| 1907 | regression | managed | 60 | 40 | 14,385,237 | 51.23 | 8 |
| 1907 | regression | manager_disabled | 20 | 18 | 5,155,784 | 16.45 | 0 |
| 1907 | regression | manager_disabled | 40 | 30 | 10,962,976 | 34.61 | 0 |
| 1907 | regression | manager_disabled | 60 | 37 | 17,547,901 | 55.28 | 0 |
| 2909 | regression | discard | 20 | 18 | 5,141,595 | 16.97 | 0 |
| 2909 | regression | discard | 40 | 30 | 11,035,023 | 35.83 | 0 |
| 2909 | regression | discard | 60 | 37 | 17,638,766 | 56.99 | 0 |
| 2909 | regression | managed | 20 | 18 | 3,893,453 | 14.70 | 4 |
| 2909 | regression | managed | 40 | 34 | 8,607,165 | 31.96 | 7 |
| 2909 | regression | managed | 60 | 46 | 13,569,391 | 50.08 | 9 |
| 2909 | regression | manager_disabled | 20 | 18 | 5,087,180 | 16.26 | 0 |
| 2909 | regression | manager_disabled | 40 | 30 | 10,949,751 | 34.60 | 0 |
| 2909 | regression | manager_disabled | 60 | 37 | 17,541,865 | 55.35 | 0 |
| 3911 | regression | discard | 20 | 18 | 5,180,387 | 17.48 | 0 |
| 3911 | regression | discard | 40 | 30 | 11,060,208 | 36.78 | 0 |
| 3911 | regression | discard | 60 | 37 | 17,646,721 | 57.88 | 0 |
| 3911 | regression | managed | 20 | 15 | 4,544,799 | 16.62 | 3 |
| 3911 | regression | managed | 40 | 27 | 9,837,251 | 36.21 | 5 |
| 3911 | regression | managed | 60 | 39 | 15,156,409 | 55.19 | 7 |
| 3911 | regression | manager_disabled | 20 | 18 | 5,125,600 | 17.12 | 0 |
| 3911 | regression | manager_disabled | 40 | 30 | 10,974,244 | 36.16 | 0 |
| 3911 | regression | manager_disabled | 60 | 37 | 17,548,858 | 56.54 | 0 |
| 4903 | fresh | discard | 20 | 18 | 5,044,842 | 16.96 | 0 |
| 4903 | fresh | discard | 40 | 30 | 10,930,576 | 35.73 | 0 |
| 4903 | fresh | discard | 60 | 37 | 17,526,798 | 56.79 | 0 |
| 4903 | fresh | managed | 20 | 17 | 4,164,854 | 15.68 | 4 |
| 4903 | fresh | managed | 40 | 34 | 7,933,332 | 30.41 | 8 |
| 4903 | fresh | managed | 60 | 47 | 13,003,781 | 49.03 | 10 |
| 4903 | fresh | manager_disabled | 20 | 18 | 4,989,505 | 16.47 | 0 |
| 4903 | fresh | manager_disabled | 40 | 30 | 10,843,504 | 34.70 | 0 |
| 4903 | fresh | manager_disabled | 60 | 37 | 17,427,332 | 55.44 | 0 |
| 5903 | fresh | discard | 20 | 18 | 5,132,183 | 16.82 | 0 |
| 5903 | fresh | discard | 40 | 30 | 11,047,647 | 36.02 | 0 |
| 5903 | fresh | discard | 60 | 37 | 17,695,563 | 57.23 | 0 |
| 5903 | fresh | managed | 20 | 18 | 4,055,485 | 15.30 | 4 |
| 5903 | fresh | managed | 40 | 34 | 8,778,868 | 33.16 | 7 |
| 5903 | fresh | managed | 60 | 46 | 13,812,032 | 51.49 | 9 |
| 5903 | fresh | manager_disabled | 20 | 18 | 5,075,936 | 16.03 | 0 |
| 5903 | fresh | manager_disabled | 40 | 30 | 10,959,808 | 34.75 | 0 |
| 5903 | fresh | manager_disabled | 60 | 37 | 17,595,298 | 55.30 | 0 |
| 6907 | fresh | discard | 20 | 18 | 5,141,462 | 16.86 | 0 |
| 6907 | fresh | discard | 40 | 30 | 11,038,921 | 36.04 | 0 |
| 6907 | fresh | discard | 60 | 37 | 17,650,638 | 57.37 | 0 |
| 6907 | fresh | managed | 20 | 18 | 3,766,605 | 14.07 | 4 |
| 6907 | fresh | managed | 40 | 34 | 7,642,607 | 29.58 | 7 |
| 6907 | fresh | managed | 60 | 45 | 12,972,040 | 49.42 | 9 |
| 6907 | fresh | manager_disabled | 20 | 18 | 5,084,353 | 16.48 | 0 |
| 6907 | fresh | manager_disabled | 40 | 30 | 10,949,614 | 35.09 | 0 |
| 6907 | fresh | manager_disabled | 60 | 37 | 17,550,316 | 56.21 | 0 |

## Limitations

- Canonicalization is supplied and specific to the fixed pure reducer language, not arbitrary JS or effects.
- New seeds use the same generator; they are held-out instances/order, not new domains.
- The original negative run remains untouched.
- manager_disabled uses the same scheduler with an empty catalog; it isolates retention from scheduler effects.
- Graph-step totals charge management and audit; CPU/wall include SQLite and storage bytes are separate.
