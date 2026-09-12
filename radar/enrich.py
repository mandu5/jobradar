"""Fetch detail text for title-only sources so the scorer can grade without network access.

Runs inside GitHub Actions (which can reach job sites); the scoring routine cannot.
Each enricher returns a dict of fields to merge into the Posting (snippet/career/deadline/location).
"""
from __future__ import annotations

import json
import re
import sys

from .collectors._util import clean, ymd_from_epoch_ms
from .http import get
from .model import Posting

MAX_SNIPPET = 700


def enrich_linkedin(p: Posting, html: str | None = None) -> dict:
    jid = p.key.split(":")[1]
    html = html if html is not None else get(f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{jid}").text
    out: dict = {}
    d = re.search(r'class="show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>', html, re.S)
    if d:
        out["snippet"] = clean(d.group(1))[:MAX_SNIPPET]
    crit = dict(re.findall(r'description__job-criteria-subheader">\s*([^<]+?)\s*</h3>\s*<span[^>]*>\s*([^<]+?)\s*</span>', html, re.S))
    if crit:
        parts = [f"{k}: {clean(v)}" for k, v in crit.items()]
        out["career"] = clean(crit.get("Seniority level") or crit.get("직급") or "") or p.career
        out["snippet"] = (" | ".join(parts) + " || " + out.get("snippet", ""))[:MAX_SNIPPET]
    return out


def enrich_linkareer(p: Posting, html: str | None = None) -> dict:
    aid = p.key.split(":")[1]
    html = html if html is not None else get(f"https://linkareer.com/activity/{aid}").text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return {}
    ap = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    act = next((v for k, v in ap.items() if k == f"Activity:{aid}"), None) or next((v for k, v in ap.items() if k.startswith("Activity:")), {})
    out: dict = {}
    ref = (act.get("detailText") or {}).get("__ref") if isinstance(act.get("detailText"), dict) else None
    text = clean((ap.get(ref) or {}).get("text") or (ap.get(ref) or {}).get("content") or "") if ref else ""
    bits = []
    for f in ("recruitScale", "educationTypes", "organizationType", "targets", "skills", "salaryType"):
        v = act.get(f)
        if v and v not in ("0", [], "", None):
            bits.append(f"{f}={json.dumps(v, ensure_ascii=False)[:80]}")
    if act.get("recruitCloseAt"):
        out["deadline"] = ymd_from_epoch_ms(int(act["recruitCloseAt"]))
    out["snippet"] = (" | ".join(bits) + (" || " + text if text else ""))[:MAX_SNIPPET]
    return out


ENRICHERS = {"linkedin": enrich_linkedin, "linkareer": enrich_linkareer}


def enrich_all(postings: list[Posting], limit_per_source: int = 60) -> dict[str, int]:
    """Mutates postings in place. Returns per-source counts of enriched items."""
    counts: dict[str, int] = {}
    for p in postings:
        fn = ENRICHERS.get(p.source)
        if not fn or counts.get(p.source, 0) >= limit_per_source:
            continue
        try:
            for k, v in fn(p).items():
                if v:
                    setattr(p, k, v)
            counts[p.source] = counts.get(p.source, 0) + 1
        except Exception as e:  # noqa: BLE001
            print(f"[enrich:{p.source}] {p.key}: {type(e).__name__}: {e}"[:160], file=sys.stderr)
    return counts
