#!/usr/bin/env bash
# HISTORICAL (2026-10-10): this script was run on 9 Oct 2026 and the project was then deleted. Kept as a record and as a
# template; every command targets PROJECT_ID, which no longer exists.
# Agent GovBench teardown. Run step by step: ./teardown.sh <step>   (default prints the plan; nothing runs without a step)
# Never disables any API (Project B needs aiplatform and others). Never deletes the project.
# Steps in order:
#   thu-night  stop time-billed things after the last paid run (Thu 8 Oct, after 20:00 IST check)
#   export     copy our bucket prefixes and local data to exports/ and the D: mirror (Fri)
#   fri        delete everything this project created (Fri, after export is verified)
#   buckets    empty OUR prefixes in the shared data bucket (only after Project B confirms it is done)
#   check      list anything left that this project created
set -euo pipefail
P=PROJECT_ID
R=us-central1
NUM=PROJECT_NUMBER
DATA=gs://PROJECT_ID-data
HERE="$(cd "$(dirname "$0")" && pwd)"
run() { echo "+ $*"; "$@"; }

case "${1:-plan}" in
plan)
  sed -n '2,11p' "$0" ;;

thu-night)
  # Agent Runtime and the stubs bill by instance time; drop them to zero so nothing idles overnight.
  run gcloud run services update govbench-tools --region=$R --project=$P --min-instances=0 --quiet
  for s in legacy-dms corporate-email income-verification; do run gcloud run services update $s --region=$R --project=$P --min-instances=0 --quiet; done
  echo "Agent engines are min 0 already (check: 'gcloud beta ai reasoning-engines list --region=$R')." ;;

export)
  mkdir -p "$HERE/exports/bucket"
  for pfx in gold scenarios replay traces report; do
    run gcloud storage rsync -r "$DATA/$pfx" "$HERE/exports/bucket/$pfx" || true
  done
  run gcloud storage rsync -r gs://$P-staging/fixtures "$HERE/exports/fixtures"
  run rsync -a "$HERE/data/" "$HERE/exports/local_data/"
  run rsync -a "$HERE/ledger/" "$HERE/exports/ledger/"
  mkdir -p /mnt/d/Project/gcp/agent-govbench-exports
  run rsync -a "$HERE/exports/" /mnt/d/Project/gcp/agent-govbench-exports/
  du -sh "$HERE/exports" /mnt/d/Project/gcp/agent-govbench-exports ;;

fri)
  read -r -p "Exports verified on D:? type yes: " ok; [ "$ok" = yes ]
  # 1. Agent Runtime engines (not managed by Terraform). --force also deletes their sessions.
  # NOTE: gcloud SDK 587 has no reasoning-engines command; delete via REST DELETE .../reasoningEngines/ID?force=true or with the project
  for e in 1916563391300763648 1140817530852474880 7516789527935975424 9187572213132296192; do
    run gcloud beta ai reasoning-engines delete "$e" --region=$R --project=$P --force --quiet || true
  done
  # 2. Resources created outside Terraform
  run gcloud run services delete govbench-tools --region=$R --project=$P --quiet || true
  run gcloud iam service-accounts delete govbench-tools-sa@$P.iam.gserviceaccount.com --project=$P --quiet || true
  run gcloud model-armor templates delete govbench-pi-low --location=$R --project=$P --quiet || true
  run gcloud projects remove-iam-policy-binding $P --member="principalSet://agents.global.proj-$NUM.system.id.goog/attribute.platformContainer/aiplatform/projects/$NUM" --role=roles/modelarmor.user --condition=None --quiet || true
  run gcloud projects remove-iam-policy-binding $P --member="user:$(gcloud config get-value account 2>/dev/null)" --role=roles/iam.serviceAccountUser --condition=None --quiet || true
  # Codelab local-exec that terraform destroy does not undo
  run gcloud beta services mcp content-security remove modelarmor.googleapis.com --project=$P || echo "check manually: gcloud beta services mcp content-security --help"
  # 3. Terraform stack (codelab copy). The Cloud Build bucket has force_destroy=false: empty it first.
  run gcloud storage rm -r "gs://${P}_cloudbuild/**" || true
  (cd "$HERE/infra/codelab/terraform" && run terraform destroy -input=false -auto-approve)
  # 4. Our buckets (not the shared data bucket)
  run gcloud storage rm -r gs://$P-staging || true
  run gcloud storage rm -r gs://$P-tfstate || true
  echo "Not touched on purpose: Model Armor template govbench-basic (pre-existing), the quota preference govbench-re-query-120, all APIs, the project." ;;

buckets)
  read -r -p "Project B confirmed it no longer needs gold/ scenarios/ replay/ traces/ report/? type yes: " ok; [ "$ok" = yes ]
  for pfx in gold scenarios replay traces report; do run gcloud storage rm -r "$DATA/$pfx/**" || true; done ;;

check)
  run gcloud beta ai reasoning-engines list --region=$R --project=$P
  run gcloud run services list --region=$R --project=$P
  run gcloud compute routers list --project=$P
  run gcloud compute networks list --project=$P
  run gcloud compute network-attachments list --project=$P
  run gcloud compute forwarding-rules list --project=$P
  run gcloud artifacts repositories list --location=$R --project=$P
  run gcloud alpha network-services agent-gateways list --location=$R --project=$P
  run gcloud alpha agent-registry services list --location=$R --project=$P
  run gcloud model-armor templates list --location=$R --project=$P
  run gcloud storage ls --project=$P
  run gcloud iam service-accounts list --project=$P ;;

*) echo "unknown step $1"; exit 1 ;;
esac
