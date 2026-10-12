#!/bin/sh
# Full run, part 1: unguarded (G0) live runs on every scenario of the 999 set, both prompts. Standard tier.
cd "$(dirname "$0")/.."
uv run python -m agent_govbench.run --tag full-policy --configs G0 --variant policy --ids-file data/full_g0_policy_ids.txt --workers 8 --upload > data/full_policy.log 2>&1
uv run python -m agent_govbench.run --tag full-task --configs G0 --variant task_only --ids-file data/full_g0_task_only_ids.txt --workers 8 --upload > data/full_task.log 2>&1
date -u > data/full_g0.done
