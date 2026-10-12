"""Item 3: unguarded agent, task-only prompt, gemini-3.1-pro-preview vs gemini-3.8-flash on the same test scenarios.
Failed runs are counted (and counted as errors in a second column). Writes report/pro_agent.md."""
import statistics as st

from .analysis import boot_ci, fmt
from .config import REPO_ROOT
from .report_runs import latest


def main():
    ids = set((REPO_ROOT / "data" / "pro_agent_ids.txt").read_text().split())
    pro = {t["scenario_id"]: t for t in latest("pro-agent-task")}
    flash = {}
    for tag in ("full-task", "v2-task", "pilot-task", "full-task-r"):
        for t in latest(tag):
            if t["scenario_id"] in ids and (t["scenario_id"] not in flash or flash[t["scenario_id"]]["error"]):
                flash[t["scenario_id"]] = t
    lines = ["# Agent model comparison: unguarded, task-only prompt, same 149 test scenarios (standard tier)", "",
             "| agent model | runs attempted | failed | attack success (completed runs) | attack success (failures as errors) | benign completed (log) | median latency s | USD per run |",
             "|---|---|---|---|---|---|---|---|"]
    for name, d in (("gemini-3.8-flash", flash), ("gemini-3.1-pro-preview", pro)):
        ts = [d[i] for i in ids if i in d]
        ok = [t for t in ts if not t["error"]]
        fail = [t for t in ts if t["error"]]
        att = [(t["family_id"], int(t["eval"]["attack_success"])) for t in ok if t["is_attack"]]
        att_e = att + [(t["family_id"], 1) for t in fail if t["is_attack"]]
        ben = [(t["family_id"], int(t["eval"]["benign_completed"])) for t in ok if not t["is_attack"]]
        lat = [t["latency_s"] for t in ok]
        usd = st.mean(t["cost"]["agent"]["usd"] for t in ok) if ok else 0
        lines.append(f"| {name} | {len(ts)} | {len(fail)} | {fmt(boot_ci(att))} | {fmt(boot_ci(att_e))} | {fmt(boot_ci(ben))} | "
                     f"{st.median(lat):.1f} | {usd:.4f} |")
    lines += ["", "Flash latency for full-task runs excludes quota waits; pilot-task Flash runs (if any of these scenarios) include them."]
    (REPO_ROOT / "report" / "pro_agent.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
