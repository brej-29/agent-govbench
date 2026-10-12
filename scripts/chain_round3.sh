#!/bin/sh
# Override round (2026-10-09): item 2 then item 3, Pro engine, standard tier, hard stop 14:00 IST (08:30 UTC).
cd "$(dirname "$0")/.."
ENG=projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/9187572213132296192
left() { echo $(( $(date -u -d "2026-10-09 08:30:00" +%s) - $(date -u +%s) )); }
timeout $(left) uv run python -m agent_govbench.run --tag pro-agent-task-guards --configs G6,G4:G2p+G6 --variant task_only \
  --ids-file data/pro_agent_ids.txt --engine $ENG --agent-model gemini-3.1-pro-preview --workers 8 --retries 3 \
  --usd-cap 4.0 --paired-order --upload > data/pro_guards.log 2>&1
timeout $(left) uv run python -m agent_govbench.run --tag pro-agent-policy --configs G0 --variant policy \
  --ids-file data/pilot_ids.txt --engine $ENG --agent-model gemini-3.1-pro-preview --workers 8 --retries 3 \
  --usd-cap 1.0 --paired-order --upload > data/pro_policy.log 2>&1
date -u > data/round3.done
