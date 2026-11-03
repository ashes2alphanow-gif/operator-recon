# Brief for ChatGPT — the A2A Publishing Factory

Paste this whole file into ChatGPT as a single message. It is written to be read
by an AI assistant that cannot see the repository, so everything it needs is in
here. Last verified against the live code on 2026-11-03.

---

## 0. How to answer

You are being brought in as a second opinion on a system that is already built,
tested, and running. You are not being asked to design it, rebuild it, or
suggest a framework. You are being asked to find what is wrong with it and what
is missing from it, in specific, actionable terms.

The operator is Chris G. Stewart. He is a U.S. Border Patrol Agent since 2007,
BORSTAR-selected in 2009, K-9 handler and instructor, SAR / tracking / human
remains detection specialist, SOG operations supervisor, Army veteran with SFAS
experience. He runs the brand **Ashes to Alpha (A2A)**.

Write to him the way you would brief a supervisor who has fifteen minutes.
Direct, high signal density, numbers before adjectives, no motivational framing,
no corporate consultant language, no "great question," no restating his request
back to him. If you think something is a bad idea, say so once, clearly, and
then give him the best version of it anyway. He owns prioritization. You do not
veto his initiatives on capacity grounds.

**Required output format** is specified in section 9. Follow it.

---

## 1. What this project is

Chris publishes nonfiction under Ashes to Alpha to Amazon KDP. The catalogue is
doctrine, transformation, guided practice, and devotional material for law
enforcement, veterans, first responders, K-9 handlers, blue-collar men, and
fathers.

He saw an online course teaching people to build a **repeatable KDP publishing
engine** rather than a single book. The reference prompt that course teaches
(reproduced in full in section 2) is aimed at low-content puzzle books. Chris
asked for the same architectural idea, built properly, for his kind of book:
books with an argument in them, written in his voice, where being wrong has
consequences.

The result is the **A2A Publishing Factory**: a Python engine in the repository
`ashes2alphanow-gif/operator-recon`, on branch
`claude/a2a-publishing-factory-rysby6`, under `factory/`.

It takes **one title spec in** and produces **a print-ready KDP package out**,
and it **refuses to finish** when the book is not good enough to publish.

---

## 2. The reference prompt that started it

This is the prompt the course teaches, verbatim from Chris's screenshots:

> I publish [BOOK TYPE] to Amazon KDP under one brand.
> I do not want you to make me a book. I want you to build a repeatable ENGINE
> that makes them, which I will run many times with different inputs.
>
> The engine must:
> 1. Take a single niche as its input
> 2. Build the complete interior to print-ready spec
> 3. Run a quality check that can FAIL the build and stop it
> 4. Generate the cover wrap at the exact trim, bleed and spine width for the
>    final page count
> 5. Produce the full listing pack: title, subtitle, description, 7 keywords,
>    3 categories, price
>
> Constraints:
> - Deterministic where it can be. Use code, not prose, for anything countable:
>   page math, spine width, content generation, file naming
> - Every stage writes real files to /output/<slug>/
> - Never let the same step both produce and approve an artifact
>
> Before you build anything: ask me every clarifying question you need about the
> book type, my quality bar, and my brand. I would rather answer fifteen
> questions now than get a beautiful engine for the wrong book.
>
> Then build it, and prove it by running it end to end on one real example while
> I watch.

The course slides add the part most people miss:

> **This is what is baked in.**
> 1. Build the interior → STOP: Substance check — padded or thin, the run halts here
> 2. Build the cover → STOP: Spec check — wrong spine or trim, the run halts here
> 3. Write the listing
> 4. Upload to KDP → STOP: Me — nothing publishes without a human looking at it
>
> **The stop points are baked into the engine, not the prompt.**

That last line is the whole thesis. A prompt that says "check quality" is a
wish. A gate that reads the finished PDF off disk and returns non-zero is a
control.

---

## 3. Chris's actual request, in full

He asked for the following, in his own words, paraphrased only to remove
dictation artifacts:

1. Study the reference prompts in depth.
2. Build something similar **for his style of books**, not puzzle books. He
   named: *FORGED*, *A Warrior's Code of Prayer*, *Battlefield Relationships*,
   *The Healing Games*, *What Your Dad Didn't Teach You About Money*, *Smarter
   Than You Think*, plus other unfinished products in his project folders.
3. He has done puzzle books before (inside *The Healing Games*) and does not
   want that lane discounted, but it is not the center of the company.
4. Research and reverse-engineer comparable commercial products, specifically
   naming **Sean Dollwet's CoAuthor.ai**.
5. Build a KDP book publishing factory at "tier one Ashes to Alpha level."
6. Stated goal, his words: *"We are going to make this business make money and
   change lives in the process."*

---

## 4. What was actually built

~3,600 lines of Python across 24 modules, plus prompt packs, docs, a dated rate
table, specs, manuscripts, and a 25-test regression suite. All tests pass.

### 4.1 The line

Producers live in `stages/`. Approvers live in `gates/`. Every stage writes real
files to `output/<slug>/`. Every gate reads those files **back off disk**. No
stage approves its own work.

```
G0  intake        resolve spec, freeze + fingerprint inputs
G1  blueprint     architecture, word budgets, page + money estimate
    GATE  structure     overlapping units, impossible page count, thin margin
G3  manuscript    assemble authored units into a typed block stream
    GATE  substance     thin / padded / repetitive / abstract / placeholders
G5  interior      print-ready PDF; margins iterate against real page count
    GATE  interior_spec measured from the file itself
G7  cover         wrap at exact trim, bleed, spine for the FINAL page count
    GATE  cover_spec    geometry re-derived independently, file measured
G9  listing       title, subtitle, description, 7 keywords, 3 categories, price
    GATE  listing       Amazon limits, claim language, price floor
G11 compliance    claim / source / story / AI-origin / decision ledgers
    GATE  compliance    evidence the lane requires
G13 package       manifest with SHA-256 per artifact, upload checklist
    STOP          human signs APPROVAL_REQUIRED.md. No publish flag exists.
```

Any **P0** finding halts the build, writes `BUILD_HALTED.md`, and produces
nothing downstream. There is no override. `--keep-going` exists for diagnostics
and the run state it writes still says the build did not complete.

### 4.2 The hard separation that matters

`stages/interior.py` and `stages/cover.py` write PDFs using **reportlab**.

`pdfinspect.py` — the module the gates use to measure those PDFs — **does not
import reportlab**. It is a from-scratch PDF reader: it parses objects, handles
ASCII85-over-Flate stream filters, counts `/Type /Page`, reads `/MediaBox`,
detects `/FontFile2` embedding, finds unembedded base-14 fonts, and rebuilds
each font's ToUnicode CMap to decode text back out of the content streams.

If both sides shared a library, a bug in that library would pass its own
inspection.

### 4.3 The four lanes

A lane is a risk-and-structure profile, not a genre. It sets the evidence
burden, the sections every unit must contain, and which gates are advisory.

| lane | titles | unit type | words/unit | required sections | claim risk | source ledger | professional review | concrete floor | repetition ceiling |
|---|---|---|---|---|---|---|---|---|---|
| `doctrine` | FORGED, Battlefield Relationships, Smarter Than You Think | chapter | 1400–4500 | opening, doctrine, drill | elevated | required | no (developmental edit) | 2.5 | 3% |
| `technical` | Money Manual, Survival Is a Decision | chapter | 1200–5000 | opening, doctrine, drill, sources | high | required | **required — licensed professional** | 3.5 | 2% |
| `practice` | The Healing Games, journals, workbooks | session | 150–1200 | prompt, practice | elevated | no | **required — clinician if trauma/grief** | 1.5 | 5% |
| `devotional` | A Warrior's Code of Prayer, Unbreakable | entry | 200–900 | anchor, body, drill, prayer | low | required | no (scripture licensing check) | 2.0 | 4% |

The technical lane will not pass the compliance gate without a named reviewer
and a date recorded in the spec. That is code, not policy.

### 4.4 The substance gate — the part that matters most

Padding is fluent. It passes spell check and grammar check and reads fine for
two paragraphs. What it cannot do is be about something. The gate measures
properties padding cannot fake.

**Concrete-marker density** — markers per 100 words. Markers are: any digit;
counting words (`two` through `thousand`, `dozen` — deliberately **excluding**
`one`, `first`, `second`, `half`, which act as pronouns and hedges far more
often than measurements); time and measurement units; named equipment (radio,
tourniquet, truck, leash, uniform, ledger, receipt, mic, battery,
channel, etc.); and somebody doing something (`he said`, `she handed`, `they
signed`).

Before measuring, the text is cleaned of two things that look concrete without
being concrete: **scripture citations** (`Psalm 46:10` carries digits) and
**filler phrases** (`at the end of the day` carries a time word). Quoted anchor
lines are excluded entirely — that is somebody else's writing.

Calibration, measured not guessed:

| corpus | density |
|---|---|
| synthetic abstract devotional prose | **0.00** |
| synthetic generic leadership prose | **0.00** |
| the deliberately padded fixture | **0.97** |
| the pilot book, average | **3.11** |
| the pilot book, lowest entry | **1.45** |

Lane floors: 2.0 devotional, 2.5 doctrine, 3.5 technical, 1.5 practice.
Per-unit floor is 60% of the book floor.

**Near-duplicate paragraphs** — Jaccard similarity over content tokens with a
token index so it does not go quadratic. Reported as the share of paragraphs
caught in at least one pair. Padded fixture: 55%. Pilot: 0%.

**Filler density** — a list of phrases that occupy space without carrying
information (`in today's world`, `at the end of the day`, `delve into`,
`tapestry`, `multifaceted`, `navigate the complexities`, `it's worth noting`,
`unleash`, `level up`, `crush it`), counted per thousand words.

**Also**: sentence-length variance (low variance over 40+ sentences flags as
machine-made), repeated three-word sentence openings, placeholders
(`[INSERT X]`, TBD, TODO, lorem ipsum), missing required sections, units under
the word floor, em dashes against house style.

### 4.5 The interior gate

Measured from the file, not from what the builder believed:

- page count in the file vs. page count the builder recorded (mismatch = P0,
  because spine width and print cost are both computed off that number)
- even page count (books print on leaves)
- uniform page size, trim within 0.01 in of spec
- every font embedded, zero unembedded base-14 fonts
- live extractable text (an image-only interior kills Look Inside and
  accessibility)
- **manuscript probe**: pulls five 7-word phrases from the draft that cleared
  the substance gate and looks for them in text extracted back out of the
  finished PDF. Proves the file on disk holds the approved manuscript. Pilot
  scores 5/5.
- **flat-tier headroom**: tells you how many more pages would cost nothing

Margins are genuinely circular — KDP's gutter minimum depends on page count,
and page count depends on margins. The interior stage iterates (max 5 attempts)
until the gutter band it used is the band the finished book actually needs, and
records the convergence history.

### 4.6 The cover gate

Recomputes the geometry **from the interior's page count on disk** rather than
trusting the cover stage's own arithmetic, then measures the written file:
spine mismatch, stale page count, multi-page wrap, wrong wrap size, illegal
spine text, unembedded fonts.

Two files come out of the cover stage: the production wrap, and a proof with
trim, spine, and safe-zone guides drawn on it plus a `NOT FOR UPLOAD` banner.
Plus a `cover_art_brief.md` with the exact pixel dimensions at 300 DPI for
whoever does the artwork. **No brand mark is auto-stamped.** Art direction is a
human decision.

### 4.7 Evidence control — four ledgers

- **Source ledger** — id, citation, url, access date, type.
- **Claim ledger** — declared claims each pointing at a source id with a status.
  Separately, the engine scans the **finished manuscript** for sentences
  carrying a dollar figure, a percentage, a quantity, an appeal to research
  (`studies show`), an absolute (`always`, `never`, `proven`), or a named
  authority (IRS, FDIC, TSP, 401k, Roth, VA, OSHA, FAA, DOT) and matches them to
  inline `[c:some-id]` tags. In doctrine and technical lanes an untracked claim
  is a **P0**. In devotional it is advisory.
- **Story ledger** — every story is first-hand, composite, or sourced. No
  provenance = P0 in every lane. A fabricated operational story is the one
  mistake this brand does not survive.
- **AI origin** — text, images, translation, each `ai-generated` /
  `ai-assisted` / `none`. Unresolved = P0. Drives the KDP disclosure sheet and
  the copyright page statement.

### 4.8 The money

Everything comes from `factory/rates/kdp_rates_2026-09.json`, a dated versioned
table: paper calipers (white 0.002252, cream 0.0025, premium color 0.002347 in
per page), spine cover allowance 0.06 in, bleed 0.125 in, cover height allowance
0.25 in, gutter bands (24–150: 0.375; 151–300: 0.5; 301–500: 0.625; 501–700:
0.75; 701–828: 0.875), page limits, print cost tiers (US B&W regular trim:
≤108 pages flat $2.30; above that $1.00 + $0.012/page), royalty 60%, minimum
list price = print cost ÷ 0.60.

**Each print-cost band carries a confidence flag. A band marked `unverified`
refuses to produce a price at all** unless the caller explicitly asks for a
scratch estimate. The color bands are currently marked unverified. The table
also records that `kdp.amazon.com` was unreachable from the build host on the
capture date, that the figures were cross-checked against independent
calculators, and that they must be confirmed inside KDP title setup before any
price is committed.

### 4.9 Locked

- Byline: `Chris G. Stewart`. A spec asking for another name fails validation.
- Imprint: `Ashes to Alpha`.
- No auto-applied brand mark on covers.
- The line ends at `07_package/APPROVAL_REQUIRED.md` with a signature line, the
  build fingerprint, and the rate table version.

### 4.10 Prompt packs

Seven human-facing prompts in `factory/prompts/`: master orchestrator,
positioning, architecture, unit authoring, developmental edit, listing copy,
companion product. The **voice contract** lives in exactly one place
(`promptpack.py`) so changing the voice changes every future authoring pack at
once. When a manuscript file is missing, the build auto-generates one authoring
pack per missing unit, pre-filled with that unit's thesis, word target, required
sections, and the voice contract, and then stops.

---

## 5. The proof run

**A Warrior's Code of Prayer, Volume I: Standing Post** — devotional lane, 40
entries, 16,302 words, 5.5 × 8.5 in, cream.

| measurement | value |
|---|---|
| pages | 96 (even) |
| gutter / outer margins | 0.5 in / 0.625 in |
| spine | 0.3000 in |
| cover wrap | 11.5500 × 8.7500 in |
| print cost | $2.30 (flat tier, ≤108 pages) |
| KDP price floor | $3.84 |
| list price | $13.99 |
| royalty | **$6.09 a copy** |
| break-even on $150 fixed spend | 25 copies |
| artifacts | 23 files, each SHA-256 hashed in the manifest |

**The first run failed, and it failed on something real.** The substance gate
rejected two entries:

```
abstract-unit  entry 7  'The Radio Goes Quiet'   0.78 markers/100w
abstract-unit  entry 37 'The Man at the Funeral' 0.25 markers/100w
filler                  'in order to'
```

Both were fluent. Both were about nothing you could put your hands on. Entry 7
discussed silence without a radio, a channel, or an hour in it. Entry 37
discussed attendance at a funeral without a uniform, a drive time, or a number.
Both were rewritten with the specifics that should have been there. A human
editor reading forty entries in one sitting would have passed both.

**Two engine defects the pilot exposed**, both fixed by *tightening* the
measurement rather than loosening it:

1. Spelled-out numbers were not counting as concrete. "four hours each way" is
   as specific as "4 hours." Adding counting words raised every score, so the
   lane floors were **recalibrated against known-abstract prose** rather than
   left where they were.
2. Scripture citations and filler phrases were scoring as concrete. Both are now
   stripped before measurement; quoted anchors are excluded from the author's
   own word count.

**The padded fixture** (`factory/specs/_fixture-padded.yml`) is a deliberately
padded 20-entry book: abstract prose, recycled paragraphs, stock filler, an
unfilled placeholder, missing drills. It exists so the gate can be proven to
still bite:

```
structure gate: PASS
substance gate: FAIL — 45 P0 blockers
  thin-unit x20, abstract-unit x17, missing-section x4, abstract-book x1,
  repetition (46 of 83 paragraphs, 55%, in 395 near-duplicate pairs),
  filler (100 hits), placeholder x1
BUILD HALTED at substance. Nothing downstream was built.
```

The regression suite asserts this book never builds. If a future change lets it
through, the tests fail.

**Honest disclosure about the pilot content**: the 16,302 words were produced by
the engine's authoring layer, not by Chris. `compliance.ai_origin.text` is set
to `ai-generated`, so KDP gets a yes, the copyright page carries the matching
statement, and the disclosure sheet says so. If Chris rewrites it in his own
hand, that field flips to `ai-assisted` and both artifacts change with it. The
factory records the decision; it does not help anyone hide it.

---

## 6. Competitive position, as researched

| product | what it does | what it cannot do |
|---|---|---|
| **CoAuthor.ai** (Sean Dollwet) | guided 14-step nonfiction flow: niche research → outline → section drafting → edit → cover → description; exports publish-ready files for KDP, Apple Books, IngramSpark, Draft2Digital | serves thousands of publishers, so it optimizes for the median user: cannot enforce a house voice, cannot demand a source ledger, cannot refuse to finish |
| **Youbooks** | long-form nonfiction to 300k words, user-supplied sources or web research, multi-model routing, "human model" style training from samples | supplying sources ≠ proving each claim traces to one |
| **Dibbly Create** | nonfiction-only guided flow, assistant "KIP", publisher-grade collaboration: real-time editing, permissions, inline comments, suggestion mode, version history | does not compute a spine width for the final page count |
| **Book Bolt** | low-content specialization: Amazon keyword/niche research, interior templates, cover wizard around KDP trim and bleed | anything with an argument in it |

**What this factory adds that none of them own**: it can fail; producers never
approve; it measures what padding cannot fake; it proves the file holds the
approved manuscript; evidence is a build artifact; money comes from a dated
table that refuses to price unverified configurations; a human signs.

**The legal edge of the road**: the FTC's 2026 action concerning Publishing.com
addressed alleged misleading earnings claims, refund claims, and testimonial and
endorsement practices in exactly this market. Two consequences are enforced in
code: the listing gate fails a build on outcome language (guaranteed, cure,
heal, passive income, get rich, risk-free, "proven to"), and nothing this
factory produces promises income.

**Amazon's AI disclosure rules**: KDP requires disclosure of AI-**generated**
content (text, images including cover, translations) where an AI produced the
material even if a human edited it afterward. It does not require disclosure of
AI-**assisted** work. Disclosure is internal to Amazon and not shown on the
product page. Non-disclosure is a terms violation that can get a title blocked
or an account terminated.

---

## 7. The business arithmetic

The pilot is a good paperback: $13.99 list, $2.30 print, **$6.09 a copy**.

$100,000 at $6.09 a copy is **16,420 copies**. Across eight titles that is just
over 2,000 copies each — a strong result for an unknown indie nonfiction title,
and not a plan you can schedule.

The same $100,000 is:
- **1,000 toolkit sales at $99** (no printing cost at all), or
- **250 institutional or unit licences at $400**, or
- **35 training blocks at $2,850** — the one that uses what Chris has that
  nobody can buy.

So the paperback is the front door, not the business. The engine supports this
with a `companion_products` field in the spec and a companion-product prompt
pack, but **the companion side is specified, not built.** See section 8.

---

## 8. Known gaps — the honest list

These are what an outside reviewer should push on. They are stated plainly here
so you do not waste effort rediscovering them.

1. **The companion/revenue side is a prompt, not an engine.** The factory builds
   books. The toolkit, journal, card deck, digital product, and institutional
   licence side is specified in a prompt pack and nothing more. This is the
   single largest gap relative to the stated revenue goal.
2. **No market intelligence layer.** The engine has no idea whether a title will
   sell. There is no category competitiveness check, no keyword volume data, no
   competing-title scan, no price-band analysis. The listing gate enforces
   Amazon's *limits*; it does not evaluate *strategy*.
3. **Rate table is unverified at the source.** `kdp.amazon.com` was blocked from
   the build host. Figures were cross-checked against independent calculators
   and flagged. Color bands refuse to price at all.
4. **The substance metrics are proxies and the code says so.** They reliably
   detect *empty*. They cannot detect *wrong*, *boring*, or *derivative*. A
   fluent, concrete, well-structured chapter that is also useless will pass
   every gate.
5. **No ebook / Kindle path.** Print interior only. No EPUB, no reflowable
   layout, no Kindle-specific metadata.
6. **No series/catalogue-level logic.** Each build is a title in isolation. No
   cross-title consistency check, no series page strategy, no back-matter
   cross-promotion between titles, no read-through modelling.
7. **Typography is utilitarian.** Liberation Serif/Sans (SIL OFL, embedded,
   print-legal). It is correct, not beautiful.
8. **The pilot's scripture quotations are unverified.** World English Bible,
   public domain, but typed from memory and not checked against a WEB text. On
   the approval sheet as a do-not-publish item.
9. **Catalogue status is assumed.** Chris's actual draft manuscripts are not in
   this repository, so the lane assignments are solid but the "how finished is
   it" column is a guess.
10. **No review-velocity or launch mechanics.** Nothing about pre-orders, launch
    sequencing, ARC readers, A+ content, or Amazon Ads.

---

## 9. What we want from you — required output

Answer in exactly these six sections, in this order. Skip nothing. If you have
nothing for a section, say "nothing to add" and move on rather than padding it.

**SECTION 1 — RED TEAM THE SUBSTANCE GATE.**
This is the highest-value thing you can do. Describe specific patterns of
fluent-but-empty nonfiction prose that would score **above 2.5 concrete markers
per 100 words**, show **zero near-duplicate paragraphs**, hit **zero filler
phrases**, carry **high sentence-length variance**, and still be worthless to a
reader. For each pattern, propose a measurable detector — something computable
over plain text, not a judgment call. Be concrete enough that it could be
implemented as a regex, a statistic, or a cheap heuristic. This is adversarial
work: you are trying to beat the gate.

**SECTION 2 — THE MARKET LAYER THAT DOES NOT EXIST.**
Specify what a market-intelligence stage should check before a title is written,
given that the engine can make HTTP requests and parse HTML but has no paid data
subscriptions. What signals are obtainable, what are they worth, and what are
the decision rules? Name the specific checks (category depth, price bands,
review counts on the top N, publication recency, large-print/senior/occasion
gaps, etc.) and the thresholds at which a title should be killed, repositioned,
or proceeded with. Be specific to the four lanes in section 4.3 — the answer for
a devotional is not the answer for a money book.

**SECTION 3 — THE COMPANION AND INSTITUTIONAL REVENUE MODEL.**
This is gap #1 and the direct path to the stated goal. For each of the four
lanes, specify the companion product that should ship alongside the book: what
it is, what it costs to build, what it sells for, through what channel, and what
breaks if it is not synchronized with the book. Then address the institutional
path specifically: selling to federal/state/local agencies, academies,
departments, and peer-support programs. What does procurement actually look like
for a $400–$3,000 training product bought by a law enforcement agency? What
would have to exist for that sale to be possible? Be concrete about GSA
schedules, purchase cards, sole-source justification, and unit-level discretion
where relevant, and flag clearly where you are uncertain.

**SECTION 4 — KDP LAUNCH AND LISTING STRATEGY.**
The engine enforces Amazon's limits. It does not optimize. Give the strategy
layer: category selection logic (including whether to request additional
categories and how), keyword construction for these specific audiences, series
page setup, pre-order mechanics and whether they help or hurt an unknown author,
A+ content for a sole proprietor, review velocity without a mailing list, and
whether Amazon Ads make sense at a $6.09 royalty. State where your information
could be out of date.

**SECTION 5 — WHAT WE GOT WRONG.**
Attack the design. Candidates: the four-lane model, the P0/P1/P2 severity
scheme, the decision to gate on computable text properties at all, the locked
byline, the refusal to price unverified rate bands, the choice to build a
bespoke PDF reader rather than use a library, the producer/approver separation
as implemented, the decision to end at a human approval sheet rather than
automating upload. For each: is it right, is it over-built, or is it wrong? Say
which, and why, in one or two sentences each. Do not be polite about it.

**SECTION 6 — SEQUENCING.**
Given everything above, what are the next three things to build, in order, and
why that order? Chris has roughly 5–8 hours a week for this and runs several
other initiatives simultaneously. The constraint is his hours and the review
burden on high-risk titles, not engine throughput — the engine builds a title in
under a minute once the manuscript exists. Do not propose anything that requires
him on camera.

---

## 10. Constraints your answer must respect

- **Do not propose a rewrite or a new framework.** The engine is built, tested,
  and running. Propose additions and corrections to what exists.
- **Do not propose anything that makes the engine unable to fail.** Every
  suggestion must preserve: gates can halt the build, no override flag, no step
  approves its own output.
- **Do not propose income claims, outcome guarantees, or anything that walks
  toward the FTC line described in section 6.**
- **Do not propose hiding AI involvement from Amazon.**
- **Do not propose putting Chris on camera.** The brand is faceless by design.
- **Assume no paid data subscriptions** unless you flag the cost explicitly.
- **Flag your uncertainty.** Amazon's rules, FTC posture, and KDP rates change.
  Where your information may be stale, say so rather than stating it flatly.
- **Do not restate this brief back.** Start at Section 1.

---

## 11. One thing to be aware of

Chris's own operating doctrine includes a rule about suppressing infrastructure
addiction: building systems instead of shipping product, endless Phase 2
thinking, architecture replacing deployment. Two AI assistants reviewing each
other's architecture is exactly the shape that failure mode takes.

The highest-value thing you can contribute is **sections 1, 2, 3 and 4** —
adversarial red-teaming of the quality gate, and the market, revenue, and launch
layers that genuinely do not exist yet. Section 5 is useful as a sanity check.
Be disciplined about section 6: if your honest answer is "stop building the
engine and go sell something," say that.
