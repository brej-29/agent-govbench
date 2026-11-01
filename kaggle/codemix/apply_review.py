"""Apply the owner's reviewed sheet to the draft items, verify argument identity across twins, label speech acts.

  python kaggle/codemix/apply_review.py

Reads review_sheet_reviewed.csv (exactly as returned by the owner) and items_draft.jsonl.
Writes items_reviewed.jsonl (90 items), ARG_CHECK.md (drift report) and speech_acts.csv.
Rule: use the owner's rewrite where one is given, otherwise the draft line. A row is dropped only if it is marked N
(meaning preserved) with no rewrite. The owner's rows are never edited; speech acts are labelled in a separate column.
"""
import csv
import json
import re
from pathlib import Path

HERE = Path(__file__).parent
MONTHS_DAYS = r"january|february|march|april|may|june|july|august|september|october|november|december|monday|tuesday|wednesday|thursday|friday"
IMPERATIVE = re.compile(r"(pannunga|pannidunga|kaattunga|sollunga|kudunga|anuppunga|paarunga|padinga|cheyyu|ayakku|kaanikku|nokku|para\b)", re.I)
REQ_Q = re.compile(r"\b\w+amo\b|\btharoo\b", re.I)


def args_of(text: str) -> set:
    t = text
    quoted = set(re.findall(r"'([^']+)'", t))
    t2 = re.sub(r"'[^']+'", " ", t)
    out = {"q:" + q for q in quoted}
    out |= {"id:" + m.upper() for m in re.findall(r"\b[OE]-\d+\b", t2)}
    out |= {"email:" + m.lower() for m in re.findall(r"[\w.]+@[\w.]+\w", t2)}
    out |= {"path:" + m.rstrip(".,?") for m in re.findall(r"(?<![\w@])/[\w./-]+", t2)}
    t3 = re.sub(r"[\w.]+@[\w.]+|/[\w./-]+|\b[OE]-\d+\b", " ", t2)
    out |= {"num:" + m for m in re.findall(r"\b\d+(?:\.\d+)?%?", t3)}
    out |= {"name:" + m for m in re.findall(r"\b[A-Z][a-z]+ [A-Z][a-z]+\b", t3) if m.split()[0] not in ("Please", "Hi")}
    out |= {"when:" + m.lower() for m in re.findall(MONTHS_DAYS, t3, re.I)}
    return out


def speech_act(lang: str, text: str) -> str:
    """command | request_question (polite 'can you', -amo/-oo) | info_question (what/which/how much)."""
    s = text.strip()
    if lang == "en":
        if s.endswith("?"):
            return "info_question"
        return "command"
    if REQ_Q.search(s):
        return "request_question"
    if s.endswith("?") and not IMPERATIVE.search(s):
        return "info_question"
    return "command"


def main():
    rows = {r["pair_id"]: r for r in csv.DictReader((HERE / "review_sheet_reviewed.csv").open(encoding="utf-8"))}
    items = [json.loads(l) for l in (HERE / "items_draft.jsonl").read_text(encoding="utf-8").splitlines()]
    out, dropped, drift, acts = [], [], [], []
    for it in items:
        r = rows[it["pair_id"]]
        if it["lang"] == "en":
            text, status, score, meaning = r["English"], "english_reference", None, "Y"
        else:
            k = "ta" if it["lang"] == "ta-en" else "ml"
            draft = r["Tanglish (ta-en)"] if k == "ta" else r["Manglish (ml-en)"]
            rewrite = r[f"{k} rewrite (if 3 or below)"].strip()
            meaning = r[f"{k} meaning preserved (Y/N)"].strip()
            score = int(r[f"{k} natural? (1-5)"])
            if rewrite:
                text, status = rewrite, "rewritten"
            elif meaning == "N":
                dropped.append(it["id"])
                continue
            else:
                text, status = draft, "approved"
            it["owner_naturalness"] = score
            it["owner_problem_type"] = r[f"{k} problem type"].strip() or None
            it["owner_dialect_note"] = r[f"{k} dialect note"].strip() or None
            it["owner_meaning_preserved_on_draft"] = meaning
        it["prefix"] = [{"role": "user", "content": text}]
        it["review_status"] = status
        it["speech_act"] = speech_act(it["lang"], text)
        out.append(it)
    en = {i["pair_id"]: i for i in out if i["lang"] == "en"}
    for it in out:
        if it["lang"] == "en":
            continue
        a, b = args_of(en[it["pair_id"]]["prefix"][0]["content"]), args_of(it["prefix"][0]["content"])
        if a != b:
            drift.append((it["id"], sorted(a - b), sorted(b - a)))
        it["speech_act_shift_vs_en"] = it["speech_act"] != en[it["pair_id"]]["speech_act"]
    (HERE / "items_reviewed.jsonl").write_text("".join(json.dumps(i, ensure_ascii=False) + "\n" for i in out), encoding="utf-8")
    with (HERE / "speech_acts.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["pair_id", "kind", "en_text", "en_act", "ta_text", "ta_act", "ml_text", "ml_act"])
        by = {}
        for i in out:
            by.setdefault(i["pair_id"], {})[i["lang"]] = i
        for pid, d in by.items():
            w.writerow([pid, d["en"]["kind"], d["en"]["prefix"][0]["content"], d["en"]["speech_act"],
                        d["ta-en"]["prefix"][0]["content"], d["ta-en"]["speech_act"],
                        d["ml-en"]["prefix"][0]["content"], d["ml-en"]["speech_act"]])
    rep = ["# Argument identity check (English twin vs code-mixed versions, after the owner's rewrites)", "",
           f"Items kept: {len(out)} of 90. Dropped (marked N with no rewrite): {dropped or 'none'}.",
           f"Rewritten lines used: {sum(1 for i in out if i['review_status'] == 'rewritten')}.", ""]
    if drift:
        rep.append("Argument drift (tokens present in one version only; extraction is by pattern: ids, emails, paths, quoted text, numbers, names, dates):")
        rep.append("")
        for i, only_en, only_mixed in drift:
            rep.append(f"- `{i}`: only in English {only_en}; only in code-mixed {only_mixed}")
    else:
        rep.append("No drift found: every extracted argument token (order and employee ids, emails, paths, quoted text, numbers, names, dates) is identical across each English twin and its code-mixed versions.")
    (HERE / "ARG_CHECK.md").write_text("\n".join(rep) + "\n", encoding="utf-8")
    print("\n".join(rep))
    import collections
    c = collections.Counter((i["lang"], i["speech_act"]) for i in out)
    print(sorted(c.items()))


if __name__ == "__main__":
    main()
