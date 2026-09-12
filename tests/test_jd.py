import json
from pathlib import Path

from radar import jd

FIX = Path(__file__).parent / "fixtures" / "jd"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8", errors="ignore")


def test_jumpit_jd_sections():
    r = jd.jd_jumpit("54917021", raw=json.loads(_read("jumpit_54917021.json")))
    assert "## 주요업무" in r["text"] and "## 자격요건" in r["text"] and "LLM" in r["text"]
    assert r["meta"]["deadline"] == "2026-10-01"


def test_greenhouse_jd_content():
    r = jd.jd_greenhouse("daangn", "7666768003", raw=json.loads(_read("greenhouse_daangn_job.json")))
    assert "당근" in r["text"] and "<" not in r["text"][:200]


def test_linkareer_jd_text():
    r = jd.jd_linkareer("348333", html=_read("linkareer_348333.html"))
    assert "NH농협은행" in r["text"] and "모집분야" in r["text"] and "<p>" not in r["text"]


def test_linkedin_jd_criteria_and_body():
    r = jd.jd_linkedin("4433412610", html=_read("linkedin_post.html"))
    assert r["meta"]["criteria"] and len(r["text"]) > 300


def test_naver_jd_starts_at_posting():
    r = jd.jd_naver("30005381", html=_read("naver_30005381.html"))
    assert "Robot System Software Engineer" in r["text"] and "모집 경력" in r["text"] and "무관" in r["text"]


def test_saramin_detail_has_note():
    r = jd.jd_saramin("54912763", html=_read("saramin_detail_54912763.html"))
    assert "국민은행" in r["text"] and "[참고]" in r["text"]


def test_line_pagedata_strings():
    r = jd.jd_line("3044", raw=json.loads(_read("line_3044_pagedata.json")))
    assert len(r["text"]) > 200


def test_fetch_jd_never_raises(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("network down")
    monkeypatch.setattr(jd, "get", boom)
    r = jd.fetch_jd("jumpit:1", "https://example.invalid/x")
    assert r["text"] == "" and "error" in r["meta"]


def test_text_clipped():
    assert len(jd._clip("x" * 10000)) < 10000 + 20


def test_ats_lever_key_routes_to_lever_handler(monkeypatch):
    called = {}

    def fake_lever(token, jid, raw=None):
        called["args"] = (token, jid)
        return {"text": "ok", "meta": {}}

    monkeypatch.setattr(jd, "jd_lever", fake_lever)
    r = jd.fetch_jd("lever_palantir:abc-123", "https://jobs.lever.co/palantir/abc-123")
    assert called["args"] == ("palantir", "abc-123") and r["text"] == "ok"


def test_ats_greenhouse_key_routes_to_greenhouse_handler(monkeypatch):
    called = {}

    def fake_gh(board, jid, raw=None):
        called["args"] = (board, jid)
        return {"text": "ok", "meta": {}}

    monkeypatch.setattr(jd, "jd_greenhouse", fake_gh)
    r = jd.fetch_jd("gh_moloco:7666768003", "http://x")
    assert called["args"] == ("moloco", "7666768003") and r["text"] == "ok"


def test_lever_parses_lists_into_sections():
    raw = {"text": "FDE, New Grad", "categories": {"location": "Seoul", "team": "Delta", "commitment": "Full-time"},
           "description": "<p>Role intro</p>", "lists": [{"text": "What we value", "content": "<li>Evidence</li>"}],
           "additional": "<p>Extra</p>"}
    r = jd.jd_lever("palantir", "x", raw=raw)
    assert "FDE, New Grad" in r["text"] and "## What we value" in r["text"] and "Evidence" in r["text"]
    assert r["meta"]["location"] == "Seoul"
