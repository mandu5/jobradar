"""RADAR.md — the one page he actually reads.

Why a Markdown file in this repo rather than a local HTML file or a hosted site:

  - The routine runs in Anthropic's cloud and his Mac is usually off, so nothing can write to a
    file on his laptop. Whatever the page is, the automation has to be able to reach it.
  - The repo is private, so a page committed here is private too, with no new hosting, no new
    login and no public URL that leaks which companies he is applying to.
  - GitHub renders Markdown on phone and desktop, so one bookmark is the whole interface.

So the daily routine writes this file and pushes it. The email shrinks to a notification that
links here. Approval still happens in Notion, because that is where the 상태 field lives.
"""
from __future__ import annotations

from radar.config import TRACKER_URL

from datetime import date


def _esc(s: str) -> str:
    """Keep table cells from breaking on pipes; leave everything else as the source wrote it."""
    return str(s or "").replace("|", "\\|").replace("\n", " ").strip()


def _dday(deadline: str, today: date) -> str:
    if not deadline:
        return "상시"
    try:
        y, m, d = (int(x) for x in deadline.split("-"))
    except ValueError:
        return _esc(deadline)
    n = (date(y, m, d) - today).days
    if n < 0:
        return f"지남 ({deadline[5:]})"
    return f"**D-{n}** ({deadline[5:]})" if n <= 14 else f"D-{n} ({deadline[5:]})"


def _job_table(rows: list[dict], today: date, show_reason: bool = True) -> list[str]:
    head = ["| 회사 | 공고 | 점수 | 마감 |" + (" 판단 |" if show_reason else ""),
            "|---|---|---|---|" + ("---|" if show_reason else "")]
    for s in rows:
        line = (f"| {_esc(s.get('company'))} "
                f"| [{_esc(s.get('title'))}]({s.get('url') or '#'}) "
                f"| {_esc(s.get('score'))} "
                f"| {_dday(s.get('deadline') or '', today)} |")
        if show_reason:
            line += f" {_esc((s.get('reason') or '')[:90])} |"
        head.append(line)
    return head


def render(today: str, scored: list[dict], upcoming: list[dict], stats: dict, failures: dict,
           fixed: list[dict] | None = None, contests: list[dict] | None = None,
           collected: int | None = None) -> str:
    d = date(int(today[:4]), int(today[5:7]), int(today[8:10]))
    fixed = sorted(fixed or [], key=lambda f: f.get("days_left", 9999))
    contests = sorted(contests or [], key=lambda c: (c.get("deadline") or "9999"))
    a = sorted([s for s in scored if s.get("grade") == "A"], key=lambda s: -float(s.get("score") or 0))
    b = sorted([s for s in scored if s.get("grade") == "B"], key=lambda s: -float(s.get("score") or 0))
    n_c = sum(1 for s in scored if s.get("grade") == "C")

    L = [
        "# 잡 레이더",
        "",
        f"`{today}` 기준 · A {len(a)} · B {len(b)} · 제외 {n_c} · 마감임박 {len(upcoming)} · 대회 {len(contests)}",
        "",
        (f"[추적판에서 승인하기]({TRACKER_URL}) — "
         "지원할 공고는 상태를 **지원예정**으로 바꾸면 그날 밤 22:00에 지원서 패키지가 만들어진다."
         if TRACKER_URL else
         "지원 여부는 사람이 정한다. 이 페이지는 읽을 공고를 고를 뿐, 아무 데도 지원하지 않는다."),
        "",
        "---",
        "",
    ]

    # An empty page can mean "nothing came in" or "the run broke". On 2026-09-08 it meant the
    # second, and nothing on the page said so. Never let those two look alike again.
    if not scored:
        if collected:
            L += [f"> ⚠️ **채점이 실행되지 않았다.** 오늘 {collected}건을 수집했지만 등급이 매겨진 공고가 0건이다. "
                  "08:30 루틴이 실패했거나 한도에 걸린 것이다. 아래 목록이 비어 있는 것은 공고가 없어서가 아니다.", ""]
        else:
            L += ["> ⚠️ **수집이 실행되지 않았다.** 오늘 후보 공고가 0건이다. "
                  "`collect` 워크플로 실행 기록을 확인할 것.", ""]

    L += ["## 고정 마감", ""]
    if fixed:
        L += ["| D-day | 트랙 | 항목 | 메모 |", "|---|---|---|---|"]
        for f in fixed:
            n = f.get("days_left", 0)
            tag = f"**D-{n}**" if n <= 14 else f"D-{n}"
            if not f.get("verified", True):
                tag += " ⚠"
            title = _esc(f.get("title"))
            if f.get("url"):
                title = f"[{title}]({f['url']})"
            L.append(f"| {tag} | {_esc(f.get('track'))} | {title} | {_esc(f.get('note'))[:110]} |")
        L += ["", "⚠ = 날짜 미확인. 공식 공지로 확인이 필요하다.", ""]
    else:
        L += ["60일 안에 걸린 고정 마감이 없다.", ""]

    if upcoming:
        L += ["## 마감 임박 — 아직 지원하지 않은 A·B", ""]
        L += _job_table(upcoming, d)
        L += [""]

    L += ["## A등급", ""]
    L += _job_table(a, d) if a else ["오늘 A등급으로 올라온 공고가 없다.", ""]
    L += [""]

    L += ["## B등급", ""]
    L += _job_table(b, d, show_reason=False) if b else ["없음.", ""]
    L += [""]

    L += ["## 대회 · 해커톤", ""]
    if contests:
        L += ["| 주최 | 대회 | 마감 | 분야 |", "|---|---|---|---|"]
        for c in contests:
            L.append(f"| {_esc(c.get('company'))} "
                     f"| [{_esc(c.get('title'))}]({c.get('url') or '#'}) "
                     f"| {_dday(c.get('deadline') or '', d)} "
                     f"| {_esc((c.get('reason') or c.get('snippet') or ''))[:70]} |")
    else:
        L += ["참가할 만한 대회가 없다.", ""]
    L += [""]

    fail_txt = ", ".join(f"{k}: {v}" for k, v in (failures or {}).items()) or "없음"
    L += [
        "---",
        "",
        "<details><summary>수집 통계</summary>",
        "",
        "```",
        "\n".join(f"{k}: {v}" for k, v in (stats or {}).items()),
        "```",
        "",
        f"실패한 소스 — {fail_txt}",
        "",
        "</details>",
        "",
        f"이 파일은 매일 08:30 KST에 `job-radar-daily` 루틴이 덮어쓴다. 직접 고쳐도 다음 날 사라진다.",
    ]
    return "\n".join(L) + "\n"
