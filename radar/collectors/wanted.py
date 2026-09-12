from __future__ import annotations

from ..config import WANTED_PARAMS
from ..http import get
from ..model import Posting
from ._util import clean, ymd

URL = "https://www.wanted.co.kr/api/chaos/navigation/v1/results"


def parse(raw: dict) -> list[Posting]:
    out = []
    for j in raw.get("data", []):
        jid = j.get("id")
        if not jid:
            continue
        comp = (j.get("company") or {}).get("name", "")
        addr = j.get("address") or {}
        loc = " ".join(x for x in [addr.get("location", ""), addr.get("district", "")] if x)
        a_from, a_to = j.get("annual_from"), j.get("annual_to")
        career = "신입" if j.get("is_newbie") else (f"경력 {a_from}~{a_to}년" if a_from is not None else "")
        out.append(Posting(
            key=f"wanted:{jid}", source="wanted", company=clean(comp), title=clean(j.get("position") or j.get("title")),
            url=f"https://www.wanted.co.kr/wd/{jid}", location=loc, deadline=ymd(j.get("due_time")), career=career,
            tags=[clean(t) for t in (j.get("skill_tags") or [])][:8], scope_hint="중견유니콘",
        ))
    return out


def fetch() -> list[Posting]:
    r = get(URL, params=WANTED_PARAMS)
    return parse(r.json())
