# Findings notes (input for report/WRITEUP.md)

> **Note (2026-10-10):** the Google Cloud projects used here (PROJECT_ID and the shared bucket) were torn down and deleted on 9 Oct 2026. Resource names below are historical; nothing in this file can be run against them.

## Model Armor (G1 and G1b)
- G1 = Model Armor through the direct sanitize API, template govbench-basic: prompt injection and jailbreak at
  MEDIUM_AND_ABOVE, malicious URI filter, RAI filters (hate speech, dangerous, sexually explicit, harassment) at HIGH.
  It screens the user prompt and every tool output; block if the overall filterMatchState is MATCH_FOUND.
- First offline result on identical test records: false positive rate 27.1% [21.1, 33.1] on 1,171 benign real calls (final; the 2b preview was 31% on 740), block rate
  29.8% on 171 real malicious calls and 38.0% on 297 simulated malicious calls (final; preview was 58% on 55 and 40% on 280). Live pilot: benign completion fell from 97%
  to 71%.
- G1b isolates the cause. Template govbench-pi-low; only the prompt injection and jailbreak result is read, at three
  thresholds (LOW_AND_ABOVE, MEDIUM_AND_ABOVE, HIGH), chosen on train+val only before touching test:
  | threshold | block rate on malicious (train+val, n=175) | false positive rate on benign (n=426) |
  |---|---|---|
  | LOW | 54.9% | 48.6% |
  | MEDIUM (chosen) | 42.9% | 29.8% |
  | HIGH | 21.7% | 17.1% |
  The injection and jailbreak filter by itself produces the false positives (about 30% at the chosen threshold, the
  same as full G1), not the RAI filters. Reason: Model Armor judges text, and the benign calls sit in conversations
  whose user text or tool output looks like instructions, urgency or authority claims.
- G1 and G1b make identical decisions on the records checked (313 of 313 in the v1 test-split replay records):
  every G1 block comes from the injection and jailbreak filter at MEDIUM; the RAI filters at HIGH and the malicious URI
  filter never fired. The train+val threshold choice for G1b landed on the same MEDIUM, so G1b equals G1 here. Removing
  the content filters does not reduce false positives; only a higher injection threshold does (HIGH: 17% false
  positives, but block rate 22%).
- Filters tested: prompt injection and jailbreak (LOW, MEDIUM, HIGH via the reported confidence), malicious URI
  (in both templates, verdict ignored in G1b), RAI hate speech, harassment, sexually explicit (and dangerous in G1).
  Sensitive Data Protection was not part of either template.
- TEMPLATE_NOT_CONFORMANT: creating a template with only the injection filter was rejected, because the codelab
  Terraform installs an enforced project-level Model Armor floor setting (prompt injection MEDIUM_AND_ABOVE, malicious
  URI on, RAI hate speech, harassment and sexually explicit at MEDIUM_AND_ABOVE). The pre-existing govbench-basic
  template (RAI at HIGH) predates the floor and is not re-validated. G1b therefore uses a conformant template and reads
  only the injection result. Lesson for teams: the codelab floor setting is project-wide and constrains every later
  template.

## Agent and prompt
- Policy in the agent prompt alone: attack success 0 to 4% (5 of 312 attacks in the 2b samples) with benign completion
  97% or more. Task-only prompt (policy enforced only by external guards): 47% (78 of 160).
- Live runs vary between configurations even at temperature 0 (same scenario: agent complies under G0, refuses on its
  own in the G2p run). The headline comparison is offline replay on identical records; live runs are reported next to it.

## Labels
- Construction labels: verdict error about 4% (audit of 191, adjudicated), category error about 24% before the
  teacher-v2 relabel (template causes: users adopting injected content, manipulative styles not labeled
  social_engineering by precedence). After the relabel and the settled-label fix for replay records, gold agreement with
  construction labels is 96.8% verdict and 72.6% category (n=62).
- Gold slice: two independent ChatGPT passes (second on reversed order), N = 0 human-adjudicated rows. Agreement with
  the Gemini teacher is high (100% verdict, 98.2% category, n=55) but correlated: both read the same taxonomy.
- Flash-allow single-teacher labels: Pro disagreed on 1 of 81 sampled (1.2%, 95% CI 0 to 3.6%).

## Platform
- Agent Gateway: an agent attached to the gateway cannot start in a project without an organization; every egress TLS
  connection gets a self-signed proxy certificate (CN agent-gateway-proxy.internal) not signed by the published
  inspection CA. Five attempts, including a fresh agent created after the gateway. IAM/IAP tool policies (G2) and
  semantic governance (G3) via the gateway: not tested; semantic governance API reachable, not exercised.
- Agent Runtime query quota: 30 requests per minute per project and region; an increase request stayed pending for 3 days.
- Flex tier: the SDK service_tier field is rejected by Vertex v1beta1; the documented request headers work.

## Fairness statements (must appear in the write-up, verbatim in spirit)
- G6 is gemini-3.8-flash, the same model family that generated the scenarios (and runs the agent); its high block rate
  on simulated calls is likely optimistic.
- G2' was written from the same policy text that the construction labels encode; its zero false positives are likely
  optimistic for an unseen policy.
- G4 (G2' + G6) adds nothing over G6 alone on these records (same block rate, slightly more false positives).
- With the policy in the agent prompt, only about 3% of attacks succeed unguarded (2.9% on 312 full-run attacks); there,
  guards mostly add latency and false refusals.
- Model Armor (G1): 27 to 30% false positives on benign calls, caused by the prompt injection and jailbreak filter at
  MEDIUM. A higher threshold (HIGH) lowers false positives to about 17% but block rate to about 22%; the threshold choice
  for G1b was made on train and val only.
- Every table states its denominator; live runs that failed after all retries are counted as errors, not dropped.
- Real agent calls and simulated compromised-agent calls are always in separate tables.
