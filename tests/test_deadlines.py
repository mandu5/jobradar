from datetime import date
from pathlib import Path

from radar import deadlines


ITEMS = [
    {"id": "soon", "track": "T", "title": "곧", "date": "2026-09-20", "verified": True, "note": "n", "url": ""},
    {"id": "far", "track": "T", "title": "멀다", "date": "2027-06-01", "verified": True, "note": "n", "url": ""},
    {"id": "past", "track": "T", "title": "지남", "date": "2026-09-01", "verified": True, "note": "n", "url": ""},
    {"id": "bad", "track": "T", "title": "형식오류", "date": "미정", "verified": False, "note": "n", "url": ""},
]


def test_due_window_and_order():
    got = deadlines.due(date(2026, 9, 7), ITEMS)
    assert [g["id"] for g in got] == ["soon"]
    assert got[0]["days_left"] == 13


def test_due_includes_today_and_excludes_yesterday():
    items = [{"id": "today", "date": "2026-09-07"}, {"id": "yesterday", "date": "2026-09-06"}]
    got = deadlines.due(date(2026, 9, 7), items)
    assert [g["id"] for g in got] == ["today"] and got[0]["days_left"] == 0


def test_real_file_parses():
    # Your own data/deadlines.json when you have one, otherwise the shipped example.
    path = deadlines.PATH if deadlines.PATH.exists() else Path("data/deadlines.example.json")
    items = deadlines.load(path)
    assert len(items) >= 5
    assert all("title" in i and "date" in i and "track" in i for i in items)


def test_email_shows_fixed_deadlines():
    from radar.email_render import render
    fixed = [{"id": "x", "track": "캐나다", "title": "IEC 등록", "date": "2026-12-19", "verified": False,
              "note": "만 30세 전", "url": "https://example.com", "days_left": 10}]
    subject, body = render("2026-09-07", [], [], {}, {}, fixed=fixed)
    assert "고정 마감" in body and "IEC 등록" in body and "D-10" in body and "날짜 확인 필요" in body
    assert "마감임박 1" in subject
