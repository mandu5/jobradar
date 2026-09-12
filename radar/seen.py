from __future__ import annotations

import json
from pathlib import Path

DEFAULT = Path("data/seen.json")


def load(path: Path = DEFAULT) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8") or "{}")


def save(seen: dict, path: Path = DEFAULT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(seen, ensure_ascii=False, indent=0, sort_keys=True), encoding="utf-8")


def is_new(seen: dict, key: str) -> bool:
    return key not in seen
