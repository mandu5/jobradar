from __future__ import annotations

from ..http import get
from ..model import Posting
from ._util import clean, ymd

URL = "https://recruit.navercorp.com/rcrt/loadJobList.do"


def parse(raw: dict) -> list[Posting]:
    out = []
    for l in raw.get("list", []):
        aid = l.get("annoId")
        if not aid:
            continue
        out.append(Posting(
            key=f"naver:{aid}", source="naver", company=clean(l.get("sysCompanyCdNm") or "NAVER"), title=clean(l.get("annoSubject")),
            url=f"https://recruit.navercorp.com/rcrt/view.do?annoId={aid}", deadline=ymd(l.get("endYmdTime")),
            career=clean(l.get("entTypeCdNm")), posted=ymd(l.get("staYmdTime")),
            snippet=" / ".join(x for x in [clean(l.get("empTypeCdNm")), clean(l.get("subJobCdNm")), clean(l.get("classCdNm"))] if x),
            scope_hint="대기업신입",
        ))
    return out


def fetch() -> list[Posting]:
    return parse(get(URL, params={"firstIndex": 0, "recordCountPerPage": 100}).json())
