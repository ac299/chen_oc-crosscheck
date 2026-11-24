| method | runs | resolved | 95% CI | mean hidden pass | mean tokens | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| crosscheck:v7@s2 | 60 | 41 (68%) | 56%–79% | 88.6% | 241,228 | 141,731 | 0.0196 | 73 | 1 | 15 |
| single-sh | 60 | 39 (65%) | 52%–76% | 88.9% | 38,495 | 33,583 | 0.0034 | 16 | 1 | 2 |
| single | 60 | 38 (63%) | 51%–74% | 84.2% | 32,072 | 26,334 | 0.0028 | 18 | 0 | 3 |
| team-collab@s2 | 60 | 41 (68%) | 56%–79% | 85.3% | 476,228 | 442,960 | 0.0316 | 102 | 8 | 25 |
| duo@s2 | 60 | 41 (68%) | 56%–79% | 86.8% | 222,932 | 140,044 | 0.0195 | 78 | 6 | 31 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | crosscheck:v7@s2 | single-sh | single | team-collab@s2 | duo@s2 |
|---|---|---|---|---|---|
| c_1 | 3/3 · 152k | 3/3 · 43k | 0/3 · 26k | 3/3 · 368k | 3/3 · 125k |
| c_18 | 2/3 · 159k | 0/3 · 38k | 3/3 · 22k | 1/3 · 375k | 0/3 · 152k |
| c_2 | 2/3 · 92k | 2/3 · 39k | 2/3 · 50k | 3/3 · 400k | 3/3 · 95k |
| c_21 | 3/3 · 263k | 2/3 · 61k | 2/3 · 36k | 3/3 · 342k | 3/3 · 182k |
| c_22 | 3/3 · 231k | 3/3 · 25k | 3/3 · 18k | 2/3 · 658k | 3/3 · 159k |
| c_3 | 3/3 · 84k | 3/3 · 23k | 3/3 · 18k | 3/3 · 470k | 3/3 · 94k |
| c_30 | 3/3 · 125k | 3/3 · 26k | 3/3 · 21k | 3/3 · 713k | 2/3 · 404k |
| c_37 | 3/3 · 110k | 3/3 · 31k | 3/3 · 20k | 3/3 · 377k | 3/3 · 87k |
| c_38 | 0/3 · 405k | 0/3 · 25k | 0/3 · 19k | 0/3 · 414k | 0/3 · 101k |
| c_5 | 3/3 · 323k | 3/3 · 43k | 0/3 · 16k | 3/3 · 552k | 3/3 · 205k |
| c_6 | 3/3 · 74k | 3/3 · 20k | 3/3 · 23k | 3/3 · 366k | 3/3 · 81k |
| c_60 | 3/3 · 191k | 3/3 · 31k | 3/3 · 32k | 3/3 · 418k | 3/3 · 83k |
| c_65 | 0/3 · 125k | 0/3 · 59k | 0/3 · 51k | 0/3 · 571k | 0/3 · 439k |
| c_71 | 3/3 · 703k | 2/3 · 101k | 3/3 · 45k | 3/3 · 603k | 3/3 · 396k |
| c_79 | 3/3 · 103k | 3/3 · 32k | 3/3 · 37k | 3/3 · 432k | 3/3 · 116k |
| c_89 | 0/3 · 133k | 0/3 · 28k | 0/3 · 16k | 0/3 · 491k | 0/3 · 583k |
| c_91 | 1/3 · 72k | 1/3 · 29k | 2/3 · 51k | 2/3 · 391k | 2/3 · 194k |
| c_92 | 0/3 · 375k | 0/3 · 31k | 0/3 · 25k | 0/3 · 292k | 0/3 · 140k |
| c_97 | 0/3 · 454k | 2/3 · 52k | 2/3 · 90k | 0/3 · 630k | 1/3 · 724k |
| c_99 | 3/3 · 651k | 3/3 · 34k | 3/3 · 26k | 3/3 · 660k | 3/3 · 99k |

Paired by (task, repeat) against crosscheck:v7@s2: wins = only crosscheck:v7@s2 resolved

| baseline | pairs | both | only crosscheck:v7@s2 | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single-sh | 60 | 35 | 6 | 4 | 15 | 0.754 |
| single | 60 | 32 | 9 | 6 | 13 | 0.607 |
| team-collab@s2 | 60 | 39 | 2 | 2 | 17 | 1.000 |
| duo@s2 | 60 | 37 | 4 | 4 | 15 | 1.000 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 23 | 18 | 99 |
| L2 audit | 15 | 8 | 134 |
| L3 repair | 5 | 3 | 266 |
| L4 diversify | 16 | 11 | 548 |
| error | 1 | 1 | 95 |

Independent suites: 59 runs, 1576 cases, 1258 valid on reference (79.8%), 1130 fail-on-base-and-pass-on-reference (71.7%).
Auditor: 212 verdicts, 68 correct (32%); kept invalid 144, dropped valid 0.
Early stops (L1–L3): 43; of these unresolved on hidden tests: 14 ['c_91__crosscheck-v7@s2__r0__1795329445', 'c_89__crosscheck-v7@s2__r0__1795329486', 'c_65__crosscheck-v7@s2__r0__1795329907', 'c_38__crosscheck-v7@s2__r0__1795330325', 'c_89__crosscheck-v7@s2__r1__1795331443', 'c_65__crosscheck-v7@s2__r1__1795331908', 'c_97__crosscheck-v7@s2__r1__1795332315', 'c_92__crosscheck-v7@s2__r1__1795332623', 'c_2__crosscheck-v7@s2__r1__1795332857', 'c_91__crosscheck-v7@s2__r2__1795333462', 'c_89__crosscheck-v7@s2__r2__1795333497', 'c_18__crosscheck-v7@s2__r2__1795333883', 'c_65__crosscheck-v7@s2__r2__1795333955', 'c_38__crosscheck-v7@s2__r2__1795334438']
