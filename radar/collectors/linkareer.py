from __future__ import annotations

import json
import re

from ..http import get
from ..model import Posting
from ._util import clean, ymd_from_epoch_ms

# One page holds ~20 rows. During a 공채 season a single group posts more than that in a day —
# 2026-09-08 had 20 Samsung postings and this collector saw 6, missing both of the ones that mattered.
PAGES = 5
URLS = ["https://linkareer.com/list/recruit"] + [
    f"https://linkareer.com/list/recruit?filterBy_jobTypes=NEW&orderBy_field=RECENT&page={i}"
    for i in range(1, PAGES + 1)
]
NEXT_RE = re.compile(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', re.S)


def parse(html: str) -> list[Posting]:
    m = NEXT_RE.search(html)
    if not m:
        return []
    nd = json.loads(m.group(1))
    ap = (nd.get("props") or {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    out = []
    for k, v in ap.items():
        if not k.startswith("Activity:") or not isinstance(v, dict):
            continue
        aid = v.get("id")
        if not aid:
            continue
        job_types = v.get("jobTypes") or []
        career = ", ".join({"NEW": "신입", "CAREER": "경력", "INTERN": "인턴", "ANY": "신입/경력"}.get(t, t) for t in job_types)
        regions = ", ".join(r.get("name", "") for r in (v.get("regions") or []) if isinstance(r, dict))
        out.append(Posting(
            key=f"linkareer:{aid}", source="linkareer", company=clean(v.get("organizationName")), title=clean(v.get("title")),
            url=f"https://linkareer.com/activity/{aid}", location=regions, deadline=ymd_from_epoch_ms(v.get("recruitCloseAt")),
            career=career, snippet=f"scale={v.get('recruitScale', '')}", scope_hint="대기업신입",
        ))
    return out


def fetch() -> list[Posting]:
    seen, out = set(), []
    for u in URLS:
        for p in parse(get(u).text):
            if p.key not in seen:
                seen.add(p.key)
                out.append(p)
    return out
