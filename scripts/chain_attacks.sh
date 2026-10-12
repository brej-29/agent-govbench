#!/bin/sh
# Item 1 is already running (done marker data/hijack.done). Then item 2 (deeper adaptive loop).
cd "$(dirname "$0")/.."
until [ -f data/hijack.done ]; do sleep 30; done
uv run python -m agent_govbench.attacks assemble-hijack > data/hijack_assemble.log 2>&1
uv run python -m agent_govbench.attacks loop > data/loop.log 2>&1
uv run python -m agent_govbench.attacks assemble-loop > data/loop_assemble.log 2>&1
date -u > data/loop.done
