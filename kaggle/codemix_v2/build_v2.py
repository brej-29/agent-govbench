"""Build pilot v2 items and the review chunks (DRAFT; no model runs).

  python kaggle/codemix_v2/build_v2.py

Writes items_v2_draft.jsonl, review_chunk_01..04.csv (15 rows each, the last holds the remainder), ARG_CHECK_V2.md.
Row = one paraphrase of one intent. New block: 20 intents x 2 paraphrases = 40 rows, each with 6 lines (English / Tanglish / Manglish x
command / polite question). Bridge block: the 18 v1 intents whose Manglish line was a polite question, with a new Manglish COMMAND line
(the v1 English, Tanglish and Manglish-question lines are carried over from the owner's reviewed v1 items).
"""
import csv
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "codemix"))
sys.path.insert(0, str(HERE.parents[1] / "src"))
from agent_govbench import world  # noqa: E402
import apply_review  # noqa: E402
from intents import BRIDGE_ML_COMMAND, INTENTS  # noqa: E402

E = world.BASE["employees"]
P = {"emp": "E-1371", "clerk": "E-1149", "mgr": "E-1223", "hr": "E-1001", "it": "E-1297"}
VARIANTS = [("en", "command"), ("en", "question"), ("ta-en", "command"), ("ta-en", "question"), ("ml-en", "command"), ("ml-en", "question")]


LEAD = {"Email", "Send", "Find", "Write", "Look", "Check", "Read", "Refund", "Delete", "Save", "Use", "Run", "Tell", "Open", "Calculate",
        "Summarise", "Give", "Process", "Could", "Can", "Clean", "Please", "Order", "As", "Calculate"}


def toks(text):
    """apply_review.args_of on the text with its first letter lower-cased, so a sentence-initial English verb ("Find Hiro Tanaka")
    is not mistaken for part of a name."""
    first = text.split()[0] if text.split() else ""
    return apply_review.args_of(text[:1].lower() + text[1:] if first in LEAD else text)


def sess(role):
    e = E[P[role]]
    return (f"Authenticated principal: {e['employee_id']} ({e['name']}, {e['email']}), role: {e['role']}, "
            f"department: {e['department']}. Date: 2026-10-06.")


def item(iid, rid, intent, block, lang, form, text, role, kind, tests, required, forbidden):
    return {"id": iid, "row_id": rid, "intent": intent, "block": block, "lang": lang, "form": form, "script": "latin", "kind": kind,
            "tests": tests, "principal": E[P[role]]["employee_id"], "role": E[P[role]]["role"], "session_context": sess(role),
            "prefix": [{"role": "user", "content": text}], "required_calls": required, "forbidden_calls": forbidden,
            "review_status": "pending"}


def main():
    items, rows, drift = [], [], []
    for k, (iid, (block, role, kind, tests, req, forb, paras)) in enumerate(INTENTS.items()):
        for pi, lines in enumerate(paras, 1):
            rid = f"{iid}-p{pi}"
            tk = [toks(t) for t in lines]
            if any(t != tk[0] for t in tk):
                drift.append((rid, [sorted(tk[0] ^ t) for t in tk]))
            for (lang, form), text in zip(VARIANTS, lines):
                items.append(item(f"v2-{rid}-{lang}-{form[0]}", rid, iid, block, lang, form, text, role, kind, tests, req, forb))
            rows.append({"row_id": rid, "block": block, "kind": kind, "tests (what this item is meant to test)": tests,
                         "English command": lines[0], "English question": lines[1], "Tanglish command": lines[2], "Tanglish question": lines[3],
                         "Manglish command": lines[4], "Manglish question": lines[5]})
    v1 = {}
    for l in (HERE.parent / "codemix" / "items_reviewed.jsonl").read_text(encoding="utf-8").splitlines():
        i = json.loads(l)
        v1[(i["pair_id"], i["lang"])] = i
    for pid, ml_c in BRIDGE_ML_COMMAND.items():
        en, ta, mq = v1[(pid, "en")], v1[(pid, "ta-en")], v1[(pid, "ml-en")]
        texts = [en["prefix"][0]["content"], ta["prefix"][0]["content"], mq["prefix"][0]["content"], ml_c]
        tk = [toks(t) for t in texts]
        if any(t != tk[0] for t in tk):
            drift.append((f"bridge-{pid}", [sorted(tk[0] ^ t) for t in tk]))
        rid = f"bridge-{pid}"
        for (lang, form), text, src in zip([("en", "v1"), ("ta-en", "v1"), ("ml-en", "question"), ("ml-en", "command")], texts, ["v1", "v1", "v1", "new"]):
            it = dict(en, id=f"v2-{rid}-{lang}-{form[0]}", row_id=rid, intent=pid, block="bridge", lang=lang, form=form, tests="Request form: same Manglish request as a polite question (v1) and as a command (new)",
                      review_status="carried_from_v1" if src == "v1" else "pending")
            it["prefix"] = [{"role": "user", "content": text}]
            it.pop("pair_id", None)
            items.append(it)
        rows.append({"row_id": rid, "block": "bridge", "kind": en["kind"], "tests (what this item is meant to test)": "Request form vs language: the v1 Manglish line is a polite question; the new Manglish command keeps the same request.",
                     "English command": texts[0], "English question": "", "Tanglish command": texts[1], "Tanglish question": "",
                     "Manglish command": ml_c, "Manglish question": texts[2]})
    (HERE / "items_v2_draft.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in items), encoding="utf-8")
    owner = ["Tanglish command natural (1-5)", "Tanglish command rewrite (if 3 or below)", "Tanglish question natural (1-5)", "Tanglish question rewrite (if 3 or below)",
             "Manglish command natural (1-5)", "Manglish command rewrite (if 3 or below)", "Manglish question natural (1-5)", "Manglish question rewrite (if 3 or below)",
             "Tanglish meaning preserved (Y/N)", "Manglish meaning preserved (Y/N)", "problem type (register / over-mixing / under-mixing / meaning drift)", "dialect note (one word)", "notes"]
    fields = list(rows[0]) + owner
    for c in range(0, len(rows), 15):
        with (HERE / f"review_chunk_{c // 15 + 1:02d}.csv").open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(rows[c:c + 15])
    rep = ["# Argument identity check, pilot v2 draft", "",
           f"Rows: {len(rows)} ({sum(1 for r in rows if r['block'] != 'bridge')} new + {sum(1 for r in rows if r['block'] == 'bridge')} bridge). Items: {len(items)}.",
           "No drift: every extracted argument token is identical across the lines of each row." if not drift else "Drift:"]
    rep += [f"- `{r}`: {d}" for r, d in drift]
    (HERE / "ARG_CHECK_V2.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))
    print("chunks:", -(-len(rows) // 15), "| new items", sum(1 for i in items if i["review_status"] == "pending"))


if __name__ == "__main__":
    main()
