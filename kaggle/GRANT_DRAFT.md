# Draft: Kaggle Benchmarks Resource Grant application (for the owner to review; not submitted)

I could not retrieve the form or its criteria (only secondary coverage: the grant gives compute and infrastructure support and
marketing help to people who build new benchmarks but lack the compute to run them at scale). Adapt this text to the actual questions.
Numbers below are from `RESULTS.md` as of the last update; refresh them before submitting. Do not submit anything public-facing without checking the claims.

## Project name
Agent GovBench: policy adherence of tool-using agents and AI guards

## One-paragraph summary
Agent GovBench measures whether AI agents and AI guards keep a company policy when the input is adversarial: instructions hidden in tool
output, user-side manipulation, false authority and approval claims. It has three tasks on a fictional company with ten stubbed tools:
a guard judge (400 labelled tool calls, half harmful, with look-alike legitimate calls to catch over-blocking) and an agent task
(105 attack and 75 legitimate scenarios) run with and without the policy in the system prompt. Scoring is programmatic (no LLM judge).
The Kaggle port reproduces the headline of an earlier Google Cloud study (task-only attack success 49.5% vs 51.5% originally for gemini-3.8-flash)
and shows that a stronger model is not safer by default: gemini-3.1-pro is more exploitable than gemini-3.8-flash without the policy in the prompt
(attack success 59% vs 50%, paired p = 0.013 on identical scenarios).

## What is new
- Pairs of attack scenarios and look-alike legitimate ones, so over-blocking and over-refusing are scored, not just attack success.
- The same data scored two ways (model as guard, model as agent), which separates "can it recognise the violation" from "does it avoid it when acting".
- A planned code-mixed Tamil-English and Malayalam-English tool-use set with matched English twins, to test whether policy holds outside English
  (pilot items reviewed; results pending).

## Evidence of results so far (single runs, 95% family-bootstrap intervals in RESULTS.md)
- 12+ models from several labs, open and closed, sizes from small to frontier; per-run cost recorded from Kaggle's own figures.
- Agent, task-only prompt: resist rate from 0.23 (gemini-3.1-flash-lite) to 0.79 (claude-opus-5-5); the policy prompt lifts every model.
- Judge: balanced accuracy 0.85 to 0.98; strict output parsing costs claude-haiku-5-5 3.5 points relative to a lenient parse.

## Why resources are needed
One full pass of three tasks costs from under $1 (small models) to about $12 (frontier models) at current prices, and the sweep so far used
most of a $100 monthly Model Proxy quota. Needs: (1) runs of the remaining frontier models and repeated runs (3 to 5 per model) to
measure run-to-run variance; (2) re-running as new models appear, which Kaggle's hosted benchmarks can do; (3) a larger code-mixed set
(100+ intents, 4 languages, native-script variants) with a native-speaker review budget; (4) larger scenario sets so per-category intervals are tight.

## Plan and deliverables
1. Variance study (3 to 5 runs per model) and a paired-test table across all models.
2. Code-mixed set v1 (Tamil, Malayalam, Hindi, Kannada, Telugu; Latin and native script) with a fixed argument-identity check and speech-act control.
3. Public write-up, item files (CC BY 4.0) and task code (Apache-2.0); results kept current as models are added.

## Limits we state up front
Synthetic data and LLM-assisted labels (two independent ChatGPT passes on a 120-record slice, no human adjudication); one fictional company and
policy, English-first; success checks derived from labelled harmful calls rather than the original generator's checks; scripted session prefixes
replace live fixtures; temperature is not controllable through the proxy, so results include sampling noise; GPT-6-family agent runs need reasoning off.

## About the applicant
[Owner to write: background, affiliation, links (GitHub brej-29/agent-govbench, Hugging Face BrejBala/agent-govbench).]
Review provenance of the code-mixed items (owner's statement): "All scores, rewrites are my own. Notes drafted with AI help, every row checked and approved by me." Initial item drafts were written by Claude.
