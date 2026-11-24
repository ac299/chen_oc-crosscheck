| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 24 | 17 (71%) | 51%–85% | 90.5% | 43,662 | 0.0056 | 30 | 3 | 2 |
| team | 24 | 20 (83%) | 64%–93% | 91.2% | 204,285 | 0.0448 | 155 | 3 | 2 |
| team-collab | 24 | 18 (75%) | 55%–88% | 92.9% | 600,465 | 0.0422 | 150 | 14 | 2 |
| duo | 24 | 19 (79%) | 60%–91% | 96.9% | 137,202 | 0.0279 | 115 | 0 | 11 |
| crosscheck | 24 | 21 (88%) | 69%–96% | 99.0% | 175,841 | 0.0283 | 78 | 0 | 0 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | team | team-collab | duo | crosscheck |
|---|---|---|---|---|---|
| h1_cron | 3/3 · 71k | 2/3 · 428k | 2/3 · 731k | 2/3 · 451k | 3/3 · 399k |
| h2_calc | 2/3 · 46k | 3/3 · 229k | 3/3 · 640k | 3/3 · 360k | 3/3 · 183k |
| h3_glob | 0/3 · 320k | 2/3 · 644k | 0/3 · 611k | 2/3 · 416k | 2/3 · 567k |
| t1_semver | 3/3 · 37k | 3/3 · 235k | 3/3 · 549k | 3/3 · 102k | 3/3 · 157k |
| t3_lruttl | 3/3 · 31k | 3/3 · 71k | 3/3 · 623k | 3/3 · 121k | 3/3 · 129k |
| t4_allocate | 3/3 · 36k | 3/3 · 111k | 3/3 · 422k | 3/3 · 68k | 3/3 · 192k |
| t5_toposort | 3/3 · 35k | 3/3 · 264k | 3/3 · 400k | 3/3 · 79k | 3/3 · 92k |
| t7_bizdays | 0/3 · 73k | 1/3 · 485k | 1/3 · 708k | 0/3 · 794k | 1/3 · 148k |

Paired by (task, repeat) against crosscheck: wins = only crosscheck resolved

| baseline | pairs | both | only crosscheck | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 24 | 17 | 4 | 0 | 3 | 0.125 |
| team | 24 | 18 | 3 | 2 | 1 | 1.000 |
| team-collab | 24 | 17 | 4 | 1 | 2 | 0.375 |
| duo | 24 | 19 | 2 | 0 | 3 | 0.500 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 9 | 8 | 109 |
| L2 audit | 7 | 6 | 179 |
| L3 repair | 3 | 3 | 202 |
| L4 diversify | 5 | 4 | 552 |

Independent suites: 24 runs, 1916 cases, 1887 valid on reference (98.5%), 1590 fail-on-base-and-pass-on-reference (83.0%).
Auditor: 40 verdicts, 38 correct (95%); kept invalid 2, dropped valid 0.
Early stops (L1–L3): 19; of these unresolved on hidden tests: 2 ['t7_bizdays__crosscheck__r1__1795180338', 't7_bizdays__crosscheck__r2__1795186211']
