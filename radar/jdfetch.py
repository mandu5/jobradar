"""CLI: fetch JD full text for scored A + top-N B postings (or explicit keys) and write data/jd/<safe-key>.md.

    python -m radar.jdfetch --date 2026-09-07 [--top-b 10]
    python -m radar.jdfetch --keys jumpit:54917021,naver:30005381
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from .collectors._util import KST
from .jd import fetch_jd

JD_DIR = Path("data/jd")


def safe(key: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", key)


def write_jd(p: dict) -> Path:
    JD_DIR.mkdir(parents=True, exist_ok=True)
    out = JD_DIR / f"{safe(p['key'])}.md"
    if out.exists():
        return out
    r = fetch_jd(p["key"], p["url"])
    fm = {
        "key": p["key"], "company": p.get("company", ""), "title": p.get("title", ""), "url": p["url"],
        "deadline": p.get("deadline", ""), "grade": p.get("grade", ""),
        "fetched": datetime.now(KST).strftime("%Y-%m-%d %H:%M"), "meta": r.get("meta", {}),
    }
    out.write_text("---\n" + json.dumps(fm, ensure_ascii=False) + "\n---\n\n" + (r.get("text") or "(본문 수집 실패)") + "\n", encoding="utf-8")
    return out


def targets_for(date: str, top_b: int) -> list[dict]:
    sp = Path(f"data/scored/{date}.json")
    if not sp.exists():
        return []
    scored = json.loads(sp.read_text(encoding="utf-8")).get("scored", [])
    a = [s for s in scored if s.get("grade") == "A"]
    b = sorted([s for s in scored if s.get("grade") == "B"], key=lambda s: -float(s.get("score") or 0))[:top_b]
    return a + b


def targets_for_keys(keys: list[str]) -> list[dict]:
    seen = json.loads(Path("data/seen.json").read_text(encoding="utf-8"))
    out = []
    for k in keys:
        if k in seen:
            out.append({"key": k, **seen[k]})
        else:
            print(f"[jdfetch] unknown key {k}", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    ap.add_argument("--top-b", type=int, default=10)
    ap.add_argument("--keys", default="")
    a = ap.parse_args(argv)
    keys = [k.strip() for k in a.keys.split(",") if k.strip()]
    targets = targets_for_keys(keys) if keys else targets_for(a.date, a.top_b)
    n = 0
    for p in targets:
        try:
            out = write_jd(p)
            n += 1
            print(f"[jdfetch] {p['key']} -> {out}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"[jdfetch] {p['key']} FAIL {type(e).__name__}: {e}", file=sys.stderr)
    print(json.dumps({"fetched": n, "targets": len(targets)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
