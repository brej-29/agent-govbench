# Kaggle port: status

Updated: 2026-10-29 (session 1). A fresh session can resume from this file.

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
