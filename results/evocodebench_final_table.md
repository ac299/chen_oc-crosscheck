| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 24 | 19 (79%) | 60%–91% | 89.0% | 51,199 | 0.0045 | 23 | 0 | 0 |
| team-collab@s2 | 24 | 18 (75%) | 55%–88% | 79.6% | 671,951 | 0.0311 | 259 | 14 | 5 |
| duo@s2 | 24 | 19 (79%) | 60%–91% | 87.6% | 370,669 | 0.0207 | 245 | 0 | 19 |
| crosscheck:v5@s2 | 24 | 19 (79%) | 60%–91% | 84.2% | 321,151 | 0.0311 | 266 | 1 | 12 |
| crosscheck:v22b@s2 | 24 | 19 (79%) | 60%–91% | 87.2% | 578,143 | 0.0351 | 325 | 0 | 3 |
| crosscheck:v6@s2 | 24 | 16 (67%) | 47%–82% | 75.6% | 372,025 | 0.0291 | 327 | 2 | 12 |
| crosscheck:v7@s2 | 24 | 19 (79%) | 60%–91% | 88.1% | 281,839 | 0.0247 | 211 | 0 | 9 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | team-collab@s2 | duo@s2 | crosscheck:v5@s2 | crosscheck:v22b@s2 | crosscheck:v6@s2 | crosscheck:v7@s2 |
|---|---|---|---|---|---|---|---|
| r_camp_zipnerf_resample | 0/3 · 142k | 0/3 · 753k | 1/3 · 791k | 0/3 · 669k | 0/3 · 639k | 0/3 · 628k | 0/3 · 566k |
| r_deluder_destroy | 3/3 · 51k | 3/3 · 745k | 3/3 · 741k | 3/3 · 446k | 3/3 · 676k | 2/3 · 314k | 3/3 · 494k |
| r_microagents_find_closest_agent | 3/3 · 58k | 3/3 · 639k | 3/3 · 297k | 3/3 · 297k | 3/3 · 427k | 2/3 · 223k | 3/3 · 278k |
| r_microsearch_search | 3/3 · 39k | 3/3 · 441k | 3/3 · 244k | 3/3 · 279k | 3/3 · 351k | 3/3 · 459k | 3/3 · 147k |
| r_searcharray_edismax | 1/3 · 246k | 1/3 · 652k | 0/3 · 789k | 2/3 · 758k | 1/3 · 752k | 1/3 · 689k | 1/3 · 683k |
| r_tanuki_py_add | 3/3 · 37k | 3/3 · 550k | 3/3 · 420k | 3/3 · 496k | 3/3 · 593k | 3/3 · 386k | 3/3 · 216k |
| r_test_agent_run_cmd | 3/3 · 26k | 3/3 · 466k | 3/3 · 179k | 3/3 · 293k | 3/3 · 451k | 3/3 · 382k | 3/3 · 180k |
| r_uhgeval_statistics | 3/3 · 53k | 2/3 · 450k | 3/3 · 377k | 2/3 · 131k | 3/3 · 183k | 2/3 · 106k | 3/3 · 188k |

Paired by (task, repeat) against crosscheck:v5@s2: wins = only crosscheck:v5@s2 resolved

| baseline | pairs | both | only crosscheck:v5@s2 | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 24 | 17 | 2 | 2 | 3 | 1.000 |
| team-collab@s2 | 24 | 16 | 3 | 2 | 3 | 1.000 |
| duo@s2 | 24 | 17 | 2 | 2 | 3 | 1.000 |
| crosscheck:v22b@s2 | 24 | 18 | 1 | 1 | 4 | 1.000 |
| crosscheck:v6@s2 | 24 | 15 | 4 | 1 | 4 | 0.375 |
| crosscheck:v7@s2 | 24 | 17 | 2 | 2 | 3 | 1.000 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 44 | 40 | 257 |
| L2 audit | 4 | 2 | 294 |
| L3 repair | 6 | 6 | 373 |
| L4 diversify | 39 | 25 | 652 |
| error | 3 | 0 | 0 |

Independent suites: 84 runs, 1691 cases, 1323 valid on reference (78.2%), 1299 fail-on-base-and-pass-on-reference (76.8%).
Auditor: 42 verdicts, 18 correct (43%); kept invalid 24, dropped valid 0.
Early stops (L1–L3): 54; of these unresolved on hidden tests: 6 ['r_camp_zipnerf_resample__crosscheck-v5@s2__r0__1795205215', 'r_camp_zipnerf_resample__crosscheck-v22b@s2__r2__1795213175', 'r_microagents_find_closest_agent__crosscheck-v6@s2__r0__1795213547', 'r_searcharray_edismax__crosscheck-v6@s2__r0__1795213905', 'r_camp_zipnerf_resample__crosscheck-v6@s2__r1__1795214766', 'r_camp_zipnerf_resample__crosscheck-v7@s2__r1__1795221740']
