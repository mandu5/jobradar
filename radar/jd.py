"""Fetch the full text of a job description for a Posting key/url (runs in GitHub Actions, not in the routine sandbox).

fetch_jd(key, url) -> dict(text, meta); text is plain text <= MAX_CHARS. Per-source handlers first, generic HTML last.
"""
from __future__ import annotations

import html as _html
import json
import re

from .http import get

MAX_CHARS = 7000


def to_text(h: str) -> str:
    h = re.sub(r"<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
    h = re.sub(r"<br\s*/?>|</p>|</li>|</div>|</h\d>|</tr>", "\n", h, flags=re.I)
    t = _html.unescape(re.sub(r"<[^>]+>", " ", h))
    t = re.sub(r"[ \t ]+", " ", t)
    t = re.sub(r"\n\s*\n+", "\n", t)
    return t.strip()


def _clip(t: str) -> str:
    return t[:MAX_CHARS] + ("\n…[truncated]" if len(t) > MAX_CHARS else "")


def _g(pat: str, s: str) -> str:
    m = re.search(pat, s, re.S | re.I)
    return m.group(1) if m else ""


def jd_jumpit(jid: str, raw: dict | None = None) -> dict:
    raw = raw or get(f"https://api.jumpit.co.kr/api/position/{jid}").json()
    r = raw.get("result") or {}
    parts = [f"# {r.get('title', '')} — {r.get('companyName', '')}"]
    for k, label in (("responsibility", "주요업무"), ("qualifications", "자격요건"), ("preferredRequirements", "우대사항"), ("recruitProcess", "전형절차"), ("welfares", "복지")):
        v = r.get(k)
        if v:
            parts.append(f"## {label}\n{to_text(str(v))}")
    meta = {
        "deadline": str(r.get("closedAt") or "")[:10],
        "career": f"{r.get('minCareer')}~{r.get('maxCareer')}년" + (" 신입" if r.get("newcomer") else ""),
        "location": to_text(str(r.get("workingPlaces") or r.get("location") or ""))[:120],
        "education": str(r.get("educationName") or ""),
    }
    return {"text": _clip("\n\n".join(parts)), "meta": meta}


def jd_greenhouse(board: str, jid: str, raw: dict | None = None) -> dict:
    raw = raw or get(f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs/{jid}").json()
    content = _html.unescape(raw.get("content") or "")
    text = f"# {raw.get('title', '')} — {raw.get('company_name', board)}\n{to_text(content)}"
    return {"text": _clip(text), "meta": {"deadline": str(raw.get("application_deadline") or "")[:10], "location": (raw.get("location") or {}).get("name", "")}}


def jd_linkareer(aid: str, html: str | None = None) -> dict:
    html = html if html is not None else get(f"https://linkareer.com/activity/{aid}").text
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return {"text": _clip(to_text(html)), "meta": {}}
    ap = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    act = next((v for k, v in ap.items() if k == f"Activity:{aid}"), {}) or next((v for k, v in ap.items() if k.startswith("Activity:")), {})
    texts = [to_text(v.get("text") or v.get("content") or "") for k, v in ap.items() if k.startswith("ActivityText:")]
    head = f"# {act.get('title', '')} — {act.get('organizationName', '')}"
    return {"text": _clip(head + "\n" + "\n".join(t for t in texts if t)), "meta": {"scale": act.get("recruitScale", ""), "jobTypes": act.get("jobTypes", [])}}


def jd_naver(aid: str, html: str | None = None) -> dict:
    html = html if html is not None else get(f"https://recruit.navercorp.com/rcrt/view.do?annoId={aid}").text
    t = to_text(html)
    i = t.find("모집 부서")
    t = t[max(0, i - 200):] if i > 0 else t
    return {"text": _clip(t), "meta": {}}


def jd_saramin(rid: str, html: str | None = None) -> dict:
    html = html if html is not None else get(f"https://www.saramin.co.kr/zf_user/jobs/relay/view-detail?rec_idx={rid}").text
    t = to_text(html)
    note = "\n\n[참고] 사람인 공고 본문은 이미지인 경우가 많아 위 텍스트는 직종·요약 정보 위주일 수 있음. 상세는 링크에서 확인."
    return {"text": _clip(t + note), "meta": {}}


def jd_line(sid: str, raw: dict | None = None) -> dict:
    raw = raw or get(f"https://careers.linecorp.com/page-data/ko/jobs/{sid}/page-data.json").json()
    strings: list[str] = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k != "locales":
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str) and len(o) > 120:
            strings.append(to_text(o))

    walk(raw.get("result", {}).get("data", {}))
    seen, out = set(), []
    for s in strings:
        if s not in seen:
            seen.add(s)
            out.append(s)
    return {"text": _clip("\n\n".join(out)), "meta": {}}


def jd_lever(token: str, jid: str, raw: dict | None = None) -> dict:
    raw = raw or get(f"https://api.lever.co/v0/postings/{token}/{jid}").json()
    cat = raw.get("categories") or {}
    head = f"# {raw.get('text', '')} — {token}\n{cat.get('location', '')} / {cat.get('team', '')} / {cat.get('commitment', '')}"
    parts = [head, to_text(raw.get("description") or "")]
    for lst in raw.get("lists") or []:
        parts.append(f"## {clean_text(lst.get('text', ''))}\n{to_text(lst.get('content') or '')}")
    parts.append(to_text(raw.get("additional") or ""))
    return {"text": _clip("\n\n".join(p for p in parts if p.strip())), "meta": {"team": cat.get("team", ""), "location": cat.get("location", "")}}


def clean_text(s: str) -> str:
    return to_text(s)


def jd_generic(url: str, html: str | None = None) -> dict:
    html = html if html is not None else get(url).text
    title = to_text(_g(r"<title>(.*?)</title>", html))
    return {"text": _clip(f"# {title}\n{to_text(html)}"), "meta": {"generic": True}}


def _guard(fn, url: str) -> dict:
    """Run a handler; on failure fall back to the generic page, and record why."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        try:
            g = jd_generic(url)
            g["meta"]["handler_error"] = f"{type(exc).__name__}: {exc}"[:160]
            return g
        except Exception as exc2:  # noqa: BLE001
            return {"text": "", "meta": {"error": f"{type(exc).__name__}: {exc} / {type(exc2).__name__}: {exc2}"[:300]}}


HANDLERS = {
    "jumpit": lambda rest, url: jd_jumpit(rest),
    "greenhouse": lambda rest, url: jd_greenhouse(*rest.partition(":")[::2]),
    "linkareer": lambda rest, url: jd_linkareer(rest),
    "naver": lambda rest, url: jd_naver(rest),
    "saramin": lambda rest, url: jd_saramin(rest),
    "line": lambda rest, url: jd_line(rest),
}


def fetch_jd(key: str, url: str) -> dict:
    """Source handler when one exists; otherwise the generic page text. Errors are returned in meta, never raised."""
    src, _, rest = key.partition(":")
    # ATS collector keys look like gh_<token>, ashby_<token>, lever_<token>
    if "_" in src:
        ats, _, token = src.partition("_")
        if ats == "gh":
            return _guard(lambda: jd_greenhouse(token, rest), url)
        if ats == "ashby":
            return _guard(lambda: jd_generic(url), url)
        if ats == "lever":
            return _guard(lambda: jd_lever(token, rest), url)
    handler = HANDLERS.get(src)
    try:
        return handler(rest, url) if handler else jd_generic(url)
    except Exception as e:  # noqa: BLE001 — a JD fetch must never abort the batch
        if handler:
            try:
                g = jd_generic(url)
                g["meta"]["handler_error"] = f"{type(e).__name__}: {e}"[:160]
                return g
            except Exception as e2:  # noqa: BLE001
                return {"text": "", "meta": {"error": f"{type(e).__name__}: {e} / generic: {type(e2).__name__}: {e2}"[:300]}}
        return {"text": "", "meta": {"error": f"{type(e).__name__}: {e}"[:300]}}
