| method | runs | resolved | 95% CI | mean hidden pass | mean tokens | median tokens | mean cost $ | mean s | failed status | escape runs |
|---|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|
| crosscheck:v7@s2 | 60 | 31 (52%) | 39%–64% | 71.4% | 420,363 | 536,955 | 0.0465 | 150 | 1 | 9 |
| single-sh | 60 | 25 (42%) | 30%–54% | 54.0% | 333,151 | 108,893 | 0.0212 | 51 | 27 | 1 |
| single | 60 | 29 (48%) | 36%–61% | 64.9% | 73,241 | 38,415 | 0.0110 | 63 | 12 | 5 |
| team-collab@s2 | 60 | 26 (43%) | 32%–56% | 52.6% | 373,949 | 257,677 | 0.0269 | 88 | 34 | 9 |
| duo@s2 | 60 | 26 (43%) | 32%–56% | 54.6% | 496,931 | 788,946 | 0.0300 | 105 | 2 | 8 |

Resolved runs per task (out of repeats), mean tokens in thousands

| task | crosscheck:v7@s2 | single-sh | single | team-collab@s2 | duo@s2 |
|---|---|---|---|---|---|
| io_add_mod_4 | 1/3 · 686k | 0/3 · 424k | 2/3 · 99k | 0/3 · 519k | 0/3 · 794k |
| io_add_mod_6 | 2/3 · 683k | 0/3 · 710k | 3/3 · 81k | 0/3 · 745k | 1/3 · 792k |
| io_alternating_last3 | 0/3 · 715k | 0/3 · 794k | 0/3 · 60k | 0/3 · 567k | 0/3 · 796k |
| io_diff_abs_values | 3/3 · 292k | 2/3 · 58k | 1/3 · 24k | 0/3 · 361k | 1/3 · 796k |
| io_extra_allpositive | 0/3 · 440k | 0/3 · 13k | 0/3 · 18k | 2/3 · 420k | 0/3 · 243k |
| io_extra_balancedparentheses | 0/3 · 658k | 0/3 · 401k | 0/3 · 281k | 0/3 · 417k | 0/3 · 791k |
| io_extra_hammingweight | 3/3 · 117k | 3/3 · 22k | 3/3 · 52k | 3/3 · 228k | 3/3 · 321k |
| io_extra_listproduct | 3/3 · 52k | 3/3 · 19k | 2/3 · 22k | 3/3 · 291k | 3/3 · 61k |
| io_extra_modulo | 3/3 · 251k | 3/3 · 17k | 2/3 · 44k | 3/3 · 237k | 3/3 · 312k |
| io_extra_polishrpn | 3/3 · 100k | 2/3 · 288k | 3/3 · 34k | 3/3 · 309k | 3/3 · 226k |
| io_extra_reverselist | 3/3 · 74k | 3/3 · 17k | 3/3 · 24k | 2/3 · 259k | 3/3 · 71k |
| io_leetcode_geo_447_numberofboomerangs | 0/3 · 642k | 0/3 · 781k | 0/3 · 40k | 0/3 · 237k | 0/3 · 797k |
| io_leetcode_geo_593_validsquare | 0/3 · 685k | 0/3 · 678k | 0/3 · 67k | 1/3 · 608k | 1/3 · 565k |
| io_leetcode_geo_boundingboxperimeter | 3/3 · 380k | 1/3 · 307k | 1/3 · 280k | 2/3 · 286k | 1/3 · 580k |
| io_leetcode_geo_midpointintegercheck | 0/3 · 533k | 0/3 · 277k | 0/3 · 158k | 0/3 · 339k | 0/3 · 384k |
| io_majority_0_2 | 0/3 · 681k | 0/3 · 782k | 0/3 · 74k | 0/3 · 575k | 0/3 · 791k |
| io_max_seen | 3/3 · 124k | 3/3 · 28k | 3/3 · 25k | 3/3 · 250k | 3/3 · 86k |
| io_newton_spring | 3/3 · 78k | 3/3 · 15k | 3/3 · 19k | 3/3 · 241k | 3/3 · 63k |
| io_parity_zeros | 0/3 · 716k | 2/3 · 651k | 2/3 · 36k | 0/3 · 352k | 1/3 · 670k |
| io_sum_last5 | 1/3 · 502k | 0/3 · 381k | 1/3 · 27k | 1/3 · 237k | 0/3 · 799k |

Paired by (task, repeat) against crosscheck:v7@s2: wins = only crosscheck:v7@s2 resolved

| baseline | pairs | both | only crosscheck:v7@s2 | only baseline | neither | sign-test p |
|---|---:|---:|---:|---:|---:|---:|
| single-sh | 60 | 23 | 8 | 2 | 27 | 0.109 |
| single | 60 | 24 | 7 | 5 | 24 | 0.774 |
| team-collab@s2 | 60 | 22 | 9 | 4 | 25 | 0.267 |
| duo@s2 | 60 | 24 | 7 | 2 | 27 | 0.180 |

CrossCheck: where runs stopped

| level | runs | resolved | mean tokens (k) |
|---|---:|---:|---:|
| L1 verify | 23 | 22 | 106 |
| L2 audit | 1 | 1 | 330 |
| L4 diversify | 27 | 8 | 600 |
| error | 9 | 0 | 693 |

Independent suites: 34 runs, 594 cases, 566 valid on reference (95.3%), 564 fail-on-base-and-pass-on-reference (94.9%).
Auditor: 11 verdicts, 10 correct (91%); kept invalid 1, dropped valid 0.
Early stops (L1–L3): 24; of these unresolved on hidden tests: 1 ['io_leetcode_geo_midpointintegercheck__crosscheck-v7@s2__r2__1795328196']
