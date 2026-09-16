"""G0 - intake. Resolve the spec, freeze the inputs, state the assumptions."""
from __future__ import annotations

from .. import kdp
from ..context import Run


def run(ctx: Run) -> None:
    spec = ctx.spec
    lane = spec.lane_profile
    kdp.trim_class(spec.trim[0], spec.trim[1], ctx.rates)     # raises on a bad trim
    kdp.paper_caliper(spec.paper, ctx.rates)

    resolved = spec.as_dict()
    resolved["lane_profile"] = lane.as_dict()
    resolved["rate_table"] = ctx.rates["table_version"]
    resolved["rate_table_captured"] = ctx.rates["captured_utc"]

    ctx.write_json("intake", "spec.resolved.json", resolved)

    lines = [
        f"# Intake - {spec.full_title}",
        "",
        f"- **Slug**: `{spec.slug}`",
        f"- **Byline**: {spec.author} / {spec.imprint} (locked)",
        f"- **Lane**: {lane.name} (`{lane.key}`) - claim risk {lane.claim_risk}",
        f"- **Units**: {len(spec.units)} {lane.unit_plural}",
        f"- **Trim / paper / ink**: {spec.trim[0]}x{spec.trim[1]} / {spec.paper} / {spec.ink}",
        f"- **Rate table**: {ctx.rates['table_version']} captured {ctx.rates['captured_utc']}",
        f"- **Spec fingerprint**: `{spec.fingerprint()}`",
        "",
        "## Reader",
        f"- **Who**: {spec.reader}",
        f"- **Problem**: {spec.reader_problem}",
        f"- **Promise**: {spec.promise}",
        f"- **Transformation**: {spec.transformation}",
        "",
        "## Gates this lane arms",
        f"- Source ledger required: **{lane.source_ledger_required}**",
        f"- Professional review required: **{lane.professional_review_required}**"
        + (f" ({lane.review_discipline})" if lane.professional_review_required else ""),
        f"- Max near-duplicate paragraph ratio: **{lane.max_repetition_ratio:.0%}**",
        f"- Min concrete markers per 100 words: **{lane.min_concrete_density}**",
        "",
        lane.notes,
        "",
    ]
    ctx.write("intake", "intake.md", "\n".join(lines))
    ctx.say(f"intake: {len(spec.units)} {lane.unit_plural}, lane={lane.key}, slug={spec.slug}")
