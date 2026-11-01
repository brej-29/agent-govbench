# Kaggle port: status

Updated: 2026-10-29 (session 1). A fresh session can resume from this file.

## Results (dated; full table in kaggle/RESULTS.md, regenerate with kaggle/results_table.py)
2026-10-31, partial sweep, single runs, 0 errored item runs, $17.6 of the quota spent.
- Pro vs Flash, task-only prompt, 105 attack scenarios, same items for both: attack success Pro 0.590, Flash 0.495, difference +0.095
  [+0.029, +0.162] (family bootstrap); discordant pairs 12 vs 2, exact McNemar p = 0.013. Pro is more exploitable, as in the original
  (67.8% vs 47.8%); the effect is smaller here.
- Same comparison with the policy in the prompt: 0.067 vs 0.048, difference +0.019 [-0.029, +0.067], McNemar p = 0.69 (no difference).
- Judge balanced accuracy: gemini-3.8-flash 0.978, gemma-4-31b 0.970, gpt-oss-120b 0.932, haiku-5-5 0.927 (0.963 with a lenient parse),
  gemini flash-lite 0.895 to 0.900, gemma-4-26b 0.892, gpt-5.4-mini 0.863, gpt-5.4-nano 0.855, haiku-4-5 0.850 (over-blocks: allow rate 0.76).
- Agent task-only score ranges 0.528 (gemini-3.1-flash-lite) to 0.804 (haiku-5-5); the policy prompt lifts every model, most for the
  weakest (gemini-3.1-flash-lite 0.528 to 0.769).

## Wake log
- 2026-10-31 04:35 to 07:30 UTC: day-1 sweep had stalled while the session idled (the driver dies with the container; always run it
  to completion within a wake). Restarted as queue_day2/day2b. Done so far (3 tasks each): gemini-3.8-flash, haiku-5-5, gpt-5.4-nano,
  gpt-oss-120b, gemma-4-26b/31b, gemini-3.1-flash-lite, gemini-3.5-flash-lite, gpt-5.4-mini, haiku-4-5. gemini-3.1-pro: both agent tasks
  (judge still to run, about $4). Quota used $17.6 of $100; today's window is spent (resets 04:35 UTC 1 Nov). Wake scheduled 04:45 UTC 1 Nov.
- Next queue: gemini-3.1-pro judge, opus-5-5 (split across windows), sonnet-5-5, gemini-3.6-flash, gpt-5.4, gpt-6-sol, then reruns.

## State (2026-10-30 17:40 UTC)
- Branch `claude/kind-ritchie-xs4sfk`; no PR yet. Nothing is public. Quota used: about $6.7 of $100 (30-day window to 28 Nov).
- Dataset (private): `brejeshbalakrishnan/agent-govbench-items`. Tasks (private, v1): `agent-govbench-guard-judge`,
  `agent-govbench-agent-policy-in-prompt`, `agent-govbench-agent-task-only-prompt`. Pushing a task runs it once on
  gemini-3.8-flash (about $1.1 to $1.5 each): do not re-push casually; a new version needs every model rerun.
- Validated on gemini-3.8-flash, claude-haiku-5-5, gpt-5.4-nano, gpt-oss-120b (all 3 tasks, 0 errored runs).
- Sweep driver: `kaggle/sweep.py --queue kaggle/queue_dayN.txt --max-inflight 2 --daily-cap 9`; ledger in `kaggle/ledger.jsonl`;
  results downloaded to a runs dir and flattened with `kaggle/analyze.py`. Queue lines already in the ledger are skipped.
- `kaggle/queue_day1.txt` (gemma-4-26b/31b, gemini flash-lite x2, gpt-5.4-mini, haiku-4-5) was started; re-run the same command
  to continue (completed lines are skipped; a half-run line is relaunched, check `kaggle b t status` first).
- Code-mixed pilot: drafts and review sheet in `kaggle/codemix/`; waiting for the owner's review. Not pushed.
- Not yet done: benchmark grouping (web UI, held), PR, analysis write-up, grant draft.

## Platform facts (verified)
- Local runs are impossible from this sandbox: `mp-staging.kaggle.net` is blocked by the network policy. All runs go through `kaggle b t push/run` (cloud).
- Quota: $10 per rolling 24h and $100 per rolling 30 days from first use (monthly refill 2026-11-28), not calendar. `kaggle b quota`.
- Max 40 concurrent batch CPU sessions per account: schedule at most about 30 model runs at once. More than about 6 -m flags per call is fine; 35 in one call returns HTTP 400.
- Model Proxy reserves quota for `max_tokens`: always pass `extra_api_params={"max_completion_tokens": N}` (works for all models; `max_output_tokens` does not).
- Tool-use quirks: GPT-5.6 and GPT-6.x reject tools with reasoning on chat completions (retry with `reasoning="none"`; `gpt-6-astra` cannot do tools at all); `gemini-2.5-*` reject multiple function tools; `grok-4.5-0708` and `grok-4.6` are listed in the catalog but return 404 at inference.
- Temperature is not controllable through the proxy for OpenAI-route models; expect run-to-run variance.
- Task description must be at most 255 characters; task names must be literal strings in the decorator (the CLI parses the file statically).

## Next
Follow `kaggle/PLAN.md` day by day; runs queue for 10 to 30 minutes when the batch CPU cap is busy (gpt-oss-120b queued longest).

## Wake 2026-10-31 19:10 UTC
Window not reset yet (daily $9.48 used, resets 04:35 UTC 1 Nov; wake scheduled 04:45 UTC, trigger trig_0183cz7f2SghzkQXGbJMFFux). No runs launched.
Done instead: rubric (`kaggle/codemix/RUBRIC.md`) and sheet columns, `kaggle/results_table.py`, `kaggle/RESULTS.md`.
Dropped for cost: gemini-3.1-pro full pass stays split (judge about $4 pending), opus-5 (about $22), gpt-5.5 (about $13), gemini-3-flash-preview.

## Wake 2026-11-01 04:45 UTC (scheduled)
Window used: $9.90 of $10 (next window opens 2026-11-02 04:46 UTC). Month: $27.51 of $100. Ran: opus-5-5 task-only ($2.42) and judge ($3.70),
gemini-3.1-pro judge (about $3.8). Pro now has all three tasks; opus-5-5 still needs the policy task (about $2.4).
Download gotcha: `sweep.py` can leave an empty model folder that makes a later `kaggle b t download -m` report 0 runs; download into a fresh dir.
Next window: opus-5-5 policy, gemini-3.6-flash (3 tasks), sonnet-5-5 judge/task-only, then gpt-5.4, gpt-6-sol, variance reruns. Wake trigger needed for 2026-11-02 04:50 UTC.
