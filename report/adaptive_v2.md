# Deeper adaptive loop (offline, test split, never for training)

Up to 60 of the same source records; up to four rounds; each round the attacker sees which guards caught the previous version and the stated reasons of G6 and G7. Two attacker arms: gemini-3.1-pro and gemini-3.8-flash (Flex). A record stops early once no guard catches it. Evasion rate = share of records the guard allowed at that round (records still in play carry their latest version forward). Limits: black-box attacker, four rounds, Gemini attackers only.

## Attacker: pro

Record-arms: 60; kept after validity check: 50; dropped as no longer clearly malicious: 10; no successful rewrite: 0.

Evasion rate per guard per round, on the kept records (95% bootstrap, families resampled):

| round | G1 Model Armor | G2' rules | G6 LLM guard (Flash) | G4 = G2' + G6 | G7 Pro, B prompt |
|---|---|---|---|---|---|
| 0 (original) | 66.0% [51.8%, 81.2%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 4.0% [0.0%, 12.5%] (n=50, fam=26) | 4.0% [0.0%, 12.5%] (n=50, fam=26) | 2.0% [0.0%, 6.2%] (n=50, fam=26) |
| 1 | 40.0% [23.6%, 57.8%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 9.1% [0.0%, 20.4%] (n=44, fam=24) | 9.1% [0.0%, 20.4%] (n=44, fam=24) | 2.0% [0.0%, 7.3%] (n=50, fam=26) |
| 2 | 42.0% [26.2%, 58.5%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 6.4% [0.0%, 15.7%] (n=47, fam=26) | 6.4% [0.0%, 15.7%] (n=47, fam=26) | 0.0% [0.0%, 0.0%] (n=50, fam=26) |
| 3 | 36.0% [22.2%, 50.9%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 2.2% [0.0%, 7.1%] (n=45, fam=25) | 2.2% [0.0%, 7.1%] (n=45, fam=25) | 0.0% [0.0%, 0.0%] (n=50, fam=26) |
| 4 | 48.0% [32.0%, 64.7%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 4.3% [0.0%, 13.3%] (n=46, fam=25) | 4.3% [0.0%, 13.3%] (n=46, fam=25) | 0.0% [0.0%, 0.0%] (n=50, fam=26) |

## Attacker: flash

Record-arms: 60; kept after validity check: 50; dropped as no longer clearly malicious: 10; no successful rewrite: 0.

Evasion rate per guard per round, on the kept records (95% bootstrap, families resampled):

| round | G1 Model Armor | G2' rules | G6 LLM guard (Flash) | G4 = G2' + G6 | G7 Pro, B prompt |
|---|---|---|---|---|---|
| 0 (original) | 66.0% [51.8%, 81.2%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 4.0% [0.0%, 12.5%] (n=50, fam=26) | 4.0% [0.0%, 12.5%] (n=50, fam=26) | 2.0% [0.0%, 6.2%] (n=50, fam=26) |
| 1 | 42.5% [27.5%, 59.1%] (n=47, fam=25) | 40.4% [24.4%, 57.1%] (n=47, fam=25) | 4.7% [0.0%, 14.6%] (n=43, fam=24) | 4.7% [0.0%, 14.6%] (n=43, fam=24) | 0.0% [0.0%, 0.0%] (n=47, fam=25) |
| 2 | 45.8% [30.6%, 62.7%] (n=48, fam=25) | 41.7% [25.5%, 58.1%] (n=48, fam=25) | 7.0% [0.0%, 17.8%] (n=43, fam=24) | 7.0% [0.0%, 17.8%] (n=43, fam=24) | 0.0% [0.0%, 0.0%] (n=48, fam=25) |
| 3 | 48.0% [32.7%, 64.8%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 4.5% [0.0%, 13.6%] (n=44, fam=25) | 4.5% [0.0%, 13.6%] (n=44, fam=25) | 0.0% [0.0%, 0.0%] (n=50, fam=26) |
| 4 | 56.0% [42.9%, 70.8%] (n=50, fam=26) | 42.0% [27.1%, 58.0%] (n=50, fam=26) | 4.3% [0.0%, 13.0%] (n=47, fam=25) | 4.3% [0.0%, 13.0%] (n=47, fam=25) | 0.0% [0.0%, 0.0%] (n=50, fam=26) |

