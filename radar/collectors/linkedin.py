from __future__ import annotations

import re

from ..config import LINKEDIN_QUERIES
from ..http import get
from ..model import Posting
from ._util import clean

URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
CARD_RE = re.compile(r'<div class="base-card[^"]*"(.*?)</div>\s*</div>\s*</li>', re.S)


def parse(html: str, scope_hint: str = "AI경력") -> list[Posting]:
    out = []
    for li in re.split(r"<li>", html)[1:]:
        m = re.search(r'data-entity-urn="urn:li:jobPosting:(\d+)"', li)
        if not m:
            continue
        jid = m.group(1)
        title = clean(_g(r'class="base-search-card__title">(.*?)</h3>', li))
        company = clean(_g(r'class="base-search-card__subtitle">(.*?)</h4>', li))
        loc = clean(_g(r'class="job-search-card__location">(.*?)</span>', li))
        posted = _g(r'datetime="([^"]+)"', li)
        out.append(Posting(
            key=f"linkedin:{jid}", source="linkedin", company=company, title=title,
            url=f"https://www.linkedin.com/jobs/view/{jid}", location=loc, posted=posted, scope_hint=scope_hint,
        ))
    return out


def _g(pat: str, s: str) -> str:
    m = re.search(pat, s, re.S)
    return m.group(1) if m else ""


def fetch() -> list[Posting]:
    seen, out = set(), []
    for kw, loc, exp in LINKEDIN_QUERIES:
        params = {"keywords": kw, "location": loc, "start": 0}
        if exp:
            params["f_E"] = exp
        hint = "해외대학원" if loc != "South Korea" else "AI경력"
        for p in parse(get(URL, params=params).text, scope_hint=hint):
            if p.key not in seen:
                seen.add(p.key)
                out.append(p)
    return out
