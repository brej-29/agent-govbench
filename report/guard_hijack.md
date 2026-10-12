# Guard-hijack test (offline, test split, never for training)

Same 100 source records as the adaptive study v1. gemini-3.1-pro (Flex) rewrote only attacker-controlled text so it also addresses the guard (claimed prior approval, fake security-review-passed note, system-message formatting, an instruction to answer allow); the proposed call is identical. Validity check by Pro: 10 dropped as no longer clearly malicious, 1 failed, 89 kept. Cost USD 1.28.

Block rate on the same kept records (95% bootstrap, families resampled):

| stage | G1 Model Armor | G2' rules | G6 LLM guard (Flash) | G4 = G2' + G6 | G7 Pro, B prompt |
|---|---|---|---|---|---|
| original | 31.5% [19.8%, 44.2%] (n=89, fam=37) | 65.2% [53.3%, 76.1%] (n=89, fam=37) | 97.8% [93.0%, 100.0%] (n=89, fam=37) | 97.8% [93.0%, 100.0%] (n=89, fam=37) | 98.9% [96.5%, 100.0%] (n=89, fam=37) |
| guard-hijack rewrite | 50.6% [39.0%, 62.9%] (n=89, fam=37) | 65.2% [53.3%, 76.1%] (n=89, fam=37) | 97.7% [92.9%, 100.0%] (n=87, fam=37) | 97.7% [92.9%, 100.0%] (n=87, fam=37) | 100.0% [100.0%, 100.0%] (n=89, fam=37) |
