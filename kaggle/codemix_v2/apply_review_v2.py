"""Apply the owner's filled v2 review chunks and verify argument identity (no model runs).

  python kaggle/codemix_v2/apply_review_v2.py review_chunk_01_filled.csv review_chunk_02_filled.csv ...

Rule (same as v1): where the owner scored a line 3 or below and gave a rewrite, the rewrite is used; a line is dropped only if its language is
marked N (meaning preserved) and it has no rewrite. Lines scored 4 or 5 are kept as drafted. English lines and the carried-over bridge lines are
not re-rated. Writes items_v2_reviewed.jsonl and ARG_CHECK_V2_REVIEWED.md. Copy the result to kaggle/data/codemix_v2_items.jsonl.
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import build_v2  # noqa: E402

COLS = {("ta-en", "command"): ("Tanglish command", "Tanglish command natural (1-5)", "Tanglish command rewrite (if 3 or below)", "Tanglish meaning preserved (Y/N)"),
        ("ta-en", "question"): ("Tanglish question", "Tanglish question natural (1-5)", "Tanglish question rewrite (if 3 or below)", "Tanglish meaning preserved (Y/N)"),
        ("ml-en", "command"): ("Manglish command", "Manglish command natural (1-5)", "Manglish command rewrite (if 3 or below)", "Manglish meaning preserved (Y/N)"),
        ("ml-en", "question"): ("Manglish question", "Manglish question natural (1-5)", "Manglish question rewrite (if 3 or below)", "Manglish meaning preserved (Y/N)")}


def main(files):
    rows = {}
    for f in files:
        for r in csv.DictReader(open(f, encoding="utf-8-sig")):
            rows[r["row_id"]] = r
    items = [json.loads(l) for l in (HERE / "items_v2_draft.jsonl").read_text(encoding="utf-8").splitlines()]
    out, dropped, used = [], [], 0
    for it in items:
        r = rows.get(it["row_id"])
        key = (it["lang"], it["form"])
        if r is None or key not in COLS or it["review_status"] == "carried_from_v1" and not (it["block"] == "bridge" and key == ("ml-en", "command")):
            out.append(it)
            continue
        text_col, score_col, rw_col, mean_col = COLS[key]
        score = (r.get(score_col) or "").strip()
        rewrite = (r.get(rw_col) or "").strip()
        meaning = (r.get(mean_col) or "").strip().upper()
        if rewrite:
            it["prefix"] = [{"role": "user", "content": rewrite}]
            it["review_status"] = "rewritten"
            used += 1
        elif meaning == "N":
            dropped.append(it["id"])
            continue
        else:
            it["review_status"] = "approved"
        it["owner_naturalness"] = int(score) if score.isdigit() else None
        it["owner_dialect_note"] = (r.get("dialect note (one word)") or "").strip() or None
        out.append(it)
    by = {}
    for it in out:
        by.setdefault(it["row_id"], []).append(it)
    drift = []
    for rid, its in by.items():
        ref = build_v2.toks(next((i for i in its if i["lang"] == "en"), its[0])["prefix"][0]["content"])
        for i in its:
            if build_v2.toks(i["prefix"][0]["content"]) != ref:
                drift.append((i["id"], sorted(ref ^ build_v2.toks(i["prefix"][0]["content"]))))
    (HERE / "items_v2_reviewed.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in out), encoding="utf-8")
    rep = ["# Argument identity check, pilot v2 after the owner's review", "", f"Items kept: {len(out)} of {len(items)}. Rewrites used: {used}. Dropped: {dropped or 'none'}.",
           "No drift." if not drift else "Drift (fix before running):"] + [f"- `{i}`: {d}" for i, d in drift]
    (HERE / "ARG_CHECK_V2_REVIEWED.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))


if __name__ == "__main__":
    main(sys.argv[1:])
