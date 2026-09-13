"""CLI: run all collectors, drop already-seen keys, prefilter, write data/candidates/<date>.json.

    python -m radar.collect                      # all sources
    python -m radar.collect --only wanted,jumpit
    python -m radar.collect --extra data/candidates/2026-09-06.gmail.json   # merge agent-supplied postings

Output schema: {"date", "postings": [Posting...], "failures": {source: error}, "stats": {...}}
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from . import seen as seen_mod
from .collectors import COLLECTORS
from .collectors._util import KST
from .config import MAX_PER_SOURCE
from .enrich import enrich_all
from .model import Posting
from .prefilter import keep


def run_collectors(only: list[str] | None = None) -> tuple[list[Posting], dict[str, str]]:
    postings, failures = [], {}
    for name, mod in COLLECTORS.items():
        if only and name not in only:
            continue
        try:
            got = mod.fetch()
            if not got:
                # A collector that filters rows by role may set `last_raw` to the number of rows
                # it parsed before filtering. Rows parsed but none relevant is a quiet day, not a
                # broken parser; only an empty parse is a structure warning.
                raw = getattr(mod, "last_raw", None)
                if raw:
                    print(f"[{name}] 0 relevant of {raw} parsed", file=sys.stderr)
                else:
                    failures[name] = "0 postings parsed (site structure changed?)"
            postings += got
            print(f"[{name}] {len(got)}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            failures[name] = f"{type(e).__name__}: {e}"[:200]
            print(f"[{name}] FAIL {failures[name]}", file=sys.stderr)
    return postings, failures


def priority(p: Posting) -> int:
    """Order within a source before the per-source cap applies. A 대기업 신입 공채 must never be
    truncated away because an unrelated posting happened to arrive first."""
    text = f"{p.title} {p.career} {p.snippet}"
    score = 0
    if re.search(r"신입|공채|New\s*Grad|Graduate|Entry", text, re.I):
        score -= 4
    if re.search(r"AI|인공지능|머신러닝|데이터|소프트웨어|Software|Engineer|개발", text, re.I):
        score -= 2
    if p.deadline:
        score -= 1
    return score


def dedup_and_filter(postings: list[Posting], seen: dict) -> tuple[list[Posting], Counter]:
    stats: Counter = Counter()
    keys, out = set(), []
    per_source: dict[str, int] = {}
    postings = sorted(postings, key=priority)
    for p in postings:
        stats["collected"] += 1
        if p.key in keys:
            stats["dup_in_run"] += 1
            continue
        keys.add(p.key)
        if not seen_mod.is_new(seen, p.key):
            stats["already_seen"] += 1
            continue
        ok, why = keep(p)
        if not ok:
            stats[f"drop_{why}"] += 1
            continue
        if per_source.get(p.source, 0) >= MAX_PER_SOURCE:
            stats["overflow_skipped"] += 1
            # Do NOT mark it seen. Marking overflow as seen retired the posting permanently on the
            # day the source happened to be busy — exactly the days that matter. Leaving it unseen
            # lets tomorrow's run pick it up.
            continue
        per_source[p.source] = per_source.get(p.source, 0) + 1
        stats["kept"] += 1
        out.append(p)
    return out, stats


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--extra", action="append", default=[], help="JSON file with {'postings': [...]} to merge")
    ap.add_argument("--out", default="")
    ap.add_argument("--seen", default=str(seen_mod.DEFAULT))
    ap.add_argument("--enrich", action="store_true", help="fetch detail text for title-only sources (linkedin, linkareer)")
    a = ap.parse_args(argv)

    today = datetime.now(KST).strftime("%Y-%m-%d")
    out_path = Path(a.out or f"data/candidates/{today}.json")
    seen = seen_mod.load(Path(a.seen))

    postings: list[Posting] = []
    failures: dict[str, str] = {}
    if a.only != "none":
        postings, failures = run_collectors([s for s in a.only.split(",") if s] or None)
    for ex in a.extra:
        raw = json.loads(Path(ex).read_text(encoding="utf-8"))
        postings += [Posting.from_dict(d) for d in raw.get("postings", [])]
    # If an output file already exists today (e.g. re-run with --extra), merge with it.
    if out_path.exists() and a.extra:
        prev = json.loads(out_path.read_text(encoding="utf-8"))
        postings = [Posting.from_dict(d) for d in prev.get("postings", [])] + postings
        failures = {**prev.get("failures", {}), **failures}

    kept, stats = dedup_and_filter(postings, seen)
    if a.enrich:
        for src, n in enrich_all(kept).items():
            stats[f"enriched_{src}"] = n
    if stats.get("overflow_skipped") and a.seen != "/dev/null":
        seen_mod.save(seen, Path(a.seen))  # overflow keys are recorded so they never resurface
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({"date": today, "postings": [p.to_dict() for p in kept], "failures": failures, "stats": dict(stats)}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"out": str(out_path), "kept": len(kept), "failures": failures, "stats": dict(stats)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
