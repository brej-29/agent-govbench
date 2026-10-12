"""Override round (2026-10-09): Pro agent with live G6 and G4 (task-only) and Pro agent with the policy prompt (no guard),
each beside the Flash agent on the same scenarios. Failed runs are counted. Writes report/agent_models.md."""
import statistics as st

from .analysis import boot_ci, fmt
from .config import REPO_ROOT
from .report_runs import latest

FLASH_TASK = {"G0": ["full-task", "v2-task", "pilot-task", "full-task-r"], "G6": ["live-task-guards"], "G4:G2p+G6": ["live-task-guards"]}
PRO_TASK = {"G0": ["pro-agent-task"], "G6": ["pro-agent-task-guards"], "G4:G2p+G6": ["pro-agent-task-guards"]}
FLASH_POLICY = ["pilot", "full-policy", "g0test", "v2-policy", "full-policy-r"]


def collect(tags, config, variant):
    out = {}
    for tag in tags:
        p = REPO_ROOT / "data" / "runs" / tag / "traces.jsonl"
        if not p.exists():
            continue
        for t in latest(tag):
            if t["config"] != config or t.get("prompt_variant", "policy") != variant:
                continue
            if t["scenario_id"] not in out or out[t["scenario_id"]]["error"]:
                out[t["scenario_id"]] = t
    return out


def line(name, ts):
    ok = [t for t in ts if not t["error"]]
    fail = [t for t in ts if t["error"]]
    att = [(t["family_id"], int(t["eval"]["attack_success"])) for t in ok if t["is_attack"]]
    att_e = att + [(t["family_id"], 1) for t in fail if t["is_attack"]]
    ben = [(t["family_id"], int(t["eval"]["benign_completed"])) for t in ok if not t["is_attack"]]
    lat = [t["latency_s"] for t in ok]
    usd = st.mean(t["cost"]["agent"]["usd"] + sum(g["usd"] for g in t["cost"]["guards"].values()) for t in ok) if ok else 0
    return (f"| {name} | {len(ts)} | {len(fail)} | {fmt(boot_ci(att))} | {fmt(boot_ci(att_e))} | {fmt(boot_ci(ben))} | "
            f"{st.median(lat):.1f} | {usd:.4f} |" if ok else f"| {name} | {len(ts)} | {len(fail)} | n/a | n/a | n/a | n/a | n/a |")


HEAD = ["| agent, guard | runs | failed | attack success (completed) | attack success (failures as errors) | benign completed (log) | median latency s | USD per run (agent + guard) |",
        "|---|---|---|---|---|---|---|---|"]


def main():
    lines = ["# Agent model comparison (standard tier, 95% bootstrap, families resampled)", ""]
    # task-only, by guard, on scenarios both agents completed for that guard
    lines += ["## Task-only prompt: Flash vs Pro agent, unguarded and with live guards", "",
              "Each guard row pair uses only scenarios where both agents have a run with that guard.", ""] + HEAD
    for cfg, label in (("G0", "no guard"), ("G6", "G6 LLM guard"), ("G4:G2p+G6", "G4 = G2' + G6")):
        f = collect(FLASH_TASK[cfg], cfg, "task_only")
        p = collect(PRO_TASK[cfg], cfg, "task_only")
        common = sorted(set(f) & set(p))
        lines.append(line(f"Flash, {label} ({len(common)} scenarios)", [f[i] for i in common]))
        lines.append(line(f"Pro, {label} ({len(common)} scenarios)", [p[i] for i in common]))
    # policy prompt, no guard, pilot scenarios
    pilot = set((REPO_ROOT / "data" / "pilot_ids.txt").read_text().split())
    f = {k: v for k, v in collect(FLASH_POLICY, "G0", "policy").items() if k in pilot}
    p = collect(["pro-agent-policy"], "G0", "policy")
    common = sorted(set(f) & set(p))
    lines += ["", "## Policy prompt, no guard: Flash vs Pro agent (pilot scenarios)", ""] + HEAD
    lines.append(line(f"Flash, no guard ({len(common)} scenarios)", [f[i] for i in common]))
    lines.append(line(f"Pro, no guard ({len(common)} scenarios)", [p[i] for i in common]))
    lines += ["", "Flash pilot runs predate the latency fix (their latency includes quota waits); compare latency only within Pro rows "
              "or against full-run Flash rows."]
    (REPO_ROOT / "report" / "agent_models.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
