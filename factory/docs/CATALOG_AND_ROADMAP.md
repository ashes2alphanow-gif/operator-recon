# Catalogue and 90-day roadmap

## Standing assumption, flagged

The titles below come from what Chris has named in conversation, not from
reading his project folders, which are not in this repository. Stage, word
count and completeness for everything except the pilot are **assumptions**.
Correct them and this document becomes accurate; until then treat the lane
assignments as the useful part and the status column as a guess.

## The catalogue, by lane

| title | lane | why that lane | what it needs before a build |
| --- | --- | --- | --- |
| FORGED | doctrine | argued transformation, elevated claim risk | unit list with non-overlapping theses; story provenance for every anecdote |
| Battlefield Relationships | doctrine | same, plus other people's stories | consent recorded for any story not Chris's |
| Smarter Than You Think | doctrine | argument about capability | source ledger; this lane's claims get cited |
| What Your Dad Didn't Teach You About Money | **technical** | money = high claim risk | source ledger, claim ledger, **named licensed reviewer**, worked examples |
| Survival Is a Decision | **technical** | physical safety = high claim risk | same, plus a reviewer qualified in the subject |
| The Healing Games | practice | reader does the work; grief and trauma | **clinician review**, crisis resources in the front matter |
| A Warrior's Code of Prayer | devotional | short-form daily | scripture verified against a public domain text |
| Unbreakable | devotional / legacy | father-to-son | story provenance |

The two technical titles are the ones that can hurt somebody or draw a
complaint. The engine will not let either finish without a named reviewer, and
that is not negotiable in code.

## The arithmetic nobody enjoys

The pilot is a good paperback: $13.99 list, $2.30 print, **$6.09 a copy**.

$100,000 of income at $6.09 a copy is **16,420 copies**. Across eight titles
that is a little over 2,000 copies each, which is a strong result for an unknown
indie nonfiction title and is not a plan you can schedule.

The same $100,000 is:

- **1,000 toolkit sales at $99**, with no printing cost at all, or
- **250 institutional or unit licences at $400**, or
- **35 training blocks at $2,850**, which is the one that uses the thing Chris
  actually has that nobody can buy.

So the paperback is the front door, not the business. Every title in the
catalogue should ship with the companion designed at the same time, and the book
should carry a real working URL to it. That is what `companion_products` in the
spec and `prompts/06-companion-product.md` are for.

State it once and move on: a catalogue of eight paperbacks with no companions is
a hobby with good production values.

## 90 days

The constraint is Chris's hours, not the engine's throughput. The engine can
build a title in under a minute once the manuscript exists. Writing is the
bottleneck, and so is review.

### Days 1-30: prove the line on something already written

Pick the title closest to a finished draft (assumption: **Battlefield
Relationships**) and put it through the factory as-is.

1. Write the spec. Unit list with real theses.
2. Drop the existing draft into `factory/manuscripts/<slug>/`, one file per
   chapter, in the markdown dialect.
3. Run the build and let the substance gate tell you what is thin. Expect it to
   find things. That is the point.
4. Fix, rebuild, get to a passing run and an approval sheet.
5. Design the companion before you publish, not after.

Deliverable at day 30: one title with a signed approval sheet and a companion
specified.

### Days 31-60: the technical lane, properly

**What Your Dad Didn't Teach You About Money** is the flagship and it is also
the highest-risk thing in the catalogue. Do it second, while the line is proven
but before the habit of moving fast has set in.

1. Build the source ledger first. Every figure, every threshold, every rule, with
   a citation and an access date.
2. Tag every claim in the manuscript as `[c:some-id]`.
3. Name the licensed reviewer and get a date on the calendar. The compliance
   gate will not pass without a reviewer and a date recorded.
4. Build the toolkit alongside the book, and version them together.

Deliverable at day 60: the book at a passing build, held at the approval sheet
pending the reviewer.

### Days 61-90: the second lane and the institutional test

1. Take one devotional or practice title through, because those lanes are cheap
   to produce and they keep the catalogue moving while the technical title sits
   in review.
2. Run one institutional conversation. One agency, one academy, one peer support
   programme. Ask what a bulk or licensed version would have to contain. That
   conversation is worth more than the next three titles.

Deliverable at day 90: three titles through the line, one companion shipped, one
institutional conversation with a real answer in it.

## What stays queued

Everything else. Not because Chris cannot run parallel tracks, but because the
review burden on the technical lane is the actual constraint and it does not
parallelise. Queue order is his call; the engine does not care and will build
whatever has a spec and a manuscript.

## Recurring

- **Re-verify the rate table** before any pricing decision. `factory/rates/`
  is dated and the bands carry confidence flags for a reason.
- **Re-run every passing build** after any engine change. The gates move; a
  title that passed in September is not certified forever. The manifest carries
  the fingerprint and the rate table version so you can tell what it passed
  against.
