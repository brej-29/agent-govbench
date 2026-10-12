"""G1: Model Armor through its direct sanitize API (the gateway extension path was not reachable).

Screens text: the user prompt (sanitizeUserPrompt) and each tool output (sanitizeModelResponse is meant for model
output; tool output is untrusted input to the model, so it is screened with sanitizeUserPrompt as well, which is
where prompt-injection detection applies). Block iff the overall filterMatchState is MATCH_FOUND.
"""

from __future__ import annotations

import time

MA_VERSION = "g1-v1"
MAX_CHARS = 40_000  # keep requests well inside Model Armor limits; longer text is truncated, and the result says so


def _session():
    import google.auth
    from google.auth.transport.requests import AuthorizedSession

    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    return AuthorizedSession(creds)


_SESSION = None


def screen(text: str, project: str, location: str, template: str, session=None) -> dict:
    """Returns {verdict: allow|block|error, findings: {...}, latency_ms, chars, truncated}. Never raises."""
    global _SESSION
    t0 = time.time()
    truncated = len(text) > MAX_CHARS
    body = {"userPromptData": {"text": text[:MAX_CHARS]}}
    url = (f"https://modelarmor.{location}.rep.googleapis.com/v1/projects/{project}/locations/{location}"
           f"/templates/{template}:sanitizeUserPrompt")
    try:
        s = session or _SESSION or _session()
        if session is None:
            _SESSION = s
        r = s.post(url, json=body, timeout=30)
        r.raise_for_status()
        res = r.json().get("sanitizationResult", {})
        findings = {}
        for k, v in (res.get("filterResults") or {}).items():
            inner = next(iter(v.values()), {}) if isinstance(v, dict) else {}
            if inner.get("matchState") == "MATCH_FOUND":
                findings[k] = {x: y for x, y in inner.items() if x in ("matchState", "confidenceLevel", "raiFilterTypeResults")}
        verdict = "block" if res.get("filterMatchState") == "MATCH_FOUND" else "allow"
        out = {"verdict": verdict, "findings": findings, "invocation": res.get("invocationResult")}
    except Exception as e:  # noqa: BLE001
        out = {"verdict": "error", "findings": {}, "error": str(e)[:300]}
    return {**out, "latency_ms": round((time.time() - t0) * 1000, 1), "chars": len(text), "truncated": truncated,
            "guard_version": MA_VERSION, "template": template}
