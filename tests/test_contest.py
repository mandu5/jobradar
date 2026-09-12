import json
from datetime import datetime
from pathlib import Path

from radar.collectors import contest
from radar.collectors._util import KST
from radar.model import Posting
from radar.prefilter import keep

FIX = Path(__file__).parent / "fixtures" / "contest"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


def test_dacon_parses_open_competitions_only():
    out = contest.parse_dacon(_read("dacon.html"))
    assert out, "no DACON competitions parsed — the list markup changed"
    assert all(p.source == "dacon" and p.scope_hint == "대회" for p in out)
    assert all(p.title and p.url.startswith("https://dacon.io/competitions/") for p in out)
    # 연습/마감 boards must never reach the digest.
    assert not any(contest.DACON_CLOSED_RE.search(p.career) for p in out)


def test_dacon_keys_are_unique():
    out = contest.parse_dacon(_read("dacon.html"))
    assert len({p.key for p in out}) == len(out)


def test_devpost_keeps_ai_online_hackathons():
    out = contest.parse_devpost(json.loads(_read("devpost.json")))
    assert out
    for p in out:
        assert p.scope_hint == "대회" and p.key.startswith("devpost:")
        assert "online" in p.location.lower() or p.location == "Online"
        assert contest.RELEVANT_RE.search(f"{p.title} {p.snippet}")


def test_devpost_deadline_takes_the_end_of_the_range():
    assert contest.devpost_deadline("Jul 31 - Oct 01, 2026") == "2026-10-01"
    assert contest.devpost_deadline("Sep 08 - Sep 14, 2026") == "2026-09-14"
    # No year in the string means we cannot date it; better blank than wrong.
    assert contest.devpost_deadline("Jul 31 - Oct 01") == ""
    assert contest.devpost_deadline("") == ""


def test_wevity_parses_rows_and_dday():
    out = contest.parse_wevity(_read("wevity.html"))
    assert out
    for p in out:
        assert p.key.startswith("wevity:") and p.company and p.title
        assert p.url.startswith("https://www.wevity.com/?c=find")
    assert any(p.deadline for p in out), "no D-day converted to a date"


def test_wevity_drops_design_and_recruiting_entries():
    out = contest.parse_wevity(_read("wevity.html"))
    for p in out:
        assert not contest.OFFTOPIC_RE.search(f"{p.title} {p.snippet}")
        assert not contest.NOT_A_CONTEST_RE.search(f"{p.title} {p.snippet}")


def test_dday_conversion_is_relative_to_today():
    base = datetime(2026, 9, 8, tzinfo=KST)
    assert contest._from_dday("10", base) == "2026-09-18"
    assert contest._from_dday("0", base) == "2026-09-08"
    assert contest._from_dday("", base) == ""
    assert contest._from_dday("D-3", base) == ""


def test_prefilter_lets_contests_through_untouched():
    # A contest has no career text and no job title, so every job rule below would drop it.
    p = Posting(key="dacon:1", source="dacon", company="DACON",
                title="이상탐지 AI 경진대회", url="https://x", scope_hint="대회")
    assert keep(p) == (True, "contest")


def test_prefilter_still_filters_jobs():
    p = Posting(key="wanted:1", source="wanted", company="X", title="영업 담당자", url="https://x")
    assert keep(p)[0] is False


def test_fetch_never_raises_when_a_source_dies(monkeypatch):
    def boom():
        raise RuntimeError("network down")

    monkeypatch.setattr(contest, "SUBFETCHERS", (("dacon", boom), ("devpost", lambda: [
        Posting(key="devpost:1", source="devpost", company="X", title="AI Hackathon", url="https://x",
                scope_hint="대회")])))
    out = contest.fetch()
    assert len(out) == 1 and out[0].key == "devpost:1"
