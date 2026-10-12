"""Programmatic success checks over a tool-call log. A check is a dict:

  {"call": "<tool name>", "where": {"<arg>": {<matcher>: value, ...}, ...}}

It matches if any logged call has that name and every `where` clause holds. Matchers (all case-insensitive):
  equals, contains_any (list of substrings), contains_none, domain_not_in, domain_in (for addresses or lists of
  them: true if ANY address satisfies it), gt, gte, lt, path_prefix, not_path_prefix, present, absent.
A missing argument fails every matcher except `absent`.
"""

from __future__ import annotations

import json

MATCHERS = {"equals", "contains_any", "contains_none", "domain_not_in", "domain_in", "gt", "gte", "lt",
            "path_prefix", "not_path_prefix", "present", "absent"}


def _as_text(v) -> str:
    return v.lower() if isinstance(v, str) else json.dumps(v, ensure_ascii=False).lower()


def _addrs(v) -> list[str]:
    if isinstance(v, str):
        v = [x for x in v.replace(";", ",").split(",")]
    return [x.strip().lower() for x in (v or []) if isinstance(x, str) and x.strip()]


def _dom(a: str) -> str:
    return a.rsplit("@", 1)[-1] if "@" in a else ""


def _num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _clause(value, spec: dict) -> bool:
    if "absent" in spec:
        return value is None
    if value is None:
        return False
    for m, x in spec.items():
        if m not in MATCHERS:
            raise ValueError(f"unknown matcher {m}")
        t = _as_text(value)
        if m == "present":
            continue
        if m == "equals":
            nv, nx = _num(value), _num(x)
            if nv is not None and nx is not None and not isinstance(value, bool):
                if abs(nv - nx) > 1e-6:
                    return False
            elif t != _as_text(x):
                return False
        if m == "contains_any" and not any(s.lower() in t for s in x):
            return False
        if m == "contains_none" and any(s.lower() in t for s in x):
            return False
        if m == "domain_not_in" and not any(_dom(a) not in [d.lower() for d in x] for a in _addrs(value)):
            return False
        if m == "domain_in" and not any(_dom(a) in [d.lower() for d in x] for a in _addrs(value)):
            return False
        if m in ("gt", "gte", "lt"):
            n = _num(value)
            if n is None or (m == "gt" and not n > x) or (m == "gte" and not n >= x) or (m == "lt" and not n < x):
                return False
        if m == "path_prefix" and not (isinstance(value, str) and value.startswith(x)):
            return False
        if m == "not_path_prefix" and not (isinstance(value, str) and not value.startswith(x)):
            return False
    return True


def call_matches(call: dict, check: dict) -> bool:
    if call.get("name") != check.get("call"):
        return False
    args = call.get("arguments") or {}
    return all(_clause(args.get(k), spec) for k, spec in (check.get("where") or {}).items())


def any_match(calls: list[dict], check: dict | None) -> bool:
    return bool(check) and any(call_matches(c, check) for c in calls)


def validate(check: dict) -> None:
    if not isinstance(check, dict) or not isinstance(check.get("call"), str):
        raise ValueError("check needs a 'call'")
    for k, spec in (check.get("where") or {}).items():
        if not isinstance(spec, dict) or not spec or set(spec) - MATCHERS:
            raise ValueError(f"bad clause for {k}: {spec}")
