"""Cheap keyword prefilter that runs before the LLM scorer.

Goal: drop postings that can never be A/B (senior-only, non-tech roles) without dropping
any posting a careful human would want scored. When in doubt, KEEP.
"""
from __future__ import annotations

import re

from .model import Posting

# Career text that means "3+ years required" in Korean or English.
SENIOR_KR = re.compile(r"(?<![\d.])([3-9]|1\d)\s*년\s*(이상|↑|\+)")
SENIOR_EN = re.compile(r"\b([3-9]|1\d)\s*\+?\s*(years|yrs)\b", re.I)
NEWGRAD_EN = re.compile(r"new\s*grad|entry[- ]level|junior|intern|graduate|university|campus", re.I)
DEGREE_ONLY = re.compile(r"(석사|박사)\s*(이상|필수|졸업자)|\b(PhD|Ph\.D)\b\s*(required|only)", re.I)

TECH = re.compile(
    r"AI|인공지능|머신러닝|ML\b|딥러닝|데이터|Data|개발|SW\b|S/W|소프트웨어|Software|엔지니어|Engineer|\bIT\b|정보|시스템|System|"
    r"DX|AX|디지털|Digital|LLM|에이전트|Agent|클라우드|Cloud|MLOps|백엔드|Backend|플랫폼|Platform|연구|Research|알고리즘|Algorithm|"
    r"컴퓨터|Computer|전산|보안|Security|DevOps|SRE|양산|공정|품질|Quantitative|Quant|Scientist|Analyst|분석|Solution|솔루션|Technical|기술",
    re.I,
)
GENERAL_HIRE = re.compile(r"신입|공채|채용|New\s*Grad|Graduate|Entry", re.I)
NONTECH = re.compile(
    r"영업|세일즈|Sales|마케팅|Marketing|회계|Accounting|세무|총무|인사\b|HR\b|법무|변호사|Legal|디자이너|Designer|간호|통번역|번역|"
    r"상담|텔레마케터|콜센터|CS\b|고객센터|MD\b|상품기획|경리|비서|Secretary|리셉션|물류사원|배송|운전|생산직|현장직|조리|바리스타|"
    r"Account Manager|Recruiter|People|Finance|재무|IR\b|홍보|PR\b|Community|콘텐츠 에디터|카피라이터|공인중개|보험설계|PM\b(?!.*(개발|기술|Technical))",
    re.I,
)


def keep(p: Posting) -> tuple[bool, str]:
    """Return (keep?, reason). Reason is one short token for stats."""
    # Contests are not jobs: the seniority and job-title rules below would drop every one of them
    # (a 경진대회 has no career field and no job title). The contest collector does its own filtering.
    if p.scope_hint == "대회":
        return True, "contest"
    text = f"{p.title} {p.snippet} {' '.join(p.tags)}"
    career = p.career or ""
    if DEGREE_ONLY.search(text) or DEGREE_ONLY.search(career):
        return False, "degree_only"
    if SENIOR_KR.search(career) or (SENIOR_KR.search(p.title) and "신입" not in p.title):
        return False, "senior_kr"
    if SENIOR_EN.search(career) or (SENIOR_EN.search(text) and not NEWGRAD_EN.search(text)):
        return False, "senior_en"
    m = re.search(r"min (\d+)y", career)
    if m and int(m.group(1)) >= 3:
        return False, "senior_min"
    has_tech = bool(TECH.search(text))
    has_general = bool(GENERAL_HIRE.search(text) or GENERAL_HIRE.search(career))
    if NONTECH.search(p.title) and not has_tech:
        return False, "nontech"
    if not has_tech and not has_general:
        return False, "no_signal"
    return True, "ok"
