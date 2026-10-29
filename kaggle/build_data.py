"""Build the Kaggle item files from the public sanitized dataset BrejBala/agent-govbench on Hugging Face.

  python kaggle/build_data.py --cache /tmp/govbench_hf --out kaggle/data

Only public files are read (CC BY 4.0). Output:
  judge_items.jsonl   guard-judge items: rendered decision record + label (all splits, split recorded per item)
  agent_items.jsonl   agent items: scripted prefix + target call + derived checks (train and val scenario records)
  MANIFEST.json       counts, seeds, source files
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import random
import re
import urllib.request
from pathlib import Path

HF = "https://huggingface.co/datasets/BrejBala/agent-govbench/resolve/main/"
FILES = {
    "gold": "data/gold/gold_v1.jsonl",
    "real_policy": "data/replay/a_replay_batch01_v2.jsonl",
    "real_task": "data/replay/a_replay_batch03_full-task.jsonl",
    "sim_task": "data/replay/simulated_compromised_batch03_full-task.jsonl",
    "real_policy2": "data/replay/a_replay_batch02_full-policy.jsonl",
    "real_task_r": "data/replay/a_replay_batch07_full-task-r.jsonl",
    "real_policy_r": "data/replay/a_replay_batch07_full-policy-r.jsonl",
    "sim_policy": "data/replay/simulated_compromised_batch02_full-policy.jsonl",
    "sim_policy_r": "data/replay/simulated_compromised_batch07_full-policy-r.jsonl",
    "sim_task_r": "data/replay/simulated_compromised_batch07_full-task-r.jsonl",
    "gen_train": "data/scenarios/a_generated_v1_train.jsonl",
    "gen_val": "data/scenarios/a_generated_v1_val.jsonl",
    "known_issues": "data/replay/_known_issues_v1.json",
}
SEED = 20261029
CATS = ["indirect_prompt_injection", "social_engineering", "privilege_escalation", "data_exfiltration",
        "destructive_action", "sensitive_data_exposure", "business_rule_violation"]


def fetch(cache: Path, key: str) -> Path:
    p = cache / FILES[key]
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(HF + FILES[key], p)
    return p


def jl(p: Path) -> list[dict]:
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


# ---- rendering: verbatim from src/agent_govbench/b_prompts.py (Project B's record rendering) ----
def _tool_sig(t):
    props = (t.get("parameters") or {}).get("properties", {})
    req = set((t.get("parameters") or {}).get("required", []))
    args = []
    for k, v in props.items():
        typ = v.get("type", "any") if isinstance(v, dict) else "any"
        args.append(f"{k}{'' if k in req else '?'}: {typ}")
    return f"- {t['name']}({', '.join(args)}): {t.get('description', '')}"


def _call(c):
    return f"{c['name']} {json.dumps(c['arguments'], ensure_ascii=False)}"


def _msg(m):
    if m["role"] == "tool":
        return f"[tool output: {m.get('name', '?')}]\n{m['content']}\n[end tool output]"
    out = f"[{m['role']}] {m['content']}".rstrip() if m["content"] else ""
    calls = "\n".join(f"[{m['role']} calls] {_call(c)}" for c in m.get("tool_calls") or [])
    return "\n".join(x for x in (out, calls) if x)


def render(r):
    a = r["agent"]
    parts = [f"# Agent role\n{a['role']}", f"# Operator policy\n{a['policy']}"]
    if a.get("allowed_tools"):
        parts.append("# Allowed tools for this role\n" + ", ".join(a["allowed_tools"]))
    if a.get("session_context"):
        parts.append(f"# Session facts\n{a['session_context']}")
    parts.append("# Tools\n" + "\n".join(_tool_sig(t) for t in r["tools"]))
    parts.append("# Conversation\n" + "\n".join(_msg(m) for m in r["conversation"]))
    parts.append("# Proposed call\n" + _call(r["proposed_call"]))
    return "\n\n".join(parts)


def content_key(r) -> str:
    return hashlib.sha1(json.dumps([r["conversation"], r["proposed_call"], r["agent"].get("session_context")],
                                   sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def build_judge(cache: Path, rng: random.Random) -> list[dict]:
    ki = json.loads(fetch(cache, "known_issues").read_text())
    bad = set()
    for v in ki.values():
        if isinstance(v, (list, dict)):
            bad |= set(re.findall(r"[A-Za-z0-9_\-]+-[A-Za-z0-9_\-]{6,}", json.dumps(v)))
    pools = []
    for key, origin in [("gold", "gold"), ("real_policy", "real"), ("real_task", "real"), ("real_policy2", "real"),
                        ("real_task_r", "real"), ("real_policy_r", "real"), ("sim_task", "simulated"),
                        ("sim_policy", "simulated"), ("sim_policy_r", "simulated"), ("sim_task_r", "simulated")]:
        for r in jl(fetch(cache, key)):
            if not r.get("label") or r["id"] in bad:
                continue
            if (r.get("meta") or {}).get("disputed"):
                continue
            pools.append((origin, r))
    seen, uniq = set(), []
    for origin, r in sorted(pools, key=lambda x: (x[0] != "gold", x[1]["id"])):  # gold wins ties
        k = content_key(r)
        if k not in seen:
            seen.add(k)
            uniq.append((origin, r))
    blocks = [(o, r) for o, r in uniq if r["label"]["verdict"] == "block"]
    allows = [(o, r) for o, r in uniq if r["label"]["verdict"] == "allow"]

    def take(items, n, per_family=2):
        items = items[:]
        rng.shuffle(items)
        fam, out = collections.Counter(), []
        for o, r in sorted(items, key=lambda x: x[0] != "gold"):  # gold first, then shuffled order
            if fam[r["family_id"]] >= per_family:
                continue
            fam[r["family_id"]] += 1
            out.append((o, r))
            if len(out) >= n:
                break
        return out

    sel = [x for x in blocks if x[0] == "gold"]
    left = collections.defaultdict(list)
    for o, r in blocks:
        if o != "gold":
            left[r["label"]["category"]].append((o, r))
    cap = 30
    fam = collections.Counter(r["family_id"] for _, r in sel)
    for c in CATS:
        have = sum(1 for _, r in sel if r["label"]["category"] == c)
        for o, r in take(left[c], max(0, cap - have)):
            if fam[r["family_id"]] < 2:
                fam[r["family_id"]] += 1
                sel.append((o, r))
    gold_allow = [x for x in allows if x[0] == "gold"]
    hard = [x for x in allows if x[0] != "gold" and (x[1].get("attack_notes") or {}).get("scenario_is_attack")]
    plain = [x for x in allows if x[0] != "gold" and not (x[1].get("attack_notes") or {}).get("scenario_is_attack")]
    n_allow_target = len(sel)
    sel += gold_allow
    sel += take(hard, (n_allow_target - len(gold_allow)) // 2)
    sel += take(plain, n_allow_target - len([1 for _, r in sel if r["label"]["verdict"] == "allow"]))
    items = []
    for o, r in sel:
        an = r.get("attack_notes") or {}
        items.append({
            "id": r["id"], "family_id": r["family_id"], "origin": o,
            "split": r["split"], "label_verdict": r["label"]["verdict"], "label_category": r["label"]["category"],
            "hard_negative": bool(r["label"]["verdict"] == "allow" and an.get("scenario_is_attack")),
            "technique": an.get("technique"), "tool": r["proposed_call"]["name"],
            "n_messages": len(r["conversation"]), "prompt": render(r),
        })
    rng.shuffle(items)
    return items


# ---------------------------------------------------------------- agent items
def ext_domain(addr: str) -> str:
    return addr.rsplit("@", 1)[-1].lower() if "@" in addr else ""


def build_agent(cache: Path, rng: random.Random) -> list[dict]:
    gen = jl(fetch(cache, "gen_train")) + jl(fetch(cache, "gen_val"))
    by_fam = collections.defaultdict(list)
    for r in gen:
        if r.get("label"):
            by_fam[r["family_id"]].append(r)
    items = []
    for fam, rs in by_fam.items():
        attacks = [r for r in rs if r["label"]["verdict"] == "block"]
        for r in rs:
            is_attack = r["label"]["verdict"] == "block"
            an = r["attack_notes"] or {}
            sibs = [a["proposed_call"] for a in attacks if a["id"] != r["id"]]
            conv = r["conversation"]
            principal = r["meta"]["principal"]
            items.append({
                "id": r["id"], "family_id": fam, "split": r["split"], "is_attack": is_attack,
                "category": r["label"]["category"], "technique": an.get("technique"),
                "vector": an.get("vector"), "principal": principal,
                "session_context": r["agent"]["session_context"],
                "prefix": conv,                       # contract-v0 messages before the decision point
                "target_call": r["proposed_call"],    # harmful call (attack) or intended call (benign)
                "family_harm_calls": [r["proposed_call"]] if is_attack else sibs[:3],
                "n_user_turns": sum(1 for m in conv if m["role"] == "user"),
            })
    return items


def select_agent(items: list[dict], rng: random.Random, n_attack: int, n_benign: int) -> list[dict]:
    """Stratified by (category) for attacks and by target tool for benign; one scenario per family where possible."""
    atk = [i for i in items if i["is_attack"]]
    ben = [i for i in items if not i["is_attack"] and i["family_harm_calls"]]
    rng.shuffle(atk)
    rng.shuffle(ben)
    out, used = [], collections.Counter()
    per = max(1, n_attack // len(CATS))
    cnt = collections.Counter()
    for i in atk:
        if cnt[i["category"]] < per and used[i["family_id"]] < 1:
            out.append(i)
            cnt[i["category"]] += 1
            used[i["family_id"]] += 1
    used_b = collections.Counter()
    nb = 0
    tools = collections.Counter()
    for i in ben:
        if nb >= n_benign:
            break
        t = i["target_call"]["name"]
        if used_b[i["family_id"]] < 1 and tools[t] < max(4, n_benign // 5):
            out.append(i)
            used_b[i["family_id"]] += 1
            tools[t] += 1
            nb += 1
    rng.shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default="/tmp/govbench_hf")
    ap.add_argument("--out", default="kaggle/data")
    ap.add_argument("--n-attack", type=int, default=105)
    ap.add_argument("--n-benign", type=int, default=75)
    a = ap.parse_args()
    cache, out = Path(a.cache), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    judge = build_judge(cache, rng)
    agent_all = build_agent(cache, rng)
    agent = select_agent(agent_all, rng, a.n_attack, a.n_benign)
    (out / "judge_items.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in judge), encoding="utf-8")
    (out / "agent_items.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in agent), encoding="utf-8")
    man = {
        "seed": SEED, "source": "https://huggingface.co/datasets/BrejBala/agent-govbench", "files": FILES,
        "judge": {"n": len(judge), "by_label": collections.Counter(i["label_verdict"] for i in judge),
                  "by_category": collections.Counter(i["label_category"] for i in judge),
                  "by_origin": collections.Counter(i["origin"] for i in judge),
                  "hard_negatives": sum(i["hard_negative"] for i in judge)},
        "agent": {"n": len(agent), "attack": sum(i["is_attack"] for i in agent),
                  "by_category": collections.Counter(i["category"] for i in agent),
                  "by_vector": collections.Counter(i["vector"] for i in agent)},
    }
    (out / "MANIFEST.json").write_text(json.dumps(man, indent=1))
    print(json.dumps(man, indent=1))


if __name__ == "__main__":
    main()
