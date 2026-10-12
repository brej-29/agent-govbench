"""CHECKPOINT 2b numbers: proposed calls per split and condition (real vs simulated), outcomes, cost, latency."""
import collections
import json
import statistics as st

from agent_govbench import checks
from agent_govbench.config import REPO_ROOT
from agent_govbench.records import now
from agent_govbench.report_runs import latest, pct
from agent_govbench.scenarios import load
from agent_govbench.simulated import build

S = {s["scenario_id"]: s for s in load()}
TAGS = {"pilot": "v1 pilot (100)", "pilot-task": "v1 pilot (100)", "g0test": "v1 test split (264)",
        "v2-policy": "v2 sample (160)", "v2-task": "v2 sample (160)"}


def g0(tag):
    try:
        return [t for t in latest(tag) if t["config"] == "G0" and not t["error"]]
    except FileNotFoundError:
        return []


print("## Proposed calls per split and condition (G0 runs, standard tier)\n")
print("| run set | condition | runs | real calls proposed | real malicious (construction) | real benign-scenario calls | simulated malicious | split: test real mal / sim mal |")
print("|---|---|---|---|---|---|---|---|")
for tag, label in TAGS.items():
    ts = g0(tag)
    if not ts:
        continue
    cond = ts[0].get("prompt_variant", "policy")
    calls = sum(t["eval"]["n_calls_proposed"] for t in ts)
    mal = collections.Counter()
    for t in ts:
        s = S[t["scenario_id"]]
        props = [{"name": x["name"], "arguments": x["arguments"]} for x in t["steps"] if x["kind"] == "call"]
        n = sum(checks.call_matches(c, s["attack_check"]) for c in props) if s["is_attack"] else 0
        mal[t["split"]] += n
    ben = sum(t["eval"]["n_calls_proposed"] for t in ts if not t["is_attack"])
    sim = collections.Counter(r["split"] for r in build(ts, S, now()))
    print(f"| {label} | {cond} | {len(ts)} | {calls} | {sum(mal.values())} ({dict(mal)}) | {ben} | {sum(sim.values())} ({dict(sim)}) | {mal['test']} / {sim['test']} |")

print("\n## Outcomes by condition (G0)\n")
print("| run set | condition | attack success | harmful call proposed | benign completed | median s | p95 s | agent USD/run |")
print("|---|---|---|---|---|---|---|---|")
for tag, label in TAGS.items():
    ts = g0(tag)
    if not ts:
        continue
    att = [t for t in ts if t["is_attack"]]
    ben = [t for t in ts if not t["is_attack"]]
    lat = [t["latency_s"] for t in ts]
    a = sum(t["eval"]["attack_success"] for t in att)
    h = sum(t["eval"]["harmful_call_proposed"] for t in att)
    b = sum(t["eval"]["benign_completed"] for t in ben)
    print(f"| {label} | {ts[0].get('prompt_variant', 'policy')} | {a}/{len(att)} | {h}/{len(att)} | {b}/{len(ben)} | "
          f"{st.median(lat):.1f} | {pct(lat, .95):.1f} | {st.mean(t['cost']['agent']['usd'] for t in ts):.4f} |")
print("\nLatency note: runs before the 2026-10-05 ~19:20 UTC harness fix include quota-queue wait (pilot, g0test); later runs exclude it.")
