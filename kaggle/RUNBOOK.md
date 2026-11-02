# Runbook: resume the sweep on your own machine

Everything is in `kaggle/` on branch `claude/kind-ritchie-xs4sfk` (also read `STATUS.md`, `PLAN.md`, `RESULTS.md`).

## Setup (once)
```bash
python -m venv .venv && . .venv/bin/activate
pip install kaggle-benchmarks kaggle pandas pytest
export KAGGLE_API_TOKEN=...        # your Kaggle access token; never commit it
kaggle b quota                      # daily and monthly Model Proxy spend: $10 per rolling 24 h, $100 per 30 days (refill 2026-11-28)
kaggle b t list                     # should list the three tasks (plus the pilot once pushed)
```
Needs Python 3.11+. Local runs of the tasks are not needed: `kaggle b t run` executes on Kaggle. (Local `python task.py` needs the
Model Proxy host reachable; this repo's cloud sandbox blocked it, your machine probably does not.)

## Run a queue
```bash
python kaggle/sweep.py --queue kaggle/queue_day5.txt --max-inflight 2 --daily-cap 7.0 --dl kaggle/runs
```
- Queue line: `<task-slug> <model-slug>`; `#` lines are comments. Keep `--max-inflight` at 2 or 3 (batch CPU cap is shared with your other Kaggle work).
- `--daily-cap` is the "used today" level above which no new run launches. The Model Proxy rejects requests once the day's $10 is reached,
  which silently drops items from a run in flight, so leave at least $3 of margin.
- The driver must stay alive until runs finish (it downloads results). If it dies, check `kaggle b t status <task>` and download with
  `kaggle b t download <task> -o <fresh dir> -m <model>` (use a NEW empty folder).
- A task you push runs once on gemini-3.8-flash at creation (about $1 to $1.5). Do not re-push the three main tasks; a new version means rerunning every model.
- To rerun a model on a task (variance), put a new line for it in a NEW queue file.

## Read the ledger and results
- `kaggle/ledger.jsonl`: one line per finished run: queue file and line (`key`), task, model, state, `daily_used_after` (quota used when it finished).
  A queue line whose key is in the ledger is skipped on restart.
- Per-item table: `python kaggle/analyze.py kaggle/runs --out runs.csv` (cost from Kaggle's own figures, tokens, outcome, raw judge output, lenient parse).
- Scores with intervals, cost, Pro vs Flash paired test: `python kaggle/results_table.py runs.csv --out kaggle/RESULTS.md`
  (runs with under 95% of items are marked incomplete and excluded; 95% or more count missing items as failures).
- Pilot: `python kaggle/codemix/analyze_pilot.py runs.csv --out pilot_section.md`.
- Offline tests: `python -m pytest tests/test_kaggle_port.py`.

## Runs that remain after 2026-11-05 (estimated cost)
Filled in by the final wake; at planning time: gpt-6-sol 3 tasks (about $6; test one agent item first, reasoning is forced off);
pilot reruns on opus-5-5 and gemma-4-31b (about $1.5); further variance reruns; gemini-3.1-pro judge and policy reruns (about $8). The month stays under $100 with
about $45 of headroom after the scheduled windows.

## Do by hand in the Kaggle web UI (nothing here is done yet; nothing is public)
1. Decide and say "go" before anything is made public. Until then every task and the dataset are private.
2. Publish the dataset `agent-govbench-items` (Dataset page, Settings/Sharing, set to Public) after checking its description. A public task needs public data.
3. Publish the three tasks (and the pilot if you want it): `kaggle b t publish <slug>` or the task page's Make public. Publishing also publishes the backing notebook unless you pass `--no-publish-backing-notebook`.
4. Create the benchmark and add the tasks: see `UI_STEPS.md`.
5. Review the benchmark page text and the grant draft (`GRANT_DRAFT.md`), then submit the grant form yourself.
6. Review provenance is recorded (owner's statement of 2026-11-02, in `kaggle/codemix/README.md`): keep that line wherever the pilot is published.
