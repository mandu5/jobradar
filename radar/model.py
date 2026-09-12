from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class Posting:
    """One job posting, normalized across sources.

    key: "<source>:<id>" — the dedup key.
    deadline: "YYYY-MM-DD" or "" when unknown/rolling.
    career: raw career text from the source (e.g. "신입", "경력 3년 이상").
    scope_hint: one of 대기업신입 | 중견유니콘 | AI경력 | 해외대학원 | "" (collector's guess; the scorer decides).
    """

    key: str
    source: str
    company: str
    title: str
    url: str
    location: str = ""
    deadline: str = ""
    career: str = ""
    posted: str = ""
    snippet: str = ""
    scope_hint: str = ""
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Posting":
        known = {k: d.get(k) for k in cls.__dataclass_fields__ if k in d}
        known.setdefault("tags", [])
        return cls(**known)
