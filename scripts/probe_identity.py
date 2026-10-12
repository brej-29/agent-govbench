"""Create an empty reasoning engine with AGENT_IDENTITY to read the real trust domain (no code, no compute)."""
import json, sys
import vertexai
from agent_govbench.config import get_config

cfg = get_config()
client = vertexai.Client(project=cfg.project, location=cfg.region, http_options=dict(api_version="v1beta1"))
if len(sys.argv) > 1:
    eng = client.agent_engines.get(name=sys.argv[1])
else:
    eng = client.agent_engines.create(config={"display_name": "govbench-identity-probe", "identity_type": "AGENT_IDENTITY",
                                              "labels": {"project": "agent-govbench"}})
r = eng.api_resource
print("name:", r.name)
print("spec:", json.dumps(r.spec.model_dump(exclude_none=True, mode="json") if r.spec else None, indent=1))
