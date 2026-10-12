#!/bin/sh
# Full run, part 2 (starts when part 1 is done): live guarded runs. Standard tier.
cd "$(dirname "$0")/.."
until [ -f data/full_g0.done ]; do sleep 30; done
uv run python -m agent_govbench.run --tag live-task-guards --configs G1,G2p,G6,G4:G2p+G6 --variant task_only --ids-file data/live_task_ids.txt --workers 8 --upload > data/live_task_guards.log 2>&1
uv run python -m agent_govbench.run --tag pilot-g4 --configs G4:G2p+G6 --variant policy --ids-file data/pilot_ids.txt --workers 8 --upload > data/pilot_g4.log 2>&1
date -u > data/live_guards.done
