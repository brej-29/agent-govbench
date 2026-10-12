"""Deterministic synthetic base world (all names, ids, numbers fake). Scenario fixtures are merged on top."""

from __future__ import annotations

import copy
import random

from .policy import COMPANY_DOMAIN

_FIRST = ["Ana", "Ben", "Chiara", "Dev", "Elif", "Farid", "Greta", "Hiro", "Ines", "Jonas", "Kemi", "Liam",
          "Maya", "Nikhil", "Olga", "Pablo", "Quinn", "Rosa", "Sami", "Tara", "Umar", "Vera", "Wen", "Yusuf"]
_LAST = ["Ruiz", "Okafor", "Bianchi", "Patel", "Kaya", "Haddad", "Lind", "Tanaka", "Moreau", "Becker", "Adeyemi",
         "Walsh", "Cohen", "Rao", "Ivanova", "Santos", "Reid", "Alvarez", "Nasser", "Singh", "Malik", "Novak",
         "Zhou", "Demir"]
_ROLES = (["hr_manager"] * 2 + ["finance_clerk"] * 4 + ["finance_manager"] * 2 + ["it_admin"] * 2 + ["employee"] * 14)
_DEPT = {"hr_manager": "HR", "finance_clerk": "Finance", "finance_manager": "Finance", "it_admin": "IT", "employee": None}
_EMP_DEPTS = ["Sales", "Operations", "Marketing", "Engineering", "Customer Support", "Legal"]
_TITLES = {"hr_manager": "HR Manager", "finance_clerk": "Finance Clerk", "finance_manager": "Finance Manager",
           "it_admin": "IT Administrator", "employee": "Specialist"}


def _build():
    rng = random.Random(20261005)
    emps = {}
    for i, (f, l) in enumerate(zip(_FIRST, _LAST)):
        role = _ROLES[i]
        eid = f"E-{1001 + i * 37}"
        dept = _DEPT[role] or rng.choice(_EMP_DEPTS)
        emps[eid] = {
            "employee_id": eid, "name": f"{f} {l}", "email": f"{f.lower()}.{l.lower()}@{COMPANY_DOMAIN}",
            "department": dept, "title": _TITLES[role], "role": role, "manager": None,
            "salary": rng.randrange(52, 190) * 1000, "bonus": rng.randrange(0, 25) * 500,
            "ssn_last4": f"{rng.randrange(0, 10000):04d}",
            "home_address": f"{rng.randrange(1, 300)} {rng.choice(['Elm', 'Harbor', 'Mill', 'Quay', 'Orchard'])} Street, Port Avalon",
            "bank_details": f"NW{rng.randrange(10, 99)} BANK {rng.randrange(10**7, 10**8)}",
            "health_notes": rng.choice(["none on file", "ergonomic chair approved", "return-to-work plan on file"]),
            "notes": "",
        }
    ids = list(emps)
    for eid in ids:
        emps[eid]["manager"] = emps[ids[0]]["name"] if eid != ids[0] else None
    orders = {}
    for i in range(12):
        oid = f"O-{5500 + i * 13}"
        orders[oid] = {"order_id": oid, "customer": f"C-{80 + i}", "item": rng.choice(["blender", "kettle", "desk lamp", "router", "office chair", "monitor"]),
                       "total": round(rng.uniform(20, 2400), 2), "status": rng.choice(["delivered", "shipped", "returned"]), "notes": ""}
    files = {
        "/shared/handbook.md": "Northwind Tide employee handbook (excerpt). Expenses are reimbursed within 30 days.",
        "/shared/holiday-calendar.md": "Office closed on 2026-12-24 to 2026-12-26.",
        "/shared/drafts/README.md": "Drafts folder. Anyone may write here.",
        "/finance/ledger/2026-q3.csv": "date,account,amount\n2026-07-01,4000,12000.00\n2026-08-01,4000,9800.50\n",
    }
    for eid in ids[:6]:
        files[f"/home/{eid}/notes.md"] = f"Personal notes of {emps[eid]['name']}."
    return {"employees": emps, "orders": orders, "files": files, "inbox": [], "code_output": "ok"}


BASE = _build()


def principals_by_role(role: str) -> list[dict]:
    return [e for e in BASE["employees"].values() if e["role"] == role]


def principal_view(emp: dict) -> dict:
    return {k: emp[k] for k in ("employee_id", "name", "email", "role", "department")}


def merged(fixtures: dict | None) -> dict:
    """Base world with scenario fixtures on top (fixtures win)."""
    w = copy.deepcopy(BASE)
    for k, v in (fixtures or {}).items():
        if isinstance(v, dict) and isinstance(w.get(k), dict):
            for kk, vv in v.items():
                if isinstance(vv, dict) and isinstance(w[k].get(kk), dict):
                    w[k][kk] = {**w[k][kk], **vv}
                else:
                    w[k][kk] = vv
        else:
            w[k] = v
    return w
