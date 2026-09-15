"""HTTP for collectors: identified User-Agent, robots.txt gate (RFC 9309), per-host politeness delay.

Why: jobradar fetches public job listings on a daily schedule. It should look like what it is
(a named crawler with a contact URL), obey each site's robots.txt including `*`/`$` wildcards,
and never hammer a host. A collector whose endpoint is disallowed is skipped and reported, not
fetched anyway.
"""
from __future__ import annotations

import re
import threading
import time
from dataclasses import dataclass, field
from importlib.metadata import PackageNotFoundError, version
from urllib.parse import urlsplit

import requests

try:
    _VERSION = version("jobradar")
except PackageNotFoundError:  # running from a checkout without `pip install -e .`
    _VERSION = "dev"

PRODUCT = "jobradar"
UA = f"{PRODUCT}/{_VERSION} (+https://github.com/mandu5/jobradar)"
TIMEOUT = 25
ROBOTS_TIMEOUT = 10
MIN_INTERVAL = 1.0  # seconds between requests to the same host


class RobotsDisallowed(Exception):
    """The site's robots.txt does not allow this URL for our user agent."""


@dataclass
class _Group:
    agents: list[str]
    rules: list[tuple[bool, str]] = field(default_factory=list)  # (allow, pattern)


@dataclass
class Robots:
    """Minimal RFC 9309 matcher: longest matching rule wins, allow wins ties, `*` and `$` supported."""

    groups: list[_Group]

    @classmethod
    def parse(cls, text: str) -> "Robots":
        groups: list[_Group] = []
        current: _Group | None = None
        saw_rule = True  # so the first user-agent line starts a new group
        for raw in text.splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line or ":" not in line:
                continue
            key, _, val = line.partition(":")
            key, val = key.strip().lower(), val.strip()
            if key == "user-agent":
                if current is None or saw_rule:
                    current = _Group(agents=[])
                    groups.append(current)
                    saw_rule = False
                current.agents.append(val.lower())
            elif key in ("allow", "disallow") and current is not None:
                saw_rule = True
                if val == "" and key == "disallow":
                    continue  # empty Disallow = allow everything (no rule)
                if val:
                    current.rules.append((key == "allow", val))
        return cls(groups)

    def _group_for(self, agent: str) -> _Group | None:
        token = agent.lower()
        best: _Group | None = None
        best_len = -1
        for g in self.groups:
            for a in g.agents:
                if a != "*" and a in token and len(a) > best_len:
                    best, best_len = g, len(a)
        if best is not None:
            return best
        for g in self.groups:
            if "*" in g.agents:
                return g
        return None

    @staticmethod
    def _match(pattern: str, path: str) -> bool:
        anchored = pattern.endswith("$")
        pat = pattern[:-1] if anchored else pattern
        if not pat.startswith("/"):
            pat = "/" + pat  # tolerate `Disallow: mypage/**`
        rx = "".join(".*" if ch == "*" else re.escape(ch) for ch in pat)
        rx = "^" + rx + ("$" if anchored else "")
        return re.match(rx, path) is not None

    def allowed(self, url: str, agent: str = PRODUCT) -> bool:
        parts = urlsplit(url)
        path = parts.path or "/"
        if parts.query:
            path += "?" + parts.query
        group = self._group_for(agent)
        if group is None:
            return True
        verdict, longest = True, -1
        for allow, pattern in group.rules:
            if self._match(pattern, path):
                n = len(pattern)
                if n > longest or (n == longest and allow):
                    verdict, longest = allow, n
        return verdict


_lock = threading.Lock()
_robots: dict[str, Robots | None] = {}  # host -> parsed (None = allow all)
_last_hit: dict[str, float] = {}


def _fetch_robots(scheme: str, host: str) -> Robots | None:
    """RFC 9309 §2.3.1: 2xx -> parse; 4xx -> unrestricted; 5xx/unreachable -> treat as disallow-all."""
    url = f"{scheme}://{host}/robots.txt"
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=ROBOTS_TIMEOUT, allow_redirects=True)
    except requests.RequestException:
        return Robots([_Group(agents=["*"], rules=[(False, "/")])])
    if 200 <= r.status_code < 300:
        return Robots.parse(r.text)
    if 400 <= r.status_code < 500:
        return None
    return Robots([_Group(agents=["*"], rules=[(False, "/")])])


def robots_allows(url: str) -> bool:
    parts = urlsplit(url)
    host = parts.netloc.lower()
    with _lock:
        if host not in _robots:
            _robots[host] = _fetch_robots(parts.scheme or "https", host)
        robots = _robots[host]
    return True if robots is None else robots.allowed(url)


def _be_polite(host: str) -> None:
    with _lock:
        now = time.monotonic()
        scheduled = max(now, _last_hit.get(host, 0.0) + MIN_INTERVAL)
        _last_hit[host] = scheduled
    if scheduled > now:
        time.sleep(scheduled - now)


def get(url: str, params: dict | None = None, headers: dict | None = None, retries: int = 2) -> requests.Response:
    """GET with an identified UA, robots.txt check, per-host delay, timeout and simple retry."""
    if not robots_allows(url):
        raise RobotsDisallowed(f"robots.txt disallows {urlsplit(url).netloc}{urlsplit(url).path} for {PRODUCT}")
    h = {"User-Agent": UA, "Accept": "application/json, text/html;q=0.9, */*;q=0.8", "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
    if headers:
        h.update(headers)
    host = urlsplit(url).netloc.lower()
    last: Exception | None = None
    for attempt in range(retries + 1):
        _be_polite(host)
        try:
            r = requests.get(url, params=params, headers=h, timeout=TIMEOUT)
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            last = e
            time.sleep(1.5 * (attempt + 1))
    assert last is not None
    raise last
