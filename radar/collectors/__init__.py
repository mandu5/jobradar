"""Collector registry. Each module exposes fetch() -> list[Posting] and parse(raw) -> list[Posting]."""
from . import ats, contest, greenhouse, jumpit, line, linkareer, linkedin, naver, saramin, simplify, wanted, woowa

COLLECTORS = {
    "wanted": wanted,
    "jumpit": jumpit,
    "saramin": saramin,
    "linkareer": linkareer,
    "linkedin": linkedin,
    "naver": naver,
    "woowa": woowa,
    "line": line,
    "greenhouse": greenhouse,
    "simplify": simplify,
    "ats": ats,
    "contest": contest,
}
