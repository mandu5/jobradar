"""Every parser must turn its fixture into >=1 Posting with a key, company, title and absolute url."""
import re

from radar.collectors import greenhouse, jumpit, line, linkareer, naver, saramin, simplify, wanted
from radar.model import Posting


def _check(posts, source, min_n=1):
    assert len(posts) >= min_n, f"{source}: parsed {len(posts)}"
    keys = [p.key for p in posts]
    assert len(keys) == len(set(keys)), f"{source}: duplicate keys"
    for p in posts:
        assert isinstance(p, Posting)
        assert p.key.startswith(source + ":") and p.source == source
        assert p.title, f"{source}: empty title {p}"
        assert p.url.startswith("http"), f"{source}: bad url {p.url}"
        assert p.deadline == "" or re.fullmatch(r"\d{4}-\d{2}-\d{2}", p.deadline), f"{source}: bad deadline {p.deadline}"


def test_wanted(fixture_json):
    posts = wanted.parse(fixture_json("wanted.json"))
    _check(posts, "wanted", 5)
    assert all(p.company for p in posts)
    assert any(p.career == "신입" for p in posts)


def test_jumpit(fixture_json):
    posts = jumpit.parse(fixture_json("jumpit.json"))
    _check(posts, "jumpit", 5)
    assert all(p.company for p in posts)
    assert any(p.tags for p in posts)


def test_saramin(fixture_text):
    posts = saramin.parse(fixture_text("saramin.html"))
    _check(posts, "saramin", 20)
    assert all(p.company for p in posts)
    assert any("신입" in p.career for p in posts)
    assert any(p.scope_hint == "대기업신입" for p in posts)


def test_linkareer(fixture_text):
    posts = linkareer.parse(fixture_text("linkareer.html"))
    _check(posts, "linkareer", 10)
    assert all(p.company for p in posts)
    assert sum(1 for p in posts if p.deadline) >= 5
    assert any(p.career == "신입" for p in posts)


def test_naver(fixture_json):
    posts = naver.parse(fixture_json("naver.json"))
    _check(posts, "naver", 5)
    assert sum(1 for p in posts if p.deadline) >= 3


def test_line(fixture_json):
    posts = line.parse(fixture_json("line.json"))
    _check(posts, "line", 50)


def test_greenhouse(fixture_json):
    posts = greenhouse.parse(fixture_json("greenhouse_daangn.json"), "daangn", "당근")
    _check(posts, "greenhouse", 10)
    assert all(p.company == "당근" for p in posts)


def test_simplify(fixture_text):
    posts = simplify.parse(fixture_text("simplify.md"), max_age_days=30)
    _check(posts, "simplify", 20)
    assert all(p.career == "New Grad" for p in posts)
    assert all(p.company and p.company != "↳" for p in posts)
    assert any("Machine Learning" in p.snippet or "Data Science" in p.snippet for p in posts)


def test_greenhouse_foreign_board_keeps_only_early_career(fixture_json):
    raw = {"jobs": [
        {"id": 1, "title": "Staff Software Engineer, Infrastructure", "location": {"name": "San Francisco"}, "absolute_url": "http://x/1"},
        {"id": 2, "title": "Research Engineer, New Grad (2026)", "location": {"name": "San Francisco"}, "absolute_url": "http://x/2"},
        {"id": 3, "title": "Solutions Engineer", "location": {"name": "Seoul, Korea"}, "absolute_url": "http://x/3"},
    ]}
    posts = greenhouse.parse(raw, "anthropic", "Anthropic")
    assert [p.key for p in posts] == ["greenhouse:anthropic:2", "greenhouse:anthropic:3"]
    assert all(p.scope_hint == "해외대학원" for p in posts)


def test_rows_parsed_but_none_relevant_is_not_a_failure(monkeypatch):
    # A role-filtering collector reports how many rows it parsed via `last_raw`. Parsed rows
    # with nothing relevant is a quiet day; an empty parse is the structure warning.
    import types
    from radar import collect

    quiet = types.SimpleNamespace(last_raw=4, fetch=lambda: [])
    broken = types.SimpleNamespace(last_raw=0, fetch=lambda: [])
    plain = types.SimpleNamespace(fetch=lambda: [])  # a collector that never sets last_raw
    monkeypatch.setattr(collect, "COLLECTORS", {"quiet": quiet, "broken": broken, "plain": plain})
    _, failures = collect.run_collectors()
    assert set(failures) == {"broken", "plain"} and "structure" in failures["broken"]
