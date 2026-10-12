"""Pre-publication text replacements, applied after all scoring (2026-10-11).

Lookalike attack domains that are not under a reserved name (RFC 2606/6761: .example, .test, .invalid, example.com)
get ".test" appended, so they stay visibly lookalike but can never resolve to a real registrant. Real provider or
company domains become .example. Customer names that match a public figure or a real firm are renamed. Guard verdicts
and labels were computed on the original text; the replacements do not change what a call does.

Usage: python scripts/sanitize_release.py FILE_OR_DIR ...   (rewrites text files in place, prints counts)
"""
import re
import sys
from collections import Counter
from pathlib import Path

LOOKALIKE = ["northwind-example.com", "northwind-example.net", "northwind-example.org", "northwind.example.co",
             "northwind.example.biz", "ledgerline-audit.example.co", "ledgerline-audit.co",
             "northwind.corp-example.com", "northwind-payroll.com"]
REAL = {"protonmail.com": "proton.example", "acme.com": "acme.example", "megabank.com": "megabank.example"}
NAMES = {"Avery Brooks": "Avery Brookfield", "Apex Retail": "Quillmere Retail", "Vanguard Marine": "Brackwater Marine"}
# real firms used as scenario parties (customers); product names that only describe a tool (Slack, Jira, Stripe) stay
FIRMS = {"Vanguard": "Vandermoor", "Loomis Tech": "Lowick Tech"}
TEXT = {".jsonl", ".json", ".md", ".csv", ".tsv", ".txt", ".py", ".sh", ".tf", ".tmpl", ".yaml", ".yml", ".toml", ""}


def _dom(d):  # whole domain only: not inside a longer host name, not followed by another label
    return re.compile(r"(?<![A-Za-z0-9.\-])" + re.escape(d) + r"(?![A-Za-z0-9\-]|\.[A-Za-z0-9])", re.I)


RULES = ([(d, _dom(d), lambda m: m.group(0) + ".test") for d in LOOKALIKE]
         + [(d, _dom(d), lambda m, r=r: r) for d, r in REAL.items()]
         + [(n, re.compile(re.escape(n)), lambda m, r=r: r) for n, r in NAMES.items()]
         + [(n, re.compile(r"(?<![A-Za-z])" + re.escape(n) + r"(?![A-Za-z])"), lambda m, r=r: r) for n, r in FIRMS.items()])


def run(paths):
    rules = RULES
    total = Counter()
    files = [f for p in map(Path, paths) for f in ([p] if p.is_file() else sorted(p.rglob("*")))
             if f.is_file() and ".git" not in f.parts and f.suffix in TEXT and f.name not in ("MANIFEST.sha256", "LICENSE")]
    for f in files:
        s = f.read_text(encoding="utf-8")
        new = s
        for key, rx, rep in rules:
            new, n = rx.subn(rep, new)
            total[key] += n
        if new != s:
            f.write_text(new, encoding="utf-8")
    for k, n in total.items():
        if n:
            print(f"{n:6d}  {k}")
    return total


if __name__ == "__main__":
    run(sys.argv[1:])
