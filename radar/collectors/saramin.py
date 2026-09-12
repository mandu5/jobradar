from __future__ import annotations

import re

from ..config import SARAMIN_URLS
from ..http import get
from ..model import Posting
from ._util import clean

ITEM_RE = re.compile(r'<div id="rec-(\d+)" class="list_item(.*?)(?=<div id="rec-\d+" class="list_item|<div class="item_paging|</section>)', re.S)


def _first(pattern: str, s: str) -> str:
    m = re.search(pattern, s, re.S)
    return clean(m.group(1)) if m else ""


def parse(html: str) -> list[Posting]:
    out = []
    for m in ITEM_RE.finditer(html):
        rid, body = m.group(1), m.group(2)
        title = _first(r'class="str_tit\s*"[^>]*title="([^"]+)"', body) or _first(r'<div class="job_tit">.*?<span>(.*?)</span>', body)
        company = _first(r'company_nm">\s*<a[^>]*class="str_tit"[^>]*>(.*?)</a>', body)
        group = _first(r'class="main_corp" title="([^"]+)"', body)
        size = _first(r'class="info_stock" title="([^"]+)"', body)
        sectors = " ".join(re.findall(r"<span>([^<]+)</span>", _first(r'(<span class="job_sector">.*?</span>\s*</span>)', body) or ""))
        loc = _first(r'class="work_place">(.*?)</p>', body)
        career = _first(r'class="career">(.*?)</p>', body)
        edu = _first(r'class="education">(.*?)</p>', body)
        if not company:
            company = group or _first(r'company_nm">.*?title="([^"]+)"', body)
        if not title or not company:
            continue
        hint = "대기업신입" if size in ("대기업", "공기업") else "중견유니콘"
        out.append(Posting(
            key=f"saramin:{rid}", source="saramin", company=company, title=title,
            url=f"https://www.saramin.co.kr/zf_user/jobs/relay/view?rec_idx={rid}", location=loc, career=career,
            snippet=" / ".join(x for x in [group, size, sectors, edu] if x), scope_hint=hint,
        ))
    return out


def fetch() -> list[Posting]:
    out = []
    for u in SARAMIN_URLS:
        out += parse(get(u).text)
    return out
