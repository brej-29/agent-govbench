# RESOURCES

> **Note (2026-10-10):** the Google Cloud projects used here (PROJECT_ID and the shared bucket) were torn down and deleted on 9 Oct 2026. Resource names below are historical; nothing in this file can be run against them.

Every Google Cloud resource created by this project. Teardown must match this list.

| Name | Type | Created | Time-billed cost | Status |
|---|---|---|---|---|
| (pre-existing) govbench-basic | Model Armor template, us-central1 | before Phase 0 | per token only | not mine, keep |
| (pre-existing) gs://PROJECT_ID-data | GCS bucket | before Phase 0 | storage only | shared with B, keep |
| reasoningEngines/1140817530852474880 (govbench-identity-probe) | Agent Runtime engine, us-central1, empty shell with AGENT_IDENTITY | 2026-10-05 Phase 1 | none while empty (no code deployed) | now serves the codelab agent WITHOUT gateway (min 0, 1 vCPU / 2 GiB) | delete Friday |
| gs://PROJECT_ID-tfstate | GCS bucket (versioned), Terraform state | 2026-10-05 Phase 1 | storage only (KBs) | delete Friday after destroy |
| codelab Terraform stack (227 resources, state prefix agent-gateway) | see infra/codelab/terraform, list via `terraform state list` | 2026-10-05 Phase 1 | see COSTS.md time-billed table | terraform destroy Friday |
| gs://PROJECT_ID-staging | GCS bucket, agent deploy staging | 2026-10-05 | storage only | delete Friday |
| Cloud Build images legacy-dms, corporate-email, income-verification-api in gateway-docker AR repo | Artifact Registry images | 2026-10-05 | storage (<0.5 GB free) | removed by terraform destroy (repo) |
| IAM binding user:<owner account> roles/iam.serviceAccountUser (codelab step 6) | project IAM | 2026-10-05 | none | remove Friday |
| Model Armor floor setting (project, GOOGLE_MCP_SERVER) + `gcloud beta services mcp content-security add modelarmor` (local-exec, not removed by destroy) | project setting | 2026-10-05 | none | teardown: `gcloud beta services mcp content-security remove modelarmor.googleapis.com` |
| Cloud Run legacy-dms, corporate-email, income-verification (codelab MCP servers) | Cloud Run, us-central1, min 1 instance each, 1 vCPU / 512 MiB | 2026-10-05 ~12:12 UTC | ~0.32 USD/day each, ~1 USD/day total (user approved keeping min 1 on 2026-10-05) | deleted by terraform destroy |
| reasoningEngines/7516789527935975424 (govbench-fresh-agent) | Agent Runtime engine, failed gateway experiment, empty shell | 2026-10-05 | none (no serving instance) | delete Friday |
| iap.egressor bindings for engine 7516789527935975424 on 3 MCP servers + 61 registry endpoints | IAP IAM | 2026-10-05 | none | removed with registry entries by terraform destroy |
| user:<owner account> roles/iam.serviceAccountTokenCreator on agent-mcp-invoker SA (local agent testing) | SA IAM | 2026-10-05 | none | remove Friday |
| principalSet agents.global.proj-PROJECT_NUMBER (all agents in project) roles/modelarmor.user | project IAM | 2026-10-05 | none | remove Friday |
| govbench-tools (Cloud Run, us-central1) | MCP stubs (mail, hr, payments, files, code), SA govbench-tools-sa, invoker agent-mcp-invoker SA only, min 0 / max 10, 1 vCPU 512 MiB | 2026-10-05 | request-billed; min 1 only during runs | delete Friday (`gcloud run services delete govbench-tools`) |
| govbench-tools-sa | service account (objectViewer on staging bucket) | 2026-10-05 | none | delete Friday |
| image gateway-docker/govbench-tools:v1 | Artifact Registry | 2026-10-05 | storage | removed with repo by terraform destroy |
| reasoningEngines/1916563391300763648 (govbench-agent) | Agent Runtime, AGENT_IDENTITY, no gateway, min 0 / max 10, 1 vCPU 2 GiB, concurrency 8 | 2026-10-05 | 0.085 USD/vCPU-h + 0.009 USD/GiB-h while instances run | delete Friday |
| gs://PROJECT_ID-staging/fixtures/ | scenario fixture JSON (synthetic) | 2026-10-05 | storage only | delete with bucket Friday |
| Codelab MCP servers legacy-dms, corporate-email, income-verification scaled to min 0 | Cloud Run change (gcloud, drifts from tfvars min 1) | 2026-10-05 15:09 UTC | ~0 idle | destroyed Friday |
| Data-access audit logs (allServices) | REMOVED 2026-10-05 via targeted terraform apply (tfvars logging_data_access = {}); measured ~27 MB/day before | | | |
| Model Armor template govbench-pi-low (us-central1) | PI LOW_AND_ABOVE + floor-required filters; G1 variant reads PI result only | 2026-10-07 | per token | delete Friday |
| govbench-tools min instances 0 -> 1 for the full run | Cloud Run change | 2026-10-07 18:05 UTC | ~0.3 USD/day | set back to 0 or delete Thu night |
| batchPredictionJobs/3903785935287877632 (global, govbench-batch-test5) | Vertex batch test, 5 trivial rows, Pro | 2026-10-07 20:00 UTC | per token, cents | finishes by itself; outputs in gs://PROJECT_ID-staging/batch/test5/ |
| govbench-tools + 3 codelab MCP services back to min 0 (teardown.sh thu-night) | Cloud Run | 2026-10-08T02:40:08Z | ~0 idle | |
| reasoningEngines/9187572213132296192 (govbench-agent-pro) | Agent Runtime, AGENT_IDENTITY, gemini-3.1-pro-preview agent model, min 0 / max 10, 1 vCPU 2 GiB (item 3) | 2026-10-08 19:00 UTC | per instance time while serving | delete Friday |
| (verified 2026-10-09 03:30 IST) govbench-agent-pro minInstances 0; govbench-tools and 3 codelab services min 0 | | | | |
| replay batches 09-11 + replay/_pro_agent_final.json | bucket objects (Pro-agent records) | 2026-10-09 | storage | with data bucket |

## Teardown result (2026-10-09, teardown.sh fri approved by the owner; step 2 skipped by owner decision)
- Deleted: Cloud Run govbench-tools, service account govbench-tools-sa, Model Armor template govbench-pi-low, IAM bindings
  (agent principalSet modelarmor.user, owner serviceAccountUser), MCP content-security setting, Cloud Build bucket
  contents, the whole codelab Terraform stack (226 resources: 111 on the first apply, 115 on the retry after the gateway's
  PSC endpoint was released by Google about 7 minutes later), staging bucket, tfstate bucket. No API was disabled.
- Remaining by decision: 4 reasoning engines (min 0, gcloud SDK 587 has no reasoning-engines command; they go with the
  project deletion), gs://PROJECT_ID-data (shared with B; our prefixes not emptied), Model Armor template
  govbench-basic (pre-existing), quota preference govbench-re-query-120.
- Remaining, not created by this project: default network, default compute service account,
  gs://cloud-ai-platform-e11dc804-5563-40c0-b570-9fa298d315b4 (Vertex default staging bucket, owner unknown, likely the
  SDK or Project B), completed batch prediction job records (no cost).

## Final resource list (2026-10-10): nothing remains
Both Google Cloud projects (PROJECT_ID, and Project C's separate PROJECT_B_ID) were deleted on
9 Oct 2026 (DELETE_REQUESTED). Everything listed above, including the four reasoning engines left at min 0, the shared
data bucket, the govbench-basic template and the quota preference, was deleted with the project. Google keeps a deleted
project recoverable for about 30 days, then purges it; no resource of this benchmark exists outside that.
