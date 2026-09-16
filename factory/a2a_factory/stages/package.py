"""G7 - the package a human signs for."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..context import Run


def run(ctx: Run) -> None:
    spec = ctx.spec
    interior = ctx.read_json("interior", "interior.json")
    cover = ctx.read_json("cover", "cover_geometry.json")
    listing = ctx.read_json("listing", "listing.json")
    econ = listing["economics"]

    verdicts = {}
    gdir = ctx.out / "gates"
    for f in sorted(gdir.glob("*.json")):
        verdicts[f.stem] = json.loads(f.read_text())

    manifest = {
        "slug": spec.slug,
        "title": spec.full_title,
        "author": spec.author,
        "imprint": spec.imprint,
        "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "spec_fingerprint": spec.fingerprint(),
        "rate_table": ctx.rates["table_version"],
        "page_count": interior["page_count"],
        "spine_in": cover["spine"],
        "wrap_in": [cover["wrap_w"], cover["wrap_h"]],
        "gate_results": {k: v["result"] for k, v in verdicts.items()},
        "gate_counts": {k: v["counts"] for k, v in verdicts.items()},
        "artifacts": ctx.artifacts,
    }
    ctx.write_json("package", "manifest.json", manifest)

    p1 = []
    for name, v in verdicts.items():
        for f in v["findings"]:
            if f["severity"] == "P1":
                p1.append(f"- **[{name}]** {f['message']}"
                          + (f"  \n  _fix_: {f['fix']}" if f.get("fix") else ""))

    lines = [
        f"# APPROVAL REQUIRED - {spec.full_title}",
        "",
        "The engine has taken this as far as a machine should. Nothing about this "
        "title reaches Amazon until a human opens the two PDFs and signs below.",
        "",
        "## What was built",
        f"- Interior: `03_interior/{interior['pdf']}` - **{interior['page_count']} pages**, "
        f"{interior['words']:,} words, {spec.trim[0]}x{spec.trim[1]} in, {spec.paper} paper",
        f"- Cover wrap: `04_cover/{cover['production_pdf']}` - "
        f"**{cover['wrap_w']:.4f} x {cover['wrap_h']:.4f} in**, spine "
        f"**{cover['spine']:.4f} in**",
        f"- Cover proof with guides: `04_cover/{cover['proof_pdf']}`",
        f"- Listing pack: `05_listing/listing.md`",
        f"- Ledgers: `06_compliance/ledgers.json`, disclosure sheet "
        f"`06_compliance/kdp_disclosure.md`",
        "",
        "## Money",
        f"- Print cost **${econ['print_cost']:.2f}** at {interior['page_count']} pages "
        f"(rate table {econ['rate_table']}, captured {ctx.rates['captured_utc']})",
        f"- List **${econ['list_price']:.2f}** against a KDP floor of "
        f"${econ['min_list_price']:.2f}",
        f"- Royalty **${econ['royalty_per_copy']:.2f}** a copy",
    ]
    if listing.get("breakeven_units"):
        lines.append(f"- Break-even on ${listing['fixed_spend_usd']:,.2f} spend: "
                     f"**{listing['breakeven_units']} copies**")
    lines += [
        "",
        "## Gates",
        "",
        "| gate | result | P0 | P1 | P2 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for k, v in verdicts.items():
        c = v["counts"]
        lines.append(f"| {k} | **{v['result']}** | {c['P0']} | {c['P1']} | {c['P2']} |")

    if p1:
        lines += ["", "## Fix before publish (P1)", ""] + p1
    lines += [
        "",
        "## Human checks the engine cannot do",
        "- [ ] Open the interior PDF and read three pages at random. Does it sound like you?",
        "- [ ] Open the cover proof. Trim guides clear of all type? Barcode zone empty?",
        "- [ ] Shrink the front cover to 160 px tall. Is the title still readable?",
        "- [ ] Confirm the printing cost inside KDP title setup against the number above.",
        "- [ ] Answer the KDP AI content questions from `06_compliance/kdp_disclosure.md`.",
        "- [ ] Confirm the three categories are still live in KDP's browse tree.",
    ]
    if spec.lane_profile.professional_review_required:
        lines.append(f"- [ ] {spec.lane_profile.review_discipline} review is on file and "
                     "the reviewer has seen this exact draft.")
    lines += [
        "",
        "## Sign-off",
        "",
        "```",
        "Approved by: ______________________   Date: ____________",
        f"Build fingerprint: {spec.fingerprint()} / rate table {ctx.rates['table_version']}",
        "```",
        "",
    ]
    ctx.write("package", "APPROVAL_REQUIRED.md", "\n".join(lines))

    upload = [
        f"# KDP upload order - {spec.full_title}", "",
        "1. Paperback > Title: paste `title` and `subtitle` from `05_listing/listing.md`",
        f"2. Author: {spec.author} (primary). Imprint/publisher: {spec.imprint}",
        "3. Description: paste the block verbatim",
        "4. Keywords: all seven slots",
        "5. Categories: all three",
        "6. AI content questions: answer from `06_compliance/kdp_disclosure.md`",
        f"7. ISBN: {listing['isbn']}",
        f"8. Print options: {spec.trim[0]} x {spec.trim[1]} in, {spec.paper} paper, "
        f"{'black & white' if spec.ink == 'bw' else spec.ink} interior, matte cover",
        f"9. Upload interior `{interior['pdf']}` and cover "
        f"`{cover['production_pdf']}`",
        "10. Run KDP's previewer end to end. If it reports a different page count than "
        f"{interior['page_count']}, stop and rebuild the cover.",
        f"11. Price: ${econ['list_price']:.2f} US. Confirm KDP's own printing cost matches "
        f"${econ['print_cost']:.2f} before saving.",
        "12. Order the proof copy. Do not hit publish off a screen.",
        "",
    ]
    ctx.write("package", "KDP_UPLOAD_CHECKLIST.md", "\n".join(upload))
    ctx.say(f"package: {len(ctx.artifacts)} artifacts, manifest + approval sheet written")
