"""Pre-publication checks for the docs and figures added on a branch.

- links and image paths: every relative link, image and HTML src/srcset in tracked Markdown files resolves to a file
  (anchors are checked against the headings of the target file);
- em dashes: none in files changed since BASE (vendored infra/codelab/ excluded);
- size: no file changed since BASE is over 1 MB;
- secrets and personal data in files changed since BASE, including SVG text: key and token patterns, email addresses
  outside reserved domains, local user paths, cloud project identifiers.

Usage: python scripts/check_docs.py BASE_COMMIT   (exit 1 on any finding)
"""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECRET = re.compile(r"AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|-----BEGIN [A-Z ]*PRIVATE KEY|\"private_key\"|ghp_[A-Za-z0-9]{36}"
                    r"|hf_[A-Za-z0-9]{30,}|sk-[A-Za-z0-9]{20,}|xox[bp]-[0-9]{6,}")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)")
RESERVED = re.compile(r"(\.(example|test|invalid)$)|(^|\.)example\.(com|org|net)$|^users\.noreply\.github\.com$|^anthropic\.com$")
PERSONAL = re.compile(r"/home/[a-z][a-z0-9_-]+/|/mnt/[a-z]/|[A-Z]:\\\\Users|brejesh|balakrishnan|gmail\.com|projects/[0-9]{6,}", re.I)


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def anchors(md_text):
    out = set()
    for h in re.findall(r"^#{1,6} (.+)$", md_text, re.M):
        a = re.sub(r"[^\w\- ]", "", h.strip().lower()).replace(" ", "-")
        out.add(a)
    return out


def main(base):
    errs = []
    for f in git("ls-files", "*.md").split():
        if f.startswith("infra/codelab/"):
            continue  # vendored upstream docs; their two upstream-only links are documented in GOVBENCH_CHANGES.md
        text = (ROOT / f).read_text()
        text_nocode = re.sub(r"```.*?```", "", text, flags=re.S)
        targets = re.findall(r"\]\(([^)\s]+)\)", text_nocode) + re.findall(r"(?:src|srcset|href)=\"([^\"]+)\"", text_nocode)
        for u in targets:
            if u.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, frag = u.partition("#")
            tgt = (ROOT / f).parent / path if path else ROOT / f
            if not tgt.resolve().exists():
                errs.append(f"broken link or image in {f}: {u}")
            elif frag and tgt.suffix == ".md" and frag not in anchors(tgt.read_text()):
                errs.append(f"missing anchor in {f}: {u}")
    changed = [x for x in git("diff", "--name-only", base, "--").split() + git("ls-files", "--others", "--exclude-standard").split()
               if (ROOT / x).exists()]
    for f in changed:
        p = ROOT / f
        if p.stat().st_size > 1_000_000:
            errs.append(f"file over 1 MB: {f} ({p.stat().st_size} bytes)")
        if p.suffix in (".png", ".jpg"):
            continue
        t = p.read_text(errors="ignore")
        if "\u2014" in t and not f.startswith("infra/codelab/"):
            errs.append(f"em dash in {f}")
        for m in SECRET.finditer(t):
            errs.append(f"secret-like string in {f}: {m[0][:12]}...")
        for m in EMAIL.finditer(t):
            if not RESERVED.search(m[1].lower()):
                errs.append(f"email outside reserved domains in {f}: {m[0]}")
        if f != "scripts/check_docs.py":
            for m in PERSONAL.finditer(t):
                errs.append(f"personal or local identifier in {f}: {m[0]}")
    print(f"checked {len(git('ls-files', '*.md').split())} Markdown files for links, {len(changed)} changed files for "
          "em dashes, size, secrets and personal data")
    for e in errs:
        print("  FAIL", e)
    print("DOCS CHECK:", "FAILED" if errs else "PASSED")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
