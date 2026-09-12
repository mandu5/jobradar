from radar import page

TODAY = "2026-09-08"


def _render(**kw):
    base = dict(scored=[], upcoming=[], stats={"collected": 3}, failures={})
    base.update(kw)
    return page.render(TODAY, **base)


def test_dday_marks_the_next_two_weeks_in_bold():
    from datetime import date
    d = date(2026, 9, 8)
    assert page._dday("2026-09-13", d) == "**D-5** (09-13)"
    assert page._dday("2026-10-30", d) == "D-52 (10-30)"
    assert page._dday("", d) == "상시"
    assert page._dday("2026-09-01", d).startswith("지남")


def test_pipes_in_a_title_do_not_break_the_table():
    md = _render(scored=[{"grade": "A", "score": 90, "company": "X",
                          "title": "AI | ML Engineer", "url": "https://x", "reason": "r"}])
    row = next(line for line in md.splitlines() if "ML Engineer" in line)
    assert "AI \\| ML Engineer" in row
    # 5 columns => 6 cell delimiters. The title's own pipe is escaped, so it is not one of them.
    assert row.replace("\\|", "").count("|") == 6, row


def test_empty_day_still_renders_every_section():
    md = _render()
    for h in ("# 잡 레이더", "## 고정 마감", "## A등급", "## B등급", "## 대회 · 해커톤"):
        assert h in md
    assert "오늘 A등급으로 올라온 공고가 없다." in md


def test_unverified_fixed_deadline_is_flagged():
    md = _render(fixed=[{"title": "IEC", "date": "2026-12-19", "days_left": 102,
                         "track": "캐나다", "note": "n", "verified": False, "url": ""}])
    assert "D-102 ⚠" in md and "날짜 미확인" in md


def test_contests_are_sorted_by_deadline():
    md = _render(contests=[
        {"title": "늦은 대회", "company": "A", "url": "https://a", "deadline": "2026-11-01"},
        {"title": "빠른 대회", "company": "B", "url": "https://b", "deadline": "2026-09-14"},
    ])
    assert md.index("빠른 대회") < md.index("늦은 대회")


def test_notion_link_uses_the_resolvable_domain():
    # app.notion.com/p/<id> does not open for every client; www.notion.so/<id> always redirects.
    md = _render()
    assert "https://www.notion.so/" in md and "app.notion.com" not in md


def test_failures_are_reported_not_swallowed():
    md = _render(failures={"saramin": "HTTP 503"})
    assert "saramin: HTTP 503" in md


def test_empty_page_says_which_stage_broke():
    # Candidates collected but nothing scored => the scoring run failed.
    md = _render(collected=124)
    assert "채점이 실행되지 않았다" in md and "124건을 수집했지만" in md
    # Nothing collected at all => the collect workflow failed.
    md = _render(collected=0)
    assert "수집이 실행되지 않았다" in md
    # A normal day carries no warning banner.
    md = _render(scored=[{"grade": "A", "score": 90, "company": "X", "title": "t",
                          "url": "u", "reason": "r"}], collected=124)
    assert "⚠️" not in md
