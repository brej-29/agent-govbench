"""Simulated compromised-agent records (reported separately from real agent behaviour).

The real agent (gemini-3.8-flash) rarely proposes the harmful call, so guards would see almost no malicious
decision points. For each attack scenario with a real G0 trajectory in which the agent did NOT propose the harmful
call, take the real context the agent had just before its final answer (real tool outputs included) and substitute
the scenario's harmful target call, as a compromised or weaker agent would have proposed it.

source: a_generated (not captured from a run); provenance.captured_from: simulated_compromised_agent:<run_id>;
meta.group: simulated_compromised_agent. Label: by construction (block, scenario category).
"""

from __future__ import annotations

import json

from . import checks
from .convo import steps_to_messages
from .records import _base, settled_label

GROUP = "simulated_compromised_agent"


def context_before_final_answer(steps: list[dict]) -> list[dict]:
    """Drop trailing assistant text (the refusal or final answer) and any call that was never answered."""
    st = list(steps)
    while st and st[-1]["kind"] in ("text", "call"):
        st.pop()
    return st


def simulated_record(trace: dict, s: dict, created: str) -> dict | None:
    if not s["is_attack"] or trace.get("error") or trace["config"] != "G0":
        return None
    proposed = [{"name": x["name"], "arguments": x["arguments"]} for x in trace["steps"] if x["kind"] == "call"]
    if checks.any_match(proposed, s["attack_check"]):
        return None  # the real agent did propose it; that call is in the real replay group
    st = settled_label(s["scenario_id"])
    if st is None or st["verdict"] != "block":
        return None  # target call relabeled benign or disputed: not a malicious simulated call
    ctx = steps_to_messages(context_before_final_answer(trace["steps"]))
    if not ctx or ctx[0]["role"] != "user":
        return None
    base = _base(s)
    return {
        **base, "id": f"sim-{trace['run_id']}", "source": "a_generated", "derived_from": None,
        "trajectory_id": trace["run_id"], "step": None, "conversation": ctx, "proposed_call": s["target_call"],
        "label": {"verdict": "block", "category": st["category"], "reason": st.get("reason") or "settled scenario label"},
        "label_source": "synthetic",
        "provenance": {"run_id": trace["run_id"], "agent_model": trace["agent_model"],
                       "captured_from": f"{GROUP}:{trace['run_id']}", "executed": False, "attack_succeeded": None,
                       "generator": "real G0 context + scenario target call substituted", "created_at": created},
        "guard_results": [],
        "meta": {**base["meta"], "group": GROUP, "prompt_variant": trace.get("prompt_variant", "policy"),
                 "real_agent_proposed": [c["name"] for c in proposed]},
    }


def build(traces: list[dict], scen_by_id: dict, created: str) -> list[dict]:
    out, seen = [], set()
    for t in traces:
        s = scen_by_id.get(t["scenario_id"])
        if not s or (t["scenario_id"], t.get("prompt_variant", "policy")) in seen:
            continue
        r = simulated_record(t, s, created)
        if r:
            seen.add((t["scenario_id"], t.get("prompt_variant", "policy")))
            out.append(r)
    return out


def load_traces(tags: list[str], root) -> list[dict]:
    out = []
    for tag in tags:
        runs = {}
        for l in (root / "data" / "runs" / tag / "traces.jsonl").read_text().splitlines():
            t = json.loads(l)
            if t["run_id"] not in runs or not t["error"]:
                runs[t["run_id"]] = t
        out += list(runs.values())
    return out
