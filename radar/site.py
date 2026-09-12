"""site/radar.json — the data the dashboard reads.

The dashboard is a single static page in site/. The routine writes this file and pushes; Vercel
rebuilds on the push. Nothing else moves.

Privacy: the Vercel account is on the hobby plan, which has no password protection, so this page
is reachable by anyone who has the URL. Therefore this file carries **no personal data** — no
name, no contact details, no CV, no application text. It carries public job postings, a grade,
and a one-line reason. Someone who stumbles on the URL sees a job board with no owner attached.
Anything identifying stays in the private repo (RADAR.md) and in Notion.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

OUT = Path("site/radar.json")

# Fields that may leave the private repo. Everything not listed here is dropped, so adding a
# personal field to the scorer later cannot silently publish it.
JOB_FIELDS = ("company", "title", "url", "score", "grade", "scope", "deadline", "reason", "source")
FIXED_FIELDS = ("title", "track", "date", "days_left", "note", "verified", "url")


def _pick(d: dict, fields: tuple[str, ...]) -> dict:
    return {k: d.get(k) for k in fields if d.get(k) not in (None, "")}


def build(today: str, jobs: list[dict], upcoming: list[dict], fixed: list[dict],
          contests: list[dict], stats: dict, failures: dict, collected: int | None = None) -> dict:
    by_grade = {g: sorted([j for j in jobs if j.get("grade") == g],
                          key=lambda j: -float(j.get("score") or 0)) for g in ("A", "B")}
    return {
        "generated": today,
        "collected": collected,
        "counts": {"A": len(by_grade["A"]), "B": len(by_grade["B"]),
                   "C": sum(1 for j in jobs if j.get("grade") == "C"),
                   "contests": len(contests), "upcoming": len(upcoming)},
        "fixed": [_pick(f, FIXED_FIELDS) for f in sorted(fixed, key=lambda f: f.get("days_left", 9999))],
        "upcoming": [_pick(u, JOB_FIELDS) | {"days_left": u.get("days_left")} for u in upcoming],
        "a": [_pick(j, JOB_FIELDS) for j in by_grade["A"]],
        "b": [_pick(j, JOB_FIELDS) for j in by_grade["B"]],
        "contests": [_pick(c, JOB_FIELDS) for c in sorted(contests, key=lambda c: (c.get("deadline") or "9999"))],
        "health": {"stats": stats, "failures": failures},
    }


def write(today: str, jobs: list[dict], upcoming: list[dict], fixed: list[dict],
          contests: list[dict], stats: dict, failures: dict, collected: int | None = None) -> Path:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(build(today, jobs, upcoming, fixed, contests, stats, failures, collected),
                              ensure_ascii=False, indent=1), encoding="utf-8")
    return OUT


def dday(deadline: str, today: date) -> int | None:
    if not deadline:
        return None
    try:
        y, m, d = (int(x) for x in deadline.split("-"))
    except ValueError:
        return None
    return (date(y, m, d) - today).days
