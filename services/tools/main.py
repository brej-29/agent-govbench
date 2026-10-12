"""GovBench MCP tool stubs: five MCP servers (mail, hr, payments, files, code) in one Cloud Run service.

Synthetic data only, no side effects: send_email sends nothing, issue_refund moves nothing, write/delete change
nothing persistent, run_python never executes code. Each request carries X-Govbench-Scenario (and X-Govbench-Run);
the stub serves that scenario's fixtures (base world merged with gs://<FIXTURE_BUCKET>/fixtures/<scenario>.json)
and logs every call as one structured line (jsonPayload.govbench_call) for the call log.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from functools import lru_cache

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from agent_govbench.world import merged

FIXTURE_BUCKET = os.environ.get("FIXTURE_BUCKET", "")
DIRECTORY_FIELDS = ["name", "email", "department", "title", "manager"]
ALL_FIELDS = DIRECTORY_FIELDS + ["salary", "bonus", "ssn_last4", "home_address", "bank_details", "health_notes", "notes"]

logging.basicConfig(stream=sys.stdout, level=logging.INFO, format="%(message)s")
log = logging.getLogger("govbench.tools")


@lru_cache(maxsize=4096)
def _fixtures(scenario_id: str) -> str:
    if not scenario_id or not FIXTURE_BUCKET:
        return "{}"
    from google.cloud import storage
    blob = storage.Client().bucket(FIXTURE_BUCKET).blob(f"fixtures/{scenario_id}.json")
    return blob.download_as_text() if blob.exists() else "{}"


def _ctx():
    h = get_http_headers() or {}
    sid = h.get("x-govbench-scenario", "")
    return sid, h.get("x-govbench-run", ""), merged(json.loads(_fixtures(sid)))


def _log(tool: str, args: dict, result) -> None:
    sid, run, _ = _ctx()
    log.info(json.dumps({"govbench_call": {"tool": tool, "args": args, "scenario_id": sid, "run_id": run,
                                            "ts": time.time(), "result_preview": json.dumps(result)[:500]}}))


RO = {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False}

mail = FastMCP(name="mail")
hr = FastMCP(name="hr")
payments = FastMCP(name="payments")
files = FastMCP(name="files")
code = FastMCP(name="code")


@mail.tool(annotations=RO)
def read_inbox(folder: str = "inbox", limit: int = 10) -> dict:
    """Read the principal's recent emails."""
    _, _, w = _ctx()
    res = {"folder": folder, "messages": (w.get("inbox") or [])[: max(1, min(limit, 50))]}
    _log("read_inbox", {"folder": folder, "limit": limit}, res)
    return res


@mail.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": True})
def send_email(to: list[str], subject: str, body: str, cc: list[str] | None = None, attachments: list[str] | None = None) -> dict:
    """Send an email from the principal's account."""
    res = {"status": "sent", "message_id": f"MSG-{uuid.uuid4().hex[:10]}", "to": to, "cc": cc or [], "attachments": attachments or []}
    _log("send_email", {"to": to, "cc": cc, "subject": subject, "body": body, "attachments": attachments}, res)
    return res


@hr.tool(annotations=RO)
def lookup_employee(employee_id: str | None = None, name: str | None = None, fields: list[str] | None = None) -> dict:
    """Look up an employee record. Returns only the requested fields (default: directory fields)."""
    _, _, w = _ctx()
    emps = w.get("employees") or {}
    rec = emps.get(employee_id) if employee_id else None
    if rec is None and name:
        rec = next((e for e in emps.values() if (e.get("name") or "").lower() == name.strip().lower()), None)
        rec = rec or next((e for e in emps.values() if name.strip().lower() in (e.get("name") or "").lower()), None)
    want = [f for f in (fields or DIRECTORY_FIELDS) if f in ALL_FIELDS] or DIRECTORY_FIELDS
    res = ({"employee_id": rec.get("employee_id", employee_id), **{f: rec.get(f) for f in want}} if rec
           else {"error": "employee not found"})
    _log("lookup_employee", {"employee_id": employee_id, "name": name, "fields": fields}, res)
    return res


@payments.tool(annotations=RO)
def lookup_order(order_id: str) -> dict:
    """Look up a customer order by id."""
    _, _, w = _ctx()
    res = (w.get("orders") or {}).get(order_id) or {"error": "order not found"}
    _log("lookup_order", {"order_id": order_id}, res)
    return res


@payments.tool(annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False})
def issue_refund(order_id: str, amount: float, approval_id: str | None = None, reason: str | None = None) -> dict:
    """Refund a customer order, fully or partly."""
    res = {"status": "refunded", "refund_id": f"RF-{uuid.uuid4().hex[:8]}", "order_id": order_id, "amount": amount}
    _log("issue_refund", {"order_id": order_id, "amount": amount, "approval_id": approval_id, "reason": reason}, res)
    return res


@files.tool(annotations=RO)
def list_files(path: str) -> dict:
    """List files in a folder."""
    _, _, w = _ctx()
    p = path if path.endswith("/") else path + "/"
    res = {"path": path, "files": sorted(k for k in (w.get("files") or {}) if k.startswith(p))}
    _log("list_files", {"path": path}, res)
    return res


@files.tool(annotations=RO)
def read_file(path: str) -> dict:
    """Read a file (documents, saved web pages, data files)."""
    _, _, w = _ctx()
    content = (w.get("files") or {}).get(path)
    res = {"path": path, "content": content} if content is not None else {"error": "file not found", "path": path}
    _log("read_file", {"path": path}, res)
    return res


@files.tool(annotations={"readOnlyHint": False, "destructiveHint": False, "openWorldHint": False})
def write_file(path: str, content: str) -> dict:
    """Create or overwrite a file."""
    res = {"status": "written", "path": path, "bytes": len(content.encode())}
    _log("write_file", {"path": path, "content": content}, res)
    return res


@files.tool(annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False})
def delete_file(path: str) -> dict:
    """Delete a file."""
    _, _, w = _ctx()
    exists = path in (w.get("files") or {})
    res = {"status": "deleted" if exists else "not found", "path": path}
    _log("delete_file", {"path": path}, res)
    return res


@code.tool(annotations={"readOnlyHint": False, "destructiveHint": True, "openWorldHint": False})
def run_python(code: str) -> dict:
    """Run a short Python snippet for calculations or formatting and return stdout."""
    _, _, w = _ctx()
    res = {"stdout": w.get("code_output") or "ok", "note": "sandbox stub, code was not executed"}
    _log("run_python", {"code": code}, res)
    return res


async def health(_):
    return JSONResponse({"status": "ok"})


_apps = {n: s.http_app(path="/mcp", stateless_http=True, json_response=True)
         for n, s in {"mail": mail, "hr": hr, "payments": payments, "files": files, "code": code}.items()}


async def _lifespan(app):
    from contextlib import AsyncExitStack
    async with AsyncExitStack() as stack:
        for a in _apps.values():
            await stack.enter_async_context(a.lifespan(a))
        yield


app = Starlette(routes=[Route("/health", health)] + [Mount(f"/{n}", app=a) for n, a in _apps.items()], lifespan=_lifespan)
