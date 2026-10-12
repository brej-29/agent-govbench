"""Fill the generated tables in README.md (key results, offline, live) from report/metrics.json, between\n<!-- generated:*:start/end --> markers. Importable: scripts/check_readme_numbers.py uses BLOCKS and fill()."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "report" / "metrics.json").read_text())


def c(v):
    return "n/a" if not v else f"{v[0] * 100:.1f}% [{v[1] * 100:.1f}, {v[2] * 100:.1f}] (n={v[3]:,})"


O = M["offline_test"]
names = {"G1": "G1 Model Armor", "G1b": "G1b Model Armor, injection filter only", "G2p": "G2' hand-written rules",
         "G6": "G6 LLM guard (Flash)", "G4": "G4 = G2' + G6"}
off = ["| Guard | Malicious calls blocked | Benign calls blocked (false positives) | Hard negatives blocked |", "|---|---|---|---|"]
off += [f"| {names[g]} | {c(O.get(f'real malicious|all|{g}'))} | {c(O.get(f'real benign|all|{g}'))} | {c(O.get(f'hard negatives|all|{g}'))} |"
        for g in ("G1", "G1b", "G2p", "G6", "G4")]

L = M["live"]
rows = [("No guard, policy in prompt", "G0|policy|full-policy"), ("No guard, task-only prompt", "G0|task_only|full-task"),
        ("G1 Model Armor", "G1|task_only|live-task-guards"), ("G2' hand-written rules", "G2p|task_only|live-task-guards"),
        ("G6 LLM guard", "G6|task_only|live-task-guards"), ("G4 = G2' + G6", "G4|task_only|live-task-guards")]
live = ["| Configuration | Runs (failed) | Attack success | Benign tasks completed | Median latency (s) |", "|---|---|---|---|---|"]
for name, k in rows:
    v = L[k]
    b = v["benign_completed_programmatic"]
    live.append(f"| {name} | {v['runs_attempted']} ({v['runs_failed_counted_as_errors']}) | {c(v['attack_success'])} | "
                f"{b[0] * 100:.1f}% | {v['latency_median_s']:.1f} |")

key = ["| Result (real agent calls only) | Value, 95% CI (n) | Measured in |", "|---|---|---|",
       f"| Attack success, no guard, task-only prompt | {c(L['G0|task_only|full-task']['attack_success'])} | live runs |",
       f"| Attack success, no guard, policy in prompt | {c(L['G0|policy|full-policy']['attack_success'])} | live runs |",
       f"| Attack success with G6 LLM guard, task-only prompt | {c(L['G6|task_only|live-task-guards']['attack_success'])} | live runs |",
       f"| Malicious calls blocked by G6 | {c(O['real malicious|all|G6'])} | offline replay, test split |",
       f"| Legitimate calls blocked by G1 Model Armor | {c(O['real benign|all|G1'])} | offline replay, test split |",
       f"| Legitimate calls blocked by G6 | {c(O['real benign|all|G6'])} | offline replay, test split |"]

BLOCKS = {"key": key, "offline": off, "live": live}


def fill(text: str) -> str:
    for tag, table in BLOCKS.items():
        text = re.sub(rf"<!-- generated:{tag}:start -->.*?<!-- generated:{tag}:end -->",
                      f"<!-- generated:{tag}:start -->\n" + "\n".join(table) + f"\n<!-- generated:{tag}:end -->", text, flags=re.S)
    return text


if __name__ == "__main__":
    (ROOT / "README.md").write_text(fill((ROOT / "README.md").read_text()))
    print("README tables filled")
