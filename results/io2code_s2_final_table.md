| method | runs | resolved | 95% CI | mean hidden pass | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 20 (67%) | 49%–81% | 74.9% | 27,587 | 0.0057 | 27 | 2 | 1 |
| team-collab@s2 | 30 | 19 (63%) | 46%–78% | 70.7% | 353,484 | 0.0251 | 66 | 10 | 8 |
| duo@s2 | 30 | 16 (53%) | 36%–70% | 63.3% | 356,890 | 0.0276 | 92 | 0 | 2 |
| crosscheck@s2 | 30 | 16 (53%) | 36%–70% | 74.7% | 142,010 | 0.0344 | 102 | 0 | 2 |
| crosscheck:v4@s2 | 30 | 17 (57%) | 39%–73% | 75.1% | 253,341 | 0.0407 | 112 | 0 | 9 |
| crosscheck:v5@s2 | 30 | 17 (57%) | 39%–73% | 66.7% | 355,298 | 0.0393 | 116 | 0 | 6 |
| crosscheck:v6@s2 | 30 | 18 (60%) | 42%–75% | 73.8% | 208,652 | 0.0394 | 121 | 1 | 6 |
| crosscheck:v7@s2 | 30 | 20 (67%) | 49%–81% | 74.4% | 296,131 | 0.0382 | 107 | 0 | 5 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | single | team-collab@s2 | duo@s2 | crosscheck@s2 | crosscheck:v4@s2 | crosscheck:v5@s2 | crosscheck:v6@s2 | crosscheck:v7@s2 |
|---|---|---|---|---|---|---|---|---|
| io_abs_current | 3/3 · 17k | 3/3 · 230k | 3/3 · 42k | 3/3 · 94k | 3/3 · 118k | 3/3 · 126k | 3/3 · 128k | 3/3 · 48k |
| io_alternating_last4 | 0/3 · 25k | 0/3 · 362k | 0/3 · 797k | 0/3 · 732k | 0/3 · 785k | 0/3 · 644k | 1/3 · 571k | 0/3 · 665k |
| io_balanced_parenthesis | 0/3 · 86k | 0/3 · 588k | 0/3 · 633k | 0/3 · 690k | 0/3 · 405k | 0/3 · 724k | 0/3 · 571k | 0/3 · 679k |
| io_bitwise_or | 3/3 · 19k | 3/3 · 283k | 3/3 · 109k | 3/3 · 112k | 3/3 · 173k | 3/3 · 217k | 3/3 · 142k | 3/3 · 102k |
| io_extra_binaryaddition | 2/3 · 52k | 2/3 · 441k | 2/3 · 651k | 0/3 · 520k | 1/3 · 724k | 1/3 · 593k | 0/3 · 567k | 3/3 · 723k |
| io_extra_fibonacci | 3/3 · 19k | 3/3 · 168k | 2/3 · 46k | 2/3 · 86k | 2/3 · 107k | 3/3 · 99k | 3/3 · 127k | 3/3 · 83k |
| io_extra_gcd | 3/3 · 37k | 3/3 · 388k | 3/3 · 85k | 3/3 · 120k | 3/3 · 194k | 3/3 · 180k | 3/3 · 205k | 3/3 · 174k |
| io_extra_trailingzeros | 3/3 · 38k | 1/3 · 502k | 1/3 · 681k | 2/3 · 329k | 2/3 · 621k | 1/3 · 561k | 2/3 · 523k | 2/3 · 652k |
| io_leetcode_geo_euclideandistancesquared | 3/3 · 21k | 3/3 · 329k | 2/3 · 329k | 3/3 · 186k | 3/3 · 133k | 3/3 · 134k | 3/3 · 226k | 3/3 · 149k |
| io_perfect_square_detector | 0/3 · 41k | 1/3 · 338k | 0/3 · 800k | 0/3 · 432k | 0/3 · 754k | 0/3 · 704k | 0/3 · 758k | 0/3 · 505k |

Paired by (task, repeat) against crosscheck@s2: wins = only crosscheck@s2 resolved

| baseline | pairs | both | only crosscheck@s2 | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single | 30 | 16 | 0 | 4 | 10 | 0.125 |
| team-collab@s2 | 30 | 15 | 1 | 4 | 10 | 0.375 |
| duo@s2 | 30 | 14 | 2 | 2 | 12 | 1.000 |
| crosscheck:v4@s2 | 30 | 15 | 1 | 2 | 12 | 1.000 |
| crosscheck:v5@s2 | 30 | 15 | 1 | 2 | 12 | 1.000 |
| crosscheck:v6@s2 | 30 | 15 | 1 | 3 | 11 | 0.625 |
| crosscheck:v7@s2 | 30 | 15 | 1 | 5 | 9 | 0.219 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 82 | 70 | 156 |
| L2 audit | 6 | 6 | 235 |
| L4 diversify | 53 | 12 | 684 |
| error | 9 | 0 | 694 |

Independent suites: 130 runs, 6517 cases, 5938 valid on reference (91.1%), 5921 fail-on-base-and-pass-on-reference (90.9%).
Auditor: 77 verdicts, 61 correct (79%); kept invalid 16, dropped valid 0.
Early stops (L1–L3): 88; of these unresolved on hidden tests: 12 ['io_extra_binaryaddition__crosscheck@s2__r0__1795200187', 'io_extra_trailingzeros__crosscheck@s2__r0__1795200413', 'io_perfect_square_detector__crosscheck@s2__r0__1795200585', 'io_extra_fibonacci__crosscheck@s2__r1__1795201081', 'io_balanced_parenthesis__crosscheck-v4@s2__r1__1795204453', 'io_extra_fibonacci__crosscheck-v4@s2__r1__1795204701', 'io_extra_binaryaddition__crosscheck-v5@s2__r2__1795208593', 'io_extra_binaryaddition__crosscheck-v6@s2__r0__1795209495', 'io_balanced_parenthesis__crosscheck-v6@s2__r2__1795212098', 'io_extra_binaryaddition__crosscheck-v6@s2__r2__1795212385', 'io_balanced_parenthesis__crosscheck-v4@s2__r2__1795213159', 'io_perfect_square_detector__crosscheck-v7@s2__r2__1795217477']
