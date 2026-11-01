# Results (generated)

| Model | Task | n | Score [95% CI] | Resist / block | Complete / allow | Cost USD |
|---|---|---|---|---|---|---|
| claude-haiku-4-5-20251001 | agent-policy | 180 | 0.840 [0.784, 0.890] | 0.933 | 0.747 | 0.83 |
| claude-haiku-5-5 | agent-policy | 180 | 0.917 [0.870, 0.954] | 0.981 | 0.853 | 0.08 |
| gemini-3.1-flash-lite-preview | agent-policy | 180 | 0.769 [0.706, 0.825] | 0.724 | 0.813 | 0.22 |
| gemini-3.1-pro-preview | agent-policy | 180 | 0.900 [0.853, 0.943] | 0.933 | 0.867 | 2.58 |
| gemini-3.5-flash-lite | agent-policy | 180 | 0.803 [0.741, 0.858] | 0.752 | 0.853 | 0.28 |
| gemini-3.8-flash | agent-policy | 180 | 0.916 [0.874, 0.956] | 0.952 | 0.880 | 1.20 |
| gemma-4-26b-a4b-it | agent-policy | 180 | 0.881 [0.831, 0.925] | 0.895 | 0.867 | 0.19 |
| gemma-4-31b-it | agent-policy | 180 | 0.882 [0.831, 0.931] | 0.924 | 0.840 | 0.17 |
| gpt-5.4-mini-2026-03-17 | agent-policy | 180 | 0.808 [0.753, 0.864] | 0.895 | 0.720 | 0.20 |
| gpt-5.4-nano-2026-03-17 | agent-policy | 180 | 0.800 [0.742, 0.857] | 0.933 | 0.667 | 0.11 |
| gpt-oss-120b | agent-policy | 180 | 0.823 [0.769, 0.876] | 0.819 | 0.827 | 0.06 |
| claude-haiku-4-5-20251001 | agent-task-only | 180 | 0.714 [0.651, 0.774] | 0.629 | 0.800 | 0.81 |
| claude-haiku-5-5 | agent-task-only | 180 | 0.804 [0.742, 0.862] | 0.781 | 0.827 | 0.08 |
| claude-opus-5-5-default | agent-task-only | 180 | 0.775 [0.714, 0.838] | 0.790 | 0.760 | 2.42 |
| gemini-3.1-flash-lite-preview | agent-task-only | 180 | 0.528 [0.470, 0.586] | 0.229 | 0.827 | 0.25 |
| gemini-3.1-pro-preview | agent-task-only | 180 | 0.645 [0.584, 0.704] | 0.410 | 0.880 | 2.62 |
| gemini-3.5-flash-lite | agent-task-only | 180 | 0.626 [0.566, 0.686] | 0.371 | 0.880 | 0.28 |
| gemini-3.8-flash | agent-task-only | 180 | 0.686 [0.625, 0.744] | 0.505 | 0.867 | 1.48 |
| gemma-4-26b-a4b-it | agent-task-only | 180 | 0.596 [0.539, 0.660] | 0.352 | 0.840 | 0.23 |
| gemma-4-31b-it | agent-task-only | 180 | 0.590 [0.536, 0.645] | 0.314 | 0.867 | 0.18 |
| gpt-5.4-mini-2026-03-17 | agent-task-only | 180 | 0.649 [0.584, 0.713] | 0.524 | 0.773 | 0.31 |
| gpt-5.4-nano-2026-03-17 | agent-task-only | 180 | 0.582 [0.518, 0.641] | 0.390 | 0.773 | 0.09 |
| gpt-oss-120b | agent-task-only | 180 | 0.580 [0.517, 0.645] | 0.333 | 0.827 | 0.06 |
| claude-haiku-4-5-20251001 | judge | 400 | 0.850 [0.813, 0.886] | 0.940 | 0.760 | 0.89 |
| claude-haiku-5-5 | judge | 400 | 0.927 [0.901, 0.952] | 0.925 | 0.930 | 0.10 |
| claude-opus-5-5-default | judge | 399 (+1 failed) | 0.917 [0.882, 0.948] | 0.860 | 0.975 | 3.70 |
| gemini-3.1-flash-lite-preview | judge | 400 | 0.895 [0.859, 0.930] | 0.845 | 0.945 | 0.21 |
| gemini-3.1-pro-preview | judge | 297 of 400 | incomplete (quota rejections), excluded; rerun | | | 3.79 |
| gemini-3.5-flash-lite | judge | 400 | 0.900 [0.868, 0.931] | 0.845 | 0.955 | 0.26 |
| gemini-3.8-flash | judge | 400 | 0.978 [0.960, 0.992] | 0.985 | 0.970 | 1.11 |
| gemma-4-26b-a4b-it | judge | 400 | 0.892 [0.853, 0.926] | 0.815 | 0.970 | 0.13 |
| gemma-4-31b-it | judge | 400 | 0.970 [0.950, 0.987] | 0.975 | 0.965 | 0.21 |
| gpt-5.4-mini-2026-03-17 | judge | 400 | 0.863 [0.827, 0.897] | 0.805 | 0.920 | 0.40 |
| gpt-5.4-nano-2026-03-17 | judge | 400 | 0.855 [0.814, 0.893] | 0.825 | 0.885 | 0.15 |
| gpt-oss-120b | judge | 400 | 0.932 [0.904, 0.957] | 0.910 | 0.955 | 0.11 |

**Pro vs Flash, agent-task-only, 105 attack scenarios.** Attack success Pro 0.590, Flash 0.495; difference (Pro minus Flash) +0.095 [+0.029, +0.162] family bootstrap. Discordant pairs: Pro exploited and Flash resisted 12, the reverse 2; exact McNemar p = 0.013.

**Pro vs Flash, agent-policy, 105 attack scenarios.** Attack success Pro 0.067, Flash 0.048; difference (Pro minus Flash) +0.019 [-0.029, +0.067] family bootstrap. Discordant pairs: Pro exploited and Flash resisted 4, the reverse 2; exact McNemar p = 0.688.

## 2026-11-01: code-mixed pilot status
Not run yet (no quota). Reviewed items ready (90, owner rewrites applied, arguments identical across twins). Design: paired by intent,
mixed minus English, per language, per speech act, per kind, pooled over a contrast lineup (closed frontier, mid, cheap, open).
Known limit before any result: speech act is aliased with language (Manglish 18 polite questions, Tanglish 0).
