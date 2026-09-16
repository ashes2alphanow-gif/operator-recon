"""Gate A - is the architecture a book, or a list of overlapping opinions?"""
from __future__ import annotations

from .. import kdp, textmetrics as tm
from ..context import Run
from .base import Verdict, P0, P1, P2

NAME = "structure"


def check(ctx: Run) -> Verdict:
    v = Verdict(NAME)
    plan = ctx.read_json("blueprint", "blueprint.json")
    spec = ctx.read_json("intake", "spec.resolved.json")
    lane = spec["lane_profile"]
    units = plan["units"]

    v.measurements = {
        "unit_count": len(units),
        "estimated_pages": plan["estimated_pages"],
        "word_budget_total": plan["word_budget_total"],
    }

    if not (lane["min_units"] <= len(units) <= lane["max_units"]):
        v.add(P0, "unit-count",
              f"{len(units)} {lane['unit_plural']} is outside the {lane['key']} lane band "
              f"({lane['min_units']}-{lane['max_units']})",
              fix="Split, merge, or move the title to another lane.")

    pages = plan["estimated_pages"]
    try:
        kdp.assert_page_count(pages, spec["paper"], ctx.rates)
    except kdp.SpecError as exc:
        v.add(P0, "page-bounds", str(exc),
              fix="Change the unit count, the target length, or the trim size.")

    dupes = tm.near_duplicate_pairs(
        [(f"{u['number']}. {u['title']}", f"{u['title']} {u['thesis']}") for u in units],
        threshold=0.45, min_words=5)
    for d in dupes:
        v.add(P0, "overlapping-units",
              f"{d['a']} and {d['b']} are {d['similarity']:.0%} the same argument",
              evidence=f"{d['a_text']} || {d['b_text']}",
              fix="One of them is the chapter. The other is a paragraph inside it.")

    thin = [u for u in units if len(tm.words(u["thesis"])) < 6]
    for u in thin:
        v.add(P1, "thin-thesis",
              f"{lane['unit_type']} {u['number']} '{u['title']}' has a thesis too vague "
              "to write against",
              evidence=u["thesis"],
              fix="State what the reader will be able to do that they cannot do now.")

    econ = plan.get("economics_estimate", {})
    if "error" in econ:
        v.add(P1, "economics-unknown", econ["error"],
              fix="Verify the printing cost in KDP and update the rate table.")
    elif econ.get("royalty_per_copy", 0) <= 0.75:
        v.add(P1, "thin-margin",
              f"estimated royalty of ${econ['royalty_per_copy']:.2f} a copy leaves no room "
              "for ads or bundles",
              fix="Raise the list price or cut page count.")

    if pages < ctx.rates["house_spine_text_min_pages"]:
        v.add(P2, "no-spine-text",
              f"at ~{pages} pages the house rule prints no spine text "
              f"(min {ctx.rates['house_spine_text_min_pages']})",
              fix="Accept it, or add material. A blank spine is invisible on a shelf.")
    return v
