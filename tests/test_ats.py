import json
from pathlib import Path

from radar.collectors import ats

FIX = Path(__file__).parent / "fixtures"


def _load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


def test_greenhouse_keeps_korea_ai_roles_and_drops_noise():
    posts = ats.parse_greenhouse(_load("ats_gh_moloco.json"), "Moloco", "moloco")
    titles = [p.title for p in posts]
    assert any("Machine Learning Engineer" in t for t in titles)
    assert all(p.key.startswith("gh_moloco:") and p.source == "ats" for p in posts)
    kr = [p for p in posts if p.scope_hint == "글로벌한국"]
    assert kr and all("Korea" in p.location or "Seoul" in p.location for p in kr)
    # senior / non-technical titles must not survive
    assert not any("Head of" in t or "Growth Manager" in t or "General Counsel" in t for t in titles)


def test_ashby_parses_and_tags_korea():
    posts = ats.parse_ashby(_load("ats_ashby_cohere.json"), "Cohere", "cohere")
    assert posts and all(p.url.startswith("http") for p in posts)
    kr = [p for p in posts if p.scope_hint == "글로벌한국"]
    assert any("Forward Deployed" in p.title for p in kr)


def test_abroad_requires_early_career():
    raw = {"jobs": [
        {"id": 1, "title": "Senior Machine Learning Engineer", "absolute_url": "http://x/1", "location": {"name": "San Francisco"}},
        {"id": 2, "title": "Software Engineer, New Grad", "absolute_url": "http://x/2", "location": {"name": "Toronto"}},
        {"id": 3, "title": "Machine Learning Engineer", "absolute_url": "http://x/3", "location": {"name": "Seoul, Korea"}},
        {"id": 4, "title": "Data Scientist II", "absolute_url": "http://x/4", "location": {"name": "New York"}},
    ]}
    posts = ats.parse_greenhouse(raw, "X", "x")
    got = {p.title: p.scope_hint for p in posts}
    assert got == {"Software Engineer, New Grad": "해외취업", "Machine Learning Engineer": "글로벌한국"}
