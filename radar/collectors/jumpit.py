from __future__ import annotations

from ..config import JUMPIT_PARAMS
from ..http import get
from ..model import Posting
from ._util import clean, ymd

URL = "https://api.jumpit.co.kr/api/positions"


def parse(raw: dict) -> list[Posting]:
    out = []
    for p in (raw.get("result") or {}).get("positions", []):
        pid = p.get("id")
        if not pid:
            continue
        mn, mx = p.get("minCareer"), p.get("maxCareer")
        career = "신입" if p.get("newcomer") or mn == 0 else f"경력 {mn}~{mx}년"
        out.append(Posting(
            key=f"jumpit:{pid}", source="jumpit", company=clean(p.get("companyName")), title=clean(p.get("title")),
            url=f"https://jumpit.saramin.co.kr/position/{pid}", location=", ".join(p.get("locations") or []),
            deadline="" if p.get("alwaysOpen") else ymd(p.get("closedAt")), career=career,
            tags=[clean(t) for t in (p.get("techStacks") or [])][:8], snippet=clean(p.get("jobCategory")), scope_hint="중견유니콘",
        ))
    return out


def fetch() -> list[Posting]:
    out = []
    for page in (1, 2):
        params = dict(JUMPIT_PARAMS, page=page)
        out += parse(get(URL, params=params).json())
    return out
