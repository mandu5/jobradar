"""Collector registry. Each module exposes fetch() -> list[Posting] and parse(raw) -> list[Posting]."""
from . import ats, contest, greenhouse, jumpit, line, linkareer, naver, saramin, simplify, wanted

COLLECTORS = {
    "wanted": wanted,
    "jumpit": jumpit,
    "saramin": saramin,
    "linkareer": linkareer,
    "naver": naver,
    "line": line,
    "greenhouse": greenhouse,
    "simplify": simplify,
    "ats": ats,
    "contest": contest,
}
