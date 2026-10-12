# STATE

> **Note (2026-10-10):** the Google Cloud projects used here (PROJECT_ID and the shared bucket) were torn down and deleted on 9 Oct 2026. Resource names below are historical; nothing in this file can be run against them.

Updated: 2026-10-07 17:20 UTC (Wed 22:50 IST)

## FINAL (2026-10-10): both Google Cloud projects deleted
Both projects (PROJECT_ID and PROJECT_B_ID) were deleted on 9 Oct 2026 by the owner (state
DELETE_REQUESTED, confirmed with gcloud projects describe). The four idle reasoning engines (min 0) went with the project.
No Google calls of any kind after that; nothing in this repo can run against the old project.
Data lives in the private Hugging Face dataset BrejBala/agent-govbench (57 files, 115,170,952 bytes, listing verified
2026-10-10) and in the local exports: exports/ and /mnt/d/Project/gcp/agent-govbench-exports, 1,236 files and
458,344,339 bytes each, identical MANIFEST.sha256, D: copy verified with sha256sum -c. Off-Hub copy of the dataset:
/mnt/d/Project/gcp/agent-govbench-hf (verified against its MANIFEST.sha256). Code: private GitHub repo brej-29/agent-govbench.

## Teardown done (2026-10-09, afternoon IST)
teardown.sh fri steps 3 to 12 completed one command at a time (step 2, reasoning engines, skipped by owner decision;
terraform destroy needed one retry after Google released the gateway's PSC endpoint). See RESOURCES.md for what remains.
Nothing time-billed remains from this project except 4 idle reasoning engines at min 0. Project NOT deleted.

## Wrap-up (2026-10-09 ~12:20 IST)
- Published (private): GitHub brej-29/agent-govbench (commit 573cd75 and later); Hugging Face dataset
  BrejBala/agent-govbench (commit d7758e5), 54 files, 115,163,820 bytes, listing verified against local (data/hf_listing.tsv).
- Backups: ~/gcp/agent-govbench/exports and /mnt/d/Project/gcp/agent-govbench-exports: 1,235 files each,
  458,341,862 bytes each, MANIFEST.sha256 identical, D: copy verified with sha256sum -c. HF dataset copy outside the Hub:
  /mnt/d/Project/gcp/agent-govbench-hf (54 files + MANIFEST.sha256, project number and ID redacted).
- Secret scan (regex, working tree and full git history): no keys, tokens, private keys or service-account JSON;
  owner email removed from tracked files (still in commit author metadata and older revisions of RESOURCES.md);
  .env, terraform.tfvars, *.tfstate*, .terraform, backend.conf, agent/local.env never committed.
- Cost: per-project Billing (provisional) USD 181.22 vs ledgers A + B 181.60: gap -0.38 (-0.2%), reconciled; the earlier +41
  "gap" was a comparison error (lecvault included). teardown.sh fri approved 2026-10-09 (B: EXPORTS COMPLETE).

## NO GOOGLE CALLS LEFT (confirmed 2026-10-09 11:30 IST)
Last Google call: teacher labels for the Pro-agent records, finished 2026-10-09 11:25 IST. No jobs running; every
reasoning engine and Cloud Run service at min 0. Remaining work is local and free (publishing, write-up), plus
./teardown.sh fri after the owner's confirmation. Project deletion only after A and B confirm exports are complete.
Pro-agent records labeled: replay/a_replay_batch09..11_*_v2.jsonl + replay/_pro_agent_final_v2.json (supersede the
unlabeled versions). Final token total USD 114.10 (COSTS.md).

- Export (./teardown.sh export, rerun 2026-10-09 ~11:35 IST after the last upload): file counts

| folder | ~/gcp/agent-govbench/exports | /mnt/d/Project/gcp/agent-govbench-exports |
|---|---|---|
| bucket/gold | 2 | 2 |
| bucket/scenarios | 2 | 2 |
| bucket/replay | 31 | 31 |
| bucket/traces | 16 | 16 |
| fixtures | 1002 | 1002 |
| local_data/runs | 30 | 30 |
| local_data/records | 35 | 35 |
| ledger | 2 | 2 |

## Where we are (2026-10-07 23:45 UTC, Thu 05:15 IST)
- ALL Google-dependent work DONE: live runs (G0 both prompts on all 999 scenarios incl. 21 reruns; 996 guarded task_only;
  100 G4 policy), offline labels and scores, judge (Pro, Flex), uploads. replay/_final.json written (15 files, 9,077 records).
- Remaining: ./teardown.sh thu-night after B writes "no Google calls left" in its STATE.md (not yet, 21:46 UTC) and user
  approval of the shown commands. Then Friday: export, analysis, write-up, dataset card, publishing, teardown fri.

- 2026-10-08 ~03:00 UTC: 10 failed guarded runs rerun (0 errors, records in replay/a_replay_batch08_live-task-guards-reruns.jsonl);
  ./teardown.sh thu-night run (user-approved, B condition waived for Cloud Run): govbench-tools, legacy-dms,
  corporate-email, income-verification at min 0; all 3 reasoning engines at minInstances 0. Rest of teardown waits for Friday.
- Data defect (reported by B): identical records in a test family (fam-222cab...) and a train family (fam-03ef2d...).
  Exact-content scan of all 11,513 published records: 3 hash groups cross splits (5 families), listed with exclusion
  advice in replay/_known_issues_v1.json. CAUSE: a replay record at the agent's first call carries only the first user
  message; terse variants of different families converged on identical openers ("Check my inbox." -> read_inbox {},
  "Check order O-5526." -> lookup_order), and scenario-level dedup compared full user turns plus fixtures, which differ.
  FIX: src/agent_govbench/leakage.py drops any new record whose content hash exists in another split (test copy kept
  within a batch); wired into pipeline.build_replay, tested in tests/test_splits.py. Published files were not modified.
- teardown.sh fix: reasoning-engines commands need `gcloud beta ai`.

- 2026-10-08: enhancements. Item 1 (G7 Pro and G5 from B's scores, report/cross_family.md), item 2 (adaptive rewrites,
  87 survivors, replay/adaptive_rewrite_v1.jsonl + replay/_adaptive_final.json, report/adaptive.md, USD 2.11), item 3
  skipped (redeploy needed; over cap). Write-up draft report/WRITEUP.md, dataset card report/DATASET_CARD.md, figures
  report/figures/. Tokens USD 100.68.
