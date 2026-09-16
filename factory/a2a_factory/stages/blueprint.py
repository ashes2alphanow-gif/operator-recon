"""G1 - architecture. Turn a spec into a build plan with real numbers in it."""
from __future__ import annotations

from .. import kdp, typography
from ..context import Run

# Measured against the house text block, not guessed: see tests/test_pagemath.py
WORDS_PER_PAGE = {"5.5x8.5": 250, "6x9": 300}


def words_per_page(trim: tuple) -> int:
    return WORDS_PER_PAGE.get(f"{trim[0]}x{trim[1]}", 270)


def run(ctx: Run) -> None:
    spec = ctx.spec
    lane = spec.lane_profile
    style = typography.style_for(spec.trim)

    target = int(spec.raw.get("target_words_per_unit") or
                 round((lane.min_words_per_unit + lane.max_words_per_unit) / 2 * 0.55))
    target = max(lane.min_words_per_unit, min(target, lane.max_words_per_unit))

    wpp = words_per_page(spec.trim)
    body_words = target * len(spec.units)
    # Each unit opener burns roughly a third of a page in white space, and units
    # are padded to an even leaf so the next one opens clean.
    body_pages = round(body_words / wpp + len(spec.units) * 0.6)
    front_pages = len(lane.front_matter) + 2
    back_pages = len(lane.back_matter) + 2
    est_pages = body_pages + front_pages + back_pages
    est_pages += est_pages % 2

    plan = {
        "slug": spec.slug,
        "lane": lane.key,
        "unit_type": lane.unit_type,
        "unit_count": len(spec.units),
        "target_words_per_unit": target,
        "word_budget_total": body_words,
        "words_per_page_model": wpp,
        "estimated_pages": est_pages,
        "front_matter": list(lane.front_matter),
        "back_matter": list(lane.back_matter),
        "required_unit_sections": list(lane.required_unit_sections),
        "style": style.as_dict(),
        "units": [u.as_dict() for u in spec.units],
    }

    # Economics are estimated here and recomputed from the real page count after
    # the interior is built. The estimate exists so a doomed title dies early.
    try:
        econ = kdp.economics(
            est_pages, spec.ink, spec.paper, spec.trim[0], spec.trim[1], ctx.rates,
            list_price=spec.list_price or None,
        )
        plan["economics_estimate"] = econ.as_dict()
    except (kdp.RateError, kdp.SpecError) as exc:
        plan["economics_estimate"] = {"error": str(exc)}

    ctx.write_json("blueprint", "blueprint.json", plan)

    out = [f"# Build plan - {spec.full_title}", "",
           f"{len(spec.units)} {lane.unit_plural} at ~{target} words each = "
           f"~{body_words:,} words -> ~{est_pages} pages at {spec.trim[0]}x{spec.trim[1]}.", ""]
    est = plan["economics_estimate"]
    if "error" in est:
        out += [f"> Economics unavailable: {est['error']}", ""]
    else:
        out += [f"Estimated print cost ${est['print_cost']:.2f}, floor price "
                f"${est['min_list_price']:.2f}, planned list ${est['list_price']:.2f}, "
                f"royalty ${est['royalty_per_copy']:.2f}/copy.", ""]
    out += ["## Outline", ""]
    for u in spec.units:
        out.append(f"{u.number}. **{u.title}** - {u.thesis}")
        if u.anchor:
            out.append(f"   - anchor: {u.anchor}")
    out.append("")
    ctx.write("blueprint", "outline.md", "\n".join(out))
    ctx.say(f"blueprint: ~{body_words:,} words -> ~{est_pages} pages (estimate)")
