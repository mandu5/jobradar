"""Fixed-date opportunities (grad school, visa lotteries, letter requests) surfaced in the daily digest.

These are not scraped postings — they are dates that must not slip. `due(today)` returns the ones
inside the notice window so the email can carry them next to the job cards.
"""
from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path

PATH = Path("data/deadlines.json")
# Days before a deadline at which it starts appearing in the digest.
NOTICE_DAYS = (60, 30, 14, 7, 3, 1, 0)


def load(path: Path = PATH) -> list[dict]:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8")).get("items", [])


def due(today: date, items: list[dict] | None = None, window: int = 60) -> list[dict]:
    """Deadlines within `window` days, soonest first. Past deadlines are dropped."""
    out = []
    for it in items if items is not None else load():
        try:
            d = datetime.strptime(it["date"], "%Y-%m-%d").date()
        except (KeyError, ValueError):
            continue
        days = (d - today).days
        if 0 <= days <= window:
            out.append({**it, "days_left": days})
    return sorted(out, key=lambda x: x["days_left"])
