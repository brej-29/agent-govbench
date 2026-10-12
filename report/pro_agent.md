# Agent model comparison: unguarded, task-only prompt, same 149 test scenarios (standard tier)

| agent model | runs attempted | failed | attack success (completed runs) | attack success (failures as errors) | benign completed (log) | median latency s | USD per run |
|---|---|---|---|---|---|---|---|
| gemini-3.8-flash | 149 | 0 | 47.8% [33.3%, 60.8%] (n=90, fam=54) | 47.8% [33.3%, 60.8%] (n=90, fam=54) | 100.0% [100.0%, 100.0%] (n=59, fam=45) | 14.3 | 0.0094 |
| gemini-3.1-pro-preview | 149 | 0 | 67.8% [55.6%, 78.8%] (n=90, fam=54) | 67.8% [55.6%, 78.8%] (n=90, fam=54) | 93.2% [86.5%, 98.4%] (n=59, fam=45) | 18.7 | 0.0117 |

Flash latency for full-task runs excludes quota waits; pilot-task Flash runs (if any of these scenarios) include them.
