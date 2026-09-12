"""CLI: merge scored results into seen.json and render digest / email / notion payload.

    python -m radar.finalize --date 2026-09-06 [--exclude-keys k1,k2]

Inputs : data/candidates/<date>.json, data/scored/<date>.json
Outputs: data/seen.json (updated), digests/<date>.md, data/out/<date>.email.html, data/out/<date>.notion.json
Scored schema: {"scored": [{key, company, title, url, source, deadline, scope, grade, score, reason, hard_fail}]}
"""
from __future__ import annotations

import argparse
import html
import json
from datetime import date, datetime, timedelta
from pathlib import Path

from . import deadlines as deadlines_mod
from . import page as page_mod
from . import site as site_mod
from . import seen as seen_mod
from .collectors._util import KST

GRADE_ORDER = {"A": 0, "B": 1, "C": 2}
EMAIL_B_LIMIT = 10  # user decision 2026-09-06: show only top-10 B in the email; the rest live in Notion
CONTEST_LIMIT = 5   # rubric §6: contests support the plan, they do not compete with it


def merge_seen(seen: dict, candidates: list[dict], scored: list[dict], today: str) -> dict:
    by_key = {s["key"]: s for s in scored}
    for c in candidates:
        s = by_key.get(c["key"], {})
        seen[c["key"]] = {
            "first_seen": today, "grade": s.get("grade", "-"), "score": s.get("score"), "deadline": s.get("deadline") or c.get("deadline", ""),
            "company": c.get("company", ""), "title": c.get("title", ""), "url": c.get("url", ""), "scope": s.get("scope", ""),
        }
    return seen


def upcoming(seen: dict, today: date, days: int = 3, exclude: set[str] | None = None) -> list[dict]:
    exclude = exclude or set()
    out = []
    for k, v in seen.items():
        # 대회 has its own section with its own D-days; the 마감 임박 block is for job applications.
        if k in exclude or v.get("grade") not in ("A", "B") or not v.get("deadline") or v.get("scope") == "대회":
            continue
        try:
            d = datetime.strptime(v["deadline"], "%Y-%m-%d").date()
        except ValueError:
            continue
        if today <= d <= today + timedelta(days=days):
            out.append({"key": k, **v, "days_left": (d - today).days})
    return sorted(out, key=lambda x: (x["days_left"], GRADE_ORDER.get(x["grade"], 9)))


def render_digest(today: str, scored: list[dict], up: list[dict], stats: dict, failures: dict) -> str:
    a = sorted([s for s in scored if s["grade"] == "A"], key=lambda s: -float(s.get("score") or 0))
    b = sorted([s for s in scored if s["grade"] == "B"], key=lambda s: -float(s.get("score") or 0))
    c = [s for s in scored if s["grade"] == "C"]
    L = [f"# 잡레이더 {today}", "", f"A {len(a)}건 · B {len(b)}건 · C {len(c)}건 · 마감임박 {len(up)}건", ""]
    L.append("## 1. 새 A등급 — 오늘 지원 준비 시작")
    L += [f"- **{s['company']} · {s['title']}** — 마감 {s.get('deadline') or '미정'} · {s.get('score')}점 · {s.get('scope','')}\n  {s.get('reason','')}\n  {s['url']}" for s in a] or ["- 없음"]
    L += ["", "## 2. 마감 3일 이내 (A/B, 미지원)"]
    L += [f"- D-{u['days_left']} {u['grade']} **{u['company']} · {u['title']}** — {u['deadline']} {u['url']}" for u in up] or ["- 없음"]
    L += ["", "## 3. 새 B등급 — 검토"]
    L += [f"- {s['company']} · {s['title']} ({s.get('score')}점, 마감 {s.get('deadline') or '미정'}) — {s.get('reason','')} {s['url']}" for s in b] or ["- 없음"]
    L += ["", "## 4. 수집 통계", f"- {json.dumps(stats, ensure_ascii=False)}"]
    L += [f"- 실패 소스: {json.dumps(failures, ensure_ascii=False)}" if failures else "- 실패 소스: 없음"]
    if c:
        L += ["", "<details><summary>C등급 제외 사유</summary>", ""] + [f"- {s['company']} · {s['title']} — {s.get('hard_fail') or s.get('reason','')}" for s in c] + ["", "</details>"]
    return "\n".join(L) + "\n"


def split_contests(scored: list[dict]) -> tuple[list[dict], list[dict]]:
    """Contests get their own section everywhere; keeping them in the A/B lists would let a
    hackathon outrank a job, which rubric §6 forbids. C-graded contests are dropped outright."""
    jobs = [s for s in scored if s.get("scope") != "대회"]
    contests = [s for s in scored if s.get("scope") == "대회" and s.get("grade") in ("A", "B")]
    return jobs, sorted(contests, key=lambda c: (c.get("deadline") or "9999"))


def render_email(today: str, scored: list[dict], up: list[dict], stats: dict, failures: dict,
                 fixed: list[dict] | None = None, contests: list[dict] | None = None) -> tuple[str, str]:
    """Delegates to radar.email_render — see that module for the layout."""
    from .email_render import render
    return render(today, scored, up, stats, failures, b_limit=EMAIL_B_LIMIT, fixed=fixed or [],
                  contests=contests or [], contest_limit=CONTEST_LIMIT)


def notion_rows(scored: list[dict], today: str) -> list[dict]:
    rows = []
    for s in scored:
        if s["grade"] not in ("A", "B") or s.get("scope") == "대회":
            continue
        rows.append({
            "공고": f"{s['company']} · {s['title']}"[:200], "회사": s["company"], "직무": s["title"], "등급": s["grade"], "점수": s.get("score"),
            "date:마감:start": s.get("deadline") or None, "링크": s["url"], "출처": s.get("source", "other"), "범위": s.get("scope", ""),
            "date:발견일:start": today, "상태": "미검토", "근거": s.get("reason", ""), "키": s["key"],
        })
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    ap.add_argument("--exclude-keys", default="", help="comma-separated keys already 지원완료/제외 in Notion")
    ap.add_argument("--seen", default=str(seen_mod.DEFAULT))
    a = ap.parse_args(argv)
    today = a.date
    cand = json.loads(Path(f"data/candidates/{today}.json").read_text(encoding="utf-8"))
    sc_path = Path(f"data/scored/{today}.json")
    scored = json.loads(sc_path.read_text(encoding="utf-8")).get("scored", []) if sc_path.exists() else []
    for s in scored:
        s.setdefault("grade", "C"); s.setdefault("score", 0); s.setdefault("reason", ""); s.setdefault("deadline", ""); s.setdefault("scope", "")
    seen = seen_mod.load(Path(a.seen))
    seen = merge_seen(seen, cand.get("postings", []), scored, today)
    seen_mod.save(seen, Path(a.seen))
    today_d = datetime.strptime(today, "%Y-%m-%d").date()
    up = upcoming(seen, today_d, exclude={k for k in a.exclude_keys.split(",") if k})
    fixed = deadlines_mod.due(today_d)
    jobs, contests = split_contests(scored)
    stats, failures = cand.get("stats", {}), cand.get("failures", {})
    Path("digests").mkdir(exist_ok=True)
    Path(f"digests/{today}.md").write_text(render_digest(today, jobs, up, stats, failures), encoding="utf-8")
    # RADAR.md is the page he actually opens; the email only points at it.
    Path("RADAR.md").write_text(
        page_mod.render(today, jobs, up, stats, failures, fixed, contests,
                        collected=len(cand.get("postings", []))), encoding="utf-8")
    # The dashboard reads this; Vercel rebuilds on push. No personal data goes in it — see radar/site.py.
    site_mod.write(today, jobs, up, fixed, contests, stats, failures,
                   collected=len(cand.get("postings", [])))
    subject, body = render_email(today, jobs, up, stats, failures, fixed, contests)
    Path("data/out").mkdir(parents=True, exist_ok=True)
    Path(f"data/out/{today}.email.html").write_text(body, encoding="utf-8")
    Path(f"data/out/{today}.email.subject").write_text(subject, encoding="utf-8")
    Path(f"data/out/{today}.notion.json").write_text(json.dumps(notion_rows(scored, today), ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"subject": subject, "fixed_deadlines": len(fixed), "A": sum(s["grade"] == "A" for s in jobs), "B": sum(s["grade"] == "B" for s in jobs), "upcoming": len(up), "contests": len(contests), "seen_total": len(seen)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
