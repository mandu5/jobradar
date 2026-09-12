"""This season's 7 real submissions must survive the prefilter (they were all A/B by hand)."""
import pytest

from radar.model import Posting
from radar.prefilter import keep

SUBMITTED = [
    ("SK하이닉스", "[SK하이닉스] 2026년 하반기 신입 채용 (IT)", "신입"),
    ("현대모비스", "[현대모비스] 2026 하반기 신입사원 채용 - SW/데이터", "신입"),
    ("LG에너지솔루션", "[LG에너지솔루션] 2026 하반기 신입 채용 (DX/AI)", "신입"),
    ("한화에어로스페이스", "[한화에어로스페이스] 2026 하반기 신입 채용 – MRO IPS", "신입"),
    ("LG CNS", "[LG CNS] AX 엔지니어 신입 채용", "신입"),
    ("현대자동차", "[현대자동차] 2026년 9월 신입 채용 - SW/디지털 엔지니어링", "신입"),
    ("현대글로비스", "[현대글로비스] 2026 하반기 신입 채용 - AI Application Development", "신입"),
]


@pytest.mark.parametrize("company,title,career", SUBMITTED)
def test_submitted_postings_pass_prefilter(company, title, career):
    p = Posting(key=f"t:{company}", source="t", company=company, title=title, url="http://x", career=career)
    ok, why = keep(p)
    assert ok, f"{company} dropped: {why}"
