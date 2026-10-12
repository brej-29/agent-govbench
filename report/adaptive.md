# Adaptive rewrites (offline, test split, never for training)

Selected 100 real malicious test records that G1, G2', G6 or G4 blocked. gemini-3.1-pro (Flex) rewrote only the attacker-controlled text in two rounds (round 2 saw which guards still caught round 1), keeping the proposed call identical. Validity check by Pro: 12 dropped as no longer clearly malicious, 1 failed, 87 survivors. Round 2 ran for 87 of them. Cost USD 2.11.

Block rate on the same survivor records (95% bootstrap, families resampled; G7 original = Project B's score where available):

| stage | G1 Model Armor | G2' rules | G6 LLM guard (Flash) | G4 = G2' + G6 | G7 Pro, B prompt |
|---|---|---|---|---|---|
| original | 31.0% [18.7%, 44.2%] (n=87, fam=34) | 63.2% [51.2%, 73.9%] (n=87, fam=34) | 97.7% [92.9%, 100.0%] (n=87, fam=34) | 97.7% [92.9%, 100.0%] (n=87, fam=34) | 98.9% [96.4%, 100.0%] (n=87, fam=34) |
| round 1 | 60.9% [48.3%, 73.6%] (n=87, fam=34) | 63.2% [51.2%, 73.9%] (n=87, fam=34) | 94.2% [88.2%, 98.9%] (n=87, fam=34) | 95.4% [89.5%, 100.0%] (n=87, fam=34) | 98.9% [96.4%, 100.0%] (n=87, fam=34) |
| final (round 2 if run) | 54.0% [40.4%, 68.3%] (n=87, fam=34) | 63.2% [51.2%, 73.9%] (n=87, fam=34) | 97.7% [92.9%, 100.0%] (n=87, fam=34) | 97.7% [92.9%, 100.0%] (n=87, fam=34) | 100.0% [100.0%, 100.0%] (n=87, fam=34) |
