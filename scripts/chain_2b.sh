#!/bin/sh
# Rerun requeued empty-stream runs, then build labeled + replay-scored records per tag. No process-name waits.
cd "$(dirname "$0")/.."
uv run python -m agent_govbench.run --tag g0test --configs G0 --ids-file data/test_ids.txt --workers 8 > data/g0test_rerun.log 2>&1
uv run python -m agent_govbench.run --tag pilot --configs G0,G1,G2p,G6 --ids-file data/pilot_ids.txt --workers 8 > data/pilot_rerun.log 2>&1
for t in g0test pilot pilot-task v2-policy v2-task; do
  uv run python -m agent_govbench.pipeline replay --tag $t > data/replay_$t.log 2>&1
done
echo chain done > data/chain_2b.done
