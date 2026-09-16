"""Authoring prompts. The engine owns the machine; these own the voice."""
from __future__ import annotations

from .spec import TitleSpec, Unit, slugify

VOICE = """\
## Voice contract - Ashes to Alpha

Write like a man who has done the work and is telling another man how it is
done. Experienced, not performative. Dry humour is allowed. Certainty about
things you have seen; plain admission about things you have not.

Hard rules:
- Second person. Short sentences carry the weight. Vary the length or it reads
  like a slogan wall.
- Doctrine is stated as doctrine. No "may help you consider" hedging.
- Every abstract claim is followed inside two sentences by something concrete:
  a number, a time, a piece of equipment, a decision someone actually made.
- No em dashes. Use a period or a comma.
- Banned: unleash, crush it, level up, grind, warrior mindset as a slogan,
  "in today's world", "now more than ever", "the truth is", rhetorical
  questions stacked three deep, anything that would fit on a gym wall.
- Banned: fabricated operational stories. If a story is not Chris's, it is
  either sourced, marked as composite, or cut.
- No scripture translation other than public domain (KJV, WEB, ASV) unless the
  spec names a licensed translation and the licence is on file.
- Nothing that promises income, healing, or safety as an outcome.
"""


def unit_prompt(spec: TitleSpec, unit: Unit) -> str:
    lane = spec.lane_profile
    fname = f"factory/manuscripts/{spec.slug}/{unit.number:03d}-{slugify(unit.title)}.md"
    target = int(spec.raw.get("target_words_per_unit") or
                 round((lane.min_words_per_unit + lane.max_words_per_unit) / 2 * 0.55))
    sections = "\n".join(f"- `{s}`" for s in lane.required_unit_sections)
    return f"""\
# Authoring pack - {lane.unit_type} {unit.number}: {unit.title}

**Save the result to:** `{fname}`
**Book:** {spec.full_title} ({spec.author}, {spec.imprint})
**Lane:** {lane.name} - claim risk {lane.claim_risk}

## The job
{unit.thesis}

Reader: {spec.reader}
Their problem: {spec.reader_problem}
What this {lane.unit_type} must leave them able to do: something specific,
today, without buying anything.

## Length
{target} words, +/- 15%. Under {lane.min_words_per_unit} is thin and the
substance gate will fail the build. Over {lane.max_words_per_unit} is a lecture.

## Required sections
{sections}
{"Anchor line: " + unit.anchor if unit.anchor else ""}

## File format (A2A markdown dialect)
```
# {unit.title}
> anchor line here -- Source
Opening paragraph.
## THE DRILL
What the reader does.
::: prayer
The closing lines.
:::
```
`[[lines:8]]` renders 8 ruled write-lines. `---` is an ornamental break.

{VOICE}
## Before you hand it back
- Every factual claim carries a source you can name, or it is cut.
- No sentence survives that could appear in any other book on the shelf.
- Read the last line out loud. If it sounds like a caption, rewrite it.
"""


def listing_prompt(spec: TitleSpec) -> str:
    return f"""\
# Authoring pack - listing copy for {spec.full_title}

Write the Amazon listing. Return exactly these fields:

- `title` (<= 200 chars incl. subtitle, must match the cover exactly)
- `subtitle`
- `description` (<= 4000 chars, plain text with simple HTML <b>/<br> allowed)
- `keywords` (exactly 7, each <= 50 chars, no words already in the title,
  no competitor names, no subjective claims like "best")
- `categories` (exactly 3 KDP browse paths)
- `list_price` (USD, must clear the printing-cost floor the engine computed)

Rules:
- The description's first two lines are all most readers see. Put the reader's
  problem there in their words, not yours.
- No income, health, or safety outcome promises. No "guaranteed".
- No claim about sales, rank, or endorsements that is not true and documented.

{VOICE}"""
