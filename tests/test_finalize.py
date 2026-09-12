

def test_contests_are_split_out_of_the_job_lists():
    from radar.finalize import split_contests
    scored = [
        {"key": "a", "grade": "A", "scope": "글로벌한국", "deadline": ""},
        {"key": "b", "grade": "A", "scope": "대회", "deadline": "2026-10-01"},
        {"key": "c", "grade": "B", "scope": "대회", "deadline": "2026-09-14"},
        {"key": "d", "grade": "C", "scope": "대회", "deadline": "2026-09-20"},
    ]
    jobs, contests = split_contests(scored)
    assert [j["key"] for j in jobs] == ["a"]
    # C-graded contests are dropped, and the rest come back soonest-first.
    assert [c["key"] for c in contests] == ["c", "b"]


def test_contests_never_reach_the_notion_approval_queue():
    from radar.finalize import notion_rows
    rows = notion_rows([
        {"key": "j", "grade": "A", "scope": "글로벌한국", "company": "P", "title": "FDE", "url": "u", "source": "lever"},
        {"key": "k", "grade": "A", "scope": "대회", "company": "DACON", "title": "대회", "url": "u", "source": "dacon"},
    ], "2026-09-08")
    assert [r["키"] for r in rows] == ["j"]


def test_upcoming_ignores_contests():
    from datetime import date
    from radar.finalize import upcoming
    seen = {
        "job": {"grade": "A", "deadline": "2026-09-10", "scope": "글로벌한국", "company": "P", "title": "t", "url": "u"},
        "cnt": {"grade": "A", "deadline": "2026-09-09", "scope": "대회", "company": "D", "title": "t", "url": "u"},
    }
    assert [u["key"] for u in upcoming(seen, date(2026, 9, 8))] == ["job"]
