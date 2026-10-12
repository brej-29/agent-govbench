# COSTS

> **Note (2026-10-10):** the Google Cloud projects used here (PROJECT_ID and the shared bucket) were torn down and deleted on 9 Oct 2026. Resource names below are historical; nothing in this file can be run against them.

Budget: hard ceiling USD 140, soft stop USD 110 (stop and ask).
Token costs come from usage_metadata, logged per call in ledger/model_calls.jsonl, priced with src/agent_govbench/costs.py.

## Price table (USD)
| Item | Price | Source |
|---|---|---|
| gemini-3.8-flash (global) | standard 1.50 / 7.50 per 1M; Flex and batch 0.75 / 3.75 (billed SKU, verified 2026-10-05; intro price comes back as credits) | Cloud Billing SKU extract (B docs_ref) |
| gemini-3.1-pro-preview (global) | standard 2 / 12; Flex and batch 1 / 6 per 1M | Cloud Billing SKU extract |
| Agent Platform compute | 0.085 per vCPU-hour, 0.009 per GiB-hour, ~50 vCPU-h and 100 GiB-h free per month | brief |
| Model Armor | 2M tokens/month free, then 0.10 per 1M tokens | Security Command Center pricing page (via search, verify) |
| Agent Gateway | 1 Agent Compute vCPU-hour per 15,000 API or authz calls (about 5.7 USD per 1M calls) | search result citing Google pricing, verify |
| Cloud NAT | 0.0014 USD per VM-hour up to 32 VMs, 0.045 USD/GiB processed | Cloud NAT pricing (from memory, verify) |
| Cloud Run tier 1 | request-based: 0.000024 USD/vCPU-s active, 0.0000025 idle min instance; memory 0.0000025 USD/GiB-s | Cloud Run pricing (from memory, page did not render, verify) |
| Cloud Build | 2,500 build-minutes/month free on default pool | verify |
| Artifact Registry | 0.5 GB free, then 0.10 USD/GB-month | verify |

## Ledger by phase
| Phase | Item | Calls | Input tok | Output tok | Thinking tok | USD |
|---|---|---|---|---|---|---|
| 0 | sanity call gemini-3.8-flash | 1 | 6 | 1 | 0 | 0.00001 |

## Time-billed infrastructure (start / stop)
| Resource | Rate | Started | Stopped |
|---|---|---|---|
| Cloud NAT gateway-nat-gateway (router gateway-nat-router) | 0.0014 USD per VM-hour (no VMs here, so ~0) + 0.045 USD/GiB processed | 2026-10-05 12:1x UTC (terraform apply 11:57-12:12 UTC) | |
| Cloud Run x3 MCP servers (codelab), min 1 instance each, 1 vCPU / 512 MiB, cpu-throttling on | idle min instance ~0.0000025 USD/vCPU-s + ~0.0000025 USD/GiB-s, about 0.32 USD/day per service, ~1 USD/day for 3 (partly inside free tier) | 2026-10-05 ~12:12 UTC | |
| Agent Gateway agent-gateway | 1 Agent Compute vCPU-hour (0.085 USD) per 15,000 calls; no idle charge found | 2026-10-05 ~12:05 UTC | |
| Network attachments x2, PSC interface | no hourly charge found; data processing only | 2026-10-05 | |
| Data access audit logs, allServices (codelab foundation) | Logging ingestion 0.50 USD/GiB above 50 GiB/month free | 2026-10-05 | |

| 3-4 | scenario generation 500 families (Flex) | 516 | | | | 5.84 |
| 4 | teacher labels, audits, relabel 2,850 (Flex, Flash + Pro); incl. ~4 USD lost in a crashed run | 6,578 | | | | 24.51 |
| 4-5 | G6 offline replay (Flex) | 1,829 | | | | 2.91 |
| 5 | live agent runs + live guards (standard): smoke, pilot 400, g0test 264, pilot-task 100, v2 320 | ~1,285 traces | | | | 10.57 |

Running total tokens: USD 43.84 (2026-10-06 05:30 UTC). Infrastructure: read from Billing report (estimate USD 4-6).


## Ledger vs Billing report (gap), preliminary, 2026-10-07 report

Billing is per project, so it covers Project A (this repo) and Project B together. Source: owner-pasted Billing report,
gross usage in INR, 13 Sep to 7 Oct evening, lags up to a day. Conversion 95.99 INR per USD: the currencyConversionRate in
the Cloud Billing SKU catalog (Project B checked 4,955 SKUs, all 95.987 to 95.989), not the assumed 94.3.
Cut-off used for the ledgers: end of 2026-10-06 Pacific (2026-10-07 07:00 UTC), since the report lags about a day.

Token lines
| Line | INR | USD | Ledger A | Ledger B | A + B | Gap (billed minus ledgers) |
|---|---|---|---|---|---|---|
| Vertex AI (Gemini tokens, plus Agent Runtime compute and B's tuning) | 7,735.97 | 80.59 | 43.84 | 35.04 | 78.88 | +1.71 (2.1%) |

Ledger A 43.84 = harness ledger 33.26 (generation, labels, offline G6) + agent and live-guard tokens from usage_metadata
10.57 (the ledger shows no calls between 2026-10-06 05:30 and 2026-10-07 07:00 UTC). Ledger B 35.04 = 36.51 at 17:15 UTC
minus the 1.47 B spent on Pacific day 10-07.
Likely gap explanation, not yet verified: Agent Runtime compute (vCPU and GiB hours of the reasoning engines) bills under
Vertex AI and is in neither token ledger; most of it should sit inside the monthly free tier.

Infrastructure lines (no ledger covers these)
| Line | INR | USD | Ledger | Notes |
|---|---|---|---|---|
| Networking | 24.99 | 0.26 | none | Cloud NAT, PSC interface and network attachments, Agent Gateway (codelab stack) |
| Cloud Run | 15.81 | 0.16 | none | codelab MCP servers at min 1 for ~3 h, govbench-tools stubs |
| Cloud Storage | 1.95 | 0.02 | none | data, staging, tfstate buckets |
| Artifact Registry, Cloud Monitoring, Dataplex | 0 | 0 | none | |
| Billing total | 7,778.72 | 81.04 | | |

Flags: not covered by any ledger: Agent Runtime compute (inside Vertex AI), Networking, Cloud Run, Cloud Storage.
Not in the report at all (expected 0): Model Armor (inside the 2M tokens per month free tier so far), Cloud Build
(free tier), Cloud Logging (free tier). Final comparison with the Friday morning numbers.

## FINAL cost comparison (PROVISIONAL until the owner re-pastes the Billing report on Saturday)

Per-project Billing report, gross usage, 13 Sep to 9 Oct (lags up to a day). Rate 95.99 INR per USD
(currencyConversionRate in the Cloud Billing SKU catalog).

| Item | INR | USD |
|---|---|---|
| PROJECT_ID (Project A and Project B together) | 17,395.53 | 181.22 |
| Ledgers: A (this repo, final) + B (B's COSTS.md) | | 114.10 + 67.50 = 181.60 |
| Gap (billed minus ledgers) | | -0.38 (-0.2%) |
| lecvault (Project C, separate project, not compared) | 4,531.81 | 47.21 |

The project reconciles: the two token ledgers match the billed amount within 0.2%. Infrastructure (Networking, Cloud
Run, Cloud Storage, Artifact Registry, Agent Runtime compute) is inside that noise. The earlier "+41 USD gap" was a
comparison error: the 21,468.38 INR total included lecvault. Project A's spend is about USD 114, under the USD 140
ceiling. Note: the report shows a Vertex AI region label asia-southeast1 that does not match our us-central1 and global
usage; cause unknown; totals reconcile.

## Teacher labels for the Pro-agent records, 2026-10-09 (cap USD 2.6, Flex): USD 1.53
413 previously unlabeled records labeled (teacher-v2, Flash first, Pro on Flash blocks and a 10% sample), 4 disputed.
Finished 11:25 IST.

## FINAL token total (no Google calls after 2026-10-09 11:25 IST): USD 114.10
Harness ledger 69.21 (generation, labels, offline guards, judge, adaptive and hijack studies) + live agent and live guard
tokens from usage_metadata 44.89. Infrastructure (Billing report, see gap table; plus estimates in ledger/infra.jsonl) is
on top; final comparison with the owner's Friday Billing numbers.

## Override round, 2026-10-09 (cap USD 8, hard stop 14:30 IST): USD 4.96 tokens
| Item | Cap | USD (standard tier) | Result |
|---|---|---|---|
| 1 Policy-prompt live G1, G2', G6 on the 100 pilot scenarios | 3 | 0 | skipped: already existed (pilot tag, 100 runs each, 0 failed) |
| 2 Pro agent with live G6 and G4, task-only, 149 test scenarios | 4 | 4.00 | stopped at the cap: 116 scenarios x 2 configs = 232 runs, 0 failed |
| 3 Pro agent, policy prompt, no guard, pilot scenarios | 1 | 0.96 | stopped at the cap: 76 of 100 runs, 0 failed |
No teacher labels for the new records (would have cost about 2.4 and left little headroom); uploaded with construction
labels only. Infrastructure: Agent Runtime compute for govbench-agent-pro about 0.2 (estimate, under Vertex AI).
Project tokens after this round: about USD 112.6.

## Enhancements round 2, 2026-10-08/09 (cap USD 20, deadline Fri 08:00 IST): USD 6.93 tokens
| Item | Cap | USD (billed rates, Flex for 1 and 2, standard for 3) |
|---|---|---|
| 1 Guard-hijack test (Pro rewrites, validity, G6, G7) | 4 | 1.28 |
| 2 Deeper adaptive loop (4 rounds, Pro and Flash attackers, G6, G7, validity; incl. 16 reruns) | 8 | 3.91 |
| 3 Pro as agent model (149 unguarded task-only runs, standard tier) | 7 | 1.74 |
Infrastructure for these items (ledger/infra.jsonl, estimates): Agent Runtime compute for govbench-agent-pro about 0.15
(under Vertex AI); Cloud Run stub requests inside the free tier; no Cloud Build builds and no Artifact Registry images
in this project (Agent Runtime builds the container on Google's side); Model Armor inside its free tier.
Project tokens after round 2: USD 107.60 (ledger 67.68 + live agent and guards 39.92).

## Enhancements 2026-10-08 (cap USD 12 for items 2 and 3)
| Item | USD |
|---|---|
| 10 guarded reruns + labels (standard + Flex) | about 0.2 |
| G1b screening of 155 remaining texts (Model Armor) | about 0 (free tier) |
| Item 1 cross-family G7/G5 (B's existing scores, no Google calls) | 0 |
| Item 2 adaptive rewrites (Pro rewrites, validity, G6, G7; Flex) | 2.11 |
| Item 3 Pro as agent model | skipped (needs container redeploy; about 5.3 projected for 150 runs, over the 4 cap) |

## Status 2026-10-07 23:45 UTC (Thu 05:15 IST): all paid work done
Tokens USD 98.37 (harness ledger 60.31: generation, labels, offline G6, judge; live agent and live guards 38.06).
Infrastructure billed so far about USD 0.4 plus Agent Runtime compute inside the Vertex AI line (see gap table).
Remaining paid: none planned. Time-billed: govbench-tools at min 1 until ./teardown.sh thu-night.

## Projection for plan A (updated 2026-10-07 19:55 UTC)
Tokens now 71.90 (harness 46.09 + live 25.81). Remaining: live guard runs about 13, labels and offline scores about 13, judge about 4; infrastructure about 5. Projected total about 107. Pause line 118.

### Earlier projection (2026-10-07 17:20 UTC)
Spent tokens 43.84 + remaining tokens about 51 (live G0 13.5, live guards 15, labels and offline scores 18, judge 4)
+ infrastructure about 10 = about 105. Pause line 118, hard ceiling 140.
