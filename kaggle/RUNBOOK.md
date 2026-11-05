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

## Get the data back (this session's downloaded runs are not kept)
The run files stay on Kaggle. A flattened per-item table of everything run up to 2026-11-05 is committed: `kaggle/results/runs_table.csv.gz`
(`gunzip -k` it, or pass it to the scripts below after unzipping). To refetch raw runs:
```bash
for t in agent-govbench-guard-judge agent-govbench-agent-policy-in-prompt agent-govbench-agent-task-only-prompt agent-govbench-code-mixed-tool-use-pilot; do
  kaggle b t download $t -o kaggle/runs/ -f; done          # all models; if a model folder comes back empty use a fresh folder
python kaggle/analyze.py kaggle/runs --out runs.csv
```

## Read the ledger and results
- `kaggle/ledger.jsonl`: one line per finished run: queue file and line (`key`), task, model, state, `daily_used_after` (quota used when it finished).
  A queue line whose key is in the ledger is skipped on restart.
- Per-item table: `python kaggle/analyze.py kaggle/runs --out runs.csv` (cost from Kaggle's own figures, tokens, outcome, raw judge output, lenient parse).
- Scores with intervals, cost, Pro vs Flash paired test: `python kaggle/results_table.py runs.csv --out kaggle/RESULTS.md`
  (runs with under 95% of items are marked incomplete and excluded; 95% or more count missing items as failures).
- Pilot: `python kaggle/codemix/analyze_pilot.py runs.csv --out pilot_section.md`.
- Offline tests: `python -m pytest tests/test_kaggle_port.py`.

## Runs that remain after 2026-11-05 (estimated cost)
All planned sweep runs are finished (16 models x 3 tasks; month used $58.38 of $100, refill 2026-11-28 19:21 UTC; about $41 of headroom now). Nothing is queued.
Optional, in value order (estimates from measured costs):
| Run | Est. $ |
|---|---|
| Third runs for variance on the 11 pairs with two runs (judge x4 about $2.2, agent task-only x7 about $8) | about 10 |
| Second runs of the remaining frontier tasks: gemini-3.1-pro and opus-5-5 judge (about $4.8 and $3.7), opus-5-5 task-only ($2.4) | about 11 |
| Pilot v2 (after your review): one pass of opus-5-5, gemini-3.8-flash, gemma-4-31b, haiku-5-5; three passes | about 9; about 26 |
| gemini-3.1-pro and opus-5-5 policy-task second runs | about 5 |
| Not run: claude-opus-5 (about $22 per full pass), gpt-5.5 (about $13), gemini-3-flash-preview (about $4) | optional |
| Cannot run: grok-4.5 and grok-4.6 (404 at inference), gpt-6-astra (no tool support), gemini-2.5-* (multiple-tools error) | n/a |
Keep each day under $10 (rolling 24 h) and launch below about $6 "used" so an in-flight run cannot cross the limit. Queue files for reruns go in NEW files.

## Do by hand in the Kaggle web UI (nothing here is done yet; nothing is public)
1. Decide and say "go" before anything is made public. Until then every task and the dataset are private.
2. Publish the dataset `agent-govbench-items` (Dataset page, Settings/Sharing, set to Public) after checking its description. A public task needs public data.
3. Publish the three tasks (and the pilot if you want it): `kaggle b t publish <slug>` or the task page's Make public. Publishing also publishes the backing notebook unless you pass `--no-publish-backing-notebook`.
4. Create the benchmark and add the tasks: see `UI_STEPS.md`.
5. Review the benchmark page text and the grant draft (`GRANT_DRAFT.md`; every unverified claim is tagged `[UNVERIFIED]`), then submit the grant form yourself.
6b. The README has a hidden (commented) Kaggle section; uncomment it and fill in the benchmark and dataset URLs only after you say go.
7. Review provenance is recorded (owner's statement of 2026-11-02, in `kaggle/codemix/README.md`): keep that line wherever the pilot is published.

## Pilot v2 (draft, to run after your review; nothing has been run)
Design, item counts and what each intent tests: `codemix_v2/DESIGN.md`. Review the four chunks `codemix_v2/review_chunk_01..04.csv` (fill the owner columns, same rules
as `codemix/RUBRIC.md`: rewrite lines scored 3 or below, keep every argument value identical, mark meaning N only if a line asks for something different), save the
filled files as `review_chunk_0N_filled.csv` in the same folder, then:
```bash
python kaggle/codemix_v2/apply_review_v2.py kaggle/codemix_v2/review_chunk_0{1,2,3,4}_filled.csv   # rewrites, drops, argument-identity check
cp kaggle/codemix_v2/items_v2_reviewed.jsonl kaggle/data/codemix_v2_items.jsonl
kaggle datasets version -p kaggle/data -m "Add codemix_v2_items.jsonl"                           # dataset stays private until you decide
python kaggle/build_tasks.py 12                                                                 # writes kaggle/dist/codemix_v2.py
kaggle b t push agent-govbench-code-mixed-tool-use-v2 -f kaggle/dist/codemix_v2.py -d brejeshbalakrishnan/agent-govbench-items --wait
#   (the slug comes from the task name; if the CLI rejects it, it prints the available slug)
#   pushing runs the task once on gemini-3.8-flash: about $2.4
printf 'agent-govbench-code-mixed-tool-use-v2 claude-opus-5-5-default\nagent-govbench-code-mixed-tool-use-v2 claude-haiku-5-5\nagent-govbench-code-mixed-tool-use-v2 gemma-4-31b-it\n' > kaggle/queue_v2.txt
python kaggle/sweep.py --queue kaggle/queue_v2.txt --max-inflight 2 --daily-cap 6.0 --dl kaggle/runs
python kaggle/analyze.py kaggle/runs --out runs.csv
python kaggle/codemix_v2/analyze_pilot_v2.py runs.csv --out pilot_v2_section.md
```
Cost: about $8.8 per pass of {opus-5-5, gemini-3.8-flash, gemma-4-31b, haiku-5-5}; three passes about $26 (see DESIGN.md for cheaper options). Repeat a queue line in a NEW queue file
to rerun. Use one opus pass per day at most ($5.8 of the $10 daily quota). The monthly quota refills on 2026-11-28 19:21 UTC; until then the month total is capped at $100
(about $54 will remain after the scheduled windows).
