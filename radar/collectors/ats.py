"""Global tech job boards (Greenhouse / Ashby / Lever) for Korea offices and overseas early-career roles.

Kept deliberately narrow: these boards carry hundreds of postings each, and only two slices matter —
anything located in Korea (no visa problem, high pay) and early-career AI/SWE roles abroad.
"""
from __future__ import annotations

import re

from ..config import ATS_BOARDS
from ..http import get
from ..model import Posting
from ._util import clean, ymd

ROLE_RE = re.compile(
    r"machine learning|\bML\b|\bAI\b|artificial intelligence|deep learning|research engineer|research scientist|"
    r"applied scientist|data engineer|data scientist|software engineer|backend|full[- ]stack|infrastructure|"
    r"forward deployed|solutions engineer|platform engineer|머신러닝|인공지능|데이터|개발",
    re.I,
)
EARLY_RE = re.compile(
    r"new ?grad|university grad|university recruit|early[- ]career|entry[- ]level|\bjunior\b|\bintern\b|internship|"
    r"apprentice|residency|rotational|campus|\bI\b(?![A-Za-z])|\bL[123]\b|\bE[34]\b|신입|주니어|인턴",
    re.I,
)
SENIOR_RE = re.compile(
    r"\bstaff\b|principal|\bsenior\b|\bsr\.?\b|\blead\b|manager|director|head of|\bVP\b|architect|"
    r"\bII+\b|\bL[4-9]\b|시니어|리드|팀장|책임|수석",
    re.I,
)
EXCLUDE_RE = re.compile(
    r"counsel|legal|attorney|marketing|\bsales\b|account executive|recruit|talent acquisition|\bHR\b|people ops|"
    r"finance|accounting|controller|payroll|procurement|communications|\bPR\b|designer|\bUX\b|content|copywrit|"
    r"customer success|support specialist|물류|영업|마케팅|법무|인사|채용",
    re.I,
)
KOREA_RE = re.compile(r"korea|seoul|서울|한국|판교|pangyo", re.I)


def _mk(company: str, jid, title: str, url: str, loc: str, deadline: str, posted: str, snippet: str, src_tag: str) -> Posting | None:
    title = clean(title)
    loc = clean(loc)
    if not title or not url:
        return None
    if not ROLE_RE.search(title) or EXCLUDE_RE.search(title):
        return None
    in_korea = bool(KOREA_RE.search(loc)) or bool(KOREA_RE.search(title))
    if SENIOR_RE.search(title) and not EARLY_RE.search(title):
        return None
    if not in_korea and not EARLY_RE.search(title):
        return None  # abroad: early-career only, everything else needs sponsorship we do not have
    return Posting(
        key=f"{src_tag}:{jid}", source="ats", company=company, title=title, url=url, location=loc,
        deadline=deadline, posted=posted, snippet=snippet[:600],
        scope_hint="글로벌한국" if in_korea else "해외취업",
    )


def parse_greenhouse(raw: dict, company: str, token: str) -> list[Posting]:
    out = []
    for j in raw.get("jobs", []):
        p = _mk(company, j.get("id"), j.get("title", ""), j.get("absolute_url", ""),
                (j.get("location") or {}).get("name", ""), ymd(j.get("application_deadline")),
                ymd(j.get("first_published") or j.get("updated_at")),
                " / ".join(d.get("name", "") for d in (j.get("departments") or []) if isinstance(d, dict)),
                f"gh_{token}")
        if p:
            out.append(p)
    return out


def parse_ashby(raw: dict, company: str, token: str) -> list[Posting]:
    out = []
    for j in raw.get("jobs", []):
        loc = j.get("location") or ""
        if not loc and j.get("address"):
            loc = str(j.get("address"))
        p = _mk(company, j.get("id") or j.get("jobId"), j.get("title", ""),
                j.get("jobUrl") or j.get("applyUrl") or "", loc, "", ymd(j.get("publishedAt")),
                " / ".join(x for x in [j.get("department") or "", j.get("team") or "", j.get("employmentType") or ""] if x),
                f"ashby_{token}")
        if p:
            out.append(p)
    return out


def parse_lever(raw: list, company: str, token: str) -> list[Posting]:
    out = []
    for j in raw or []:
        cat = j.get("categories") or {}
        p = _mk(company, j.get("id"), j.get("text", ""), j.get("hostedUrl", ""), cat.get("location", ""),
                "", "", " / ".join(x for x in [cat.get("team", ""), cat.get("commitment", "")] if x), f"lever_{token}")
        if p:
            out.append(p)
    return out


FETCHERS = {
    "greenhouse": (lambda t: f"https://boards-api.greenhouse.io/v1/boards/{t}/jobs", parse_greenhouse),
    "ashby": (lambda t: f"https://api.ashbyhq.com/posting-api/job-board/{t}", parse_ashby),
    "lever": (lambda t: f"https://api.lever.co/v0/postings/{t}?mode=json", parse_lever),
}


def fetch() -> list[Posting]:
    out: list[Posting] = []
    for company, ats, token in ATS_BOARDS:
        url_fn, parser = FETCHERS[ats]
        try:
            out += parser(get(url_fn(token)).json(), company, token)
        except Exception as exc:  # noqa: BLE001 — one dead board must not kill the sweep
            print(f"[ats] {company}/{ats}/{token}: {type(exc).__name__}: {exc}"[:160])
    return out
