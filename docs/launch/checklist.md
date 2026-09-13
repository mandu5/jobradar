# Launch checklist — jobradar

## Pre-launch gates

- [x] Public repo, MIT license file present (GitHub shows the badge).
- [x] CI green on `main` (`test` workflow).
- [x] Topics set; description set; issues enabled.
- [x] No personal data in the tree or history (fresh repo, 2 commits; 84 files swept).
- [x] `collect` cron off by default (a public fork would commit scraped data daily).
- [x] README numbers match the code (12 collectors, 08:30 KST scoring).
- [x] Fresh clone of the *public* repo installs and passes (author, 2026-09-12: 79 passed;
      `collect --only saramin,jumpit` → 182 collected, 102 kept, 0 failures).
- [ ] A second person has run `pip install -e . && pytest -q` on their machine.
- [ ] A second person has run `python -m radar.collect --only saramin,jumpit` and got postings.
      Ask text in `smoke-test-request.md`; the test needs no profile and no login.

## Channels, in order

1. **GeekNews** — 2026-09-13 or later. Verified 09-12 16:22 KST: `/write` is gated with
   "가입 후 일주일이 지나야 작성할 수 있습니다" (joined 09-06). `geeknews.md` has the form
   fields, the title convention (the site prepends "Show GN:" — do not type it), and the body
   rewritten to the site's guidelines (no-signup try path first, reproducible numbers, Show
   type). Primary channel: the Korean-board coverage is the differentiator and the audience is
   here. First comment within ten minutes. Four hours on the thread.
2. **Show HN** — posted early (Sun 09-13) and auto-flagged; see Log. Waiting on hn@ycombinator.com.
   If unflagged: post the limitations comment immediately. If not: a new account cannot Show HN
   cold — build karma with ordinary comments for 2-3 weeks, then retry in a Tue-Thu 14:00 UTC slot.
3. **r/ClaudeAI** — the day after HN. `reddit-discussions.md`.
4. **anthropics/claude-code Discussions** — Show and Tell, same day as Reddit.
5. **awesome-claude-code** — not before the repo is 14 days old (2026-09-26) or has 100 stars.
   Web issue form, filled by a human, one-line factual description.

## Log

- **2026-09-13 12:20 KST — GeekNews posted.** https://news.hada.io/topic?id=33610 (Show GN,
  title 1). First comment (rubric order + "cap the grade, name the fact that lifts it") at
  12:22, cid65367. Site prepends "Show GN:" and the domain itself. The human-verification
  checkbox must be clicked by a person; the 등록 button stays disabled until then.
- T+0 snapshot: 0 stars, 0 forks, 0 views (GitHub traffic lags ~1h).
- **2026-09-13 12:31 KST (Sun 03:31 UTC) — Show HN posted and auto-flagged within a minute.**
  https://news.ycombinator.com/item?id=49679841, title "Show HN: Job search agent that grades
  postings by your rubric and never applies" (79 chars; the draft's title 1 was 86 and would
  have been cut at 80). API shows `dead: true`. Cause: brand-new account (mandu00005, karma 1,
  first submission) — HN's new-account filter, not human flags. Comment box is gone, so the
  limitations comment could not be posted. Posted off-schedule (Sunday, not the Tuesday slot)
  at the author's call. Remedy: email hn@ycombinator.com asking for a manual unflag (draft in
  Gmail); do NOT resubmit. Lesson for the checklist: a Show HN from a new account needs either
  prior karma (a few weeks of ordinary comments) or a heads-up to the mods first.

## Measure

Baseline at publish (2026-09-12): 0 stars, 0 forks, 0 views. Snapshot `gh api
repos/mandu5/jobradar/traffic/views` daily after each channel; attribute by day, not by feeling.

## After

- Every reported collector failure becomes an issue the same day, with the fixture that
  reproduces it.
- If someone posts their own rubric, ask to link it from `profile/` as a second example.
- Requests for auto-apply: answer with the design reason, do not add it.
