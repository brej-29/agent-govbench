# Sweep plan and budget

Quota: $10 per day (resets 19:21 UTC), $100 per 30 days (refills 2026-11-28). Spent before the sweep: about $6.2 (probes, pushes).
Targets set by the owner: one full pass about $55 to $60; reserve about $20 for variance reruns and the code-mixed pilot.
At most 2 or 3 task runs in flight (the owner's other project shares the batch CPU cap).

Cost per model for one full pass (judge 400 items + agent policy 180 + agent task-only 180), from 4-item probes except
where measured (M). Estimates for GPT-6 are guesses until its agent probe works.

| Model | Lab / kind | Est. $ | Role in the comparison |
|---|---|---|---|
| gemini-3.8-flash | Google, closed, mid | 3.8 (M) | the original agent and guard model |
| gemini-3.1-pro-preview | Google, closed, frontier | 11.4 | replicate Pro vs Flash |
| claude-opus-5-5-default | Anthropic, closed, frontier | 12.6 | frontier, other lab |
| gpt-6-sol | OpenAI, closed, frontier | ~6 | frontier, third lab (agent runs with reasoning off) |
| claude-sonnet-5-5-default | Anthropic, closed, mid | 7.6 | size ladder |
| gemini-3.6-flash | Google, closed, mid | 5.2 | version ladder |
| gpt-5.4-2026-03-05 | OpenAI, closed, mid | 4.3 | |
| claude-haiku-4-5-20251001 | Anthropic, closed, small, older | 2.3 | |
| claude-haiku-5-5 | Anthropic, closed, small | 0.3 (M) | |
| gpt-5.4-nano / gpt-5.4-mini | OpenAI, closed, small | 0.4 (M) / 1.2 | |
| gemini-3.1-flash-lite-preview, gemini-3.5-flash-lite | Google, closed, small | 0.9 / 1.0 | |
| gpt-oss-120b | OpenAI, open weights | 0.3 | open |
| gemma-4-26b-a4b-it, gemma-4-31b-it | Google, open weights | 0.8 / 1.1 | open, size |

Total about $59. Not run: grok-* (404), gpt-6-astra (no tool support), gemini-2.5-* (agent tasks fail with multiple tools),
claude-opus-4-x and claude-opus-5 (cost), gemini-3-flash-preview, gpt-5.5 (cost).

Variance reruns (reserve): judge x2 more on the cheap and mid models; agent task-only x1 more on 5 to 6 cheap and mid models.
Code-mixed pilot: about 6 models, held until the owner approves the item sheet.

Order (use each daily window fully): day 1 validation and cheap models; day 2 gemini-3.1-pro and opus-5-5; day 3 sonnet,
gpt-6-sol, gemini-3.6-flash; day 4 remaining mid models and reruns; day 5 code-mixed pilot and leftovers.

## Remaining schedule (set 2026-11-02; credits expire 2026-11-05 13:29 IST = 07:59 UTC)
Wakes (UTC): 11-02 04:50 (trigger from earlier), 11-03 04:50, 11-04 04:50, 11-05 04:50 (final, must end before 07:30). Quota already
used this month: $27.6 of $100. Each window keeps launches below $7 "used" so in-flight runs cannot cross $10 (a run that crosses
loses items: the first gemini-3.1-pro judge run lost 103 of 400).

| Window | Queue file | Contents | Est. $ |
|---|---|---|---|
| 11-02 | queue_day4.txt | gemini-3.1-pro judge rerun; push pilot task; pilot on opus-5-5, haiku-5-5, gemma-4-31b (+ gemini-3.8-flash at creation); opus-5-5 policy | about 8.3 |
| 11-03 | queue_day5.txt | claude-sonnet-5-5 (3 tasks) | about 7.6 |
| 11-04 | queue_day6.txt | gemini-3.6-flash (3 tasks), gpt-5.4 judge, judge reruns on haiku-5-5, gpt-oss-120b, gemma-4-31b | about 8.0 |
| 11-05 | queue_day7.txt | gpt-5.4 agent tasks, agent task-only reruns on 3 cheap models, pilot rerun on haiku-5-5 | about 3.2 |

Month total at the end: about $55. Left for the owner (see RUNBOOK.md): gpt-6-sol (3 tasks, about $6, agent runs need reasoning off),
more variance reruns, pilot reruns on opus-5-5 and gemma-4-31b, gemini-3.1-pro policy/judge reruns if wanted (about $10).
Dropped for cost: opus-5 (about $22), gpt-5.5 (about $13), gemini-3-flash-preview. Dropped for platform reasons: grok-4.5/4.6 (404),
gpt-6-astra (no tool support), gemini-2.5-* (multiple-tools error).
