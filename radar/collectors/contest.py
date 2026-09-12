"""Competitions, hackathons and challenges — the "스펙" lane, separate from job postings.

Three sources, chosen because each covers something the others do not:
  - DACON     Korean AI/ML competitions. A placing here is the one contest line that reads as
              engineering evidence on a 국내 대기업 서류.
  - Devpost   Global online hackathons. Remote-eligible, no visa, sponsor-run (many are LLM/agent
              themed), and a submitted project is a portfolio artifact even without a prize.
  - wevity    The Korean 공모전 index. Only the 웹/모바일/IT board is read, and even there most
              entries are marketing or design — the filter below is deliberately harsh.

These are NOT jobs. They carry scope_hint="대회" so the prefilter lets them through untouched and
the scorer applies the contest rules in profile/rubric.md §5 instead of the job rules.
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta

from ..http import get
from ..model import Posting
from ._util import KST, clean, ymd

# Worth his time: AI/ML/data/software. A 디자인·영상·마케팅 공모전 is not a spec line for this profile.
RELEVANT_RE = re.compile(
    r"\bAI\b|인공지능|머신러닝|딥러닝|\bML\b|\bLLM\b|에이전트|agent|데이터|data|알고리즘|algorithm|"
    r"소프트웨어|software|개발|developer|해커톤|hackathon|코딩|coding|프로그래밍|challenge|경진대회|"
    r"컴퓨터비전|vision|자연어|\bNLP\b|시계열|이상탐지|anomaly|추천|robotics|로봇|보안|security|클라우드|cloud",
    re.I,
)
# Categories that are never worth it even when the title mentions AI (AI 포스터 공모전 등).
OFFTOPIC_RE = re.compile(
    r"영상/UCC|사진|예체능|미술|음악|웹툰|만화|문학|소설|시나리오|포스터|캐릭터|슬로건|네이밍|"
    r"수기|에세이|글쓰기|숏폼|브이로그|댄스|노래",
    re.I,
)
# Recruiting drives and paid courses dressed up as contests.
NOT_A_CONTEST_RE = re.compile(
    r"서포터즈|기자단|앰버서더|ambassador|수강생|교육생|아카데미|교육\s?과정|참여자 모집|설문|무료]", re.I)

MAX_PER_CONTEST_SOURCE = 15


def _relevant(text: str) -> bool:
    return bool(RELEVANT_RE.search(text)) and not OFFTOPIC_RE.search(text) and not NOT_A_CONTEST_RE.search(text)


def _first(pat: re.Pattern, s: str) -> str:
    m = pat.search(s)
    return m.group(1) if m else ""


def _from_dday(days: str, today: datetime | None = None) -> str:
    """DACON and wevity show a D-day badge, not a date. Turn D-14 into a real date so the
    digest can sort and flag it like every other deadline."""
    if not days.isdigit():
        return ""
    base = today or datetime.now(KST)
    return (base + timedelta(days=int(days))).strftime("%Y-%m-%d")


# ---------------------------------------------------------------- DACON

DACON_CARD_RE = re.compile(
    r'<a href="(/competitions/(?:official|open)/(\d+)/[^"]*)"[^>]*>(.*?)</a>', re.S)
DACON_NAME_RE = re.compile(r'class="name[^"]*"[^>]*>(.*?)</p>', re.S)
DACON_KEYWORD_RE = re.compile(r'class="info2[^"]*"[^>]*>(.*?)</p>', re.S)
DACON_DDAY_RE = re.compile(r'class="dday"[^>]*>(.*?)</div>', re.S)
# "마감임박" still accepts entries; a bare "마감" does not — so anchor on the whole badge.
DACON_CLOSED_RE = re.compile(r"연습|종료|완료|^마감$")


def parse_dacon(html: str) -> list[Posting]:
    out, seen = [], set()
    for href, cid, block in DACON_CARD_RE.findall(html):
        if cid in seen:
            continue
        seen.add(cid)
        name = clean(_first(DACON_NAME_RE, block))
        if not name:
            continue
        kw = clean(_first(DACON_KEYWORD_RE, block))
        state = clean(_first(DACON_DDAY_RE, block))
        # "연습" is a permanent practice board and "마감"/"종료" means entry has closed —
        # neither is something he can still enter, so neither belongs in the digest.
        if DACON_CLOSED_RE.search(state):
            continue
        if not _relevant(f"{name} {kw}"):
            continue
        out.append(Posting(
            key=f"dacon:{cid}", source="dacon", company="DACON", title=name,
            url=f"https://dacon.io{href}", snippet=kw, career=state,
            # The list page shows a D-day badge, not a date; the real date is on the detail page.
            deadline=ymd(state), scope_hint="대회", tags=[t.strip() for t in kw.split("|") if t.strip()],
        ))
    return out[:MAX_PER_CONTEST_SOURCE]


def fetch_dacon() -> list[Posting]:
    return parse_dacon(get("https://dacon.io/competitions").text)


# ---------------------------------------------------------------- Devpost

MONTHS = {m: i for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}
# "Jul 31 - Oct 01, 2026" — the submission deadline is the second date; the year appears once, at the end.
DEVPOST_RANGE_RE = re.compile(r"([A-Z][a-z]{2})\s+(\d{1,2}),?\s*(\d{4})?\s*$")


def devpost_deadline(dates: str) -> str:
    m = DEVPOST_RANGE_RE.search(clean(dates))
    if not m or not m.group(3):
        return ""
    mon = MONTHS.get(m.group(1))
    return f"{int(m.group(3)):04d}-{mon:02d}-{int(m.group(2)):02d}" if mon else ""


def parse_devpost(raw: dict) -> list[Posting]:
    out = []
    for h in raw.get("hackathons", []):
        hid = h.get("id")
        title = clean(h.get("title"))
        if not hid or not title:
            continue
        if h.get("open_state") not in (None, "", "open", "upcoming"):
            continue
        themes = ", ".join(clean(t.get("name")) for t in (h.get("themes") or []))
        if not _relevant(f"{title} {themes}"):
            continue
        loc = clean((h.get("displayed_location") or {}).get("location"))
        # Online only: flying to a campus hackathon in another country is not a real option for him.
        if loc and not re.search(r"online|virtual|worldwide|anywhere", loc, re.I):
            continue
        prize = clean(h.get("prize_amount"))
        out.append(Posting(
            key=f"devpost:{hid}", source="devpost", company=clean(h.get("organization_name")) or "Devpost",
            title=title, url=clean(h.get("url")), location=loc or "Online",
            deadline=devpost_deadline(h.get("submission_period_dates") or ""),
            snippet=" · ".join(x for x in (f"상금 {prize}" if prize else "", themes) if x),
            career=clean(h.get("time_left_to_submission")),
            scope_hint="대회", tags=[t.strip() for t in themes.split(",") if t.strip()],
        ))
    return out[:MAX_PER_CONTEST_SOURCE]


def fetch_devpost() -> list[Posting]:
    return parse_devpost(get("https://devpost.com/api/hackathons", params={"page": 1, "status[]": "open"}).json())


# ---------------------------------------------------------------- wevity

# Each row is `<li ...><!--class="bg" --> <div class="tit"> ...` — the comment is always there.
WEVITY_LI_RE = re.compile(
    r'<li[^>]*>\s*(?:<!--.*?-->\s*)?<div class="tit">\s*<a href="([^"]*ix=(\d+))"[^>]*>(.*?)</a>(.*?)</li>', re.S)
WEVITY_SUB_RE = re.compile(r'class="sub-tit"[^>]*>(.*?)</div>', re.S)
WEVITY_ORGAN_RE = re.compile(r'class="organ"[^>]*>(.*?)</div>', re.S)
WEVITY_DDAY_RE = re.compile(r'class="day"[^>]*>\s*D-(\d+)', re.S)


def parse_wevity(html: str) -> list[Posting]:
    out = []
    for href, ix, title_html, rest in WEVITY_LI_RE.findall(html):
        title = clean(re.sub(r"<span[^>]*>.*?</span>", "", title_html, flags=re.S))
        if not title:
            continue
        fields = clean(WEVITY_SUB_RE.search(rest).group(1) if WEVITY_SUB_RE.search(rest) else "")
        organ = clean(WEVITY_ORGAN_RE.search(rest).group(1) if WEVITY_ORGAN_RE.search(rest) else "")
        if not _relevant(f"{title} {fields}"):
            continue
        m = WEVITY_DDAY_RE.search(rest)
        dd = m.group(1) if m else ""
        out.append(Posting(
            key=f"wevity:{ix}", source="wevity", company=organ or "위비티", title=title,
            url="https://www.wevity.com/" + href.lstrip("/"), snippet=fields,
            deadline=_from_dday(dd), career=f"D-{dd}" if dd else "", scope_hint="대회",
        ))
    return out[:MAX_PER_CONTEST_SOURCE]


def fetch_wevity() -> list[Posting]:
    # cidx=20 is the 웹/모바일/IT board; gub=1 is 공모전 (not 대외활동).
    # VERIFIED 2026-09-08: wevity 403s GitHub Actions runners and the full browser header set
    # below did NOT change that — the block is by IP, the same way wanted blocks us. So this
    # source only produces rows when the collector runs from a Korean/residential address; from
    # CI it fails and the digest reports it as a failed source. Kept because the headers are
    # correct for any other caller and because 과기부·중기부 공모전 only appear here.
    r = get("https://www.wevity.com/", params={"c": "find", "s": 1, "gub": 1, "cidx": 20},
            headers={"Referer": "https://www.wevity.com/",
                     "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                     "Upgrade-Insecure-Requests": "1", "Sec-Fetch-Mode": "navigate",
                     "Sec-Fetch-Site": "same-origin", "Sec-Fetch-Dest": "document"})
    r.encoding = "utf-8"
    return parse_wevity(r.text)


# ---------------------------------------------------------------- registry entry

SUBFETCHERS = (("dacon", fetch_dacon), ("devpost", fetch_devpost), ("wevity", fetch_wevity))


def fetch() -> list[Posting]:
    out: list[Posting] = []
    for name, fn in SUBFETCHERS:
        try:
            got = fn()
            out += got
            print(f"[contest/{name}] {len(got)}")
        except Exception as e:  # noqa: BLE001 — one dead board must not kill the rest
            print(f"[contest/{name}] FAIL {type(e).__name__}: {e}")
    return out
