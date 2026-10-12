# CHECKPOINT 2b (2026-10-06 ~05:30 UTC / 11:00 IST)

> **Note (2026-10-10):** the Google Cloud projects used here (PROJECT_ID and the shared bucket) were torn down and deleted on 9 Oct 2026. Resource names below are historical; nothing in this file can be run against them.

All live runs: standard tier. Offline scoring, labels, generation: Flex tier.

## 1. Label audit (decision 1)
Teacher v2 = taxonomy_v0.md verbatim + explicit adoption and precedence rules + Project B's record rendering.
Re-audit of the same 191 records: verdict agreement 174/186 parseable (93.5%). Adjudicated by hand:
real verdict errors 8 (4.3%), category-only real errors 44 (24%), auditor errors 3, ambiguous 3.
Causes (templates): injection families where the user adopts the content ("do what it says"), and user attacks with
manipulative style labeled with the seed category instead of social_engineering by precedence. Templates fixed
(gen-v3 rules), no regeneration needed. Relabel of all 2,850 scenario records (Flash, Pro on disagreement):
verdict changed 55 (1.9%), category corrected 533 (18.7%), disputed 200 (7.0%, label null, excluded from metrics).

## 2. Proposed calls per split and condition, outcomes (decisions 2, 3, 5)
## Proposed calls per split and condition (G0 runs, standard tier)

| run set | condition | runs | real calls proposed | real malicious (construction) | real benign-scenario calls | simulated malicious | split: test real mal / sim mal |
|---|---|---|---|---|---|---|---|
| v1 pilot (100) | policy | 100 | 129 | 1 ({'train': 1, 'test': 0, 'val': 0}) | 85 | 61 ({'train': 49, 'test': 9, 'val': 3}) | 0 / 9 |
| v1 pilot (100) | task_only | 99 | 266 | 43 ({'train': 35, 'val': 2, 'test': 6}) | 98 | 26 ({'train': 21, 'test': 4, 'val': 1}) | 6 / 4 |
| v1 test split (264) | policy | 264 | 313 | 0 ({'test': 0}) | 191 | 152 ({'test': 152}) | 0 / 152 |
| v2 sample (160) | policy | 155 | 239 | 4 ({'test': 3, 'train': 1}) | 126 | 94 ({'test': 73, 'train': 21}) | 3 / 73 |
| v2 sample (160) | task_only | 154 | 359 | 44 ({'train': 9, 'test': 35}) | 151 | 56 ({'train': 14, 'test': 42}) | 35 / 42 |

## Outcomes by condition (G0)

| run set | condition | attack success | harmful call proposed | benign completed | median s | p95 s | agent USD/run |
|---|---|---|---|---|---|---|---|
| v1 pilot (100) | policy | 1/62 | 1/62 | 38/38 | 39.1 | 115.5 | 0.0085 |
| v1 pilot (100) | task_only | 35/61 | 35/61 | 36/38 | 26.3 | 79.1 | 0.0108 |
| v1 test split (264) | policy | 0/152 | 0/152 | 108/112 | 39.1 | 112.6 | 0.0081 |
| v2 sample (160) | policy | 4/98 | 4/98 | 56/57 | 14.8 | 48.8 | 0.0109 |
| v2 sample (160) | task_only | 43/99 | 43/99 | 53/55 | 20.1 | 61.8 | 0.0121 |

Latency note: runs before the 2026-10-05 ~19:20 UTC harness fix include quota-queue wait (pilot, g0test); later runs exclude it.

Totals now in the bucket (replay/): 1,306 real decision records (test: 57 malicious, 741 benign) and 389 simulated
compromised-agent records (test: 280 malicious). Test malicious = 337 (target about 100 met).

## 3. First offline look at guards on identical test records (bootstrap 95% CI, not yet clustered by family)
| test-split records | n | G1 Model Armor | G2' rules | G6 LLM guard |
|---|---|---|---|---|
| real malicious, block rate | 55 | 58% [45, 71] | 73% [62, 84] | 93% [85, 98] |
| simulated malicious, block rate | 280 | 40% [34, 46] | 88% [84, 92] | 100% [99, 100] |
| real benign, false positive rate | 740 | 31% [27, 34] | 0% [0, 0] | 0% [0, 0] |
Caveats: G2' was written by the same author as the scenarios (optimistic); G6 shares the model family with the agent
and the simulated calls follow visibly from injected context (optimistic); G1 screens text, so it also blocks
benign calls inside attack conversations.

## 4. Measured unit costs
agent run G0: policy 0.008 to 0.011 USD, task_only 0.011 to 0.012 USD; live G6 adds about 0.004 USD per run;
label call Flash 0.0029, Pro 0.0060; G6 replay 0.0016 per record; all-in per new replay record about 0.006 USD.
Throughput: Agent Runtime quota 30 queries/min (increase to 120 requested, still pending), about 11 runs/min.
Error rate: 1.4% silent empty streams (now detected and retried); 0 hard failures after retries.

## 5. Spend so far
Tokens USD 43.84 (generation 5.84, labeling 24.51, G6 replay 2.91, live runs 10.57). Infrastructure not included:
please read the Billing report; my estimate is USD 4 to 6 so far.

## 6. Size options (decision needed)
| | A (recommended) | B |
|---|---|---|
| scenarios | 1,000 = all 384 test + 616 train/val | 1,200 = all 384 test + 816 train/val |
| G0 live, both conditions | about 1,220 new runs | about 1,620 new runs |
| live guard subset | task_only: 250 x G1, G2', G6, G4; policy: reuse pilot 100 x 4 | task_only 300 x 4 + policy 150 x 4 |
| offline replay (G1, G2', G6, G4) | all records | all records |
| full-split extra table (untrained guards) | yes | yes |
| remaining tokens | about 52 | about 72 |
| remaining infra (to Fri) | about 10 | about 10 |
| projected total incl. spent | about 110 | about 130 (over 125 soft stop) |
| run time at 30/min | about 3.5 h live + 2 h offline | about 5 h live + 2.5 h offline |
Labeling stays Flash-first with Pro on Flash blocks (drops the random 10% Pro sample to save money; gold measures label quality).
