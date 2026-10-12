#!/bin/sh
# Judge benign runs (Flex). G0 tags start now; guarded tags after the live guard runs and reruns.
cd "$(dirname "$0")/.."
J="uv run python -m agent_govbench.judge"
$J full-policy full-task g0test pilot pilot-task v2-policy v2-task > data/judge_g0.log 2>&1
until [ -f data/reruns.done ]; do sleep 60; done
$J live-task-guards pilot-g4 full-policy-r full-task-r > data/judge_guarded.log 2>&1
$J full-policy full-task g0test pilot pilot-task v2-policy v2-task live-task-guards pilot-g4 full-policy-r full-task-r > data/judge_retry.log 2>&1
date -u > data/judge.done
