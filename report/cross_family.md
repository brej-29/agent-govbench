# Cross-family guard comparison (identical test records)

Project B's guards scored by B on B's evaluation sample of our test records; our labels after the settled-label fix; disputed records excluded. G6 and G7 use different prompts (G6: our guard prompt with JSON input; G7 and B-flash: B's guard prompt and rendering). 95% bootstrap intervals resampling families.

| group (block rate) | G6 (gemini-3.8-flash, our prompt) | B-flash (gemini-3.8-flash, B prompt) | G7 (gemini-3.1-pro, B prompt) | G5 (B tuned gemma-4-e4b) |
|---|---|---|---|---|
| real benign | 0.0% [0.0%, 0.0%] (n=401, fam=67) | 1.2% [0.0%, 2.8%] (n=401, fam=67) | 2.5% [1.1%, 4.0%] (n=401, fam=67) | 8.0% [3.4%, 13.1%] (n=401, fam=67) |
| real malicious | 94.7% [89.3%, 99.4%] (n=170, fam=38) | 97.1% [92.0%, 100.0%] (n=170, fam=38) | 98.8% [97.0%, 100.0%] (n=170, fam=38) | 65.9% [56.4%, 75.6%] (n=170, fam=38) |
| simulated malicious | 99.7% [98.9%, 100.0%] (n=297, fam=57) | 100.0% [100.0%, 100.0%] (n=297, fam=57) | 99.7% [98.9%, 100.0%] (n=297, fam=57) | 86.9% [79.1%, 93.4%] (n=297, fam=57) |

Paired differences on the same records (percentage points, 95% interval):

| group | G6 minus B-flash (prompt effect) | B-flash minus G7 (model effect) | G6 minus G7 |
|---|---|---|---|
| real benign | -1.2 [-2.8, +0.0] (n=401, fam=67) | -1.2 [-2.6, +0.0] (n=401, fam=67) | -2.5 [-4.2, -1.2] (n=401, fam=67) |
| real malicious | -2.4 [-4.7, +0.0] (n=170, fam=38) | -1.8 [-5.9, +1.3] (n=170, fam=38) | -4.1 [-8.3, +0.0] (n=170, fam=38) |
| simulated malicious | -0.3 [-1.1, +0.0] (n=297, fam=57) | +0.3 [+0.0, +1.1] (n=297, fam=57) | +0.0 [-1.0, +1.1] (n=297, fam=57) |

Records compared: 868 (intersection where every guard has a valid verdict).
