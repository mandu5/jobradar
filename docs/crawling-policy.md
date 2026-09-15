# Crawling policy

jobradar identifies itself and obeys `robots.txt`. This is how, not a promise layered on top of
the code — `radar/http.py` is the enforcement point every collector goes through.

- **Identified User-Agent.** Every request sends `jobradar/<version> (+https://github.com/mandu5/jobradar)`,
  so a site owner looking at their logs can tell what hit them and where to complain.
- **`robots.txt` honored per RFC 9309**, `*` and `$` wildcards included, checked before every
  request (not once at startup). A disallowed endpoint is skipped, not fetched — the collector
  raises `RobotsDisallowed` and `collect.py` reports it as a failure line instead of silently
  returning zero postings.
- **Unreachable `robots.txt` means do not fetch.** A 5xx or network error is treated as
  disallow-all for that host, not as "no policy found." Only a 4xx (no `robots.txt` published) is
  treated as unrestricted.
- **At least 1 second between requests to the same host**, enforced per host, not globally.
- **Only public listing and detail pages.** jobradar never fetches a page behind a login wall,
  and never touches applicant or personal data — it reads what a browser would see logged out.
- **Results are cached per day** in `data/candidates/<date>.json`; the default schedule is one
  collection run per day, not continuous polling.

## Sources removed on 2026-09-15

Two collectors were removed because their host's `robots.txt` disallows the endpoints they used:

- **LinkedIn** (`radar/collectors/linkedin.py`, unofficial `jobs-guest` API): `linkedin.com/robots.txt`
  has `User-agent: *` / `Disallow: /`.
- **우아한형제들 (Woowa Brothers)** (`radar/collectors/woowa.py`, `career.woowahan.com/w1/recruits`):
  `career.woowahan.com/robots.txt` has `Disallow: /w1/**`.

All other sources in `radar/collectors/` are allowed by their host's `robots.txt` as of the same
date.

## Asking for removal

If you run a site jobradar collects from and want it excluded, open an issue at
[github.com/mandu5/jobradar/issues](https://github.com/mandu5/jobradar/issues).

---

## 한국어

jobradar는 신원이 드러나는 User-Agent(`jobradar/<version> (+https://github.com/mandu5/jobradar)`)로
요청하고, RFC 9309 기준으로 `robots.txt`(`*`, `$` 와일드카드 포함)를 매 요청마다 확인합니다. 금지된
엔드포인트는 건너뛰고 실패로 보고하며, `robots.txt`에 접근할 수 없으면(5xx·네트워크 오류) 전체 금지로
간주해 아예 요청하지 않습니다. 같은 호스트로는 최소 1초 간격을 둡니다. 로그인 없이 보이는 공개
목록·상세 페이지만 읽고, 지원자·개인정보는 절대 건드리지 않습니다. 결과는 하루 단위로 캐시되며 기본
실행 주기는 하루 한 번입니다. 2026-09-15에 LinkedIn(`Disallow: /`)과 우아한형제들
(`Disallow: /w1/**`) 수집기를 이 정책에 따라 제거했습니다. 사이트 운영자로서 제외를 요청하려면
[이슈](https://github.com/mandu5/jobradar/issues)를 열어주세요.
