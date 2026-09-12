from __future__ import annotations

from ..http import get
from ..model import Posting
from ._util import clean, ymd

URL = "https://careers.linecorp.com/page-data/ko/jobs/page-data.json"


def parse(raw: dict) -> list[Posting]:
    out = []
    edges = (((raw.get("result") or {}).get("data") or {}).get("allStrapiJobs") or {}).get("edges", [])
    for e in edges:
        n = e.get("node") or {}
        sid = n.get("strapiId")
        if not sid or n.get("publish") is False or n.get("is_public") is False:
            continue
        comp = (n.get("company") or {}).get("name") if isinstance(n.get("company"), dict) else "LINE"
        city = (n.get("city") or {}).get("name") if isinstance(n.get("city"), dict) else ""
        cat = (n.get("job_category") or {}).get("name") if isinstance(n.get("job_category"), dict) else ""
        out.append(Posting(
            key=f"line:{sid}", source="line", company=clean(comp or "LINE"), title=clean(n.get("title") or n.get("title_en")),
            url=f"https://careers.linecorp.com/ko/jobs/{sid}", location=clean(city), deadline="" if n.get("until_filled") else ymd(n.get("end_date")),
            posted=ymd(n.get("start_date")), snippet=clean(cat), scope_hint="중견유니콘",
        ))
    return out


def fetch() -> list[Posting]:
    return parse(get(URL).json())
