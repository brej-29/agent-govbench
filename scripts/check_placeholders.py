"""Fail on unfilled placeholders before publishing.

Looks for "[NAME]", "<<<", TODO, FIXME, PASTE, TBD, XXX and square-bracket placeholders such as [YOUR EMAIL],
[INSERT LINK] or [FILL IN] in every text file under the given folders. Matches inside the generated attack text of the
dataset (data/) are reported separately: that text is synthetic scenario content, not something to fill in.
Exit code 1 if any match is found outside data/.

Usage: python scripts/check_placeholders.py FOLDER ...
"""
import re
import sys
from collections import Counter
from pathlib import Path

WORDS = r"NAME|YOUR[ _A-Z]*|INSERT[ _A-Z]*|FILL[ _A-Z]*|PLACEHOLDER|AUTHOR|COPYRIGHT HOLDER|ORG(?:ANIZATION)?|EMAIL|URL|LINK|YEAR|DATE|TBD|TODO"
PATTERNS = {
    "[NAME]": re.compile(r"\[NAME\]"),
    "<<<": re.compile(r"<<<(?!\s*[\"'$])"),  # not a bash here-string such as <<<"${line}"
    "TODO": re.compile(r"\bTODO\b"),
    "FIXME": re.compile(r"\bFIXME\b"),
    "PASTE": re.compile(r"\bPASTE\b"),
    "TBD": re.compile(r"\bTBD\b"),
    "XXX": re.compile(r"\bXXX\b"),
    "[placeholder]": re.compile(r"\[(?:" + WORDS + r")(?::[^\]]*)?\]"),
}
SKIP_SUFFIX = {".png", ".jpg", ".pdf", ".lock"}
SELF = Path(__file__).name


def scan(root: Path):
    hits = []
    for f in sorted(root.rglob("*")):
        if not f.is_file() or ".git" in f.parts or f.suffix in SKIP_SUFFIX or f.name == SELF:
            continue
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for key, rx in PATTERNS.items():
                for m in rx.finditer(line):
                    hits.append((key, f.relative_to(root), i, line[max(0, m.start() - 40): m.end() + 40]))
    return hits


def main(folders):
    fail = False
    for folder in map(Path, folders):
        hits = scan(folder)
        doc = [h for h in hits if h[1].parts[0] != "data"]
        gen = [h for h in hits if h[1].parts[0] == "data"]
        print(f"{folder}: {len(doc)} placeholder matches outside data/, {len(gen)} inside generated data/")
        for key, path, line, ctx in doc:
            print(f"  FAIL {key} {path}:{line}: {ctx!r}")
        for key, n in Counter(h[0] for h in gen).most_common():
            print(f"  data/ {key}: {n}")
        fail |= bool(doc)
    print("PLACEHOLDER CHECK:", "FAILED" if fail else "PASSED")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
