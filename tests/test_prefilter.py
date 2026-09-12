from radar.model import Posting
from radar.prefilter import keep


def P(title, career="", snippet="", tags=()):
    return Posting(key="t:1", source="t", company="X", title=title, url="http://x", career=career, snippet=snippet, tags=list(tags))


def test_senior_korean_dropped():
    assert keep(P("AI 엔지니어", career="경력 3년 이상"))[0] is False
    assert keep(P("AI 엔지니어", career="경력 5년↑"))[0] is False


def test_junior_korean_kept():
    assert keep(P("AI 엔지니어", career="경력 1년 이상"))[0] is True
    assert keep(P("AI 엔지니어", career="신입"))[0] is True
    assert keep(P("AI 엔지니어", career="경력 2년 이상"))[0] is True


def test_senior_english_dropped_unless_newgrad():
    assert keep(P("Machine Learning Engineer, 5+ years", career=""))[0] is False
    assert keep(P("Machine Learning Engineer (New Grad) 5 years program", career="New Grad"))[0] is True


def test_degree_only_dropped():
    assert keep(P("연구원 (박사 이상)"))[0] is False
    assert keep(P("Research Scientist, PhD required"))[0] is False


def test_nontech_dropped_when_no_tech_signal():
    assert keep(P("[현대종합금속] 신입 사원 모집 (영업직)"))[0] is False
    assert keep(P("사내 변호사 (경력)"))[0] is False
    assert keep(P("일본어 전문 통번역 프리랜서"))[0] is False


def test_nontech_kept_when_tech_signal():
    assert keep(P("데이터 마케팅 분석가 (신입)"))[0] is True


def test_woowa_min_years():
    assert keep(P("백엔드 개발자", career="경력 (min 3y)"))[0] is False
    assert keep(P("백엔드 개발자", career="경력 (min 1y)"))[0] is True


def test_general_hire_without_tech_word_kept():
    # 대기업 공채 titles often carry no tech keyword at all; the scorer must see them.
    assert keep(P("[현대자동차] 2026년 9월 신입 채용"))[0] is True
    assert keep(P("[SK하이닉스] 2026 하반기 신입 공채"))[0] is True
