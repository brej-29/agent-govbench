# Phase 1 outcome (final, 2026-10-05 ~15:20 UTC / 20:50 IST)

> **Note (2026-10-10):** the Google Cloud projects used here (PROJECT_ID and the shared bucket) were torn down and deleted on 9 Oct 2026. Resource names below are historical; nothing in this file can be run against them.

## Outcome table

| Capability | Works as documented | Works with changes | Blocked |
|---|---|---|---|
| Codelab Terraform stack, project without organization | | YES. Removed organization_id; Agent Identity principal uses project trust domain `agents.global.proj-<PROJECT_NUMBER>.system.id.goog` (verified on a live engine). No org-level role grants exist in the stack, all grants are project-level. 227 resources applied, exit 0. | |
| Agent Gateway (AGENT_TO_ANYWHERE) creation | YES (created in 2m25s, root CA published) | | |
| MCP servers on Cloud Run + Agent Registry | YES (3 services, 3 registry mcpServers) | | |
| Per-MCP iap.egressor grant for an agent principal | | YES (grant script with proj- trust domain; setIamPolicy accepted on 2 MCP servers) | |
| Agent Runtime agent with AGENT_IDENTITY, no gateway | | YES (codelab agent, gemini-3.8-flash, 1 vCPU / 2 GiB / min 0 instead of 2 x 4 vCPU / 8 GiB). Registry discovery + MCP call to Cloud Run via SA impersonation work; one query 24.2 s incl. cold start. | |
| Model Armor, direct sanitize API (G1 fallback) | YES. Injection prompt -> `pi_and_jailbreak MATCH_FOUND (HIGH)` on both govbench-basic and agw-request-template; agw-request-template also flagged `rai harassment MEDIUM_AND_ABOVE` on the same benign-ish text. | | |
| Agent Runtime agent attached to the gateway | | | BLOCKED, see evidence |
| (a) IAP/IAM tool policy enforcement, 403 on disallowed tool | | | NOT REACHED (needs agent traffic through gateway) |
| (b) Model Armor via gateway CONTENT_AUTHZ | | | NOT REACHED (same reason). Extension and policy resources were created fine. |
| (c) Semantic governance policy | API reachable, not exercised. Reason: needs gateway-routed traffic. (`gcloud beta ai semantic-governance-policies list` returns 0 items, no permission error.) | | |

## Evidence for the blocker

Agent update with `agent_gateway_config.agent_to_anywhere_config.agent_gateway = .../agentGateways/agent-gateway`
fails with: `{'code': 13, 'message': "The Reasoning Engine failed to deploy and cannot serve traffic. ..."}`.

Container log: `UserCodeControlPlaneError: ... HTTPSConnectionPool(host='telemetry.mtls.googleapis.com', port=443): Max retries exceeded ...
SSLCertVerificationError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate')`,
plus the same error from Agent Registry discovery and IAM credentials calls.

Tried (each a different change):
1. Codelab deploy as is (only sizing changed) -> fails.
2. Shipped a CA bundle = certifi + gateway `agentGatewayCard.rootCertificates` (CN "Agent Gateway TLS Inspection CA (us-central1)"),
   set REQUESTS_CA_BUNDLE / SSL_CERT_FILE / GRPC_DEFAULT_SSL_ROOTS_FILE_PATH -> same failure. (Workaround from codelab known-issues #17.)
3. In-container TLS diagnostic: env vars are set, bundle file exists, but the gateway proxy presents a SELF-SIGNED leaf
   `subject=issuer=CN=agent-gateway-proxy.internal,O=Google Cloud Managed Service`, SAN `agent-gateway-proxy.internal`,
   for every host tested: telemetry(.mtls), aiplatform(.mtls), agentregistry(.mtls), oauth2.googleapis.com, the Cloud Run MCP URL, www.example.com.
   It is not signed by the published inspection CA, and its SAN never matches the target host, so no client trust store can accept it.
4. No gateway data-plane / IAP logs exist for these requests: traffic dies at the TLS handshake inside the agent.

Interpretation (not confirmed): the gateway's TLS inspection is not issuing per-host certificates in this project, and it serves a
fallback certificate instead. Possible causes: a provisioning issue, a dependency on something only org-scoped projects get, or a
Preview limitation. I cannot fix this from the client side without disabling TLS verification, which would invalidate the measurement.
5. Gateway proxy load-balancer logs (`LoadBalancerLogEntry`, SECURE_WEB_GATEWAY) since 12:00 UTC: 0 entries. So the requests may never
   reach the managed Secure Web Proxy at all; the self-signed `agent-gateway-proxy.internal` cert may come from a local forwarding hop
   inside the runtime. Not confirmed.

## Remaining untested hypothesis
The engine used for all attempts was created (as an empty AGENT_IDENTITY shell) BEFORE the gateway existed, then updated. Codelab
known-issue 17 says the deploy pipeline bakes gateway trust in when the gateway is ready at deploy time; the codelab flow creates the
shell after terraform apply. A fresh engine created after the gateway is the one cheap experiment left (~10 min, ~0 USD).

## Fresh-agent experiment (approved extension, 2026-10-05 ~15:00 UTC)
New engine `reasoningEngines/7516789527935975424`, shell created after the gateway was ready, exact codelab flow
(shell, grant script on 3 MCP servers + 61 endpoints, update with code). Result: identical failure, the same self-signed
`CN=agent-gateway-proxy.internal` leaf on aiplatform.googleapis.com and the Cloud Run URL. Hypothesis rejected.

## Decision
No-gateway path (user instruction 2026-10-05): G0, G1 via direct Model Armor API, a deterministic in-agent policy
layer (G2') as the G2/G3 stand-in, G4, G5 (replay), G6. G2 via IAP and G3 semantic governance: not tested, reason above.
