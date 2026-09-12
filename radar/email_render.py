"""HTML email for the daily digest — table-based, mobile-first, safe in dark-mode clients.

Design goal: the reader decides in 30 seconds. Subject carries the decision, the first block is
"today's actions", everything else is one tap away in Notion.
"""
from __future__ import annotations

import html
import json

from radar.config import REPO_URL, TRACKER_URL

NOTION_URL = TRACKER_URL
PAGE_URL = f"{REPO_URL}/blob/main/RADAR.md"

INK = "#111418"
MUTED = "#5b6472"
LINE = "#e3e6ea"
CARD = "#ffffff"
PAGE = "#f4f5f7"
ACCENT = "#1f4fd8"
URGENT = "#c0392b"

e = html.escape


def _pill(text: str, color: str, bg: str) -> str:
    return (f"<span style=\"display:inline-block;padding:2px 8px;border-radius:999px;background:{bg};"
            f"color:{color};font-size:12px;font-weight:700;line-height:18px\">{e(text)}</span>")


def _card(inner: str, border: str = LINE) -> str:
    return (f"<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" "
            f"style=\"background:{CARD};border:1px solid {border};border-radius:12px;margin:0 0 12px\">"
            f"<tr><td style=\"padding:16px 18px\">{inner}</td></tr></table>")


def _job_card(s: dict, rank: int | None = None, urgent_days: int | None = None) -> str:
    title = e(s.get("title") or "")
    company = e(s.get("company") or "")
    url = e(s.get("url") or "")
    deadline = s.get("deadline") or ""
    score = s.get("score")
    scope = s.get("scope") or ""
    reason = e(s.get("reason") or "")
    head = f"{rank}. " if rank else ""
    pills = []
    if urgent_days is not None:
        pills.append(_pill(f"D-{urgent_days}", "#ffffff", URGENT))
    if deadline:
        pills.append(_pill(f"마감 {deadline[5:]}", MUTED, "#eef0f3"))
    else:
        pills.append(_pill("상시", MUTED, "#eef0f3"))
    if score is not None:
        pills.append(_pill(f"{score}점", MUTED, "#eef0f3"))
    if scope:
        pills.append(_pill(scope, MUTED, "#eef0f3"))
    inner = (
        f"<div style=\"font-size:13px;color:{MUTED};margin:0 0 2px\">{head}{company}</div>"
        f"<div style=\"font-size:17px;font-weight:700;line-height:1.35;margin:0 0 8px\">"
        f"<a href=\"{url}\" style=\"color:{INK};text-decoration:none\">{title}</a></div>"
        f"<div style=\"margin:0 0 10px\">{' '.join(pills)}</div>"
        f"<div style=\"font-size:14px;line-height:1.6;color:{INK}\">{reason}</div>"
        f"<div style=\"margin-top:10px\"><a href=\"{url}\" style=\"color:{ACCENT};font-size:13px;font-weight:600;"
        f"text-decoration:none\">공고 열기 →</a></div>"
    )
    return _card(inner, border="#f0d3ce" if urgent_days is not None else LINE)


def _section(title: str, sub: str = "") -> str:
    s = f"<div style=\"font-size:13px;font-weight:700;letter-spacing:.04em;color:{MUTED};margin:22px 0 10px\">{e(title.upper())}"
    if sub:
        s += f" <span style=\"font-weight:400;letter-spacing:0\">· {e(sub)}</span>"
    return s + "</div>"


def _fixed_card(f: dict) -> str:
    d = f.get("days_left", 0)
    urgent = d <= 14
    pills = [_pill(f"D-{d}" if d else "오늘", "#ffffff" if urgent else MUTED, URGENT if urgent else "#eef0f3"),
             _pill(f.get("track", ""), MUTED, "#eef0f3")]
    if not f.get("verified", True):
        pills.append(_pill("날짜 확인 필요", MUTED, "#fdf3e7"))
    url = e(f.get("url") or "")
    link = (f"<div style=\"margin-top:8px\"><a href=\"{url}\" style=\"color:{ACCENT};font-size:13px;"
            f"font-weight:600;text-decoration:none\">공식 안내 →</a></div>") if url else ""
    return _card(
        f"<div style=\"font-size:16px;font-weight:700;line-height:1.4;margin:0 0 8px\">{e(f.get('title',''))}</div>"
        f"<div style=\"margin:0 0 10px\">{' '.join(pills)}</div>"
        f"<div style=\"font-size:13px;line-height:1.6;color:{MUTED}\">{e(f.get('date',''))} · {e(f.get('note',''))}</div>"
        + link,
        border="#f0d3ce" if urgent else LINE)


def _contest_rows(items: list[dict]) -> str:
    rows = []
    for c in items:
        dl = c.get("deadline") or ""
        left = c.get("career") or ""
        when = f"마감 {dl[5:]}" if dl else (left or "상시")
        rows.append(
            f"<tr><td style=\"padding:9px 0;border-top:1px solid {LINE}\">"
            f"<a href=\"{e(c.get('url') or '')}\" style=\"color:{INK};text-decoration:none;font-size:14px;font-weight:600\">"
            f"{e(c.get('title') or '')}</a>"
            f"<div style=\"font-size:12px;color:{MUTED};margin-top:3px\">{e(c.get('company') or '')} · {e(when)}"
            f"{' · ' + e((c.get('reason') or c.get('snippet') or '')[:56]) if (c.get('reason') or c.get('snippet')) else ''}"
            f"</div></td></tr>")
    return "".join(rows)


def render(today: str, scored: list[dict], upcoming: list[dict], stats: dict, failures: dict,
           b_limit: int = 10, fixed: list[dict] | None = None,
           contests: list[dict] | None = None, contest_limit: int = 5) -> tuple[str, str]:
    fixed = fixed or []
    contests = sorted(contests or [], key=lambda c: (c.get("deadline") or "9999"))[:contest_limit]
    a = sorted([s for s in scored if s.get("grade") == "A"], key=lambda s: -float(s.get("score") or 0))
    b_all = sorted([s for s in scored if s.get("grade") == "B"], key=lambda s: -float(s.get("score") or 0))
    b = b_all[:b_limit]
    n_c = sum(1 for s in scored if s.get("grade") == "C")

    if a:
        headline = f"오늘 볼 것 {len(a)}건"
    elif upcoming:
        headline = f"마감 임박 {len(upcoming)}건"
    else:
        headline = "오늘 A등급 없음"
    subject = f"[잡레이더 {today[5:7]}/{today[8:10]}] {headline} · B {len(b_all)} · 마감임박 {len(upcoming) + len(fixed)}"

    body = [
        f"<div style=\"background:{PAGE};padding:20px 12px;font-family:-apple-system,BlinkMacSystemFont,"
        f"'Apple SD Gothic Neo','Pretendard',Segoe UI,sans-serif;color:{INK}\">",
        f"<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\" style=\"max-width:600px;margin:0 auto\"><tr><td>",
        f"<div style=\"font-size:12px;color:{MUTED};letter-spacing:.06em;font-weight:700\">잡레이더 · {e(today)}</div>",
        f"<div style=\"font-size:26px;font-weight:800;line-height:1.25;margin:6px 0 4px\">{e(headline)}</div>",
        f"<div style=\"font-size:14px;color:{MUTED};margin:0 0 6px\">A {len(a)} · B {len(b_all)} · 제외 {n_c} · 마감임박 {len(upcoming)} · 고정마감 {len(fixed)}</div>",
        f"<div style=\"margin:14px 0 4px\"><a href=\"{NOTION_URL}\" style=\"display:inline-block;background:{INK};"
        f"color:#fff;font-size:14px;font-weight:700;padding:11px 18px;border-radius:10px;text-decoration:none\">"
        f"Notion에서 승인하기 →</a>"
        f"<a href=\"{PAGE_URL}\" style=\"display:inline-block;margin-left:8px;border:1px solid {LINE};"
        f"color:{INK};font-size:14px;font-weight:700;padding:10px 16px;border-radius:10px;text-decoration:none\">"
        f"전체 보기 →</a></div>",
        f"<div style=\"font-size:12px;color:{MUTED};margin:6px 0 0\">지원할 공고는 상태를 <b>지원예정</b>으로 바꾸세요. 그날 밤 지원서 패키지가 만들어집니다.</div>",
    ]

    if fixed:
        body.append(_section("고정 마감", "대학원·비자·추천서"))
        body += [_fixed_card(f) for f in fixed]

    if upcoming:
        body.append(_section("마감 임박", "미지원 A·B"))
        body += [_job_card(u, urgent_days=u.get("days_left")) for u in upcoming]

    body.append(_section("새 A등급", "지원 준비 시작" if a else "없음"))
    body += [_job_card(s, rank=i) for i, s in enumerate(a[:5], 1)] or [
        _card(f"<div style=\"font-size:14px;color:{MUTED}\">오늘 A등급으로 올라온 공고가 없습니다.</div>")]

    if b:
        rows = "".join(
            f"<tr><td style=\"padding:9px 0;border-top:1px solid {LINE}\">"
            f"<a href=\"{e(s['url'])}\" style=\"color:{INK};text-decoration:none;font-size:14px;font-weight:600\">"
            f"{e(s.get('company') or '')} · {e(s.get('title') or '')}</a>"
            f"<div style=\"font-size:12px;color:{MUTED};margin-top:3px\">{e(str(s.get('score','')))}점 · "
            f"마감 {e(s.get('deadline') or '미정')} · {e((s.get('reason') or '')[:60])}</div></td></tr>"
            for s in b)
        body.append(_section("B등급", f"상위 {len(b)}/{len(b_all)}건, 나머지는 Notion"))
        body.append(_card(f"<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\">{rows}</table>"))

    if contests:
        body.append(_section("대회 · 해커톤", f"참가 가능 {len(contests)}건"))
        body.append(_card(f"<table role=\"presentation\" width=\"100%\" cellpadding=\"0\" cellspacing=\"0\">"
                          f"{_contest_rows(contests)}</table>"))

    fail_txt = ", ".join(failures) if failures else "없음"
    body += [
        f"<div style=\"font-size:11px;color:{MUTED};line-height:1.7;margin:22px 0 0;padding-top:12px;border-top:1px solid {LINE}\">"
        f"수집 {e(json.dumps(stats, ensure_ascii=False))}<br>실패 소스: {e(fail_txt)}<br>"
        f"<a href=\"{NOTION_URL}\" style=\"color:{MUTED}\">잡 레이더 추적판</a> · "
        f"<a href=\"{PAGE_URL}\" style=\"color:{MUTED}\">RADAR.md</a> · "
        f"<a href=\"{REPO_URL}\" style=\"color:{MUTED}\">저장소</a></div>",
        "</td></tr></table></div>",
    ]
    return subject, "".join(body)
