# Changes to Google's codelab (GoogleCloudPlatform/cloud-networking-solutions, demos/agent-gateway)

Upstream commit: see UPSTREAM_COMMIT.txt. Every change is tagged `GOVBENCH` in the code. Nothing else was changed.
Only demos/agent-gateway was copied, so links in README.md to codelab.md and docs/CONTRIBUTING.md point to files
that exist only upstream (https://github.com/GoogleCloudPlatform/cloud-networking-solutions/tree/main/demos/agent-gateway).
LICENSE is the upstream repository's license; NOTICE gives the attribution.

The stack was applied on 2026-10-05 in a project **without an organization**, used through 2026-10-09, destroyed with
`terraform destroy` on 2026-10-09, and the project was deleted the same day.

## Changes for a project with no organization (tag GOVBENCH-NOORG)

The codelab assumes an organization only for the Agent Identity principal. All role grants are project-level already.

| File | Change |
|---|---|
| terraform/variables.tf | variable `organization_id` removed |
| terraform/main.tf | `organization_id` no longer passed to the agent-engine module |
| terraform/modules/agent-engine/variables.tf | variable `organization_id` removed |
| terraform/modules/agent-engine/main.tf, outputs.tf | principalSet uses the project trust domain `agents.global.proj-<PROJECT_NUMBER>.system.id.goog` instead of `agents.global.org-<ORG_ID>...` (verified on a live engine's `spec.effectiveIdentity`; one docs page spells it `project-`, which is wrong) |
| terraform/example.tfvars | `organization_id` removed |
| scripts/grant_agent_mcp_egress.sh | `ORG_ID` removed; principals use the `proj-` trust domain |
| src/mortgage-agent/deploy_agent.py | no longer requires `ORG_ID` |

## Other changes

| Tag | File | Change | Why |
|---|---|---|---|
| GOVBENCH (labels) | terraform/providers.tf, cloudrun/*.yaml.tmpl | `project = agent-govbench` label on every labelable resource | cost tracking |
| GOVBENCH-COST | src/mortgage-agent/deploy_agent.py | agent min instances, CPU and memory overridable by env (codelab default 2 x 4 vCPU / 8 GiB, about USD 20 per day) | budget |
| GOVBENCH-CA | src/mortgage-agent/deploy_agent.py | ships a CA bundle (certifi + the gateway's published root CA) and points REQUESTS_CA_BUNDLE, SSL_CERT_FILE, GRPC_DEFAULT_SSL_ROOTS_FILE_PATH at it | workaround for codelab known issue 17; it did not help (see below) |
| GOVBENCH diagnostic | src/mortgage-agent/agent/__init__.py, agent/_govbench_diag.py | optional TLS diagnostic (logs only, GOVBENCH_DIAG=1) | find why the gateway-attached agent failed |
| GOVBENCH | src/corporate-email/main.py | demo addresses `@megabank.com` changed to `@megabank.example` (2026-10-11, never deployed this way) | use a reserved domain name in published code |
| local only | terraform/terraform.tfvars (untracked) | `logging_data_access = {}`: the codelab's project-wide data-access audit logs were turned off on 2026-10-05 | they logged the other project sharing the GCP project and did not help the benchmark |

## What did not work

An Agent Runtime agent attached to the Agent Gateway (AGENT_TO_ANYWHERE) never started in this project: every outbound
TLS connection received a self-signed proxy certificate (CN agent-gateway-proxy.internal) that is not signed by the
gateway's published inspection CA. Five attempts, including a fresh agent created after the gateway. IAP tool policies
and semantic governance through the gateway were therefore not tested. Evidence: docs/internal/phase1_outcome.md.

The codelab's Model Armor floor setting (enabled by default) is project-wide and rejects later templates below it
(TEMPLATE_NOT_CONFORMANT). The codelab's cleanup text uses `gcloud ai reasoning-engines`, which gcloud SDK 587 does not
ship; engines can be deleted with the REST API (`DELETE .../reasoningEngines/<ID>?force=true`) or with the project.
