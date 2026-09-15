# jobradar

A job search that runs inside Claude Code. It collects postings from Korean and global job
boards, grades every one of them A/B/C against a rubric **you** wrote, and hands you the three
worth reading instead of the ninety you would not. **It never applies for you.**

[한국어](README.ko.md)

![jobradar demo: collect from 사람인 and 점핏, then the graded RADAR.md](docs/demo.gif)

## Install

In Claude Code:

```
/plugin marketplace add mandu5/jobradar
/plugin install jobradar@jobradar
```

Or, for Claude Code and other agents (Codex, Cursor, …) via the skills CLI:

```
npx skills add mandu5/jobradar
```

Then, in a checkout of this repo (`git clone https://github.com/mandu5/jobradar && cd jobradar && pip install -e .`):

```
/jobradar setup    # five questions → profile/profile.md + profile/rubric.md
/jobradar today    # collect, grade, write RADAR.md
```

Python 3.10+ and one dependency (`requests`). No accounts, no API keys, nothing to sign up for.
Everything runs on your machine, so 원티드 — which blocks datacenter IPs — works here.

Want to try the collector before installing anything into Claude Code?

```
python -m radar.collect --only saramin,jumpit
```

## What it does

```
/jobradar setup    five questions: roles (and non-roles), experience rule, location,
                   company-type order, what you optimize for → profile + rubric
/jobradar scan     10 collectors → data/candidates/<today>.json      (network only)
/jobradar grade    rubric → A / B / C, one line of reasoning each → RADAR.md
/jobradar today    scan, then grade
```

Sources: 사람인, 원티드, 점핏, 링커리어, 네이버, 라인, Greenhouse / Ashby / Lever boards you list in
`radar/config.py` (당근, 쿠팡, Anthropic, OpenAI, Stripe … 22 shipped), a new-grad aggregator, and
contests. See [crawling policy](docs/crawling-policy.md) for what it fetches and how.

## What it will not do

Stage one — everything above — **never applies to anything.** It reads, grades, and reports.
There is an optional stage two (`prompts/apply.md`) that drafts an application package, and it
only runs for postings you approved by hand in a tracker, and it still does not submit; you do.
An agent that both finds and applies will eventually apply somewhere you would not have, and
you will find out from the recruiter.

## The two files that decide everything

Everything else is plumbing. These are the product:

- **`profile/profile.md`** — who you are, and specifically **what you are not**. Leave your
  weaknesses out and the scorer will hand you an A for a hardware role because it says "engineer".
- **`profile/rubric.md`** — hard filters, weights, grade cutoffs. When a grade comes out wrong,
  you edit this file, not the code, and the next `grade` obeys. Every rule in the example
  started as one badly-graded posting. The strongest one is boring: *if a posting lists its open
  roles and none of them is yours, it is a C no matter how good the company is.* And the most
  useful one: *when information is missing, don't guess in your favour — cap the grade and name
  the fact that would lift it.* A B that says "confirm the data track headcount → A" is
  actionable; an optimistic A is not.

Both files are gitignored, so they never end up in a public fork.

## Unattended mode

If you want it to run every morning without you, the same engine runs as two pieces:

```
04:00  GitHub Actions   collect        .github/workflows/collect.yml  (cron commented out)
08:30  Claude routine   grade+finalize prompts/daily.md
22:00  Claude routine   apply-draft    prompts/apply.md   (only for rows you approved)
```

Why split: the scheduled-agent sandbox has no outbound network access to job sites, so it cannot
scrape. The Actions runner can. They meet in a committed JSON file. `prompts/daily.md` documents
the failure modes that split produced — including the day an empty committed file convinced the
collector it had already run, and the digest went out blank.

> **If you run unattended, keep your fork private.** The pipeline commits what it collects,
> including which postings you were graded on. `profile/` is gitignored; the daily data is not.

## Hired with jobradar

No stories yet — the author is the first user, and is mid-search. When jobradar's shortlist
turns into an offer for you, open a [취업했어요 / I got hired](https://github.com/mandu5/jobradar/issues/new?template=i-got-hired.yml)
issue. You don't have to name the company. What we want to know is which rubric rule mattered,
how many postings you graded versus applied to, and — if you're willing — your rubric with the
personal details stripped, so it can be linked here as a second example.

## Adding a source

Write `radar/collectors/<name>.py` with `fetch()` and `parse()`, register it in
`radar/collectors/__init__.py`, drop a sample response in `tests/fixtures/`, and add one test.
Parsers are tested against saved fixtures, so a site redesign fails loudly in CI instead of
silently returning zero postings. `pytest -q` — 80 tests.

## Layout

| Path | What |
|---|---|
| `skills/jobradar/SKILL.md`, `commands/jobradar.md` | the Claude Code skill and its `/jobradar` command |
| `radar/collectors/` | 10 source parsers |
| `radar/prefilter.py` | drops the obvious noise before anything is graded |
| `radar/enrich.py`, `jd.py` | pulls the full posting text for shortlisted rows |
| `radar/deadlines.py` | your own fixed deadlines, merged into the digest |
| `radar/finalize.py` | dedupe, `RADAR.md`, email HTML, tracker payload |
| `prompts/` | the two routine prompts for unattended mode |
| `.github/workflows/` | `collect`, `jd-fetch`, `test` |

## Known limits

- 원티드 returns 403 from GitHub Actions (datacenter IPs). It works from a home connection.
- Grade quality is exactly rubric quality. The shipped rubric is a template, not a good rubric.
- Grading needs Claude Code. The collectors and the finalizer run anywhere.
- Parsers break on redesigns; the fixture tests make that loud, not silent.
- No auto-apply, on purpose. Issues about grading are welcome; that one is a design decision.

## License

MIT.
