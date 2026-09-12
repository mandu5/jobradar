import json
from datetime import date
from pathlib import Path

from radar import collect, finalize, seen as seen_mod
from radar.model import Posting


def _p(k, **kw):
    d = dict(key=k, source=k.split(":")[0], company="C", title="AI 엔지니어 신입", url="http://x/" + k, career="신입")
    d.update(kw)
    return Posting(**d)


def test_dedup_and_filter_counts():
    seen = {"wanted:1": {}}
    posts = [_p("wanted:1"), _p("wanted:2"), _p("wanted:2"), _p("jumpit:3", career="경력 5년 이상")]
    kept, stats = collect.dedup_and_filter(posts, seen)
    assert [p.key for p in kept] == ["wanted:2"]
    assert stats["already_seen"] == 1 and stats["dup_in_run"] == 1 and stats["drop_senior_kr"] == 1 and stats["kept"] == 1


def test_collect_cli_with_extra_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    extra = tmp_path / "gmail.json"
    extra.write_text(json.dumps({"postings": [_p("gmail:abc").to_dict(), _p("gmail:senior", career="경력 3년 이상").to_dict()]}), encoding="utf-8")
    out = tmp_path / "cand.json"
    assert collect.main(["--only", "none", "--extra", str(extra), "--out", str(out), "--seen", str(tmp_path / "seen.json")]) == 0
    got = json.loads(out.read_text(encoding="utf-8"))
    assert [p["key"] for p in got["postings"]] == ["gmail:abc"]
    assert got["stats"]["drop_senior_kr"] == 1


def test_finalize_end_to_end(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    today = "2026-09-06"
    (tmp_path / "data/candidates").mkdir(parents=True)
    (tmp_path / "data/scored").mkdir(parents=True)
    cands = [_p("wanted:1", deadline="2026-09-08").to_dict(), _p("jumpit:2").to_dict(), _p("naver:3").to_dict()]
    (tmp_path / f"data/candidates/{today}.json").write_text(json.dumps({"date": today, "postings": cands, "failures": {"line": "boom"}, "stats": {"kept": 3}}), encoding="utf-8")
    scored = [
        {"key": "wanted:1", "company": "C", "title": "AI 엔지니어 신입", "url": "http://x/wanted:1", "source": "wanted", "deadline": "2026-09-08", "scope": "중견유니콘", "grade": "A", "score": 82, "reason": "핏 좋음"},
        {"key": "jumpit:2", "company": "C", "title": "AI 엔지니어 신입", "url": "http://x/jumpit:2", "source": "jumpit", "deadline": "", "scope": "중견유니콘", "grade": "B", "score": 55, "reason": "TO 작음"},
        {"key": "naver:3", "company": "C", "title": "AI 엔지니어 신입", "url": "http://x/naver:3", "source": "naver", "deadline": "", "scope": "대기업신입", "grade": "C", "score": 10, "reason": "x", "hard_fail": "석사 필수"},
    ]
    (tmp_path / f"data/scored/{today}.json").write_text(json.dumps({"scored": scored}), encoding="utf-8")
    seen_path = tmp_path / "data/seen.json"
    assert finalize.main(["--date", today, "--seen", str(seen_path)]) == 0
    seen = seen_mod.load(seen_path)
    assert set(seen) == {"wanted:1", "jumpit:2", "naver:3"} and seen["wanted:1"]["grade"] == "A"
    digest = (tmp_path / f"digests/{today}.md").read_text(encoding="utf-8")
    assert "새 A등급" in digest and "핏 좋음" in digest and "D-2" in digest and "석사 필수" in digest and "boom" in digest
    subject = (tmp_path / f"data/out/{today}.email.subject").read_text(encoding="utf-8")
    assert subject.startswith("[잡레이더 09/06]") and "B 1" in subject and "마감임박 1" in subject
    body = (tmp_path / f"data/out/{today}.email.html").read_text(encoding="utf-8")
    assert "Notion에서 승인하기" in body and "핏 좋음" in body and "D-2" in body
    rows = json.loads((tmp_path / f"data/out/{today}.notion.json").read_text(encoding="utf-8"))
    assert [r["등급"] for r in rows] == ["A", "B"] and rows[0]["상태"] == "미검토" and rows[0]["date:마감:start"] == "2026-09-08"
    # Excluding the applied key removes it from the deadline section next time.
    up = finalize.upcoming(seen, date(2026, 9, 6), exclude={"wanted:1"})
    assert up == []


def test_per_source_cap_leaves_overflow_unseen_for_tomorrow():
    from radar.config import MAX_PER_SOURCE
    seen = {}
    posts = [_p(f"line:{i}") for i in range(MAX_PER_SOURCE + 5)] + [_p("naver:1")]
    kept, stats = collect.dedup_and_filter(posts, seen)
    assert stats["kept"] == MAX_PER_SOURCE + 1 and stats["overflow_skipped"] == 5
    assert sum(1 for p in kept if p.source == "line") == MAX_PER_SOURCE
    # Overflow must NOT be recorded as seen. Marking it seen retired a posting permanently on the
    # day its source happened to be busy — the 공채 days that matter most.
    assert seen == {}, "overflow postings were marked seen and can never come back"


def test_cap_keeps_the_공채_and_drops_the_noise():
    from radar.config import MAX_PER_SOURCE
    from radar.model import Posting
    noise = [Posting(key=f"line:n{i}", source="line", company="C", title="사무보조 상시채용",
                     url="http://x", career="경력무관") for i in range(MAX_PER_SOURCE)]
    gem = Posting(key="line:gem", source="line", company="삼성전자",
                  title="[삼성전자 DX부문] 2026년 하반기 3급 신입사원 채용 공고",
                  url="http://x", career="신입", deadline="2026-09-15")
    # The valuable posting arrives last, after the cap is already full.
    kept, stats = collect.dedup_and_filter(noise + [gem], {})
    assert any(p.key == "line:gem" for p in kept), "a 신입 공채 was truncated away by arrival order"


def test_email_shows_at_most_ten_b_rows():
    from radar.finalize import render_email
    scored = [{"key": f"x:{i}", "company": "C", "title": f"T{i}", "url": "http://x", "source": "x", "deadline": "", "scope": "", "grade": "B", "score": 50 + i, "reason": "r"} for i in range(15)]
    subject, body = render_email("2026-09-06", scored, [], {}, {})
    assert "B 15" in subject and "상위 10/15건" in body
    shown = [f"T{i}" for i in range(15) if f">C · T{i}<" in body]
    assert len(shown) == 10 and "T14" in shown and "T4" not in shown
