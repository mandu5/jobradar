from radar.enrich import enrich_linkedin, enrich_linkareer
from radar.model import Posting

LI_HTML = """<div class="show-more-less-html__markup relative overflow-hidden"><p>About ActAI</p><p>We need 0-2 years experience, Python.</p></div>
<h3 class="description__job-criteria-subheader">Seniority level</h3><span class="description__job-criteria-text">Entry level</span>
<h3 class="description__job-criteria-subheader">Employment type</h3><span class="description__job-criteria-text">Full-time</span>"""


def test_enrich_linkedin_extracts_description_and_criteria():
    p = Posting(key="linkedin:123", source="linkedin", company="ActAI", title="AI Engineer", url="http://x")
    out = enrich_linkedin(p, html=LI_HTML)
    assert out["career"] == "Entry level"
    assert "Seniority level: Entry level" in out["snippet"] and "0-2 years experience" in out["snippet"]


def test_enrich_linkareer_reads_next_data(fixture_text):
    # The list page contains the same Apollo entities as a detail page; use it as a stand-in.
    html = fixture_text("linkareer.html")
    p = Posting(key="linkareer:348348", source="linkareer", company="x", title="y", url="http://x")
    out = enrich_linkareer(p, html=html)
    assert out["deadline"].startswith("2026-")
    assert isinstance(out["snippet"], str)
