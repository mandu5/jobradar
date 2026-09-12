from __future__ import annotations

import re

from ..config import GREENHOUSE_BOARDS, GREENHOUSE_EARLY_RE, GREENHOUSE_KR_BOARDS
from ..http import get
from ..model import Posting
from ._util import clean, ymd


def parse(raw: dict, board: str, company: str) -> list[Posting]:
    out = []
    for j in raw.get("jobs", []):
        jid = j.get("id")
        if not jid:
            continue
        loc = (j.get("location") or {}).get("name", "")
        title = clean(j.get("title"))
        if board not in GREENHOUSE_KR_BOARDS and not (re.search(GREENHOUSE_EARLY_RE, title, re.I) or re.search(r"korea|seoul", loc, re.I)):
            continue
        hint = "중견유니콘" if board in GREENHOUSE_KR_BOARDS else "해외대학원"
        out.append(Posting(
            key=f"greenhouse:{board}:{jid}", source="greenhouse", company=company, title=title,
            url=j.get("absolute_url", ""), location=clean(loc), deadline=ymd(j.get("application_deadline")),
            posted=ymd(j.get("first_published") or j.get("updated_at")), scope_hint=hint,
        ))
    return out


def fetch() -> list[Posting]:
    out = []
    for board, company in GREENHOUSE_BOARDS.items():
        try:
            out += parse(get(f"https://api.greenhouse.io/v1/boards/{board}/jobs").json(), board, company)
        except Exception as e:  # noqa: BLE001 — one dead board must not kill the rest
            print(f"[greenhouse] {board}: {e}")
    return out
