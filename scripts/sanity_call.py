"""Phase 0 sanity call: one tiny gemini call in location=global, record usage and the billed project."""
from google import genai
from google.genai import types

from agent_govbench.config import get_config
from agent_govbench.costs import record

cfg = get_config()
client = genai.Client(vertexai=True, project=cfg.project, location=cfg.model_location)
for level in ("minimal", "low"):
    try:
        r = client.models.generate_content(
            model=cfg.agent_model,
            contents="Reply with the single word ok",
            config=types.GenerateContentConfig(temperature=0.0, thinking_config=types.ThinkingConfig(thinking_level=level)),
        )
        break
    except Exception as e:
        print(f"thinking_level={level} failed: {str(e)[:200]}")
print("text:", r.text.strip(), "| thinking_level:", level)
print("model_version:", r.model_version)
print("usage:", r.usage_metadata)
print("ledger:", record(cfg.agent_model, r.usage_metadata, purpose="phase0-sanity", project=cfg.project))
