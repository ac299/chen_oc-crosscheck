| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 20 (67%) | 49%–81% | 74.9% | 27,587 | 0.0057 | 27 | 2 | 1 |
| duo | 30 | 14 (47%) | 30%–64% | 55.8% | 205,299 | 0.0226 | 104 | 1 | 10 |
| duo@s2 | 30 | 16 (53%) | 36%–70% | 63.3% | 356,890 | 0.0276 | 92 | 0 | 2 |
| crosscheck | 30 | 19 (63%) | 46%–78% | 74.7% | 76,877 | 0.0289 | 123 | 0 | 2 |
| crosscheck@s2 | 30 | 16 (53%) | 36%–70% | 74.7% | 142,010 | 0.0344 | 102 | 0 | 2 |
| team-collab | 30 | 16 (53%) | 36%–70% | 62.7% | 336,475 | 0.0254 | 92 | 14 | 8 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | duo | duo@s2 | crosscheck | crosscheck@s2 | team-collab |
|---|---|---|---|---|---|---|
| io_abs_current | 3/3 · 17k | 3/3 · 33k | 3/3 · 42k | 3/3 · 61k | 3/3 · 94k | 3/3 · 413k |
| io_alternating_last4 | 0/3 · 25k | 0/3 · 794k | 0/3 · 797k | 0/3 · 634k | 0/3 · 732k | 1/3 · 455k |
| io_balanced_parenthesis | 0/3 · 86k | 0/3 · 574k | 0/3 · 633k | 0/3 · 433k | 0/3 · 690k | 0/3 · 346k |
| io_bitwise_or | 3/3 · 19k | 2/3 · 357k | 3/3 · 109k | 3/3 · 83k | 3/3 · 112k | 2/3 · 251k |
| io_extra_binaryaddition | 2/3 · 52k | 0/3 · 793k | 2/3 · 651k | 1/3 · 490k | 0/3 · 520k | 0/3 · 641k |
| io_extra_fibonacci | 3/3 · 19k | 3/3 · 26k | 2/3 · 46k | 3/3 · 59k | 2/3 · 86k | 3/3 · 232k |
| io_extra_gcd | 3/3 · 37k | 3/3 · 52k | 3/3 · 85k | 3/3 · 69k | 3/3 · 120k | 3/3 · 365k |
| io_extra_trailingzeros | 3/3 · 38k | 0/3 · 796k | 1/3 · 681k | 2/3 · 200k | 2/3 · 329k | 2/3 · 507k |
| io_leetcode_geo_euclideandistancesquared | 3/3 · 21k | 3/3 · 98k | 2/3 · 329k | 3/3 · 71k | 3/3 · 186k | 2/3 · 183k |
| io_perfect_square_detector | 0/3 · 41k | 0/3 · 385k | 0/3 · 800k | 1/3 · 425k | 0/3 · 432k | 0/3 · 147k |

Paired by (task, repeat) against crosscheck: wins = only crosscheck resolved

| baseline | pairs | both | only crosscheck | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 18 | 1 | 2 | 9 | 1.000 |
| duo | 30 | 14 | 5 | 0 | 11 | 0.062 |
| duo@s2 | 30 | 15 | 4 | 1 | 10 | 0.375 |
| crosscheck@s2 | 30 | 15 | 4 | 1 | 10 | 0.375 |
| team-collab | 30 | 15 | 4 | 1 | 10 | 0.375 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 35 | 31 | 93 |
| L3 repair | 1 | 0 | 389 |
| L4 diversify | 22 | 4 | 586 |
| error | 2 | 0 | 461 |

Independent suites: 58 runs, 2301 cases, 2069 valid on reference (89.9%), 2067 fail-on-base-and-pass-on-reference (89.8%).
Auditor: 22 verdicts, 22 correct (100%); kept invalid 0, dropped valid 0.
Early stops (L1–L3): 36; of these unresolved on hidden tests: 5 ['io_perfect_square_detector__crosscheck__r0__1795191203', 'io_extra_binaryaddition__crosscheck@s2__r0__1795200187', 'io_extra_trailingzeros__crosscheck@s2__r0__1795200413', 'io_perfect_square_detector__crosscheck@s2__r0__1795200585', 'io_extra_fibonacci__crosscheck@s2__r1__1795201081']
