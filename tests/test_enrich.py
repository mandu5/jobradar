from radar.enrich import enrich_linkareer
from radar.model import Posting


def test_enrich_linkareer_reads_next_data(fixture_text):
    # The list page contains the same Apollo entities as a detail page; use it as a stand-in.
    html = fixture_text("linkareer.html")
    p = Posting(key="linkareer:348348", source="linkareer", company="x", title="y", url="http://x")
    out = enrich_linkareer(p, html=html)
    assert out["deadline"].startswith("2026-")
    assert isinstance(out["snippet"], str)
