# What the other engines do, and what they cannot do

Research pass 2026-09-16. Everything below is either from the vendors' own
public pages or from secondary coverage, and is marked where it is secondary.
`kdp.amazon.com` was not reachable from the build host on that date, so KDP's
own numbers were cross-checked against multiple independent calculators and are
flagged in the rate table as requiring confirmation inside KDP title setup.

## The reference prompt

The prompt that started this (a low-content puzzle publisher's engine prompt)
is correct about four things, and they are the four things worth stealing:

1. **Ask for an engine, not an artifact.** "I do not want you to make me a book.
   I want you to build a repeatable ENGINE that makes them."
2. **A quality check that can FAIL the build and stop it.** Not a report. A halt.
3. **Code, not prose, for anything countable.** Page math, spine width, file
   naming.
4. **Never let the same step both produce and approve an artifact.**

And its slide deck adds the part most people miss: *the stop points are baked
into the engine, not the prompt.* A prompt that says "check quality" is a wish.
A gate that reads the finished PDF off disk and returns a non-zero exit is a
control.

That engine's economics work because puzzles are generated, verified, and
laid out by code end to end. A word search either has every word in the grid or
it does not, and a script can prove it. Doctrine and transformation writing has
no equivalent proof, which is why this factory spends its effort on measuring
the *properties* of prose that padding cannot fake, and on evidence control.

## CoAuthor.ai (Sean Dollwet)

**What it is.** A guided workflow for nonfiction authors: niche research,
outline generation, section-by-section drafting, editing, cover generation, and
description, reported publicly as a 14-step flow, exporting publish-ready files
for KDP, Apple Books, IngramSpark and Draft2Digital. (Secondary sources; the
site itself was not reachable from the build host.)

**What is worth taking.** Connected project state. The same project carries
research through outline through draft through cover through listing, so the
cover knows the title and the listing knows the book. That is the single
biggest thing separating a workflow from a pile of chat sessions, and this
factory implements it as `output/<slug>/` plus a spec fingerprint on every run.

**What it cannot own.** Chris's twenty years. A platform that serves thousands
of publishers optimises for the median user, which means it cannot enforce a
house voice, cannot demand a source ledger, and cannot refuse to finish.

## Youbooks

**What it is.** Long-form nonfiction generation, advertised up to 300,000 words,
with user-supplied source material or web research, routing across several
model families, and a "human model" style-training step from writing samples.

**What is worth taking.** Source grounding and style samples. Grounding a draft
in documents you supply beats grounding it in a model's memory.

**What it cannot own.** Verification. Supplying sources is not the same as
proving each claim traces to one. This factory's claim ledger scans the finished
manuscript for sentences that carry a number, a percentage, a named authority,
or an absolute, and requires each one to resolve to a ledger entry that resolves
to a source. In the technical lane an unresolved claim is a P0.

## Dibbly Create

**What it is.** Nonfiction-only guided book flow with an assistant ("KIP") for
content, outlining and research, plus publisher-grade collaboration: real-time
editing, permissions, inline comments, suggestion mode, version history.

**What is worth taking.** Version history and suggestion mode. Knowing which
draft a reviewer signed off on is a real control. This factory's equivalent is
the manifest: every artifact with a SHA-256, and a build fingerprint printed on
the approval sheet, so "approved" means a specific set of bytes.

**What it cannot own.** The physical product. Collaboration features do not
compute a spine width for the final page count.

## Book Bolt

**What it is.** Low-content specialisation: niche and keyword research against
Amazon data, interior templates, and a cover/interior wizard built around KDP's
trim and bleed specs.

**What is worth taking.** Category and keyword discipline as a first-class step
rather than an afterthought at upload.

**What it cannot own.** Anything with an argument in it.

## Publishing.com and the FTC

Relevant because it defines the edge of the road. The FTC's 2026 action
concerning Publishing.com addressed alleged misleading earnings claims, refund
claims, and testimonial and endorsement practices in the self-publishing
training market.

Two consequences, both enforced in code here:

1. The listing gate fails a build on outcome language: guaranteed, cure, heal,
   passive income, get rich, risk-free, "proven to".
2. Nothing this factory produces promises income. It improves the probability
   of a defensible catalogue. That is the claim, and it is the only one.

## Amazon's AI disclosure rules

KDP requires disclosure of **AI-generated** content (text, images including the
cover, and translations) where an AI produced the material, even if a human
edited it afterwards. It does not require disclosure of **AI-assisted** work,
where a human wrote it and used AI to edit, refine or brainstorm. The disclosure
is internal to Amazon and is not shown on the product page. Non-disclosure is a
terms violation and can get a title blocked or an account terminated.

The factory records the decision per component in `compliance.ai_origin`, fails
the build if any of the three is unresolved, prints the answer sheet to
`06_compliance/kdp_disclosure.md`, and puts the matching statement on the
copyright page. It does not help anybody hide AI involvement.

## Where this factory is actually different

Everything above generates. None of it refuses.

1. **It can fail.** Six gates, any of which halts the run. No override flag.
2. **Producers never approve.** The PDF reader used by the gates does not import
   the PDF writer used by the stages.
3. **It measures what padding cannot fake.** Concrete-marker density calibrated
   against known-abstract prose, near-duplicate paragraph detection, filler
   density, sentence-length variance, repeated sentence openings.
4. **It proves the file holds the approved manuscript.** The interior gate
   extracts the text back out of the finished PDF and looks for sentences from
   the draft that cleared the substance gate.
5. **Evidence is a build artifact.** Claim, source, story, AI-origin and
   decision ledgers, with per-lane enforcement.
6. **The money is computed from a dated table** that refuses to price an
   unverified configuration at all.
7. **A human signs.** The line ends at an approval sheet, on purpose.
