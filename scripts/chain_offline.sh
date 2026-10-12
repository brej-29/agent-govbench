#!/bin/sh
# Offline (Flex) processing as live batches finish: labels, offline guard scores, G1 variant screening, uploads.
# Waits on log lines and done-files only (no process-name matching).
cd "$(dirname "$0")/.."
P="uv run python -m agent_govbench.pipeline"
G1B="uv run python -m agent_govbench.g1b screen"
up() { [ -f "$1" ] && $P upload --file "$1" --prefix replay/ --name "$2" >> data/uploads.log 2>&1; }

until grep -q "^finished" data/full_policy.log 2>/dev/null; do sleep 60; done
$P replay --tag full-policy > data/replay_full-policy.log 2>&1
$G1B data/records/replay_full-policy.jsonl data/records/simulated_full-policy.jsonl >> data/g1b_screen.log 2>&1
up data/records/replay_full-policy.jsonl a_replay_batch02_full-policy
up data/records/simulated_full-policy.jsonl simulated_compromised_batch02_full-policy

$P score-scenarios > data/score_scenarios.log 2>&1
$G1B data/records/scenarios_scored.jsonl >> data/g1b_screen.log 2>&1

until [ -f data/full_g0.done ]; do sleep 60; done
$P replay --tag full-task > data/replay_full-task.log 2>&1
$G1B data/records/replay_full-task.jsonl data/records/simulated_full-task.jsonl >> data/g1b_screen.log 2>&1
up data/records/replay_full-task.jsonl a_replay_batch03_full-task
up data/records/simulated_full-task.jsonl simulated_compromised_batch03_full-task

until [ -f data/live_guards.done ]; do sleep 60; done
for t in live-task-guards pilot-g4 pilot; do $P replay-guarded --tag $t > data/replay_guarded_$t.log 2>&1; done
up data/records/replay_guarded_live-task-guards.jsonl a_replay_batch04_live-task-guards
up data/records/replay_guarded_pilot-g4.jsonl a_replay_batch05_pilot-g4
up data/records/replay_guarded_pilot.jsonl a_replay_batch06_pilot-guards
date -u > data/offline.done
