| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 20 (67%) | 49%–81% | 74.9% | 27,587 | 0.0057 | 27 | 2 | 1 |
| crosscheck | 30 | 19 (63%) | 46%–78% | 74.7% | 76,877 | 0.0289 | 123 | 0 | 2 |
| crosscheck:v3 | 30 | 17 (57%) | 39%–73% | 67.6% | 109,555 | 0.0300 | 99 | 0 | 2 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | crosscheck | crosscheck:v3 |
|---|---|---|---|
| io_abs_current | 3/3 · 17k | 3/3 · 61k | 3/3 · 44k |
| io_alternating_last4 | 0/3 · 25k | 0/3 · 634k | 0/3 · 772k |
| io_balanced_parenthesis | 0/3 · 86k | 0/3 · 433k | 0/3 · 552k |
| io_bitwise_or | 3/3 · 19k | 3/3 · 83k | 3/3 · 84k |
| io_extra_binaryaddition | 2/3 · 52k | 1/3 · 490k | 2/3 · 555k |
| io_extra_fibonacci | 3/3 · 19k | 3/3 · 59k | 2/3 · 39k |
| io_extra_gcd | 3/3 · 37k | 3/3 · 69k | 3/3 · 34k |
| io_extra_trailingzeros | 3/3 · 38k | 2/3 · 200k | 1/3 · 554k |
| io_leetcode_geo_euclideandistancesquared | 3/3 · 21k | 3/3 · 71k | 3/3 · 71k |
| io_perfect_square_detector | 0/3 · 41k | 1/3 · 425k | 0/3 · 504k |

Paired by (task, repeat) against crosscheck: wins = only crosscheck resolved

| baseline | pairs | both | only crosscheck | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 18 | 1 | 2 | 9 | 1.000 |
| crosscheck:v3 | 30 | 14 | 5 | 3 | 8 | 0.727 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 33 | 31 | 76 |
| L2 audit | 2 | 2 | 73 |
| L3 repair | 3 | 0 | 401 |
| L4 diversify | 18 | 3 | 601 |
| error | 4 | 0 | 630 |

Independent suites: 57 runs, 1858 cases, 1625 valid on reference (87.5%), 1620 fail-on-base-and-pass-on-reference (87.2%).
Auditor: 41 verdicts, 34 correct (83%); kept invalid 7, dropped valid 0.
Early stops (L1–L3): 38; of these unresolved on hidden tests: 5 ['io_perfect_square_detector__crosscheck__r0__1795191203', 'io_extra_fibonacci__crosscheck-v3__r0__1795198071', 'io_extra_binaryaddition__crosscheck-v3__r0__1795197999', 'io_perfect_square_detector__crosscheck-v3__r0__1795198144', 'io_balanced_parenthesis__crosscheck-v3__r1__1795198242']
