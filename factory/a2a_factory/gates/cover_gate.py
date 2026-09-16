"""Gate D - wrong spine or trim, the run halts here.

Recomputes the geometry from the interior's page count rather than trusting the
cover stage's own arithmetic, then measures the file that was actually written.
"""
from __future__ import annotations

from .. import kdp, pdfinspect
from ..context import Run
from .base import Verdict, P0, P1, P2

NAME = "cover_spec"
TOL = 0.01


def check(ctx: Run) -> Verdict:
    v = Verdict(NAME)
    interior = ctx.read_json("interior", "interior.json")
    claim = ctx.read_json("cover", "cover_geometry.json")
    spec = ctx.read_json("intake", "spec.resolved.json")
    pages = int(interior["page_count"])

    expect = kdp.cover_geometry(spec["trim"][0], spec["trim"][1], pages,
                                spec["paper"], ctx.rates)

    pdf = ctx.path("cover", claim["production_pdf"])
    if not pdf.exists():
        v.add(P0, "missing-file", f"{claim['production_pdf']} was not written")
        return v
    facts = pdfinspect.inspect(pdf)

    v.measurements = {
        "file": pdf.name,
        "pages_in_wrap": facts.page_count,
        "wrap_measured_in": facts.media_boxes_in[0] if facts.media_boxes_in else None,
        "wrap_expected_in": [expect.wrap_w, expect.wrap_h],
        "spine_expected_in": expect.spine,
        "spine_claimed_in": claim["spine"],
        "page_count_used": pages,
    }

    if abs(claim["spine"] - expect.spine) > 1e-6:
        v.add(P0, "spine-mismatch",
              f"cover stage used a {claim['spine']:.6f}\" spine; {pages} pages of "
              f"{spec['paper']} paper is {expect.spine:.6f}\"")
    if int(claim["pages"]) != pages:
        v.add(P0, "stale-page-count",
              f"the cover was built for {claim['pages']} pages; the interior is {pages}",
              fix="Rebuild the cover after every interior change. No exceptions.")

    if facts.page_count != 1:
        v.add(P0, "multi-page-cover",
              f"the wrap is {facts.page_count} pages; KDP takes exactly one")
    if facts.media_boxes_in:
        gw, gh = facts.media_boxes_in[0]
        if abs(gw - expect.wrap_w) > TOL or abs(gh - expect.wrap_h) > TOL:
            v.add(P0, "wrap-size",
                  f"wrap measures {gw}x{gh} in; it must be "
                  f"{expect.wrap_w:.4f}x{expect.wrap_h:.4f} in "
                  f"(bleed {expect.bleed}\" + trim + spine {expect.spine:.4f}\")")

    if claim.get("spine_text_printed") and not expect.spine_text_allowed:
        v.add(P0, "spine-text-illegal",
              f"spine text printed at {pages} pages; KDP requires at least "
              f"{ctx.rates['spine_text_min_pages']}")
    if not claim.get("spine_text_printed"):
        sev = P1 if expect.house_spine_text_allowed else P2
        v.add(sev, "spine-blank",
              f"the spine carries no text at {pages} pages "
              f"(house threshold {ctx.rates['house_spine_text_min_pages']}, "
              f"KDP minimum {ctx.rates['spine_text_min_pages']})",
              fix="A blank spine is invisible on a shelf. Adding pages to clear the "
                  "threshold may cost nothing inside the flat print tier.")

    if facts.unembedded_fonts:
        v.add(P0, "fonts-not-embedded",
              f"non-embedded fonts on the cover: {', '.join(facts.unembedded_fonts)}")
    if not ctx.path("cover", claim["proof_pdf"]).exists():
        v.add(P1, "no-proof", "no proof wrap with guides was written for human review")
    return v
