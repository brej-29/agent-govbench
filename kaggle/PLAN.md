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
