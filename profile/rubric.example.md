# Scoring rubric (example)

Copy this to `profile/rubric.md` and edit it. The scoring agent applies this file literally, so
write it as rules, not as preferences. When a grade comes out wrong, fix the rule here — do not
argue with the agent. The next morning's run picks it up.

Every rule below that starts with a date is the shape a real rule takes: it was added because a
specific posting was graded wrong on that date. Yours should read the same way. A rubric that
never grows is a rubric nobody is correcting.

## 0. Hard filters → grade C, put the reason in `hard_fail`

1. Required experience above your ceiling (set your own number; "entry" and "any" pass).
2. Required degree above yours (a *preferred* degree passes).
3. Required major outside your field (adjacent or unspecified passes).
4. Deadline is in the past.
5. Already applied — same company + same role as in your profile's application list.
6. Non-technical function (sales, marketing, HR, finance, legal, design, support, logistics).

Add your own. Hard filters are cheap and save the most time.

## 1. Score, 0-100

Give each axis a weight that sums to 100 and state what earns full marks:

| Axis | Weight | Full marks when |
|---|---|---|
| Role fit | 35 | The posting names the work you actually do |
| Eligibility | 25 | You clear every stated requirement with room to spare |
| Company tier | 20 | Matches the top of your preference order |
| Timing | 10 | Deadline far enough out to prepare properly |
| Upside | 10 | Brand, growth, or learning you would take a pay cut for |

## 2. Grades

- **A** — start preparing an application today.
- **B** — worth reading, decide later.
- **C** — excluded; `hard_fail` says why.

Set the numeric cutoffs yourself, and cap grades where you have a standing doubt. A cap is more
honest than a low score: "B ceiling until the hiring structure is confirmed."

## 3. `scope` classification

Tag each posting so the digest can group it: new grad, experienced, contract, internship,
contest/hackathon, and so on. Order matters — put the tag you act on first.

## 4. Writing `reason`

One or two sentences, in this order: why it scored what it did, then the single biggest risk,
then what would raise the grade. "Confirmed X → A" is more useful than a paragraph of praise.

## 5. Role gates

The strongest rule in practice: **if a posting lists its open roles, and none of them is yours,
it is a C — no matter how good the company is.** Most bad grades come from scoring the company
instead of the role.

## 6. When information is missing

Never guess in the candidate's favour. Grade on what the posting actually says, cap the grade,
and write in `reason` exactly which fact would settle it. A B with "confirm headcount for the
data track → A" is actionable; an optimistic A is not.

## 7. Contests and hackathons

Score by deadline distance and whether entering is compatible with your week, not by prize size.
