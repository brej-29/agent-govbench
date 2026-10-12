"""Phase 1: send one message to a deployed ADK agent on Agent Runtime and print every event (tool calls, errors, text).

Run with the agent env (needs vertexai):
  uv run --project infra/codelab/src/mortgage-agent python scripts/phase1_query.py ENGINE_NAME "message" [out.jsonl]
"""

import json
import sys
import time

import vertexai

engine_name, message = sys.argv[1], sys.argv[2]
out = sys.argv[3] if len(sys.argv) > 3 else None
project = engine_name.split("/")[1]
location = engine_name.split("/")[3]
client = vertexai.Client(project=project, location=location)
engine = client.agent_engines.get(name=engine_name)

t0 = time.time()
events = []
for ev in engine.stream_query(user_id="phase1-tester", message=message):
    ev["_t"] = round(time.time() - t0, 3)
    events.append(ev)
    content = ev.get("content") or {}
    for part in content.get("parts", []):
        if "function_call" in part:
            print(f"[{ev['_t']}s] CALL {part['function_call'].get('name')} {json.dumps(part['function_call'].get('args'))[:300]}")
        elif "function_response" in part:
            print(f"[{ev['_t']}s] RESP {part['function_response'].get('name')} {json.dumps(part['function_response'].get('response'))[:600]}")
        elif "text" in part and part["text"]:
            print(f"[{ev['_t']}s] TEXT {part['text'][:800]}")
    for k in ("error_code", "error_message"):
        if ev.get(k):
            print(f"[{ev['_t']}s] {k}: {ev[k]}")
print(f"total {time.time() - t0:.1f}s, {len(events)} events")
if out:
    with open(out, "a") as f:
        f.write(json.dumps({"engine": engine_name, "message": message, "events": events}, default=str) + "\n")
