# job-radar

A daily job search that runs itself: GitHub Actions scrapes the boards, a scheduled Claude Code
routine grades every posting against **your** rubric, and you get one email with the three
postings worth your morning — instead of ninety you will not read.

It covers the **Korean job market** (사람인, 원티드, 점핏, 링커리어, 네이버, 라인, 우아한형제들,
카카오·프로그래머스 alert mail) alongside the global ATS boards (Greenhouse, Ashby, Lever) and
new-grad lists. If you are job hunting in Korea, this is the part other tools do not have.

> **Warning, read this first.** The pipeline commits what it collects — including which postings
> you were graded on and which you approved. **Keep your fork private.** `profile/profile.md`,
> `profile/rubric.md` and `profile/corpus/` are gitignored so your résumé never lands in a public
> repo by accident, but the daily data is not.

## What it actually does

```
04:00  GitHub Actions   collect      12 collectors → data/candidates/<date>.json
08:30  Claude routine   score        your rubric → A / B / C, one line of reasoning each
       .                finalize     RADAR.md + one email + tracker rows
       .
       YOU              approve      flip a row to "지원예정" in the tracker
       .
22:00  Claude routine   apply-draft  writes a full application package for approved rows only
```

Two stages, and the split is the point. **Stage 1 never applies to anything.** It reads, grades,
and reports. Stage 2 only touches postings you approved by hand, and it still does not submit —
it writes the package and leaves the submitting to you.

## Why it is split across a runner and a routine

The scheduled agent sandbox has no outbound network access to job sites, so it cannot scrape.
The Actions runner can. So collection runs on Actions and scoring runs in the agent, and they
meet in a committed JSON file. `prompts/daily.md` documents the failure modes this produced —
including the day an empty committed file convinced the collector it had already run, and quietly
emptied the digest.

## Setup

```bash
pip install -e .
cp profile/profile.example.md profile/profile.md    # rewrite as yourself
cp profile/rubric.example.md  profile/rubric.md     # your hard filters and weights
python -m radar.collect                             # → data/candidates/<date>.json
pytest -q
```

Then register `prompts/daily.md` as a scheduled Claude Code routine (replace every
`<PLACEHOLDER>`), point it at your fork, and give it a mail connector. `prompts/apply.md` is the
optional stage-2 routine.

## The two files that decide everything

Everything else is plumbing. These two are the product:

- **`profile/profile.md`** — who you are, and specifically **what you are not**. Leave your
  weaknesses out and the scorer will hand you an A for a hardware role because it says "engineer".
- **`profile/rubric.md`** — hard filters, weights, grade cutoffs. When a grade comes out wrong,
  you edit this file, not the code, and tomorrow's run obeys. Every rule in the example started
  as one badly-graded posting.

## Adding a source

Write `radar/collectors/<name>.py` with `fetch()` and `parse()`, register it in
`radar/collectors/__init__.py`, drop a sample response in `tests/fixtures/`, and add one test.
Parsers are tested against saved fixtures, so a site redesign fails loudly in CI instead of
silently returning zero postings.

## Layout

| Path | What |
|---|---|
| `radar/collectors/` | 12 source parsers — 7 Korean boards, Greenhouse/Ashby/Lever across 22 company boards, new-grad lists, contests |
| `radar/prefilter.py` | drops the obvious noise before anything is scored |
| `radar/enrich.py`, `jd.py` | pulls the full posting text for shortlisted rows |
| `radar/deadlines.py` | your own fixed deadlines, merged into the digest |
| `radar/finalize.py` | dedupe, `RADAR.md`, email HTML, tracker payload |
| `prompts/` | the two routine prompts |
| `.github/workflows/` | `collect`, `jd-fetch`, `test` |

## 한국어

한국 채용 사이트를 매일 긁어서 **내 기준표대로** A/B/C 채점한 뒤, 아침에 메일 한 통으로 받는
파이프라인입니다. 90건을 훑는 대신 3건만 봅니다.

1단계는 **절대 지원하지 않습니다.** 읽고, 채점하고, 보고만 합니다. 내가 추적판에서 "지원예정"으로
바꾼 공고에 한해 2단계가 밤에 지원서 패키지를 씁니다. 제출도 사람이 합니다.

`profile/profile.md`(내 프로필)와 `profile/rubric.md`(채점표) 두 개가 전부입니다. 등급이 틀리면
코드가 아니라 `rubric.md`를 고치면 다음 날부터 반영됩니다.

**포크는 비공개로 두세요.** 수집 결과가 커밋되기 때문에, 공개 포크는 내 구직 활동을 공개하는 것과
같습니다. 프로필·이력서·지원서는 `.gitignore`로 막아 뒀습니다.

## License

MIT.
