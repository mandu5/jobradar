from __future__ import annotations

import html as _html
import re
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))


def clean(s: str | None) -> str:
    if not s:
        return ""
    s = _html.unescape(re.sub(r"<[^>]+>", " ", str(s)))
    return re.sub(r"\s+", " ", s).strip()


def ymd_from_epoch_ms(ms: int | float | None) -> str:
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=KST).strftime("%Y-%m-%d")


def ymd(s: str | None) -> str:
    """Normalize '2026.09.08 18:00:00' / '2026-09-08T...' / '2026-09-08' to YYYY-MM-DD. Sentinel years >= 2999 -> ''."""
    if not s:
        return ""
    m = re.search(r"(\d{4})[.\-/](\d{1,2})[.\-/](\d{1,2})", str(s))
    if not m:
        return ""
    y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y >= 2999:
        return ""
    return f"{y:04d}-{mo:02d}-{d:02d}"
