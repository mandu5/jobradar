# r/ClaudeAI and anthropics/claude-code Discussions

Post after Show HN, not before — link the HN thread if it did well, don't mention it if it didn't.

## r/ClaudeAI

**Title:** I run my job search as a scheduled Claude Code routine. The rubric is the whole product.

**Body:**

Sharing the setup, not selling anything — it's MIT on GitHub.

Every morning GitHub Actions scrapes 12 job sources and commits a JSON file. A scheduled Claude
Code routine then reads two markdown files — `profile.md` (who I am, and specifically what I'm
*not*) and `rubric.md` (hard filters, weights, grade cutoffs) — and grades every posting A/B/C
with one line of reasoning. I get one email.

Three things I learned that might save you a week:

1. **The routine sandbox has no egress to job sites.** It can't scrape. Actions can. So they're
   split, and they meet in a committed file. The failure mode: an empty committed file looks like
   a finished run. Check for actual content before skipping.
2. **Batch the scoring.** One posting per turn is slow and expensive; the whole file at once
   overflows the context and the tail gets graded carelessly. Thirty at a time, appended to a
   JSONL, then a coverage check that counts missing keys. Silently dropping the last batch looks
   exactly like a quiet day.
3. **Make it unable to apply.** Stage one only grades. Stage two only touches postings I flipped
   to "approved" by hand, and it still doesn't submit. Not a safety-theater thing — an agent that
   both finds and applies will eventually apply somewhere you wouldn't have.

The rubric example in the repo is a template. Every rule in mine came from one posting that was
graded wrong. When a grade is wrong you edit the rubric, not the code.

Repo: https://github.com/mandu5/jobradar — Korean boards + Greenhouse/Ashby/Lever. Fork it
*private*; the pipeline commits what it collects.

## anthropics/claude-code Discussions — Show and Tell

**Title:** jobradar: a two-stage job search (Actions collects, a routine grades, a human approves)

**Body:** Same as Reddit, trimmed, plus one direct question for the maintainers:

> The routine sandbox blocks egress to nearly every site, which is why collection has to live in
> Actions. Is there a supported way to declare a small allowlist per routine? `user_declared_urls`
> in the event payload didn't grant egress in my tests (2026-09-10). If it's intentional, the
> split-and-meet-in-a-file pattern in this repo is a workable answer, and I'd document it as such.
