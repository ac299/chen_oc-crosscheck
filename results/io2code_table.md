| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 20 (67%) | 49%–81% | 74.9% | 27,587 | 0.0057 | 27 | 2 | 1 |
| team-collab | 30 | 16 (53%) | 36%–70% | 62.7% | 336,475 | 0.0254 | 92 | 14 | 8 |
| duo | 30 | 14 (47%) | 30%–64% | 55.8% | 205,299 | 0.0226 | 104 | 1 | 10 |
| crosscheck | 30 | 19 (63%) | 46%–78% | 74.7% | 76,877 | 0.0289 | 123 | 0 | 2 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | team-collab | duo | crosscheck |
|---|---|---|---|---|
| io_abs_current | 3/3 · 17k | 3/3 · 413k | 3/3 · 33k | 3/3 · 61k |
| io_alternating_last4 | 0/3 · 25k | 1/3 · 455k | 0/3 · 794k | 0/3 · 634k |
| io_balanced_parenthesis | 0/3 · 86k | 0/3 · 346k | 0/3 · 574k | 0/3 · 433k |
| io_bitwise_or | 3/3 · 19k | 2/3 · 251k | 2/3 · 357k | 3/3 · 83k |
| io_extra_binaryaddition | 2/3 · 52k | 0/3 · 641k | 0/3 · 793k | 1/3 · 490k |
| io_extra_fibonacci | 3/3 · 19k | 3/3 · 232k | 3/3 · 26k | 3/3 · 59k |
| io_extra_gcd | 3/3 · 37k | 3/3 · 365k | 3/3 · 52k | 3/3 · 69k |
| io_extra_trailingzeros | 3/3 · 38k | 2/3 · 507k | 0/3 · 796k | 2/3 · 200k |
| io_leetcode_geo_euclideandistancesquared | 3/3 · 21k | 2/3 · 183k | 3/3 · 98k | 3/3 · 71k |
| io_perfect_square_detector | 0/3 · 41k | 0/3 · 147k | 0/3 · 385k | 1/3 · 425k |

Paired by (task, repeat) against crosscheck: wins = only crosscheck resolved

| baseline | pairs | both | only crosscheck | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 18 | 1 | 2 | 9 | 1.000 |
| team-collab | 30 | 15 | 4 | 1 | 10 | 0.375 |
| duo | 30 | 14 | 5 | 0 | 11 | 0.062 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 17 | 17 | 69 |
| L3 repair | 1 | 0 | 389 |
| L4 diversify | 10 | 2 | 510 |
| error | 2 | 0 | 461 |

Independent suites: 28 runs, 1032 cases, 933 valid on reference (90.4%), 933 fail-on-base-and-pass-on-reference (90.4%).
Auditor: 7 verdicts, 7 correct (100%); kept invalid 0, dropped valid 0.
Early stops (L1–L3): 18; of these unresolved on hidden tests: 1 ['io_perfect_square_detector__crosscheck__r0__1795191203']
