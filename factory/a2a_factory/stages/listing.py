"""G5 - listing pack. Title, subtitle, description, 7 keywords, 3 categories, price."""
from __future__ import annotations

import re

from .. import kdp
from ..context import Run

TITLE_MAX = 200
DESC_MAX = 4000
KEYWORD_MAX = 50
BANNED_KEYWORD = re.compile(
    r"\b(best|bestseller|best-selling|new|free|sale|on sale|cheap|#1|number one|"
    r"guaranteed|amazon|kindle)\b", re.I)
BANNED_CLAIM = re.compile(
    r"\b(guarantee[ds]?|cure[sd]?|passive income|get rich|risk[- ]free|"
    r"proven to (?:cure|heal|make)|will make you \$)\b", re.I)


def pick_keywords(seeds: list, title: str, subtitle: str) -> tuple:
    """Deterministic: filter, dedupe, then take the first seven that survive."""
    title_words = set(re.findall(r"[a-z]+", f"{title} {subtitle}".lower()))
    chosen, rejected, seen = [], [], set()
    for raw in seeds:
        k = " ".join(str(raw).split()).strip().lower()
        why = None
        if not k:
            why = "empty"
        elif k in seen:
            why = "duplicate"
        elif len(k) > KEYWORD_MAX:
            why = f"{len(k)} chars over the {KEYWORD_MAX}-char limit"
        elif BANNED_KEYWORD.search(k):
            why = "contains a term KDP disallows in keywords"
        elif all(w in title_words for w in k.split()):
            why = "every word already appears in the title; the slot is wasted"
        if why:
            rejected.append({"keyword": k, "reason": why})
            continue
        seen.add(k)
        chosen.append(k)
    return chosen[:7], chosen[7:], rejected


def build_description(spec, interior) -> str:
    r = spec.raw
    parts = []
    if r.get("listing_hook"):
        parts.append(r["listing_hook"].strip())
    if r.get("listing_body"):
        parts.append(r["listing_body"].strip())
    lane = spec.lane_profile
    inside = r.get("listing_inside")
    if inside:
        parts.append("WHAT IS INSIDE\n" + "\n".join(f"- {line}" for line in inside))
    else:
        parts.append(
            "WHAT IS INSIDE\n" +
            f"- {len(spec.units)} {lane.unit_type}s, each ending in one thing you do\n"
            f"- {interior['page_count']} pages, {interior['words']:,} words\n"
            f"- {spec.trim[0]} x {spec.trim[1]} in paperback")
    if r.get("listing_for"):
        parts.append("WHO IT IS FOR\n" + "\n".join(f"- {line}" for line in r["listing_for"]))
    if r.get("listing_not"):
        parts.append("WHAT IT IS NOT\n" + r["listing_not"].strip())
    parts.append(f"{spec.author}. {spec.imprint}.")
    return "\n\n".join(p for p in parts if p).strip()


def run(ctx: Run) -> None:
    spec = ctx.spec
    interior = ctx.read_json("interior", "interior.json")
    pages = int(interior["page_count"])

    econ = kdp.economics(pages, spec.ink, spec.paper, spec.trim[0], spec.trim[1],
                         ctx.rates, list_price=spec.list_price or None)
    keywords, spare, rejected = pick_keywords(spec.keywords_seed, spec.title, spec.subtitle)
    description = build_description(spec, interior)

    fixed = float(spec.raw.get("fixed_spend_usd") or 0.0)
    listing = {
        "title": spec.title,
        "subtitle": spec.subtitle,
        "title_field_as_submitted": spec.full_title,
        "title_length": len(spec.full_title),
        "author": spec.author,
        "imprint": spec.imprint,
        "series": spec.series,
        "description": description,
        "description_length": len(description),
        "keywords": keywords,
        "keywords_spare": spare,
        "keywords_rejected": rejected,
        "categories": spec.categories,
        "bisac": spec.bisac,
        "economics": econ.as_dict(),
        "breakeven_units": (kdp.breakeven_units(fixed, econ.royalty_per_copy)
                            if fixed > 0 else None),
        "fixed_spend_usd": fixed,
        "page_count": pages,
        "isbn": spec.isbn or "KDP-assigned ASIN",
        "ai_disclosure": spec.compliance.get("ai_origin", {}),
        "banned_claim_hits": [m.group(0) for m in BANNED_CLAIM.finditer(description)],
    }
    ctx.write_json("listing", "listing.json", listing)

    md = [f"# Listing pack - {spec.full_title}", "",
          "Paste order matches the KDP title setup screens.", "",
          "## Title", f"`{spec.title}`", "", "## Subtitle", f"`{spec.subtitle}`", "",
          "## Author", f"`{spec.author}`", "",
          "## Description", "```", description, "```", "",
          f"({len(description)} of {DESC_MAX} characters)", "",
          "## Keywords (7)"]
    md += [f"{i}. `{k}`  ({len(k)} chars)" for i, k in enumerate(keywords, 1)]
    if rejected:
        md += ["", "### Rejected by the engine"] + \
              [f"- `{r['keyword']}` - {r['reason']}" for r in rejected]
    md += ["", "## Categories (3)"] + [f"- {c}" for c in spec.categories]
    md += ["", "## Price", f"- Print cost: **${econ.print_cost:.2f}** "
                           f"({pages} pp, {spec.ink}, rate table {econ.rate_table})",
           f"- KDP floor at 60%: **${econ.min_list_price:.2f}**",
           f"- List price: **${econ.list_price:.2f}**",
           f"- Royalty per copy: **${econ.royalty_per_copy:.2f}**"]
    if listing["breakeven_units"]:
        md += [f"- Break-even on ${fixed:,.2f} of fixed spend: "
               f"**{listing['breakeven_units']} copies**"]
    md += ["", "> Printing cost and royalty come from a dated rate table. Confirm both "
           "inside KDP title setup before you hit publish.", ""]
    ctx.write("listing", "listing.md", "\n".join(md))
    ctx.say(f"listing: {len(keywords)} keywords, ${econ.list_price:.2f} list, "
            f"${econ.royalty_per_copy:.2f}/copy royalty")
