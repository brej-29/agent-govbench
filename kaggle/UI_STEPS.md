# Grouping the tasks into a benchmark and publishing (HOLD: do nothing until you say go)

Status: everything is private (dataset, tasks, notebooks). The CLI cannot create or manage benchmarks (collections); that is done in the web UI.
Menu names below come from Kaggle's announcement and docs and may differ slightly; check each screen, and tell the session if one is different.

## 0. Before anything public
- [ ] Fill in the review provenance line (`kaggle/codemix/README.md`) if the pilot is included.
- [ ] Read the dataset description and task descriptions (255 characters each) once more; confirm you are happy for the data to be CC BY 4.0 and public.
- [ ] Decide whether the pilot task is part of the first benchmark (recommended: leave it out until its results are written up; add later as a fourth task).
- [ ] Confirm all intended model runs are finished (`kaggle b t status <slug>`); the leaderboard shows what has been run when you publish.

## 1. Make the dataset public
Kaggle > Datasets > `agent-govbench-items` > Settings (or Sharing) > Visibility: Public. A public task cannot depend on a private dataset.

## 2. Make the tasks public (CLI or UI)
```bash
kaggle b t publish agent-govbench-guard-judge
kaggle b t publish agent-govbench-agent-policy-in-prompt
kaggle b t publish agent-govbench-agent-task-only-prompt
```
This also publishes each backing notebook; add `--no-publish-backing-notebook` to keep notebooks private. The pilot task slug is
`agent-govbench-code-mixed-tool-use-pilot` (confirm in `kaggle b t list`). Do not push new versions after publishing: a new version
means rerunning every model.

## 3. Create the benchmark (web UI)
1. Kaggle left navigation > Benchmarks.
2. Start a new benchmark (button near the top of the Benchmarks page).
3. Name: `Agent GovBench` . Description (suggested): "How well do tool-using AI agents, and AI guards, hold a company policy under pressure? Three tasks on a fictional company: a guard judge (allow or block one proposed tool call, 400 items) and an agent that must resist injected instructions and manipulation while still finishing legitimate work (180 scenarios, with and without the policy in its prompt). Synthetic data; scores are single runs with family-bootstrap intervals; see the write-up for limits."
4. Add tasks: choose the three tasks above (they appear under your tasks once public; search by name). Order: Guard Judge, Agent (task-only prompt), Agent (policy in prompt).
5. Select the models to evaluate. Pick the models already run so the leaderboard fills from existing runs, and avoid models that were not run (grok, gpt-6-astra, gemini-2.5) to prevent empty or failing columns.
6. Save and check the leaderboard. Each task contributes one score column (Guard Judge: balanced accuracy; the agent tasks: mean of resist and completion rate).

## 4. Publish the benchmark
Benchmark page > Share/Visibility > Public. Then check it in a private browser window.

## 5. After publishing
- Add the README link: `README.md` in the repo has a placeholder section to fill in with the benchmark URL (the session will add it when you give the URL or say go).
- Optional: add the pilot as a fourth task once its write-up is done.
- Grant: `GRANT_DRAFT.md` is a draft for you to review and submit through the form linked from Kaggle's Benchmarks announcement page; I could not retrieve the form's current questions, so adapt the draft to them.
