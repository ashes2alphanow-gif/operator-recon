"""Gate E - the listing, against Amazon's limits and A2A's claim rules."""
from __future__ import annotations

from ..context import Run
from .base import Verdict, P0, P1, P2

NAME = "listing"
TITLE_MAX, DESC_MAX, KEYWORD_MAX = 200, 4000, 50


def check(ctx: Run) -> Verdict:
    v = Verdict(NAME)
    L = ctx.read_json("listing", "listing.json")
    interior = ctx.read_json("interior", "interior.json")

    v.measurements = {
        "title_length": L["title_length"],
        "description_length": L["description_length"],
        "keywords": len(L["keywords"]),
        "categories": len(L["categories"]),
        "list_price": L["economics"]["list_price"],
        "royalty_per_copy": L["economics"]["royalty_per_copy"],
    }

    if L["title_length"] > TITLE_MAX:
        v.add(P0, "title-too-long",
              f"title + subtitle is {L['title_length']} chars, over KDP's {TITLE_MAX}")
    if not L["subtitle"]:
        v.add(P1, "no-subtitle",
              "no subtitle - the subtitle is where the search terms live")

    if L["description_length"] > DESC_MAX:
        v.add(P0, "description-too-long",
              f"description is {L['description_length']} chars, over KDP's {DESC_MAX}")
    if L["description_length"] < 400:
        v.add(P1, "description-thin",
              f"description is {L['description_length']} chars - readers decide here")

    if len(L["keywords"]) != 7:
        v.add(P0, "keyword-count",
              f"{len(L['keywords'])} usable keywords; KDP gives you 7 slots and an empty "
              "slot is free traffic thrown away",
              evidence="; ".join(f"{r['keyword']}: {r['reason']}"
                                 for r in L["keywords_rejected"][:6]),
              fix="Add more seeds to the spec and re-run.")
    for k in L["keywords"]:
        if len(k) > KEYWORD_MAX:
            v.add(P0, "keyword-too-long", f"'{k}' is {len(k)} chars, over {KEYWORD_MAX}")

    if len(L["categories"]) != 3:
        v.add(P0, "category-count",
              f"{len(L['categories'])} categories; KDP takes 3 and ranking depends on them")

    if L["banned_claim_hits"]:
        v.add(P0, "claim-language",
              "the description makes a claim A2A does not make",
              evidence=", ".join(L["banned_claim_hits"]),
              fix="The FTC's 2026 action against Publishing.com was about exactly this "
                  "kind of earnings and outcome language. Cut it.")

    econ = L["economics"]
    if econ["list_price"] < econ["min_list_price"]:
        v.add(P0, "price-below-floor",
              f"${econ['list_price']:.2f} is under the ${econ['min_list_price']:.2f} KDP "
              f"floor for a {L['page_count']}-page book")
    if econ["royalty_per_copy"] <= 0:
        v.add(P0, "negative-royalty",
              f"every copy sold loses ${abs(econ['royalty_per_copy']):.2f}")
    elif econ["royalty_per_copy"] < 1.50:
        v.add(P1, "thin-royalty",
              f"${econ['royalty_per_copy']:.2f} a copy will not fund ads or a bundle",
              fix="Price up, or make the paperback the front door to a paid companion.")
    if not econ["verified"]:
        v.add(P0, "unverified-rates",
              f"the print cost came from an unverified band in rate table {econ['rate_table']}",
              fix="Confirm the figure in KDP title setup and update the rate table.")

    if int(interior["page_count"]) != int(L["page_count"]):
        v.add(P0, "page-count-drift",
              f"listing priced {L['page_count']} pages; the interior is "
              f"{interior['page_count']}")

    if not L.get("bisac"):
        v.add(P2, "no-bisac", "no BISAC codes recorded for wider distribution later")
    return v
