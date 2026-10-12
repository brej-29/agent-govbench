"""Figures for the write-up (static PNG, from report/metrics.json). Dot = estimate, bar = 95% bootstrap interval
(families resampled). Palette: reference categorical slots 1 (blue) and 2 (orange); marker shape is a second encoding.
The palette validator (node) was not available in this environment."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "report" / "metrics.json").read_text())
OUT = ROOT / "report" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
BLUE, ORANGE, INK, MUTED, SURFACE = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#fcfcfb"
GUARDS = [("G1", "G1 Model Armor"), ("G2p", "G2' hand-written rules"), ("G6", "G6 LLM guard (Flash)"), ("G4", "G4 = G2' + G6")]
plt.rcParams.update({"font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED,
                     "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": SURFACE,
                     "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE})


def ci(key, g, src="offline_test"):
    v = M[src].get(f"{key}|{g}")
    return None if not v else (v[0] * 100, v[1] * 100, v[2] * 100, v[3])


def dot(ax, y, c, color, marker, label=None):
    if not c:
        return
    m, lo, hi, n = c
    ax.plot([lo, hi], [y, y], color=color, lw=2, solid_capstyle="round", zorder=2)
    ax.plot([m], [y], marker=marker, ms=8, color=color, mec=SURFACE, mew=2, zorder=3, label=label, ls="none")


# Figure 1: offline, identical test records
fig, (a, b) = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
ys = list(range(len(GUARDS)))[::-1]
for i, (g, name) in enumerate(GUARDS):
    dot(a, ys[i] + 0.12, ci("real malicious|all", g), BLUE, "o", "real agent calls" if i == 0 else None)
    dot(a, ys[i] - 0.12, ci("simulated malicious|all", g), ORANGE, "s", "simulated compromised-agent calls" if i == 0 else None)
    dot(b, ys[i], ci("real benign|all", g), BLUE, "o")
a.set_yticks(ys, [n for _, n in GUARDS])
a.set_xlim(0, 100); b.set_xlim(0, 40)
a.set_title("Malicious calls blocked (%)", loc="left", color=INK)
b.set_title("Benign calls blocked: false positives (%)", loc="left", color=INK)
for ax in (a, b):
    ax.grid(axis="x", color="#e6e5df", lw=0.8); ax.set_axisbelow(True)
a.legend(loc="lower left", frameon=False, fontsize=9)
fig.suptitle("Offline replay on identical test records (95% intervals, families resampled)", x=0.01, ha="left", color=INK)
fig.tight_layout(); fig.savefig(OUT / "fig1_offline_guards.png", dpi=160); plt.close(fig)

# Figure 2: live attack success, task-only prompt, plus the policy-prompt baseline
live = M["live"]
rows = [("G0 no guard, policy prompt", "G0|policy|full-policy"), ("G0 no guard, task-only prompt", "G0|task_only|full-task"),
        ("G1 Model Armor", "G1|task_only|live-task-guards"), ("G2' hand-written rules", "G2p|task_only|live-task-guards"),
        ("G6 LLM guard", "G6|task_only|live-task-guards"), ("G4 = G2' + G6", "G4|task_only|live-task-guards")]
fig, ax = plt.subplots(figsize=(7.5, 3.2))
for i, (name, k) in enumerate(rows):
    v = live.get(k, {}).get("attack_success")
    if v:
        dot(ax, len(rows) - 1 - i, (v[0] * 100, v[1] * 100, v[2] * 100, v[3]), BLUE, "o")
        ax.text(v[2] * 100 + 1.5, len(rows) - 1 - i, f"{v[0] * 100:.1f}%  (n={v[3]})", va="center", color=MUTED, fontsize=9)
ax.set_yticks(range(len(rows))[::-1], [r[0] for r in rows]); ax.set_xlim(0, 75)
ax.set_title("Live attack success (%), standard tier", loc="left", color=INK)
ax.grid(axis="x", color="#e6e5df", lw=0.8); ax.set_axisbelow(True)
fig.tight_layout(); fig.savefig(OUT / "fig2_live_attack_success.png", dpi=160); plt.close(fig)

# Figure 3: live latency per run (agent time, quota waits excluded), task-only prompt
fig, ax = plt.subplots(figsize=(7.5, 3.4))
lrows = rows[1:]
for i, (name, k) in enumerate(lrows):
    v = live.get(k, {})
    y = len(lrows) - 1 - i
    if v.get("latency_median_s") is not None:
        ax.plot([v["latency_median_s"]], [y], "o", ms=8, color=BLUE, mec=SURFACE, mew=2, label="median" if i == 0 else None)
    if v.get("latency_p95_s") is not None:
        ax.plot([v["latency_p95_s"]], [y], "s", ms=8, mfc=SURFACE, mec=ORANGE, mew=2, label="95th percentile" if i == 0 else None)
ax.set_yticks(range(len(lrows))[::-1], [r[0] for r in lrows])
ax.set_title("Live run latency, seconds (task-only prompt)", loc="left", color=INK)
ax.grid(axis="x", color="#e6e5df", lw=0.8); ax.set_axisbelow(True); ax.set_xlim(0, 110); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=2, fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "fig3_latency.png", dpi=160); plt.close(fig)
print("figures:", sorted(p.name for p in OUT.glob("*.png")))
