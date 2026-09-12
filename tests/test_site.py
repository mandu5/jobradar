from radar import site

JOB = {"company": "P", "title": "FDE", "url": "https://x", "score": 95, "grade": "A",
       "scope": "글로벌한국", "deadline": "", "reason": "r", "source": "lever",
       "key": "lever_x:1", "hard_fail": ""}


def test_only_whitelisted_fields_are_published():
    d = site.build("2026-09-08", [JOB], [], [], [], {}, {})
    published = d["a"][0]
    assert set(published) <= set(site.JOB_FIELDS)
    # The dedup key and the internal hard_fail must never reach a public page.
    assert "key" not in published and "hard_fail" not in published


def test_a_new_personal_field_cannot_leak():
    leaky = dict(JOB, phone="010-0000-0000", resume="…", 이름="홍길동")
    d = site.build("2026-09-08", [leaky], [], [], [], {}, {})
    blob = str(d)
    assert "010-" not in blob and "홍길동" not in blob


def test_counts_and_ordering():
    jobs = [dict(JOB, score=70, grade="A", title="low"), dict(JOB, score=95, grade="A", title="high"),
            dict(JOB, grade="B"), dict(JOB, grade="C")]
    d = site.build("2026-09-08", jobs, [], [], [], {}, {})
    assert d["counts"] == {"A": 2, "B": 1, "C": 1, "contests": 0, "upcoming": 0}
    assert [j["title"] for j in d["a"]] == ["high", "low"]


def test_contests_sorted_by_deadline():
    cs = [dict(JOB, title="late", deadline="2026-11-01"), dict(JOB, title="soon", deadline="2026-09-14")]
    d = site.build("2026-09-08", [], [], [], cs, {}, {})
    assert [c["title"] for c in d["contests"]] == ["soon", "late"]


def test_empty_values_are_dropped_not_null():
    d = site.build("2026-09-08", [dict(JOB, deadline="", reason="")], [], [], [], {}, {})
    assert "deadline" not in d["a"][0] and "reason" not in d["a"][0]
