#!/bin/sh
# After the live guard runs: rerun G0 runs that still failed, under separate tags, then label, score and upload them.
cd "$(dirname "$0")/.."
until [ -f data/live_guards.done ]; do sleep 60; done
uv run python -m agent_govbench.run --tag full-policy-r --configs G0 --variant policy --ids-file data/rerun_full-policy_ids.txt --workers 8 --retries 4 --upload > data/rerun_policy.log 2>&1
uv run python -m agent_govbench.run --tag full-task-r --configs G0 --variant task_only --ids-file data/rerun_full-task_ids.txt --workers 8 --retries 4 --upload > data/rerun_task.log 2>&1
until [ -f data/offline.done ]; do sleep 60; done
for t in full-policy-r full-task-r; do
  uv run python -m agent_govbench.pipeline replay --tag $t > data/replay_$t.log 2>&1
  uv run python -m agent_govbench.g1b screen data/records/replay_$t.jsonl data/records/simulated_$t.jsonl >> data/g1b_screen.log 2>&1
  uv run python -m agent_govbench.pipeline upload --file data/records/replay_$t.jsonl --prefix replay/ --name a_replay_batch07_$t >> data/uploads.log 2>&1
  [ -f data/records/simulated_$t.jsonl ] && uv run python -m agent_govbench.pipeline upload --file data/records/simulated_$t.jsonl --prefix replay/ --name simulated_compromised_batch07_$t >> data/uploads.log 2>&1
done
date -u > data/reruns.done
