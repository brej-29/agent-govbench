# Agent model comparison (standard tier, 95% bootstrap, families resampled)

## Task-only prompt: Flash vs Pro agent, unguarded and with live guards

Each guard row pair uses only scenarios where both agents have a run with that guard.

| agent, guard | runs | failed | attack success (completed) | attack success (failures as errors) | benign completed (log) | median latency s | USD per run (agent + guard) |
|---|---|---|---|---|---|---|---|
| Flash, no guard (149 scenarios) | 149 | 0 | 47.8% [33.3%, 60.8%] (n=90, fam=54) | 47.8% [33.3%, 60.8%] (n=90, fam=54) | 100.0% [100.0%, 100.0%] (n=59, fam=45) | 14.3 | 0.0094 |
| Pro, no guard (149 scenarios) | 149 | 0 | 67.8% [55.6%, 78.8%] (n=90, fam=54) | 67.8% [55.6%, 78.8%] (n=90, fam=54) | 93.2% [86.5%, 98.4%] (n=59, fam=45) | 18.7 | 0.0117 |
| Flash, G6 LLM guard (67 scenarios) | 67 | 0 | 2.4% [0.0%, 7.3%] (n=42, fam=33) | 2.4% [0.0%, 7.3%] (n=42, fam=33) | 100.0% [100.0%, 100.0%] (n=25, fam=22) | 29.9 | 0.0153 |
| Pro, G6 LLM guard (67 scenarios) | 67 | 0 | 4.8% [0.0%, 11.6%] (n=42, fam=33) | 4.8% [0.0%, 11.6%] (n=42, fam=33) | 100.0% [100.0%, 100.0%] (n=25, fam=22) | 24.8 | 0.0180 |
| Flash, G4 = G2' + G6 (67 scenarios) | 67 | 0 | 0.0% [0.0%, 0.0%] (n=42, fam=33) | 0.0% [0.0%, 0.0%] (n=42, fam=33) | 100.0% [100.0%, 100.0%] (n=25, fam=22) | 24.4 | 0.0137 |
| Pro, G4 = G2' + G6 (67 scenarios) | 67 | 0 | 2.4% [0.0%, 7.5%] (n=42, fam=33) | 2.4% [0.0%, 7.5%] (n=42, fam=33) | 100.0% [100.0%, 100.0%] (n=25, fam=22) | 21.3 | 0.0164 |

## Policy prompt, no guard: Flash vs Pro agent (pilot scenarios)

| agent, guard | runs | failed | attack success (completed) | attack success (failures as errors) | benign completed (log) | median latency s | USD per run (agent + guard) |
|---|---|---|---|---|---|---|---|
| Flash, no guard (76 scenarios) | 76 | 0 | 0.0% [0.0%, 0.0%] (n=47, fam=45) | 0.0% [0.0%, 0.0%] (n=47, fam=45) | 100.0% [100.0%, 100.0%] (n=29, fam=28) | 36.5 | 0.0082 |
| Pro, no guard (76 scenarios) | 76 | 0 | 0.0% [0.0%, 0.0%] (n=47, fam=45) | 0.0% [0.0%, 0.0%] (n=47, fam=45) | 93.1% [82.1%, 100.0%] (n=29, fam=28) | 10.1 | 0.0126 |

Flash pilot runs predate the latency fix (their latency includes quota waits); compare latency only within Pro rows or against full-run Flash rows.
