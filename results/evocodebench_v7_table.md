| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 24 | 19 (79%) | 60%–91% | 89.0% | 51,199 | 0.0045 | 23 | 0 | 0 |
| team-collab@s2 | 24 | 18 (75%) | 55%–88% | 79.6% | 671,951 | 0.0311 | 259 | 14 | 5 |
| duo@s2 | 24 | 19 (79%) | 60%–91% | 87.6% | 370,669 | 0.0207 | 245 | 0 | 19 |
| crosscheck:v7@s2 | 24 | 19 (79%) | 60%–91% | 88.1% | 281,839 | 0.0247 | 211 | 0 | 9 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | team-collab@s2 | duo@s2 | crosscheck:v7@s2 |
|---|---|---|---|---|
| r_camp_zipnerf_resample | 0/3 · 142k | 0/3 · 753k | 1/3 · 791k | 0/3 · 566k |
| r_deluder_destroy | 3/3 · 51k | 3/3 · 745k | 3/3 · 741k | 3/3 · 494k |
| r_microagents_find_closest_agent | 3/3 · 58k | 3/3 · 639k | 3/3 · 297k | 3/3 · 278k |
| r_microsearch_search | 3/3 · 39k | 3/3 · 441k | 3/3 · 244k | 3/3 · 147k |
| r_searcharray_edismax | 1/3 · 246k | 1/3 · 652k | 0/3 · 789k | 1/3 · 683k |
| r_tanuki_py_add | 3/3 · 37k | 3/3 · 550k | 3/3 · 420k | 3/3 · 216k |
| r_test_agent_run_cmd | 3/3 · 26k | 3/3 · 466k | 3/3 · 179k | 3/3 · 180k |
| r_uhgeval_statistics | 3/3 · 53k | 2/3 · 450k | 3/3 · 377k | 3/3 · 188k |

Paired by (task, repeat) against crosscheck:v7@s2: wins = only crosscheck:v7@s2 resolved

| baseline | pairs | both | only crosscheck:v7@s2 | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 24 | 19 | 0 | 0 | 5 | 1.000 |
| team-collab@s2 | 24 | 18 | 1 | 0 | 5 | 1.000 |
| duo@s2 | 24 | 18 | 1 | 1 | 4 | 1.000 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 8 | 8 | 158 |
| L2 audit | 2 | 1 | 218 |
| L3 repair | 4 | 4 | 267 |
| L4 diversify | 10 | 6 | 548 |

Independent suites: 20 runs, 211 cases, 175 valid on reference (82.9%), 174 fail-on-base-and-pass-on-reference (82.5%).
Auditor: 19 verdicts, 6 correct (32%); kept invalid 13, dropped valid 0.
Early stops (L1–L3): 14; of these unresolved on hidden tests: 1 ['r_camp_zipnerf_resample__crosscheck-v7@s2__r1__1795221740']
