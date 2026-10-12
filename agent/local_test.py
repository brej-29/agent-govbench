"""Run the agent locally (InMemoryRunner) against the deployed stubs. Usage: python local_test.py GUARDS "message" """
import asyncio, json, os, sys, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, os.path.dirname(__file__))
from google.adk.runners import InMemoryRunner
from google.genai import types
from govbench_agent.agent import root_agent
from agent_govbench.policy import session_context_text
from agent_govbench.world import BASE, principal_view

async def main(guards, msg, emp="E-1001", scen="local-none"):
    p = principal_view(BASE["employees"][emp])
    r = InMemoryRunner(agent=root_agent, app_name="t")
    s = await r.session_service.create_session(app_name="t", user_id="u", state={
        "scenario_id": scen, "run_id": "local-" + uuid.uuid4().hex[:6], "session_context": session_context_text(p),
        "principal": p, "guards": guards})
    async for ev in r.run_async(user_id="u", session_id=s.id, new_message=types.Content(role="user", parts=[types.Part(text=msg)])):
        for part in (ev.content.parts if ev.content else []):
            if part.function_call: print("CALL", part.function_call.name, json.dumps(part.function_call.args)[:200])
            if part.function_response: print("RESP", json.dumps(part.function_response.response, default=str)[:250])
            if part.text and not part.thought: print("TEXT", part.text[:300])
    s = await r.session_service.get_session(app_name="t", user_id="u", session_id=s.id)
    for g in s.state.get("guard_log", []): print("GUARD", json.dumps(g, default=str)[:300])

asyncio.run(main(json.loads(sys.argv[1]), sys.argv[2], *(sys.argv[3:])))
