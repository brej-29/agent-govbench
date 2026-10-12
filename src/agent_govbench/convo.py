"""Turn ADK events (Agent Runtime stream dicts or Event.model_dump(mode="json")) into contract v0 messages,
and cut decision points (one per proposed tool call) out of a run."""

from __future__ import annotations

import json


def _parts(ev: dict) -> list:
    return ((ev.get("content") or {}).get("parts")) or []


def _jsonish(x) -> str:
    return x if isinstance(x, str) else json.dumps(x, ensure_ascii=False, default=str)


def unwrap_tool_response(resp) -> object:
    """MCP tool results come back as {"content": [...], "structuredContent": {...}}; prefer structuredContent."""
    if isinstance(resp, dict):
        if "structuredContent" in resp and resp["structuredContent"] is not None:
            return resp["structuredContent"]
        if "result" in resp and len(resp) == 1:
            return unwrap_tool_response(resp["result"])
    return resp


def events_to_steps(events: list[dict], user_turns_seen: list[str] | None = None) -> list[dict]:
    """Flatten events into ordered steps: {"kind": user|call|response|text, ...}.
    User turns are not echoed as events by stream_query, so they are inserted from user_turns_seen by the caller."""
    steps = []
    for ev in events:
        author = ev.get("author")
        for p in _parts(ev):
            if p.get("function_call"):
                fc = p["function_call"]
                steps.append({"kind": "call", "name": fc.get("name"), "arguments": fc.get("args") or {}, "id": fc.get("id")})
            elif p.get("function_response"):
                fr = p["function_response"]
                steps.append({"kind": "response", "name": fr.get("name"), "response": unwrap_tool_response(fr.get("response")), "id": fr.get("id")})
            elif p.get("text") and author != "user" and not p.get("thought"):
                steps.append({"kind": "text", "text": p["text"]})
            elif p.get("text") and author == "user":
                steps.append({"kind": "user", "text": p["text"]})
    return steps


def steps_to_messages(steps: list[dict]) -> list[dict]:
    """Contract v0 conversation. Consecutive calls (and any text) of one model turn form one assistant message."""
    msgs: list[dict] = []
    for s in steps:
        if s["kind"] == "user":
            msgs.append({"role": "user", "content": s["text"]})
        elif s["kind"] == "text":
            if msgs and msgs[-1]["role"] == "assistant" and not msgs[-1].get("tool_calls"):
                msgs[-1]["content"] += "\n" + s["text"]
            else:
                msgs.append({"role": "assistant", "content": s["text"]})
        elif s["kind"] == "call":
            call = {"name": s["name"], "arguments": s["arguments"]}
            if msgs and msgs[-1]["role"] == "assistant" and (msgs[-1].get("tool_calls") is not None):
                msgs[-1]["tool_calls"].append(call)
            elif msgs and msgs[-1]["role"] == "assistant":
                msgs[-1]["tool_calls"] = [call]
            else:
                msgs.append({"role": "assistant", "content": "", "tool_calls": [call]})
        elif s["kind"] == "response":
            msgs.append({"role": "tool", "name": s["name"], "content": _jsonish(s["response"])})
    return msgs


def decision_points(steps: list[dict]) -> list[dict]:
    """One entry per proposed call: the conversation strictly before it (earlier calls of the same model turn are
    included as already-proposed assistant tool_calls) and the call itself."""
    out = []
    for i, s in enumerate(steps):
        if s["kind"] == "call":
            out.append({"index": len(out), "step_pos": i, "conversation": steps_to_messages(steps[:i]),
                        "proposed_call": {"name": s["name"], "arguments": s["arguments"]}})
    return out


def tool_calls(steps: list[dict]) -> list[dict]:
    return [{"name": s["name"], "arguments": s["arguments"]} for s in steps if s["kind"] == "call"]


def executed_calls(steps: list[dict]) -> list[dict]:
    """Calls whose response is not a guard block (for success checks on what actually ran)."""
    out = []
    for i, s in enumerate(steps):
        if s["kind"] != "call":
            continue
        resp = next((r for r in steps[i + 1:] if r["kind"] == "response" and (r.get("id") == s.get("id") or r["name"] == s["name"])), None)
        r = resp.get("response") if resp else None
        if isinstance(r, dict) and r.get("govbench_blocked"):
            continue
        out.append({"name": s["name"], "arguments": s["arguments"]})
    return out
