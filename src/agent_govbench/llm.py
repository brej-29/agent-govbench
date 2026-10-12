"""Gemini calls with an explicit tier (standard or flex), retries with backoff, and the cost ledger.

Standard tier: anything whose latency is reported (live agent, live guards).
Flex tier: generation, judging, offline scoring. Flex is requested with the documented Vertex headers
X-Vertex-AI-LLM-Request-Type: shared + X-Vertex-AI-LLM-Shared-Request-Type: flex (the SDK's service_tier field is
rejected by Vertex v1beta1). The tier actually used is read back from usage_metadata.traffic_type.
"""

from __future__ import annotations

import json
import random
import time
from functools import lru_cache

from google import genai
from google.genai import errors, types

from .config import get_config
from .costs import record

FLEX_HEADERS = {"X-Vertex-AI-LLM-Request-Type": "shared", "X-Vertex-AI-LLM-Shared-Request-Type": "flex"}


# Per-call timeouts (ms). Flex queues can be long; a call over its timeout is retried.
FLEX_TIMEOUT_MS = {"gemini-3.8-flash": 180_000, "gemini-3.1-pro-preview": 480_000}


@lru_cache(maxsize=8)
def client(tier: str = "standard", model: str = "gemini-3.8-flash") -> genai.Client:
    cfg = get_config()
    if tier == "flex":
        opts = types.HttpOptions(headers=FLEX_HEADERS, timeout=FLEX_TIMEOUT_MS.get(model, 180_000))
    elif tier == "standard":
        opts = types.HttpOptions(timeout=120_000)
    else:
        raise ValueError(tier)
    return genai.Client(vertexai=True, project=cfg.project, location=cfg.model_location, http_options=opts)


RETRYABLE = (429, 500, 502, 503, 504)


def generate(model: str, contents, *, purpose: str, tier: str, temperature: float = 0.0, thinking: str = "low",
             system: str | None = None, json_mode: bool = False, max_attempts: int = 6, **ledger_extra):
    """Returns (text, usage_row, latency_s). Raises after max_attempts."""
    cfg = types.GenerateContentConfig(
        temperature=temperature, system_instruction=system,
        thinking_config=types.ThinkingConfig(thinking_level=thinking),
        response_mime_type="application/json" if json_mode else None,
    )
    delay = 2.0
    HEARTBEAT.ensure_started()
    for attempt in range(1, max_attempts + 1):
        t0 = time.time()
        try:
            r = client(tier, model).models.generate_content(model=model, contents=contents, config=cfg)
            lat = time.time() - t0
            row = record(model, r.usage_metadata, purpose, latency_s=round(lat, 3), attempts=attempt, **ledger_extra)
            HEARTBEAT.tick(purpose, lat)
            return (r.text or ""), row, lat
        except errors.APIError as e:
            if getattr(e, "code", None) not in RETRYABLE or attempt == max_attempts:
                raise
        except Exception:  # network errors
            if attempt == max_attempts:
                raise
        time.sleep(delay + random.random())
        delay = min(delay * 2, 60)
    raise RuntimeError("unreachable")


def parse_json(text: str):
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1].rsplit("```", 1)[0]
    return json.loads(t)


class Heartbeat:
    """Prints one line per minute per purpose: calls done, mean latency, so slow and stuck jobs differ.
    Note: Vertex does not report Flex queue time separately; per-call latency (queue + processing) and the attempt
    count are logged in the ledger instead."""

    def __init__(self, every_s: int = 60):
        import threading
        self.every, self.lock, self.stats, self.started = every_s, threading.Lock(), {}, False

    def ensure_started(self) -> None:
        with self.lock:
            if not self.started:
                self.started = True
                import threading
                threading.Thread(target=self._loop, daemon=True).start()

    def tick(self, purpose: str, lat: float) -> None:
        self.ensure_started()
        with self.lock:
            n, tot = self.stats.get(purpose, (0, 0.0))
            self.stats[purpose] = (n + 1, tot + lat)

    def _loop(self):
        while True:
            time.sleep(self.every)
            with self.lock:
                line = "; ".join(f"{k}: {n} calls, mean {t / max(n, 1):.1f}s" for k, (n, t) in self.stats.items())
            print(f"[heartbeat {time.strftime('%H:%M:%S')}] {line}", flush=True)


HEARTBEAT = Heartbeat()
