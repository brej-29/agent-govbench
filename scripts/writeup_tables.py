"""Rebuild the results tables in report/WRITEUP.md from the generated reports, so the write-up cannot drift from the data.
Tables are replaced in place, matched by their header line."""
import json
import re
from pathlib import Path

R = Path(__file__).resolve().parents[1] / "report"
M = json.loads((R / "metrics.json").read_text())


def c(v, n=True):
    if not v:
        return "n/a"
    s = f"{v[0] * 100:.1f}% [{v[1] * 100:.1f}, {v[2] * 100:.1f}]"
    return s + (f" (n={v[3]:,})" if n else "")


def compact(cell: str) -> str:
    """'31.0% [19.4%, 44.0%] (n=87, fam=34)' -> '31.0% [19.4, 44.0]'"""
    cell = re.sub(r"\[(\-?[\d.]+)%, (\-?[\d.]+)%\]", r"[\1, \2]", cell.strip())
    return re.sub(r"\s*\(n=\d+, fam=\d+\)", "", cell)


def md_rows(path: str, start_after: str | None = None) -> list[list[str]]:
    lines = (R / path).read_text().splitlines()
    if start_after:
        lines = lines[next(i for i, l in enumerate(lines) if l.startswith(start_after)):]
    rows, started = [], False
    for l in lines:
        if l.startswith("|"):
            started = True
            if not l.startswith("|---"):
                rows.append([x.strip() for x in l.strip("|").split("|")])
        elif started:
            break
    return rows


O = M["offline_test"]
G = ["G1", "G1b", "G2p", "G6", "G4"]
GN = {"G1": "G1 Model Armor", "G1b": "G1b injection filter only", "G2p": "G2' hand-written rules", "G6": "G6 LLM guard (Flash)", "G4": "G4 = G2' + G6"}
t51 = ["| Guard | Real malicious calls blocked | Real benign calls blocked (false positives) | Real hard negatives blocked |",
       "|---|---|---|---|"] + [
    f"| {GN[g]} | {c(O.get(f'real malicious|all|{g}'))} | {c(O.get(f'real benign|all|{g}'))} | {c(O.get(f'hard negatives|all|{g}'))} |" for g in G]
t51s = ["| Guard | Simulated compromised-agent calls blocked (synthetic substitution) |", "|---|---|"] + [
    f"| {GN[g]} | {c(O.get(f'simulated malicious|all|{g}'))} |" for g in G]

L = M["live"]
rows52 = [("G0", "policy", "G0|policy|full-policy"), ("G0", "task only", "G0|task_only|full-task"), ("G1", "task only", "G1|task_only|live-task-guards"),
          ("G2'", "task only", "G2p|task_only|live-task-guards"), ("G6", "task only", "G6|task_only|live-task-guards"), ("G4", "task only", "G4|task_only|live-task-guards"),
          ("G1", "policy (pilot)", "G1|policy|pilot"), ("G2'", "policy (pilot)", "G2p|policy|pilot"), ("G6", "policy (pilot)", "G6|policy|pilot"), ("G4", "policy (pilot)", "G4|policy|pilot-g4")]
t52 = ["| Configuration | Prompt | Runs attempted (failed) | Attack success, completed runs | Attack success, failures as errors | Benign completed (log) | Judge: completed / refused | Median / p95 latency (s) | USD per 1,000 runs (guard part) |",
       "|---|---|---|---|---|---|---|---|---|"]
for cfg, prompt, k in rows52:
    v = L[k]
    lat = "quota wait included" if v["latency_median_s"] is None else f"{v['latency_median_s']:.1f} / {v['latency_p95_s']:.1f}"
    jc, jr = v["judge_completed"], v["judge_refused"]
    jtxt = f"{jc[0] * 100:.1f}% / {jr[0] * 100:.1f}%" if jc and jr else "n/a"
    t52.append(f"| {cfg} | {prompt} | {v['runs_attempted']} ({v['runs_failed_counted_as_errors']}) | {c(v['attack_success'])} | {c(v['attack_success_failures_as_errors'])} | "
               f"{c(v['benign_completed_programmatic'], False)} | {jtxt} | {lat} | {v['usd_per_1000_runs']:.2f} ({v['guard_usd_per_1000_runs']:.2f}) |")

CF = md_rows("cross_family.md")
t54 = ["| Group (block rate) | G6 Flash, our prompt | Flash, B's prompt | G7 Pro, B's prompt | G5 B's tuned gemma-4-e4b |", "|---|---|---|---|---|"]
t54s = ["| Group (block rate, simulated calls) | G6 Flash, our prompt | Flash, B's prompt | G7 Pro, B's prompt | G5 B's tuned gemma-4-e4b |", "|---|---|---|---|---|"]
for r in CF[1:]:
    n = re.search(r"\(n=(\d+), fam=(\d+)\)", r[1])
    row = f"| {r[0]} (n={n.group(1)}, {n.group(2)} families) | " + " | ".join(compact(x) for x in r[1:5]) + " |"
    (t54s if r[0].startswith("simulated") else t54).append(row)

ADA = md_rows("adaptive.md")
t55 = ["| Stage | G1 Model Armor | G2' rules | G6 LLM guard | G4 | G7 Pro, B prompt |", "|---|---|---|---|---|---|"] + [
    "| " + r[0] + " | " + " | ".join(compact(x) for x in r[1:6]) + " |" for r in ADA[1:]]
HJ = md_rows("guard_hijack.md")
t56 = ["| Stage | G1 Model Armor | G2' rules | G6 LLM guard | G4 | G7 Pro, B prompt |", "|---|---|---|---|---|---|"] + [
    "| " + r[0] + " | " + " | ".join(compact(x) for x in r[1:6]) + " |" for r in HJ[1:]]
t57 = ["| Attacker | Round | G1 Model Armor | G2' rules | G6 LLM guard | G7 Pro, B prompt |", "|---|---|---|---|---|---|"]
for arm in ("pro", "flash"):
    rows = md_rows("adaptive_v2.md", start_after=f"## Attacker: {arm}")
    for r in rows[1:]:
        if r[0].startswith("0") or r[0] == "4":
            t57.append(f"| {arm.capitalize()} | {'original' if r[0].startswith('0') else 'after 4 rounds'} | " + " | ".join(compact(r[i]) for i in (1, 2, 3, 5)) + " |")
AM = md_rows("agent_models.md")
t58 = ["| Agent, guard (scenarios) | Runs (failed) | Attack success | Benign completed (log) | Median latency (s) | USD per run |", "|---|---|---|---|---|---|"]
for r in AM[1:]:
    if r[0].startswith("agent"):
        continue
    t58.append(f"| {r[0]} | {r[1]} ({r[2]}) | {compact(r[3])} | {compact(r[5])} | {r[6]} | {r[7]} |")
AMP = md_rows("agent_models.md", start_after="## Policy prompt")
for r in AMP[1:]:
    t58.append(f"| {r[0]}, policy prompt | {r[1]} ({r[2]}) | {compact(r[3])} | {compact(r[5])} | {r[6]} | {r[7]} |")

REPL = {"| Guard | Real malicious calls blocked": t51, "| Guard | Simulated compromised-agent calls blocked": t51s,
        "| Group (block rate, simulated calls)": t54s, "| Configuration | Prompt | Runs attempted": t52, "| Group (block rate) | G6 Flash": t54,
        "| Stage | G1 Model Armor | G2' rules | G6 LLM guard | G4 | G7": None, "| Attacker | Round": t57, "| Agent model | Attack success": t58,
        "| Agent, guard (scenarios)": t58}

w = (R / "WRITEUP.md").read_text().splitlines()
out, i, stage_tables = [], 0, [t55, t56]
while i < len(w):
    line = w[i]
    key = next((k for k in REPL if line.startswith(k)), None)
    if key:
        j = i
        while j < len(w) and w[j].startswith("|"):
            j += 1
        new = REPL[key] if REPL[key] is not None else stage_tables.pop(0)
        out += new
        i = j
        continue
    out.append(line)
    i += 1
text = "\n".join(out)
if "| Guard | Simulated compromised-agent calls blocked" not in text:
    k = text.index("\n", text.index(t51[-1])) + 1
    text = text[:k] + "\nSimulated compromised-agent calls, reported separately from real agent calls:\n\n" + "\n".join(t51s) + "\n" + text[k:]
if "| Group (block rate, simulated calls)" not in text:
    k = text.index("\n", text.index(t54[-1])) + 1
    text = text[:k] + "\nSimulated calls, separately:\n\n" + "\n".join(t54s) + "\n" + text[k:]
out = text.splitlines()
(R / "WRITEUP.md").write_text("\n".join(out).replace("\u2014", "-") + "\n")
print("rebuilt tables")
