# Label quality

| check | n | verdict agreement | category agreement |
|---|---|---|---|
| gold slice (two independent ChatGPT passes) vs current labels, all | 117 | 98.3% | 84.6% |
| gold vs construction labels | 62 | 96.8% | 72.6% |
| gold vs teacher_label (Gemini) | 55 | 100.0% | 98.2% |

Gold records without a current label (disputed or dropped): 3. N human-adjudicated: 0 of 120.

| check | result |
|---|---|
| Flash-allow single-teacher labels, Pro second opinion on a random sample | Pro disagreed on 1 of 81 (1.2%, 95% CI 0.0 to 3.6%) |
| construction label audit (Pro, taxonomy verbatim), 191 sampled scenario records | real verdict errors 8 of 186 parseable (4.3%); category-only errors 44 (23.7%); auditor errors 3; ambiguous 3 |
