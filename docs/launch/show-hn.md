# Show HN draft — jobradar

Tuesday–Thursday, 14:00–16:00 UTC (23:00–01:00 KST). Earliest slot: **Tue 2026-09-15**.
HN does not care about Korean job boards. The hook here is the design and the operational story.

## Title candidates (pick one)

1. Show HN: A job search agent that grades postings against your rubric and never applies
2. Show HN: jobradar – GitHub Actions scrapes the boards, a Claude routine grades them, you get one email
3. Show HN: I split my job-search agent in two so it can't apply to anything by itself

Recommended: **1**. The "never applies" is the differentiator against every other agentic job tool.

## Body

`jobradar` runs my job search every morning without me. GitHub Actions scrapes 12 sources at
04:00, a scheduled Claude Code routine grades every posting against a rubric I wrote, and I get
one email with the three postings worth reading instead of the ninety I would not.

The part I care most about is what it refuses to do. Stage one **never applies to anything** —
it reads, grades, and reports. Stage two only touches postings I approved by hand in a tracker,
and even then it writes the application package and stops; I submit. An agent that both finds
and applies will eventually apply somewhere you would not have, and you will find out from the
recruiter.

Two engineering things that were not obvious going in:

- The scheduled-agent sandbox has no outbound network access to job sites, so it cannot scrape.
  The Actions runner can. So collection runs on Actions and scoring runs in the agent, and they
  meet in a committed JSON file. That split produced its own failure mode: the day the routine
  ran first, found nothing, and committed an *empty* file, the collector read that as "already
  done today" and the digest went out blank. The workflow now checks that the file actually
  holds postings before it skips.
- The scoring rubric is a markdown file, and it is the whole product. When a grade is wrong you
  edit the rubric, not the code, and tomorrow's run obeys. Every rule in the shipped example was
  added because one specific posting was graded wrong. The single strongest rule turned out to
  be boring: if a posting lists its open roles and none of them is yours, it is a C no matter how
  good the company is. Most bad grades came from scoring the company instead of the role.

It covers the Korean market (사람인, 원티드, 점핏, and others) plus Greenhouse/Ashby/Lever boards,
because that is my search. Adding a source is one parser file, one fixture, one test.

## Prepared first comment (limitations)

Author here. What it does not do, plainly:

- **It needs a scheduled Claude Code routine**, which means an Anthropic subscription. The
  collectors and the finalizer run anywhere, but the grading step is an agent reading a markdown
  rubric. I have not tried it with another model.
- **The collectors are Korea-heavy.** Seven of twelve are Korean boards. The global coverage is
  Greenhouse/Ashby/Lever boards you list in `config.py`, plus one new-grad aggregator.
- **One board blocks datacenter IPs.** 원티드 returns 403 from GitHub Actions; it only works from
  a residential connection.
- **Grade quality is exactly rubric quality.** A vague profile yields vague grades. The example
  rubric is a template, not a good rubric; a good one is the accumulated residue of your own
  mis-graded postings.
- **Parsers break on redesigns.** They are tested against saved fixtures, so a redesign fails CI
  loudly rather than returning zero postings quietly — but you still have to fix it.
- **The pipeline commits what it collects.** Fork it private, or your job search is public.
  `profile/` is gitignored; the daily data is not.
- **No auto-apply, on purpose.** I will take issues about the grading, not about that.

## Timing

Running for me daily since 2026-09-06. Post Tuesday 2026-09-15 at 23:00 KST, first comment within
ten minutes, stay on the thread four hours.
