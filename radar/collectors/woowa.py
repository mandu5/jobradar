from __future__ import annotations

from ..http import get
from ..model import Posting
from ._util import clean, ymd

URL = "https://career.woowahan.com/w1/recruits"


def parse(raw: dict) -> list[Posting]:
    out = []
    for r in ((raw.get("data") or {}).get("list") or []):
        seq = r.get("recruitSeq")
        if not seq:
            continue
        mn, mx = r.get("careerRestrictionMinYears"), r.get("careerRestrictionMaxYears")
        career = clean(r.get("careerType")) or (f"경력 {mn}~{mx}년" if mn is not None else "")
        if mn is not None:
            career = f"{career} (min {mn}y)"
        out.append(Posting(
            key=f"woowa:{seq}", source="woowa", company="우아한형제들", title=clean(r.get("recruitName")),
            url=f"https://career.woowahan.com/recruitment/{seq}/detail", deadline=ymd(r.get("recruitEndDate")),
            career=career, posted=ymd(r.get("recruitOpenDate")), snippet=clean(r.get("jobGroup")), scope_hint="중견유니콘",
        ))
    return out


def fetch() -> list[Posting]:
    return parse(get(URL, params={"page": 0, "size": 100}).json())
