# Factory blueprint

Why the engine is built this way, and what each control is actually defending
against.

## The design rule

**No step approves its own work.** Producers live in `stages/` and write files.
Approvers live in `gates/` and read those files back off disk. A gate never sees
a producer's in-memory objects, and the module that measures a PDF
(`pdfinspect.py`) deliberately does not import the module that wrote it. If both
sides shared a library, a bug in that library would pass its own inspection.

The second rule follows from the first: **a gate can stop the line.** Any P0
halts the build, writes `BUILD_HALTED.md`, and produces nothing downstream.
There is no override flag. `--keep-going` is a diagnostic mode and the run state
it writes still says the build did not complete.

## The stages

**G0 intake.** Validates the spec, resolves the lane, freezes the inputs, and
fingerprints them. The fingerprint appears on the approval sheet, so "approved"
refers to a specific set of inputs rather than a title.

**G1 blueprint.** Word budgets, page estimate, and a first pass at the money. A
title that cannot clear its printing cost dies here rather than after the
manuscript is written.

**G3 manuscript.** Reads authored unit files, checks each one against the
architecture (title drift between spec and file is an error), and parses the A2A
markdown dialect into a typed block stream. If files are missing, it writes one
authoring pack per missing unit and stops.

**G5 interior.** Renders the print-ready PDF. Margins depend on page count and
page count depends on margins, so the stage iterates until the gutter band it
used is the band the finished book needs. Two passes per attempt: the first
finds where each unit lands, the second prints the real page numbers in the
contents. Front and back matter are generated from the lane profile, never
hand-maintained per title. The page count is padded to an even leaf.

**G7 cover.** Reads the interior's page count *from disk* and builds the wrap at
the exact trim, bleed and spine. Two files come out: the production wrap and a
proof with trim, spine and safe-zone guides drawn on it, plus an art brief
carrying the exact pixel dimensions for whoever does the artwork.

**G9 listing.** Assembles the listing deterministically. Keywords are filtered
and chosen by code (too long, duplicated, already in the title, or containing a
term KDP disallows), and the rejections are recorded with reasons.

**G11 compliance.** Builds the ledgers: sources, declared claims, claims
detected in the finished manuscript, stories with provenance, AI origin per
component, and a decision ledger recording what the engine chose and why.

**G13 package.** Manifest with a SHA-256 for every artifact, the KDP upload
order, and the approval sheet.

## The gates

**structure.** Overlapping units (the same argument twice), page count outside
KDP bounds, a thesis too vague to write against, a royalty too thin to fund
anything.

**substance.** The one that matters. Per unit: word floor and ceiling, required
sections present, concrete-marker density, placeholders. Across the book:
concrete density, near-duplicate paragraphs, filler density, sentence-length
variance, repeated sentence openings, em dashes.

**interior_spec.** Measured from the file: page count against what the builder
claimed, even parity, uniform page size, trim to within 0.01 in, embedded fonts
with no base-14 fallbacks, live extractable text, and a probe that pulls
sentences from the approved manuscript back out of the PDF to prove the file
holds the draft that cleared the substance gate.

**cover_spec.** Recomputes the geometry from the interior's page count rather
than trusting the cover stage, then measures the written file. Spine mismatch,
stale page count, multi-page wrap, wrong wrap size, illegal spine text.

**listing.** Amazon's limits, exactly seven keywords, three categories, banned
claim language, price against the printing-cost floor, and a refusal to price
off an unverified rate band.

**compliance.** Per lane: source ledger present, declared claims resolving to
sources, risky sentences in the manuscript tracked, story provenance stated,
AI origin resolved for text, images and translation, professional review on
file where the lane requires it, scripture translation public domain or licensed.

## How the prose measurements work

Padding is fluent. It passes a spell check, it passes a grammar check, and it
reads fine for two paragraphs. What it cannot do is be about something.

- **Concrete-marker density.** Markers per 100 words: digits, counting words,
  time and measurement units, named equipment, and somebody doing something.
  Scripture citations and filler phrases are stripped before measuring, and
  quoted anchor lines are excluded, because a citation carries digits and "at
  the end of the day" carries a time word without either one saying anything.
  Calibration: known-abstract devotional and leadership prose scores **0.00**.
  The padded fixture scores **0.97**. The pilot averages **3.11**, lowest entry
  **1.45**. Lane floors sit at 2.0 (devotional), 2.5 (doctrine), 3.5 (technical),
  1.5 (practice), with the per-unit floor at 60% of the book floor.
- **Near-duplicate paragraphs.** Jaccard similarity over content tokens, with a
  token index so it does not go quadratic. Reported as the share of paragraphs
  caught in at least one pair. The padded fixture: 55%. The pilot: 0%.
- **Filler density.** A list of phrases that occupy space without carrying
  information, counted per thousand words.
- **Sentence-length variance and repeated openings.** Low variance and the same
  three-word opening over and over is the signature of generated prose.

These are proxies and they are honest about it. They cannot tell you whether a
chapter is good. They can tell you, reliably, whether it is empty, and empty is
the failure mode that a publishing line at volume actually has.

## Evidence control

Four ledgers, enforced by lane.

- **Source ledger.** Id, citation, url, access date, type.
- **Claim ledger.** Declared claims with a source id and a status. Separately,
  the engine scans the finished manuscript for sentences carrying a dollar
  figure, a percentage, a quantity, an appeal to research, an absolute, or a
  named authority, and matches them to inline `[c:some-id]` tags. In the
  technical and doctrine lanes an untracked claim is a P0; in the devotional
  lane it is advisory.
- **Story ledger.** Every story is first-hand, composite, or sourced. A story
  with no provenance is a P0 in every lane. A fabricated operational story is
  the one mistake this brand does not survive.
- **AI origin.** Text, images, translation, each one `ai-generated`,
  `ai-assisted`, or `none`. Unresolved is a P0. The answer drives the KDP
  disclosure sheet and the copyright page statement.

## Money

Everything comes from `factory/rates/kdp_rates_<version>.json`: paper calipers,
spine allowance, bleed, gutter bands, page limits, print cost bands, royalty
rate. Each print-cost band carries a confidence flag, and a band marked
unverified **refuses to produce a price** unless the caller explicitly asks for
a scratch estimate. Rates change; the table is dated and versioned so any build
can be reproduced against the numbers that were true when it ran.

The approval sheet carries the print cost, the floor, the list price, the
royalty per copy, the break-even unit count, and an instruction to confirm the
printing cost inside KDP title setup before publishing.

## Where it ends

`07_package/APPROVAL_REQUIRED.md`. Gate results, the money, every P1 still
outstanding, and a checklist of the things no engine can do: read three pages at
random and ask whether it sounds like you, look at the cover proof, shrink the
front cover to 160 px and see whether the title still reads.

Then a signature line with the build fingerprint and the rate table version
under it.
