from __future__ import annotations

import hashlib
import re

from ..config import SIMPLIFY_SECTIONS
from ..http import get
from ..model import Posting
from ._util import clean

URL = "https://raw.githubusercontent.com/SimplifyJobs/New-Grad-Positions/dev/README.md"
ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.S)


def parse(md: str, max_age_days: int = 3) -> list[Posting]:
    """Rows are: company | role | location | apply links | age ('0d','5d','1mo'). Keep rows <= max_age_days old."""
    out = []
    section = ""
    last_company = ""
    for line in md.splitlines():
        h = re.match(r"^###?\s*(.+?)\s*New Grad Roles", line.replace("💻", "").replace("🤖", "").replace("📱", "").replace("📈", "").replace("🔧", "").replace("💼", "").strip())
        if h:
            section = h.group(1).strip()
    # Sections are separated by <h3> headings in HTML; parse by walking html blocks.
    for block in re.split(r"(?=<h3>|^###? )", md, flags=re.M):
        hm = re.search(r"<h3>(.*?)</h3>|^###?\s*(.+)$", block, re.M)
        sec = clean((hm.group(1) or hm.group(2)) if hm else "")
        sec = re.sub(r"[^\w&, ]", "", sec).strip()
        if not any(s.lower() in sec.lower() for s in SIMPLIFY_SECTIONS):
            continue
        for row in ROW_RE.findall(block):
            tds = [t for t in TD_RE.findall(row)]
            if len(tds) < 5:
                continue
            comp_raw, role, loc, links, age = tds[0], tds[1], tds[2], tds[3], clean(tds[4])
            comp = clean(comp_raw)
            if comp in ("↳", ""):
                comp = last_company
            else:
                last_company = comp
            m = re.match(r"(\d+)(d|mo)", age)
            if not m or m.group(2) != "d" or int(m.group(1)) > max_age_days:
                continue
            urls = re.findall(r'href="([^"]+)"', links)
            apply_url = next((u for u in urls if "simplify.jobs/p/" not in u), "")
            if not apply_url:  # closed posting (lock icon, no apply link)
                continue
            base = re.sub(r"[?&](utm_[^&]*|ref=[^&]*)", "", apply_url) + "|" + clean(loc)
            jid = hashlib.sha1(base.encode("utf-8")).hexdigest()[:16]
            out.append(Posting(
                key=f"simplify:{jid}", source="simplify", company=comp, title=clean(role), url=apply_url,
                location=clean(loc), career="New Grad", snippet=sec, scope_hint="해외대학원",
            ))
    return out


def fetch() -> list[Posting]:
    return parse(get(URL).text)
