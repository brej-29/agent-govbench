"""Assemble the self-contained task files in kaggle/dist/ from tasks/*.py, tasks/_common.py and the original sources.

  python kaggle/build_tasks.py

Policy text, task-only prompt, guard prompt and the deterministic base world are copied verbatim from the original
code so the port cannot drift from it.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
K = Path(__file__).resolve().parent


def grab(src: str, name: str) -> str:
    m = re.search(r"^" + name + r' = """(.*?)"""', src, re.S | re.M)
    return repr(m.group(1))


def common_text(pilot_limit: int = 0) -> str:
    pol = (ROOT / "src/agent_govbench/policy.py").read_text()
    bp = (ROOT / "src/agent_govbench/b_prompts.py").read_text()
    ag = (ROOT / "agent/govbench_agent/agent.py").read_text()
    wd = (ROOT / "src/agent_govbench/world.py").read_text()
    m = re.search(r"TASK_ONLY_TEXT = \((.*?)\)\nPROMPTS", ag, re.S)
    task_only = repr(eval("(" + m.group(1) + ")"))
    world = wd.split('"""Deterministic', 1)[1].split('"""', 1)[1]
    world = world.replace("from __future__ import annotations\n", "").replace("from .policy import COMPANY_DOMAIN\n", "")
    world = world.replace("import copy\nimport random\n", "import copy\n")
    common = (K / "tasks/_common.py").read_text()
    common = (common.replace("__PILOT_LIMIT__", str(pilot_limit)).replace("__POLICY_TEXT__", grab(pol, "POLICY_TEXT")).replace("__TASK_ONLY_TEXT__", task_only)
              .replace("__GUARD_SYSTEM__", grab(bp, "GUARD_SYSTEM")).replace("__WORLD_SOURCE__", world))
    return common


def main(pilot_n: int = 12):
    out = K / "dist"
    out.mkdir(exist_ok=True)
    specs = {
        "guard_judge.py": ("guard_judge.py", {"__TASK_NAME__": "Agent GovBench: Guard Judge"}),
        "agent_policy.py": ("agent_task.py", {"__VARIANT__": "policy", "__TASK_NAME__": "Agent GovBench: Agent (policy in prompt)",
                                              "__PROMPT_DESC__": "the full company policy"}),
        "codemix.py": ("codemix_task.py", {"__TASK_NAME__": "Agent GovBench: Code-mixed tool use (pilot)"}),
        "agent_task_only.py": ("agent_task.py", {"__VARIANT__": "task_only", "__TASK_NAME__": "Agent GovBench: Agent (task-only prompt)",
                                                 "__PROMPT_DESC__": "a short role prompt that does not state the policy"}),
    }
    pilots = {}
    for fn, (src, subs) in list(specs.items()):
        pn = "pilot_" + fn
        ps = dict(subs)
        ps["__TASK_NAME__"] = "GovBench Pilot " + fn[:-3].replace("_", " ")
        pilots[pn] = (src, ps)
    specs.update(pilots)
    for fn, (src, subs) in specs.items():
        common = common_text(pilot_n if fn.startswith("pilot_") else 0)
        t = (K / "tasks" / src).read_text().replace("# @@COMMON@@", common)
        for a, b in subs.items():
            t = t.replace(a, b)
        t = t.replace("import random\n\nimport pandas", "import random\n\nimport pandas")
        (out / fn).write_text(t)
        print("wrote", out / fn, len(t))


if __name__ == "__main__":
    import sys
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
