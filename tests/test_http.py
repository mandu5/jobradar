"""robots.txt gate: wildcard matching, group selection, unreachable-robots policy, and the skip path."""
import pytest
import requests

from radar import http
from radar.http import Robots, RobotsDisallowed


def test_wildcards_and_longest_match_wins():
    r = Robots.parse("User-agent: *\nAllow: /\nDisallow: sign-in/**\nDisallow: /w1/**\nDisallow: /private$\n")
    assert r.allowed("https://x.test/recruitment/1")
    assert not r.allowed("https://x.test/w1/recruits")
    assert not r.allowed("https://x.test/sign-in/foo")
    assert not r.allowed("https://x.test/private")
    assert r.allowed("https://x.test/private/page")  # `$` anchors the end


def test_specific_group_beats_star_and_empty_disallow_means_allow():
    txt = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: *\nDisallow: /resumes\n\nUser-agent: Mediapartners-Google\nDisallow:\n"
    r = Robots.parse(txt)
    assert r.allowed("https://x.test/position/1")
    assert not r.allowed("https://x.test/resumes/me")
    assert not r.allowed("https://x.test/anything", agent="GPTBot/1.0")
    assert r.allowed("https://x.test/resumes/me", agent="Mediapartners-Google")


def test_disallow_everything_for_star_blocks_our_agent():
    r = Robots.parse("User-agent: LinkedInBot\nAllow: /\nUser-agent: *\nDisallow: /\n")
    assert not r.allowed("https://x.test/jobs-guest/jobs/api/search")
    assert r.allowed("https://x.test/jobs", agent="LinkedInBot")


def test_query_string_is_part_of_the_path():
    r = Robots.parse("User-agent: *\nDisallow: /*?sort=\n")
    assert r.allowed("https://x.test/list")
    assert not r.allowed("https://x.test/list?sort=recent")


class _Resp:
    def __init__(self, status, text=""):
        self.status_code, self.text = status, text


def _patch(monkeypatch, robots_status, robots_text=""):
    calls = []

    def fake_get(url, **kw):
        calls.append(url)
        if url.endswith("/robots.txt"):
            return _Resp(robots_status, robots_text)
        raise AssertionError("page fetched")

    monkeypatch.setattr(http.requests, "get", fake_get)
    monkeypatch.setattr(http, "_robots", {})
    return calls


def test_4xx_robots_means_unrestricted(monkeypatch):
    _patch(monkeypatch, 403)
    assert http.robots_allows("https://blocked.test/api/x")


def test_5xx_robots_means_disallow(monkeypatch):
    _patch(monkeypatch, 503)
    assert not http.robots_allows("https://down.test/api/x")


def test_unreachable_robots_means_disallow(monkeypatch):
    def boom(url, **kw):
        raise requests.ConnectionError("no route")

    monkeypatch.setattr(http.requests, "get", boom)
    monkeypatch.setattr(http, "_robots", {})
    assert not http.robots_allows("https://gone.test/x")


def test_get_raises_before_fetching_when_disallowed(monkeypatch):
    calls = _patch(monkeypatch, 200, "User-agent: *\nDisallow: /api/\n")
    with pytest.raises(RobotsDisallowed):
        http.get("https://site.test/api/positions")
    assert calls == ["https://site.test/robots.txt"]  # robots fetched once, page never


def test_user_agent_identifies_the_crawler():
    assert http.UA.startswith("jobradar/") and "github.com/mandu5/jobradar" in http.UA
