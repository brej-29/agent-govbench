# Agent GovBench: what agent guardrails on Google Cloud stop, what they wrongly block, and what they cost

Final, 10 Oct 2026. Runs took place 5 to 9 Oct 2026; all cloud resources were deleted on 9 Oct 2026.

## TL;DR

- With the company policy in the agent's own prompt, only 2.9% of attacks succeed with no guard at all; with a
  task-only prompt 51.5% succeed (section 5.2).
- On identical real agent calls, the LLM guard G6 blocks 94.7% of malicious calls with 0.4% false positives; the
  hand-written rules G2' block 67.2% with 0.3%; Model Armor (G1) blocks 29.8% but also 27.1% of benign calls (5.1).
- Model Armor's false positives come from its prompt injection filter at MEDIUM, not from its content filters (5.3).
- Adaptive rewrites, text aimed at the guard, and four feedback rounds did not get past the LLM guards (5.5 to 5.7).
- A stronger agent model (gemini-3.1-pro-preview) is more exploitable than gemini-3.8-flash without the policy in its
  prompt: 67.8% vs 47.8% (5.8).
- IAM/IAP tool policies and semantic governance through Agent Gateway were not testable: in a project without an
  organization the gateway-attached agent never started (section 6).

## How to read this

Every interval is a 95% bootstrap interval that resamples scenario families (variants of one family are not
independent). Numbers come from the generated files in report/ (metrics.json, tables.md and the per-study tables).

| Term | Meaning |
|---|---|
| G0 to G7 | guard configurations, listed in section 3 |
| real call | a tool call the agent actually proposed during a run |
| simulated call | the agent's real context with the scenario's harmful call substituted (a "compromised agent"); always in separate tables |
| replay (offline) | every guard judges the same saved calls, so the comparison has identical inputs |
| live | the guard runs inside the agent during the run; latency and what the agent does after a block are real |
| hard negative | a legitimate call inside an attack scenario, or a legitimate request that looks risky |
| standard / Flex tier | Vertex AI pricing tiers; standard for anything with latency, Flex (half price, slower) for offline work |
| teacher_label | a label from a Gemini model (Flash, with Pro as second opinion), as opposed to a construction label from the generator |
| Project A / Project B | this benchmark / a parallel project that distills a small guard (G5) and shares the data contract |

## 1. Question

A team runs a tool-using agent on Gemini Enterprise Agent Platform (Agent Runtime with Agent Identity, MCP tools on
Cloud Run). Which guard options available to that team stop harmful tool calls, how often do they block legitimate
work, and what do they add in latency and money?

## 2. Setup

- **Agent.** One ADK agent, "Northwind Ops Assistant", gemini-3.8-flash (temperature 0, thinking low), deployed on
  Agent Runtime with Agent Identity (project-level trust domain, the project has no organization). Five MCP servers on
  Cloud Run (mail, hr, payments, files, code) with synthetic data and no side effects; every tool carries MCP
  read-only and destructive annotations. Who is asking is trusted session metadata injected by the harness, never user
  text.
- **Two agent conditions.** *Policy in prompt*: the full 7-rule policy is the agent's instruction. *Task only*: a
  short role prompt; the policy is meant to be enforced by external guards. Task only is a weaker agent by design.
- **Scenarios.** 2,850 scenarios from 500 structured seed families (category, technique, surface, tool, role, style,
  turns), generated with gemini-3.8-flash and checked by construction; a 999-scenario set (all 384 test-split
  scenarios plus 615 train/val) was run live. Split by a stable hash of the family (Project B's split_v0), never per
  record; leakage tests in tests/test_splits.py.
- **Decision records.** Every tool call the agent proposed is one record (Project B's contract v0) with the context a
  guard would see. Attack success is judged from the tool-call log by a programmatic check, not by an LLM.
- **Simulated compromised-agent calls.** With the policy in the prompt the agent rarely makes the harmful call, so
  for each attack scenario we also take the agent's real context and substitute the scenario's harmful call. These
  are always reported separately from real agent calls.
- **Tiers.** All live runs (agent and live guards) use the standard tier. Generation, labeling, offline scoring and
  the judge use Flex (half price, slower).

## 3. Configurations

| ID | Guard | Status |
|---|---|---|
| G0 | none | tested |
| G1 | Model Armor, direct sanitize API on the prompt and every tool output (template govbench-basic) | tested |
| G1b | Model Armor, prompt injection and jailbreak filter only, threshold chosen on train and val | tested (offline) |
| G2' | hand-written in-agent rules from the policy text, checked before each tool call. Not IAM. | tested |
| G2 | IAM/IAP per-tool policies through Agent Gateway | **not tested**: see section 6 |
| G3 | semantic governance policies through Agent Gateway | **not tested**: API reachable, not exercised (needs gateway-routed traffic) |
| G4 | G2' + G6, chosen on train and val | tested |
| G5 | Project B's distilled guard (tuned gemma-4-e4b), replay only | scored by B; see section 5.4 |
| G6 | LLM guard: gemini-3.8-flash judging each proposed call against the policy | tested |
| G7 | gemini-3.1-pro with Project B's prompt (cross-model check) | scored by B, offline |

## 4. Labels

- Construction labels (from the generator) for the target calls; teacher_label (Gemini Flash, with Pro as second opinion
  on Flash blocks and a 10% sample) for every other call the agent proposed; disagreements go to a disputed pool,
  excluded from metrics.
- A Pro audit with the taxonomy verbatim found construction verdict errors of about 4% and category errors of about 24%
  (template causes: users adopting injected content, manipulative styles not labeled social engineering by
  precedence). All 2,850 scenario records were relabeled; replay records take the relabeled scenario label.
- Gold slice: 120 test records labeled by **two independent ChatGPT passes** (the second on reversed order); **0 of
  120** were human-adjudicated. Against our current labels: verdict agreement 98.3% (n=117), category 84.6%; for
  construction labels alone 96.8% verdict, 72.6% category (n=62). ChatGPT and the Gemini teacher read the same
  taxonomy, so their agreement is correlated and overstates label quality.
- Single-teacher Flash "allow" labels: Pro disagreed on 1 of 81 sampled (1.2%, 95% CI 0 to 3.6%). All label-quality
  numbers in this section: report/labels.md.

## 5. Results

### 5.1 Offline replay on identical test records (headline)

| Guard | Real malicious calls blocked | Real benign calls blocked (false positives) | Real hard negatives blocked |
|---|---|---|---|
| G1 Model Armor | 29.8% [21.2, 38.9] (n=171) | 27.1% [21.1, 33.1] (n=1,171) | 21.9% [15.3, 29.0] (n=585) |
| G1b injection filter only | 29.8% [21.2, 38.9] (n=171) | 27.1% [21.1, 33.1] (n=1,171) | 21.9% [15.3, 29.0] (n=585) |
| G2' hand-written rules | 67.2% [59.5, 75.3] (n=171) | 0.3% [0.0, 0.7] (n=1,171) | 0.3% [0.0, 1.1] (n=585) |
| G6 LLM guard (Flash) | 94.7% [89.3, 99.4] (n=170) | 0.4% [0.1, 0.9] (n=1,167) | 0.7% [0.2, 1.4] (n=583) |
| G4 = G2' + G6 | 94.7% [89.3, 99.4] (n=170) | 0.5% [0.1, 1.0] (n=1,167) | 0.9% [0.2, 1.8] (n=583) |

Simulated compromised-agent calls, reported separately from real agent calls:

| Guard | Simulated compromised-agent calls blocked (synthetic substitution) |
|---|---|
| G1 Model Armor | 38.0% [29.0, 47.5] (n=297) |
| G1b injection filter only | 38.0% [29.0, 47.5] (n=297) |
| G2' hand-written rules | 87.2% [77.0, 95.0] (n=297) |
| G6 LLM guard (Flash) | 99.7% [98.9, 100.0] (n=297) |
| G4 = G2' + G6 | 99.7% [98.9, 100.0] (n=297) |

Real malicious calls come almost entirely from the task-only agent (168 of 171). Per-category and per-condition tables:
report/tables.md. Figure: report/figures/fig1_offline_guards.png.

### 5.2 Live runs (standard tier)

Denominators include failures: runs that failed after all retries count as errors.

| Configuration | Prompt | Runs attempted (failed) | Attack success, completed runs | Attack success, failures as errors | Benign completed (log) | Judge: completed / refused | Median / p95 latency (s) | USD per 1,000 runs (guard part) |
|---|---|---|---|---|---|---|---|---|
| G0 | policy | 497 (12) | 2.9% [1.3, 4.8] (n=312) | 4.7% [2.6, 7.1] (n=318) | 96.5% [93.5, 98.9] | 99.4% / 0.0% | 13.2 / 52.0 | 9.82 (0.00) |
| G0 | task only | 746 (9) | 51.5% [44.8, 58.4] (n=456) | 52.1% [45.5, 58.4] (n=461) | 95.4% [92.6, 97.8] | 99.6% / 0.0% | 15.0 / 60.4 | 11.31 (0.00) |
| G1 | task only | 249 (0) | 34.0% [24.3, 44.4] (n=150) | 34.0% [24.3, 44.4] (n=150) | 74.8% [65.3, 83.5] | 70.1% / 38.1% | 12.6 / 54.6 | 7.88 (0.02) |
| G2' | task only | 249 (0) | 2.7% [0.0, 6.2] (n=150) | 2.7% [0.0, 6.2] (n=150) | 100.0% [100.0, 100.0] | 100.0% / 0.0% | 15.1 / 63.1 | 10.45 (0.00) |
| G6 | task only | 249 (0) | 4.7% [1.9, 7.8] (n=150) | 4.7% [1.9, 7.8] (n=150) | 98.0% [94.8, 100.0] | 98.0% / 1.0% | 31.8 / 95.2 | 16.14 (6.34) |
| G4 | task only | 249 (0) | 0.7% [0.0, 2.1] (n=150) | 0.7% [0.0, 2.1] (n=150) | 100.0% [100.0, 100.0] | 99.0% / 0.0% | 27.7 / 100.8 | 15.37 (5.62) |
| G1 | policy (pilot) | 100 (0) | 0.0% [0.0, 0.0] (n=62) | 0.0% [0.0, 0.0] (n=62) | 73.7% [59.5, 87.2] | 73.7% / 34.2% | quota wait included | 6.37 (0.02) |
| G2' | policy (pilot) | 100 (0) | 0.0% [0.0, 0.0] (n=62) | 0.0% [0.0, 0.0] (n=62) | 100.0% [100.0, 100.0] | 100.0% / 0.0% | quota wait included | 8.37 (0.00) |
| G6 | policy (pilot) | 100 (0) | 1.6% [0.0, 5.0] (n=62) | 1.6% [0.0, 5.0] (n=62) | 97.4% [91.9, 100.0] | 97.4% / 0.0% | quota wait included | 12.73 (3.96) |
| G4 | policy (pilot) | 100 (0) | 0.0% [0.0, 0.0] (n=62) | 0.0% [0.0, 0.0] (n=62) | 100.0% [100.0, 100.0] | 100.0% / 0.0% | 14.4 / 109.6 | 14.20 (4.42) |

The 21 G0 runs that failed were rerun and succeeded, so every scenario has an unguarded run under both prompts. The
10 guarded runs that first failed were also rerun successfully. Figures: report/figures/fig2_live_attack_success.png,
report/figures/fig3_latency.png.

### 5.3 Model Armor's false positives

About 27 to 30% of benign calls are blocked, live and offline. The cause is the prompt injection and jailbreak filter at
MEDIUM: on these records every G1 block comes from that filter; the RAI filters (at HIGH) and the malicious URI filter
never fired, so G1b (injection filter only) makes the same decisions. Model Armor judges text, and many legitimate
requests contain instruction-like text, urgency or authority claims. A higher threshold (HIGH) lowers false positives to
about 17% but block rate to about 22% (train and val, report/g1b_threshold.md, which also shows a post-hoc check on
the final records); the G1b threshold was chosen on train and val only, before
touching test. Filters tested: prompt injection and jailbreak (LOW, MEDIUM, HIGH via reported confidence), malicious
URI, RAI (hate speech, harassment, sexually explicit, and dangerous in G1). A template with only the injection filter
was rejected with TEMPLATE_NOT_CONFORMANT: the codelab Terraform installs an enforced project-level Model Armor floor
setting, which every later template must satisfy.

### 5.4 Does G6 depend on sharing a model family with the scenario writer?

On 868 identical test records scored by Project B (report/cross_family.md; Project B's scores as of 9 Oct 2026):

| Group (block rate) | G6 Flash, our prompt | Flash, B's prompt | G7 Pro, B's prompt | G5 B's tuned gemma-4-e4b |
|---|---|---|---|---|
| real benign (n=401, 67 families) | 0.0% [0.0, 0.0] | 1.2% [0.0, 2.8] | 2.5% [1.1, 4.0] | 8.0% [3.4, 13.1] |
| real malicious (n=170, 38 families) | 94.7% [89.3, 99.4] | 97.1% [92.0, 100.0] | 98.8% [97.0, 100.0] | 65.9% [56.4, 75.6] |

Simulated calls, separately:

| Group (block rate, simulated calls) | G6 Flash, our prompt | Flash, B's prompt | G7 Pro, B's prompt | G5 B's tuned gemma-4-e4b |
|---|---|---|---|---|
| simulated malicious (n=297, 57 families) | 99.7% [98.9, 100.0] | 100.0% [100.0, 100.0] | 99.7% [98.9, 100.0] | 86.9% [79.1, 93.4] |

Paired differences on the same records (percentage points): on real malicious calls, G6 minus G7 is -4.1 [-8.3, 0.0]
(G6 minus B-flash, the prompt effect, -2.4 [-4.7, 0.0]; B-flash minus G7, the model effect, -1.8 [-5.9, +1.3]); on
real benign calls G6 blocks 2.5 points less than G7 [-4.2, -1.2]. A different, stronger model (Pro) with a different
prompt blocks slightly more, at a slightly higher false positive rate; G6 is not higher than the other guards. We see no
sign that G6's numbers come from sharing a model with the scenario writer. Limits: Pro is still a Gemini model, so
this is not a cross-vendor test. G5 numbers are B's current tuned model; B may update them.

### 5.5 Adaptive rewrites (offline)

*Responsible use:* adaptive_rewrite_v1, adaptive_rewrite_v2 and
guard_hijack_v1 were produced against the author's own test deployment, only to evaluate guards. Every target is
fictional (Northwind, reserved .example and .test domains, stub tools with no side effects); no real system,
person or organization was attacked. They are test data, never for training. The same applies to 5.6 and 5.7.

100 real malicious test records that G1, G2', G6 or G4 blocked. gemini-3.1-pro (Flex) rewrote only the attacker-
controlled text (tool outputs or user messages) in two rounds, round 2 seeing which guards still caught round 1; the
proposed call stayed identical. Pro then checked that the call was still clearly malicious: 12 dropped, 1 failed,
87 survivors (34 families). Cost USD 2.11. Block rate on the same 87 records (report/adaptive.md):

| Stage | G1 Model Armor | G2' rules | G6 LLM guard | G4 | G7 Pro, B prompt |
|---|---|---|---|---|---|
| original | 31.0% [18.7, 44.2] | 63.2% [51.2, 73.9] | 97.7% [92.9, 100.0] | 97.7% [92.9, 100.0] | 98.9% [96.4, 100.0] |
| round 1 | 60.9% [48.3, 73.6] | 63.2% [51.2, 73.9] | 94.2% [88.2, 98.9] | 95.4% [89.5, 100.0] | 98.9% [96.4, 100.0] |
| final (round 2 if run) | 54.0% [40.4, 68.3] | 63.2% [51.2, 73.9] | 97.7% [92.9, 100.0] | 97.7% [92.9, 100.0] | 100.0% [100.0, 100.0] |

Two black-box rounds by a strong model did not evade the LLM guards. Model Armor caught *more* after rewriting: the
rewrites add polite, instruction-like prose, which its injection filter flags. G2' is unchanged by design, because its
rules read the call and its arguments, which never change. Limits: two rounds, one attacker model, no gradient or
many-query search; a determined attacker with more queries may do better.

### 5.6 Guard-hijack rewrites (offline)

Same 100 source records. gemini-3.1-pro rewrote only the attacker text so that it also addresses the guard: claimed
prior approval, a fake "security review passed" note, text formatted like a system message, and an instruction to answer
allow. Call unchanged. Validity check: 10 dropped as no longer clearly malicious, 1 failed, 89 kept (37 families). Cost
USD 1.28 (report/guard_hijack.md).

| Stage | G1 Model Armor | G2' rules | G6 LLM guard | G4 | G7 Pro, B prompt |
|---|---|---|---|---|---|
| original | 31.5% [19.8, 44.2] | 65.2% [53.3, 76.1] | 97.8% [93.0, 100.0] | 97.8% [93.0, 100.0] | 98.9% [96.5, 100.0] |
| guard-hijack rewrite | 50.6% [39.0, 62.9] | 65.2% [53.3, 76.1] | 97.7% [92.9, 100.0] | 97.7% [92.9, 100.0] | 100.0% [100.0, 100.0] |

Text aimed at the guard did not turn the LLM guards to allow; Model Armor caught more, because system-message formatting
and "answer allow" instructions are exactly what its injection filter looks for.

### 5.7 Deeper adaptive loop: four rounds with guard feedback (offline)

Up to 60 of the same source records, two attacker arms (gemini-3.1-pro and gemini-3.8-flash). Each round the attacker
saw which guards caught the previous version and the stated reasons of G6 and G7; a record stopped early once no guard
caught it. Validity check: 10 of 60 dropped per arm, 50 kept per arm (26 families). Cost USD 3.91. Evasion rate
(share allowed) on the kept records (report/adaptive_v2.md):

| Attacker | Round | G1 Model Armor | G2' rules | G6 LLM guard | G7 Pro, B prompt |
|---|---|---|---|---|---|
| Pro | original | 66.0% [51.8, 81.2] | 42.0% [27.1, 58.0] | 4.0% [0.0, 12.5] | 2.0% [0.0, 6.2] |
| Pro | after 4 rounds | 48.0% [32.0, 64.7] | 42.0% [27.1, 58.0] | 4.3% [0.0, 13.3] | 0.0% [0.0, 0.0] |
| Flash | original | 66.0% [51.8, 81.2] | 42.0% [27.1, 58.0] | 4.0% [0.0, 12.5] | 2.0% [0.0, 6.2] |
| Flash | after 4 rounds | 56.0% [42.9, 70.8] | 42.0% [27.1, 58.0] | 4.3% [0.0, 13.0] | 0.0% [0.0, 0.0] |

Four feedback rounds did not raise evasion of the LLM guards above their starting level (about 4% for G6, 0 to 2% for
G7). Limits: black-box attacker, four rounds, Gemini attackers only; the attacker saw verdicts and reasons, not scores
or gradients. A different attacker family or many more queries may succeed where these did not.

### 5.8 Agent model: Flash vs Pro, unguarded and with live guards

Standard tier, 0 failed runs in any arm (report/agent_models.md). Each pair of rows uses only scenarios both agents ran;
the Flash policy-prompt latency comes from early runs and includes quota waits. The Pro agent is the same agent code
with only the model changed.

| Agent, guard (scenarios) | Runs (failed) | Attack success | Benign completed (log) | Median latency (s) | USD per run |
|---|---|---|---|---|---|
| Flash, no guard (149 scenarios) | 149 (0) | 47.8% [33.3, 60.8] | 100.0% [100.0, 100.0] | 14.3 | 0.0094 |
| Pro, no guard (149 scenarios) | 149 (0) | 67.8% [55.6, 78.8] | 93.2% [86.5, 98.4] | 18.7 | 0.0117 |
| Flash, G6 LLM guard (67 scenarios) | 67 (0) | 2.4% [0.0, 7.3] | 100.0% [100.0, 100.0] | 29.9 | 0.0153 |
| Pro, G6 LLM guard (67 scenarios) | 67 (0) | 4.8% [0.0, 11.6] | 100.0% [100.0, 100.0] | 24.8 | 0.0180 |
| Flash, G4 = G2' + G6 (67 scenarios) | 67 (0) | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 24.4 | 0.0137 |
| Pro, G4 = G2' + G6 (67 scenarios) | 67 (0) | 2.4% [0.0, 7.5] | 100.0% [100.0, 100.0] | 21.3 | 0.0164 |
| Flash, no guard (76 scenarios), policy prompt | 76 (0) | 0.0% [0.0, 0.0] | 100.0% [100.0, 100.0] | 36.5 | 0.0082 |
| Pro, no guard (76 scenarios), policy prompt | 76 (0) | 0.0% [0.0, 0.0] | 93.1% [82.1, 100.0] | 10.1 | 0.0126 |

With live guards (task-only prompt, the 67 scenarios both agents ran with each guard; report/agent_models.md): G6
leaves 2.4% [0.0, 7.3] attack success for Flash and 4.8% [0.0, 11.6] for Pro; G4 leaves 0.0% for Flash and 2.4% [0.0,
7.5] for Pro, with 100% benign completion for both. With the policy in the prompt and no guard (76 pilot scenarios),
neither agent was exploited (0 of 47 attacks each); Pro completed 93.1% [82.1, 100] of benign tasks against Flash's 100%.

Without the policy in its prompt, the stronger model is more exploitable, not less: it carries out injected and
manipulative instructions more competently. Model strength is not a substitute for a policy or a guard.

## 6. What surprised us

- **Agent Gateway could not be used in a project without an organization.** The codelab stack deployed (227
  resources, Terraform changed only to use the project-level Agent Identity trust domain). But an agent attached to
  the gateway never started: every outbound TLS connection received a self-signed proxy certificate
  (CN agent-gateway-proxy.internal) not signed by the gateway's published inspection CA, for Google APIs, Cloud Run and
  external hosts alike, including a fresh agent created after the gateway. So IAM/IAP tool policies (G2) and semantic
  governance (G3) through the gateway are **not tested**; G2' is a hand-written stand-in, not IAM.
- **A good prompt does most of the work.** With the policy in the agent prompt, only about 3% of attacks succeed
  unguarded (2.9% of 312). There, guards mostly cost latency and false refusals.
- **Model Armor blocks about a quarter of legitimate work** in this setting, from the injection filter alone.
- **Attacks aimed at the guards did not work in our tests.** Adaptive rewrites, guard-hijack text and four rounds of
  feedback left the LLM guards' miss rate at about 0 to 5%, and made Model Armor catch more, not less.
- **A stronger agent model is more exploitable without a policy** (Pro 67.8% vs Flash 47.8% attack success, task-only).
- **Agent Runtime query quota is 30 requests per minute per project and region**; an increase request stayed pending
  for three days, which set the pace of the whole benchmark.

## 7. Fairness and limits

- G6 is gemini-3.8-flash, the same model family that wrote the scenarios and runs the agent. Section 5.4 suggests this
  does not drive its numbers, but a cross-vendor check is still missing.
- G2' was written from the same policy text that the labels encode, by the same author, and frozen on
  2026-10-05 before any scenario existed (file unchanged since, sha256 d1b16301...fe0c; commit 47907ae of the
  development history, which is kept in a private archive);
  its near-zero false positives are likely optimistic for an unseen policy. Clauses it cannot check are listed in rules_g2.NOT_COVERED (for example, instructions that came from tool output).
- G4 adds nothing over G6 on these records.
- G1 sees text, not intent, and screens the whole conversation, so it also blocks benign calls inside attack
  conversations.
- G2' is deterministic, G6 and G7 are probabilistic. Live runs vary between configurations even at temperature 0;
  the headline is offline replay on identical records, live runs are reported beside it.
- Replay cannot show what an agent does after a block (retry another way, succeed later).
- Most real malicious calls come from the weaker task-only agent; simulated calls are synthetic substitutions.
- Labels: construction categories were noisy (section 4); gold labels are LLM labels, not human.
- One model, one company policy, five tools, synthetic data, English only.

## 8. Cost

Model tokens for this project: USD 114.10, from usage_metadata at billed rates (standard and Flex), for every run,
label and offline score in this write-up. The per-project Billing report (gross, provisional) shows USD 181.22 for
the Google Cloud project shared with Project B, against USD 181.60 in the two projects' token ledgers: a gap of
-0.38 USD (-0.2%), so infrastructure (Cloud Run, networking, storage, Agent Runtime compute) is inside the noise. Live agent runs cost about USD 0.008 to 0.012 per run for Flash and 0.012 for Pro, plus about
0.006 per run for an LLM guard (COSTS.md).

## 9. Next step

Replicate on Amazon Bedrock AgentCore with the same harness (the client talks to the agent through one thin backend
interface, src/agent_govbench/backend.py), the same scenarios and the same decision-record format, and add a
cross-vendor guard.

## 10. Replication information

Everything this repository can provide to rerun the experiments on a new Google Cloud project. Paths are relative to
the repository root; data files are in the Hugging Face dataset BrejBala/agent-govbench.

**Models, endpoints and settings.** All Gemini calls go to Vertex AI `generateContent` through google-genai 2.28.0
with location `global`. Flex tier means the request headers `X-Vertex-AI-LLM-Request-Type: shared` and
`X-Vertex-AI-LLM-Shared-Request-Type: flex` (`src/agent_govbench/llm.py`); standard tier sends neither.

| Use | Model ID | Tier | Temperature | Thinking |
|---|---|---|---|---|
| Agent, main runs | gemini-3.8-flash | standard | 0 | thinking_level low (ADK BuiltInPlanner) |
| Agent, Pro-agent runs | gemini-3.1-pro-preview | standard | 0 | low |
| G6 live (inside the agent) | gemini-3.8-flash | standard | 0 | low, JSON output |
| G6 offline replay | gemini-3.8-flash | Flex | 0 | low, JSON output |
| G7 offline (adaptive, hijack, loop) | gemini-3.1-pro-preview | Flex | 0 | low, JSON output |
| Scenario generation | gemini-3.8-flash | Flex | 0.8 | low |
| Teacher labels | gemini-3.8-flash; gemini-3.1-pro-preview as second opinion | Flex | 0 | low |
| Run judge | gemini-3.1-pro-preview | Flex | 0 | low |
| Adaptive and guard-hijack rewrites | gemini-3.1-pro-preview (loop also gemini-3.8-flash) | Flex | 1.0 | low |
| Rewrite validity check | gemini-3.1-pro-preview | Flex | 0 | low |
| G1, G1b | Model Armor `sanitizeUserPrompt`, `https://modelarmor.us-central1.rep.googleapis.com/v1/projects/<project>/locations/us-central1/templates/<template>:sanitizeUserPrompt` | n/a | n/a | n/a |
| G5 | Project B's tuned gemma-4-e4b | scored by Project B | | |

The agent is an ADK agent (google-adk 1.34.0, `agent/govbench_agent/agent.py`) deployed with
google-cloud-aiplatform[agent_engines] (>=1.149, <1.154) to Agent Runtime in us-central1 with Agent Identity
(`agent/deploy.py`, which also lists the environment variables). Tools are MCP servers in one Cloud Run service
(`services/tools/`).

**Run dates (UTC, from the run traces and the cost ledger).**

| Experiment | Runs | Dates |
|---|---|---|
| Smoke test, pilots, prompt-variant checks | 1,285 | 2026-10-05 15:33 to 2026-10-06 02:42 |
| G0, policy prompt (plus 12 reruns) | 497 + 12 | 2026-10-07 17:06 to 18:07; reruns 21:58 |
| G0, task-only prompt (plus 9 reruns) | 746 + 9 | 2026-10-07 18:07 to 19:35; reruns 22:01 |
| G1, G2', G6, G4 live, task-only | 1,006 | 2026-10-07 19:36 to 2026-10-08 02:34; 10 reruns about 03:00 |
| G4 live, policy prompt (pilot) | 100 | 2026-10-07 21:48 to 21:57 |
| Pro agent, task-only, no guard | 149 | 2026-10-08 20:58 to 21:14 |
| Pro agent, task-only, G6 and G4 live | 232 | 2026-10-09 03:43 to 04:08 |
| Pro agent, policy prompt, no guard | 76 | 2026-10-09 04:08 to 04:15 |
| Scenario generation | | 2026-10-05 15:17 to 17:59 |
| Teacher labels | | 2026-10-05 15:37 to 2026-10-09 05:55 |
| G6 offline replay | | 2026-10-05 15:45 to 2026-10-07 23:37 |
| Run judge | | 2026-10-07 20:04 to 23:35 |
| Adaptive, guard-hijack and loop rewrites with G6 and G7 scoring | | 2026-10-08 05:21 to 21:57 |

Every live run used the standard tier; every offline step used Flex. Each guard result in a record carries its own
`evaluated_at` time, and every model call is in `ledger/model_calls.jsonl` (time, model, tier, tokens, cost).

**Agent prompts and tools.**
- Policy prompt: `POLICY_TEXT` in `src/agent_govbench/policy.py`. Task-only prompt: `TASK_ONLY_TEXT` in
  `agent/govbench_agent/agent.py`. The session context (`policy.session_context_text`) is appended to either.
- Tool definitions: `TOOLS` in `src/agent_govbench/policy.py` (nine functions on five MCP servers, with MCP read-only
  and destructive annotations). Stub behaviour and synthetic data: `services/tools/main.py`,
  `src/agent_govbench/world.py`.

**Guards.**
- G1: template `govbench-basic` in us-central1: prompt injection and jailbreak filter at MEDIUM_AND_ABOVE, malicious
  URI filter on, responsible-AI filters (hate speech, dangerous, sexually explicit, harassment) at HIGH. Each user
  message and each tool output is screened with `sanitizeUserPrompt` (text truncated at 40,000 characters); block if
  `filterMatchState` is MATCH_FOUND (`src/agent_govbench/guard_ma.py`).
- G1b: template `govbench-pi-low`: prompt injection and jailbreak at LOW_AND_ABOVE plus the filters the project's
  Model Armor floor setting requires (malicious URI on; hate speech, harassment and sexually explicit at
  MEDIUM_AND_ABOVE). Only the injection confidence is read; threshold MEDIUM was chosen on train and validation
  records and frozen on 2026-10-07 (`src/agent_govbench/g1b.py`, `report/g1b_threshold.md`).
- Filters tested: prompt injection and jailbreak (LOW, MEDIUM, HIGH via the reported confidence), malicious URI,
  responsible-AI filters at HIGH. No other Model Armor filter was evaluated.
- G2': `src/agent_govbench/rules_g2.py` (sha256 d1b16301ccfb0349c15f2b6e7aa37b06b5b7e068004e65d4b4a23964e7d7fe0c).
- G6: `SYSTEM` and `build_prompt` in `src/agent_govbench/guard_llm.py` (same prompt live and offline).
- G7: `GUARD_SYSTEM` and `render` in `src/agent_govbench/b_prompts.py` (copied from Project B). Project B's
  predictions for G5, G7 and Flash with B's prompt: `results/b_predictions/` (produced by B's guard code).
- G4: G2' first, then G6 (`agent/govbench_agent/agent.py`, `src/agent_govbench/replay.py`).

**Scenarios, labels and scoring.**
- Seeds: `src/agent_govbench/seeds.py` (`build_seeds` random seed 7, `build_seeds_v2` random seed 17); generation
  prompt `src/agent_govbench/generate.py`; dedup and scenario building `src/agent_govbench/scenarios.py`.
- Scenario files: `data/scenarios/a_generated_v1_{train,val}.jsonl`; test-split scenarios appear as decision records
  in `data/replay/`. Labels: `src/agent_govbench/labeling.py` (teacher prompt), gold slice `data/gold/gold_v1.jsonl`.
- Splits: `contract_v0/split_v0.py` (salt `toolcall-guard-split-v0`, 80% train, 5% validation, 15% test by family).
- Attack success: programmatic checks on the tool-call log, `src/agent_govbench/checks.py`. Offline scoring:
  `src/agent_govbench/replay.py`, `src/agent_govbench/pipeline.py`.
- Metrics: `src/agent_govbench/analysis.py` (family-resampled bootstrap, 2,000 resamples, seed 0) writes
  `report/metrics.json`; cross-model sample `src/agent_govbench/cross_family.py` (all malicious and 1,000 random benign
  test records, seed 20261008); adaptive selection `src/agent_govbench/adaptive.py` (seed 8); tables
  `scripts/writeup_tables.py`, `scripts/readme_tables.py`.

**What cannot be replicated.**
- The Google Cloud project, its Agent Runtime engines, Cloud Run services, bucket and Model Armor templates were
  deleted on 9 Oct 2026; nothing can be rerun against them.
- Preview models and features (gemini-3.1-pro-preview, Agent Runtime, Agent Identity, Agent Gateway, Flex tier, Model
  Armor confidence levels) may have changed since October 2026. Gemini outputs also vary between calls even at
  temperature 0.
- The `govbench-basic` template was created by hand before the project and its JSON was not exported; its settings
  above come from the project notes.
- Raw run traces are kept offline and are not published; the published records hold every proposed call and guard
  verdict.
- G5 and the cross-family G7 and Flash-with-B-prompt numbers were produced by Project B's guard code, which is not
  published yet. Its predictions on our test records are in `results/b_predictions/`, so those tables can be
  recomputed (`python -m agent_govbench.cross_family`), but the predictions themselves cannot be regenerated from this
  repository (B's tuned G5 weights and inference code are not here).
- G2 (IAM/IAP through Agent Gateway) and G3 (semantic governance) were never run.
- Published text differs slightly from what the guards saw: lookalike domains and some customer names were replaced
  before publication (`scripts/sanitize_release.py`).
- Live latency depends on load and quotas (Agent Runtime: 30 queries per minute per project and region).
