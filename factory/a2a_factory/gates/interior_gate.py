"""Gate C - the interior file, measured. Not the interior the builder meant."""
from __future__ import annotations

import re

from .. import kdp, pdfinspect
from ..context import Run
from .base import Verdict, P0, P1, P2

NAME = "interior_spec"
TOL = 0.01      # inches


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", text.lower())


def _probe_manuscript(ctx: Run, sample: str, count: int = 5) -> tuple:
    """Prove the PDF holds the manuscript that passed the substance gate."""
    try:
        src = ctx.read_json("manuscript", "blocks.json")
    except FileNotFoundError:
        return 0, []
    haystack = " ".join(_norm(sample).split())
    probes, found = [], 0
    paras = [b["text"] for u in src["units"] for b in u["blocks"]
             if b["t"] == "p" and len(b.get("text", "").split()) > 12]
    if not paras:
        return 0, []
    step = max(1, len(paras) // count)
    for para in paras[::step][:count]:
        phrase = " ".join(_norm(para).split()[:7])
        probes.append(phrase)
        if phrase and phrase in haystack:
            found += 1
    return found, probes


def check(ctx: Run) -> Verdict:
    v = Verdict(NAME)
    claim = ctx.read_json("interior", "interior.json")
    spec = ctx.read_json("intake", "spec.resolved.json")
    pdf = ctx.path("interior", claim["pdf"])

    if not pdf.exists():
        v.add(P0, "missing-file", f"{claim['pdf']} was not written")
        return v

    facts = pdfinspect.inspect(pdf, want_text=True, text_limit=2_000_000)
    v.measurements = {
        "file": pdf.name, "bytes": facts.bytes,
        "pages_counted_in_file": facts.page_count,
        "pages_claimed_by_builder": claim["page_count"],
        "page_sizes_in": facts.media_boxes_in,
        "embedded_font_streams": facts.embedded_font_streams,
        "extracted_characters": len(facts.text_sample),
        "base_fonts": facts.base_fonts,
        "words_per_page_actual": claim["words_per_page_actual"],
    }

    if facts.page_count != claim["page_count"]:
        v.add(P0, "page-count-mismatch",
              f"the builder recorded {claim['page_count']} pages; the file contains "
              f"{facts.page_count}",
              fix="The cover spine and the printing cost are both computed off this "
                  "number. Nothing ships until they agree.")

    if facts.page_count % 2:
        v.add(P0, "odd-page-count",
              f"{facts.page_count} pages - books print on leaves, so the count must be even",
              fix="Pad the back matter by one page.")

    try:
        kdp.assert_page_count(facts.page_count, spec["paper"], ctx.rates)
    except kdp.SpecError as exc:
        v.add(P0, "page-bounds", str(exc))

    want = (round(spec["trim"][0], 4), round(spec["trim"][1], 4))
    if not facts.uniform_page_size:
        v.add(P0, "mixed-page-size",
              f"the file has {len(facts.media_boxes_in)} different page sizes: "
              f"{facts.media_boxes_in}",
              fix="KDP rejects a mixed-size interior outright.")
    else:
        got = tuple(facts.media_boxes_in[0])
        if abs(got[0] - want[0]) > TOL or abs(got[1] - want[1]) > TOL:
            v.add(P0, "wrong-trim",
                  f"pages measure {got[0]}x{got[1]} in; the spec says {want[0]}x{want[1]}")

    if facts.unembedded_fonts:
        v.add(P0, "fonts-not-embedded",
              f"non-embedded base-14 fonts present: {', '.join(facts.unembedded_fonts)}",
              fix="KDP requires every font embedded. Register the TTF and re-render.")
    if facts.embedded_font_streams == 0:
        v.add(P0, "no-embedded-fonts",
              "the file carries no embedded font programs at all")

    if len(facts.text_sample.strip()) < 200:
        v.add(P0, "no-extractable-text",
              "almost no live text came out of the content streams - the interior may "
              "have rendered as images",
              fix="An image-only interior kills Look Inside and accessibility.")
    else:
        found, probes = _probe_manuscript(ctx, facts.text_sample)
        v.measurements["manuscript_probes_found"] = f"{found}/{len(probes)}"
        if probes and found == 0:
            v.add(P0, "wrong-manuscript",
                  "none of the approved manuscript's sentences were found in the PDF",
                  evidence=probes[0],
                  fix="The file on disk is not the manuscript that cleared the substance "
                      "gate. Rebuild from the approved source.")
        elif probes and found < len(probes):
            v.add(P1, "partial-manuscript",
                  f"only {found} of {len(probes)} manuscript probes were found in the PDF",
                  fix="Text may be dropping off the page. Check the last page of the "
                      "longest units.")

    model = 300 if spec["trim"][0] >= 6 else 250
    actual = claim["words_per_page_actual"]
    if actual < model * 0.45:
        v.add(P1, "low-text-density",
              f"{actual} words per page against a {model}-word model - the book is mostly air",
              fix="Either it is a workbook and that is intended, or it is padded to hit "
                  "a page count.")

    for m in claim.get("margin_convergence", []):
        if m["attempt"] > 1:
            v.add(P2, "margin-reflow",
                  f"attempt {m['attempt']}: page count crossed a gutter band, re-rendered "
                  f"at {m['gutter']}\" gutter")

    band_key = "bw_regular_trim" if spec["trim"][0] < 6.14 else "bw_large_trim"
    band = ctx.rates["print_cost"]["US"].get(band_key, {})
    flat_max = band.get("flat_max_pages") or 0
    if spec["ink"] == "bw" and 0 < facts.page_count <= flat_max:
        v.add(P2, "flat-tier-headroom",
              f"{flat_max - facts.page_count} more pages would cost nothing to print - "
              f"anything up to {flat_max} pages prints at the same flat "
              f"${band['flat_cost']:.2f}",
              fix="Free room for a longer back matter, a bonus section, or a companion "
                  "sample. Do not pad with filler; the substance gate is still armed.")

    if facts.uses_cmyk:
        v.add(P2, "cmyk-interior", "interior declares CMYK; KDP expects RGB or greyscale")
    return v
