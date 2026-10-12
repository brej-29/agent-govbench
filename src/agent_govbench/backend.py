"""Thin agent client interface. The harness only talks to an AgentBackend, so another platform (e.g. Bedrock
AgentCore) can be plugged in by implementing run_turns()."""

from __future__ import annotations

import json
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class TurnResult:
    user: str
    events: list
    t_start: float
    t_end: float
    error: str | None = None


@dataclass
class RunResult:
    session_id: str | None
    turns: list[TurnResult] = field(default_factory=list)
    final_state: dict = field(default_factory=dict)
    error: str | None = None
    backend: dict = field(default_factory=dict)


class AgentBackend(ABC):
    @abstractmethod
    def run_turns(self, user_turns: list[str], state: dict, user_id: str) -> RunResult: ...


class RateLimiter:
    """Shared sliding-window limiter: at most `per_min` calls in any 60 s (Agent Runtime query quota is 30/min)."""

    def __init__(self, per_min: int):
        self.per_min, self.calls, self.lock = per_min, [], threading.Lock()

    def wait(self):
        while True:
            with self.lock:
                now = time.time()
                self.calls = [t for t in self.calls if now - t < 60]
                if len(self.calls) < self.per_min:
                    self.calls.append(now)
                    return
                delay = 60 - (now - self.calls[0]) + 0.05
            time.sleep(delay)


class AgentRuntimeBackend(AgentBackend):
    """Gemini Enterprise Agent Platform, Agent Runtime (reasoningEngines) REST API, ADK app methods.

    Calls per run: create_session + one stream_query per user turn. The final session state is rebuilt from the
    state deltas carried by the streamed events (no get_session / delete_session), to stay inside the
    "Query Reasoning Engine requests" quota of 30 per minute per project and region.
    """

    def __init__(self, engine_name: str, region: str, timeout_s: float = 300.0, per_min: int = 28):
        import google.auth
        from google.auth.transport.requests import AuthorizedSession

        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        self.http = AuthorizedSession(creds)
        self.engine = engine_name
        self.base = f"https://{region}-aiplatform.googleapis.com/v1/{engine_name}"
        self.timeout = timeout_s
        self.limiter = RateLimiter(per_min)

    def _post(self, url: str, body: dict, stream: bool = False):
        """Returns (response, t_sent). t_sent is taken after the quota wait, so latency excludes queueing."""
        r, t_sent = None, time.time()
        for attempt in range(6):
            self.limiter.wait()
            t_sent = time.time()
            r = self.http.post(url, json=body, timeout=self.timeout, stream=stream)
            if r.status_code != 429:
                return r, t_sent
            time.sleep(min(60, 5 * 2 ** attempt))
        return r, t_sent

    def _query(self, method: str, payload: dict) -> dict:
        r, _ = self._post(f"{self.base}:query", {"class_method": method, "input": payload})
        if r.status_code >= 400:
            raise RuntimeError(f"{method} HTTP {r.status_code}: {r.text[:500]}")
        return r.json().get("output", {})

    def _stream(self, payload: dict) -> tuple[list[dict], float]:
        r, t_sent = self._post(f"{self.base}:streamQuery?alt=sse", {"class_method": "stream_query", "input": payload}, stream=True)
        if r.status_code >= 400:
            raise RuntimeError(f"stream_query HTTP {r.status_code}: {r.text[:500]}")
        events = []
        for line in r.iter_lines(decode_unicode=True):
            if not line:
                continue
            if line.startswith("data:"):
                line = line[5:].strip()
            try:
                events.append(json.loads(line))
            except ValueError:
                events.append({"_unparsed": line[:2000]})
        return events, t_sent

    def run_turns(self, user_turns, state, user_id):
        res = RunResult(session_id=None, backend={"type": "agent_runtime", "engine": self.engine})
        try:
            sess = self._query("create_session", {"user_id": user_id, "state": state})
            res.session_id = sess.get("id")
        except Exception as e:  # noqa: BLE001
            res.error = f"create_session: {e}"[:1000]
            return res
        for u in user_turns:
            t0 = time.time()
            try:
                evs, t0 = self._stream({"user_id": user_id, "session_id": res.session_id, "message": u})
                err = next((e.get("error_message") or e.get("_unparsed") for e in evs if e.get("error_code") or e.get("_unparsed")), None)
                if not evs:
                    err = "empty stream (0 events)"
                    res.error = err
                res.turns.append(TurnResult(u, evs, t0, time.time(), err))
            except Exception as e:  # noqa: BLE001
                res.turns.append(TurnResult(u, [], t0, time.time(), str(e)[:1000]))
                res.error = f"turn: {e}"[:1000]
                break
        final = dict(state)
        for t in res.turns:
            for e in t.events:
                final.update(((e.get("actions") or {}).get("state_delta")) or {})
        res.final_state = final
        return res
