"""Fail if a number in README.md differs from the report files.

1. The generated tables (<!-- generated:*:start/end -->) must equal what scripts/readme_tables.py builds from
   report/metrics.json today.
2. Every other percentage or decimal number in the README text (findings, notes, image alt text) must be listed in
   CLAIMS below with its source: a cell of report/metrics.json, a cell of a generated report table, or a fixed
   constant (license version, split share, interval level). Each listed source is read and must equal the number as
   written (same precision; "about" numbers written without decimals may round). A number that is not listed fails.
Skipped: code blocks, inline code, URLs, badge lines, and the collapsed Replication information block (versions, seeds and
dates, checked by hand against the code). Counts without a decimal or % sign are not checked.

Usage: python scripts/check_readme_numbers.py [README.md]   (exit 1 on any mismatch)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import readme_tables  # noqa: E402

M = readme_tables.M
O, L = M["offline_test"], M["live"]
CELL = re.compile(r"([\d.]+)% \[([\d.]+)%?, ([\d.]+)%?\]")


def m(group, key, idx=0, field=None, pct=True):
    v = (L[key][field] if field else O[key]) if group != "raw" else key
    v = v[idx] if isinstance(v, list) else v
    return ("metrics.json", round(v * 100, 4) if pct else v)


def md(file, row, col, idx=0, after=None):
    """Cell of the first markdown table (after the text `after`, if given) whose row starts with `row`."""
    s = (ROOT / "report" / file).read_text()
    if after:
        s = s.split(after, 1)[1]
    lines = s.splitlines()
    hi = next(i for i, l in enumerate(lines) if l.startswith("|") and col in l)
    head = [c.strip() for c in lines[hi].strip("|").split("|")]
    for l in lines[hi + 2:]:
        cells = [c.strip() for c in l.strip("|").split("|")]
        if cells[0].startswith(row):
            c = cells[head.index(col)]
            g = CELL.search(c)
            return (file, float(g[1 + idx]) if g else float(c.rstrip("%")))
    raise KeyError((file, row, col))


def text_in(file, tok):
    return (file, float(tok)) if tok in (ROOT / file).read_text() else (file, None)


def const(v, why):
    return (f"constant: {why}", v)


LIVE_G = "|task_only|live-task-guards"
AM, AV, GH, G1B = "agent_models.md", "adaptive_v2.md", "guard_hijack.md", "g1b_threshold.md"
PRO = "## Attacker: pro"
CLAIMS = {
    "51.5%": [m("live", "G0|task_only|full-task", field="attack_success")],
    "2.9%": [m("live", "G0|policy|full-policy", field="attack_success")],
    "34.0%": [m("live", "G1" + LIVE_G, field="attack_success")],
    "2.7%": [m("live", "G2p" + LIVE_G, field="attack_success")],
    "4.7%": [m("live", "G6" + LIVE_G, field="attack_success")],
    "0.7%": [m("live", "G4" + LIVE_G, field="attack_success"), m("off", "hard negatives|all|G6")],
    "100%": [m("live", "G4" + LIVE_G, field="benign_completed_programmatic")],
    "15.0": [m("live", "G0|task_only|full-task", field="latency_median_s", pct=False)],
    "12.6": [m("live", "G1" + LIVE_G, field="latency_median_s", pct=False)],
    "15.1": [m("live", "G2p" + LIVE_G, field="latency_median_s", pct=False)],
    "31.8": [m("live", "G6" + LIVE_G, field="latency_median_s", pct=False)],
    "27.7": [m("live", "G4" + LIVE_G, field="latency_median_s", pct=False)],
    "27.1%": [m("off", "real benign|all|G1"), m("off", "real benign|all|G1b")],
    "21.1": [m("off", "real benign|all|G1", 1)],
    "33.1": [m("off", "real benign|all|G1", 2)],
    "21.9%": [m("off", "hard negatives|all|G1")],
    "29.8%": [m("off", "real malicious|all|G1")],
    "0.3%": [m("off", "real benign|all|G2p"), m("off", "hard negatives|all|G2p")],
    "0.4%": [m("off", "real benign|all|G6")],
    "0.5%": [m("off", "real benign|all|G4")],
    "0.9%": [m("off", "hard negatives|all|G4")],
    "17%": [md(G1B, "HIGH", "false positive rate")],
    "22%": [md(G1B, "HIGH", "block rate")],
    "47.8%": [md(AM, "Flash, no guard (149", "attack success (completed)")],
    "67.8%": [md(AM, "Pro, no guard (149", "attack success (completed)")],
    "2.4%": [md(AM, "Flash, G6", "attack success (completed)"), md(AM, "Pro, G4", "attack success (completed)")],
    "4.8%": [md(AM, "Pro, G6", "attack success (completed)")],
    "0.0%": [md(AM, "Flash, G4", "attack success (completed)"), md(AV, "2", "G7 Pro, B prompt", after=PRO)],
    "66.0%": [md(AV, "0 (original)", "G1 Model Armor", after=PRO)],
    "36%": [md(AV, "3", "G1 Model Armor", after=PRO)],
    "48%": [md(AV, "4", "G1 Model Armor", after=PRO)],
    "42.0%": [md(AV, "0 (original)", "G2' rules", after=PRO)],
    "2.2%": [md(AV, "3", "G6 LLM guard (Flash)", after=PRO)],
    "9.1%": [md(AV, "1", "G6 LLM guard (Flash)", after=PRO)],
    "2.0%": [md(AV, "0 (original)", "G7 Pro, B prompt", after=PRO)],
    "31.5%": [md(GH, "original", "G1 Model Armor")],
    "50.6%": [md(GH, "guard-hijack rewrite", "G1 Model Armor")],
    "65.2%": [md(GH, "original", "G2' rules"), md(GH, "guard-hijack rewrite", "G2' rules")],
    "97.8%": [md(GH, "original", "G6 LLM guard (Flash)")],
    "97.7%": [md(GH, "guard-hijack rewrite", "G6 LLM guard (Flash)")],
    "98.9%": [md(GH, "original", "G7 Pro, B prompt")],
    "100.0%": [md(GH, "guard-hijack rewrite", "G7 Pro, B prompt")],
    "114.10": [text_in("COSTS.md", "114.10")],
    "0.008": [text_in("report/WRITEUP.md", "0.008")],
    "0.012": [text_in("report/WRITEUP.md", "0.012")],
    "0.006": [text_in("report/WRITEUP.md", "0.006")],
    "5%": [const(5, "under 5% threshold and the 5% validation split")],
    "15%": [const(15, "test split share, contract_v0/split_v0.py")],
    "80%": [const(80, "train split share, contract_v0/split_v0.py")],
    "95%": [const(95, "interval level")],
    "2.0": [const(2.0, "Apache License 2.0")],
    "4.0": [const(4.0, "CC BY 4.0")],
}
NUM = re.compile(r"(?<![\w.\-/])(\d+(?:\.\d+)?)(%?)(?![\w\-])")


def same(tok, v):
    if v is None:
        return False
    t = float(tok.rstrip("%"))
    d = len(tok.rstrip("%").split(".")[1]) if "." in tok else 0
    return abs(round(v, d) - t) < 1e-9


def main(path):
    text = Path(path).read_text()
    errors = []
    if readme_tables.fill(text) != text:
        errors.append("generated tables differ from report/metrics.json (run scripts/readme_tables.py)")
    for tok, sources in CLAIMS.items():
        for src, v in sources:
            if not same(tok, v):
                errors.append(f"claim {tok} does not match {src} (value {v})")
    body = re.sub(r"<!-- generated:(\w+):start -->.*?<!-- generated:\1:end -->", "", text, flags=re.S)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    body = re.sub(r"<summary><b>Replication information</b></summary>.*?</details>", "", body, flags=re.S)
    body = re.sub(r"`[^`]*`", "", body)
    body = re.sub(r"(?:https?://|srcset=\"|src=\"|href=\")[^\s\"')]+", "", body)
    body = "\n".join(l for l in body.splitlines() if not l.startswith("[!["))
    seen = 0
    for line in body.splitlines():
        for g in NUM.finditer(line):
            tok = g[1] + g[2]
            if "." not in g[1] and not g[2]:
                continue
            seen += 1
            if tok not in CLAIMS:
                errors.append(f"number without a declared source: {tok} in: {line.strip()[:110]}")
    n_gen = sum(len(t) - 2 for t in readme_tables.BLOCKS.values())
    print(f"{path}: {n_gen} generated table rows checked against report/metrics.json; {seen} numbers in text checked "
          f"against {len(CLAIMS)} declared sources")
    for e in errors:
        print("  FAIL", e)
    print("README NUMBER CHECK:", "FAILED" if errors else "PASSED")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "README.md")))
