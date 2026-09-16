# Pilot run - A Warrior's Code of Prayer, Volume I: Standing Post

End-to-end proof that the line works, run 2026-09-16 on this repository.

## What was produced

| | |
| --- | --- |
| Entries | 40 |
| Words | 16,302 |
| Pages | 96 (even, 5.5 x 8.5 in, cream) |
| Words per page, actual | 169.8 |
| Gutter / outer margins | 0.5 in / 0.625 in |
| Spine | 0.3000 in |
| Cover wrap | 11.5500 x 8.7500 in |
| Print cost | $2.30 (flat tier, <= 108 pages) |
| KDP price floor | $3.84 |
| List price | $13.99 |
| Royalty | $6.09 a copy |
| Break-even on $150 | 25 copies |
| Artifacts | 23 files, each hashed in the manifest |

Files: `output/warriors-code-of-prayer-v1/`.

## The gates did their job

The first run **failed**, and it failed on something real.

```
substance gate: FAIL (P0 2, P1 1, P2 5)
  abstract-unit  entry 7  'The Radio Goes Quiet'   0.78 markers/100w
  abstract-unit  entry 37 'The Man at the Funeral' 0.25 markers/100w
  filler                  'in order to'
```

Both entries were fluent and both were about nothing you could put your hands
on. Entry 7 talked about silence without a radio, a channel, or an hour in it.
Entry 37 talked about attendance without a uniform, a drive time, or a number.
Both were rewritten with the specifics that should have been there the first
time. The original halt report is kept at
`factory/docs/evidence/run-01-substance-gate-FAIL.md`.

That is the whole point of the thing. A human editor reading forty entries in
one sitting would have let both through.

## Two engine defects the pilot exposed

Worth recording, because both were the measurement being wrong rather than the
writing being wrong, and the fix in each case tightened the gate rather than
loosening it.

1. **Spelled-out numbers did not count as concrete.** "four hours each way" is
   as specific as "4 hours". Adding number words raised every score, so the lane
   floors were recalibrated against known-abstract prose (which scores 0.00)
   rather than left where they were.
2. **Scripture citations and filler phrases were scoring as concrete.**
   "Psalm 46:10" carries digits and "at the end of the day" carries a time word.
   Both are now stripped before the measurement, and quoted anchor lines are
   excluded from the author's own word count. After the fix, the padded fixture
   scores 0.99 and the pilot averages 3.11.

## The padded fixture

`factory/specs/_fixture-padded.yml` is a deliberately padded twenty-entry book:
abstract prose, recycled paragraphs, stock filler, a placeholder nobody filled
in, missing drills. It exists so the gate can be proven to still bite.

```
structure gate: PASS
substance gate: FAIL (P0 45)
  thin-unit x20, abstract-unit x17, missing-section x4, abstract-book,
  repetition (46 of 83 paragraphs, 55%, in 395 near-duplicate pairs),
  filler (100 hits), placeholder x1
BUILD HALTED at substance. Nothing downstream was built.
```

The regression suite asserts this book never builds. If a future change lets it
through, the tests fail.

## What the gates still want (P1 and P2 on the passing run)

- **P2 flat-tier-headroom.** 12 more pages would cost nothing to print; anything
  up to 108 pages prints at the same flat $2.30.
- **P2 spine-blank.** At 96 pages the spine carries no text. The house threshold
  is 100 pages. Twelve free pages would clear it, so the book is four pages of
  real material away from a spine that is visible on a shelf.
- **P2 repeated-opening x5.** "That is the..." opens 17 sentences, "it is a..."
  14, "it is the..." 14. A real tic across 16,000 words.
- **P2 untracked-claim x25.** Low-risk lane, so advisory. In the technical lane
  every one of these would be a P0.
- **Scripture verification is not done.** The quotations are World English Bible,
  which is public domain, but they were typed from memory and have not been
  checked against a WEB text. That is on the approval sheet and it is a
  do-not-publish item.

## The honest part

The 16,302 words were produced by the engine's authoring layer, not by Chris.
`compliance.ai_origin.text` is set to `ai-generated`, which means:

- the KDP AI content question gets answered **yes** for text
- the copyright page carries the matching statement
- the disclosure sheet at `06_compliance/kdp_disclosure.md` says so

If Chris rewrites it in his own hand, that field becomes `ai-assisted` and both
the disclosure and the copyright page change with it. The factory records the
decision. It does not help anybody hide it.

Treat this volume as a structural draft that proves the line, and as a real
candidate if Chris wants to take a voice pass through it.
