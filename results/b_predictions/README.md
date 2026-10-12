# Project B's predictions on Agent GovBench test records

Produced by Project B's guard code (the toolcall-guard repository, not published yet), on the same test decision
records as this repository's offline replay. Used by `src/agent_govbench/cross_family.py` for report/cross_family.md
and the cross-model rows of the write-up (section 5.4).

| File | Guard | Copied from (toolcall-guard, results/preds/a_replay/) |
|---|---|---|
| b_flash_b_prompt.jsonl | gemini-3.8-flash with B's prompt (the "Flash with B prompt" row) | gemini-3.8-flash zero-shot.jsonl |
| g7_pro_b_prompt.jsonl | G7: gemini-3.1-pro-preview with B's prompt | gemini-3.1-pro zero-shot.jsonl |
| g5_gemma_tuned.jsonl | G5: B's tuned gemma-4-e4b (fp16, Kaggle 2x T4) | gemma-4-e4b tuned (ours).jsonl |

One JSON object per record: `id` (the decision record id in the dataset), `pred` (verdict, category, reason),
`latency_ms`, `cost_usd`, `tokens` and the raw model output. Rows were restricted to this project's test records
(all rows for the two Gemini files; 2,365 of 2,415 for G5, the other 50 ids are not test records here) and the same
pre-publication replacements as the dataset were applied to reasons and raw outputs (scripts/sanitize_release.py:
14 lookalike domains); verdicts are unchanged. B's prompt is in src/agent_govbench/b_prompts.py.
