"""Exact-content leakage guard: normalized conversation + proposed call must never appear in two splits.

Cause found 2026-10-08: replay records at the first decision point carry only the first user message, and terse
variants in different families converged on identical openers ("Check my inbox." -> read_inbox {}), so identical
records landed in a test family and a train family. Families and splits stay hash-assigned (split_v0); this guard drops
the offending new record instead of reassigning any split.
"""

from __future__ import annotations

import glob
import hashlib
import json
import re

from .config import REPO_ROOT


def _norm(s) -> str:
    return re.sub(r"\s+", " ", (s or "").lower()).strip()


def content_hash(r: dict) -> str:
    parts = [m["role"] + ":" + _norm(m.get("content")) + ":" + json.dumps(m.get("tool_calls") or [], sort_keys=True).lower()
             for m in r["conversation"]]
    parts.append("CALL:" + json.dumps(r["proposed_call"], sort_keys=True).lower())
    return hashlib.sha256("\n".join(parts).encode()).hexdigest()


def existing_index(exclude: set[str] = frozenset()) -> dict:
    idx = {}
    for f in glob.glob(str(REPO_ROOT / "data" / "records" / "*.jsonl")):
        if f in exclude:
            continue
        for l in open(f):
            r = json.loads(l)
            idx.setdefault(content_hash(r), set()).add(r["split"])
    return idx


def drop_cross_split(new: list[dict], index: dict) -> tuple[list[dict], list[dict]]:
    """Drop new records whose content exists in another split (already published), and within the batch keep the
    test copy over train/val copies. Returns (kept, dropped)."""
    by = {}
    for r in new:
        by.setdefault(content_hash(r), []).append(r)
    kept, dropped = [], []
    for h, rs in by.items():
        prior = index.get(h, set())
        splits = {r["split"] for r in rs}
        for r in rs:
            other_prior = prior - {r["split"]}
            loses_in_batch = len(splits) > 1 and r["split"] != "test"
            (dropped if (other_prior or loses_in_batch) else kept).append(r)
    return kept, dropped
