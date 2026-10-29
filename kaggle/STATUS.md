# Kaggle port: status

Updated: 2026-10-29 (session 1). A fresh session can resume from this file.

## State
- Branch `claude/kind-ritchie-xs4sfk`. No PR yet (open one when the port is validated).
- Kaggle account: `brejeshbalakrishnan`. Credentials come from the `KAGGLE_API_TOKEN` environment variable; `kaggle b init -y` writes a short-lived `MODEL_PROXY_*` .env (never commit it).
- Dataset (private): `brejeshbalakrishnan/agent-govbench-items` (judge_items.jsonl, agent_items.jsonl, MANIFEST.json).
- Tasks pushed so far (all private): `govbench-pilot-guard-judge`, `govbench-pilot-agent-task-only` (4-item pilots), `govbench-probe-params`.
- Real tasks not yet pushed: `guard-judge`, `agent-policy`, `agent-task-only` (built in `kaggle/dist/`).

## Layout
- `kaggle/build_data.py`: public HF dataset -> item files (`kaggle/data/`).
- `kaggle/tasks/`: task templates; `kaggle/build_tasks.py` inlines `_common.py` and the original policy/guard/world sources into `kaggle/dist/*.py` (the files pushed to Kaggle).
- `kaggle/analyze.py`: downloaded runs -> one row per item run (cost, tokens, outcome).
- `tests/test_kaggle_port.py`: offline tests of tools, checks, parsing.

## Platform facts (verified)
- Local runs are impossible from this sandbox: `mp-staging.kaggle.net` is blocked by the network policy. All runs go through `kaggle b t push/run` (cloud).
- Quota: $10 per rolling 24h and $100 per rolling 30 days from first use (monthly refill 2026-11-28), not calendar. `kaggle b quota`.
- Max 40 concurrent batch CPU sessions per account: schedule at most about 30 model runs at once. More than about 6 -m flags per call is fine; 35 in one call returns HTTP 400.
- Model Proxy reserves quota for `max_tokens`: always pass `extra_api_params={"max_completion_tokens": N}` (works for all models; `max_output_tokens` does not).
- Tool-use quirks: GPT-5.6 and GPT-6.x reject tools with reasoning on chat completions (retry with `reasoning="none"`; `gpt-6-astra` cannot do tools at all); `gemini-2.5-*` reject multiple function tools; `grok-4.5-0708` and `grok-4.6` are listed in the catalog but return 404 at inference.
- Temperature is not controllable through the proxy for OpenAI-route models; expect run-to-run variance.
- Task description must be at most 255 characters; task names must be literal strings in the decorator (the CLI parses the file statically).

## Next
1. Validate full tasks on 2 to 3 cheap models; check parse rates and checks.
2. Sweep plan in `kaggle/PLAN.md`.
