#!/bin/sh
# Item 3: unguarded Pro agent, task-only prompt, 149 test scenarios. Starts when item 2 is done or at 23:00 UTC (04:30 IST).
cd "$(dirname "$0")/.."
until [ -f data/loop.done ] || [ "$(date -u +%H%M)" -ge 2300 ]; do sleep 30; done
uv run python -m agent_govbench.run --tag pro-agent-task --configs G0 --variant task_only --ids-file data/pro_agent_ids.txt \
  --engine projects/PROJECT_NUMBER/locations/us-central1/reasoningEngines/9187572213132296192 --agent-model gemini-3.1-pro-preview \
  --workers 8 --retries 3 --upload > data/pro_agent.log 2>&1
date -u > data/pro_agent.done
