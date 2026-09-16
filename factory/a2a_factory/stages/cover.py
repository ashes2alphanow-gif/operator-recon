"""G4 - cover wrap, built from the interior's real page count.

Two files come out: the production wrap and a proof wrap with the trim, spine
and safe-zone guides drawn on it. The proof is what a human looks at. The
production file is what goes to KDP.
"""
from __future__ import annotations

from reportlab.lib.colors import Color, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

from .. import kdp, typography
from ..context import Run

PT = 72.0
INK = Color(0.043, 0.047, 0.055)       # A2A black
PAPER = Color(0.93, 0.92, 0.90)        # bone
ACCENT = Color(0.78, 0.31, 0.16)       # ember


def _spaced(s: str) -> str:
    return " ".join(s)


def _fit(c, text, font, max_size, width, min_size=8.0):
    size = max_size
    while size > min_size and pdfmetrics.stringWidth(text, font, size) > width:
        size -= 0.5
    return size


def _wrap(text, font, size, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = f"{cur} {w}".strip()
        if pdfmetrics.stringWidth(t, font, size) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _draw(path, spec, g, proof: bool) -> None:
    disp = typography.FONTS["display"][0]
    dreg = typography.FONTS["display_reg"][0]
    serif = typography.FONTS["body"][0]
    ital = typography.FONTS["body_italic"][0]

    W, H = g.wrap_w * PT, g.wrap_h * PT
    c = rl_canvas.Canvas(str(path), pagesize=(W, H), initialFontName=serif)
    c.setTitle(f"{spec.full_title} - cover wrap")
    c.setAuthor(spec.author)
    c.setCreator(f"A2A Publishing Factory / {spec.imprint}")

    c.setFillColor(INK)
    c.rect(0, 0, W, H, stroke=0, fill=1)

    bleed = g.bleed * PT
    front_x = g.front_x0 * PT
    spine_x = g.spine_x0 * PT
    back_x = g.back_x0 * PT
    trim_w, trim_h = g.trim_w * PT, g.trim_h * PT
    safe = 0.25 * PT

    # ---- front ---------------------------------------------------------
    fx0, fx1 = front_x + safe, front_x + trim_w - safe
    fw = fx1 - fx0
    c.setFillColor(ACCENT)
    c.rect(fx0, bleed + trim_h * 0.70, fw * 0.16, 3.2, stroke=0, fill=1)

    title_lines = _wrap(spec.title.upper(), disp, 40, fw)
    size = _fit(c, max(title_lines, key=len), disp, 46, fw, 18)
    y = bleed + trim_h * 0.635
    c.setFillColor(PAPER)
    for ln in title_lines:
        c.setFont(disp, size)
        c.drawString(fx0, y, ln)
        y -= size * 1.12
    if spec.volume:
        c.setFont(dreg, size * 0.30)
        c.setFillColor(ACCENT)
        c.drawString(fx0, y - size * 0.15, _spaced(spec.volume.upper()))
        y -= size * 0.55
    if spec.subtitle:
        sub_size = max(9.5, size * 0.30)
        c.setFillColor(Color(0.72, 0.71, 0.69))
        for ln in _wrap(spec.subtitle, ital, sub_size, fw):
            c.setFont(ital, sub_size)
            c.drawString(fx0, y - sub_size * 1.3, ln)
            y -= sub_size * 1.45
    c.setFillColor(PAPER)
    c.setFont(disp, max(11.0, size * 0.32))
    c.drawString(fx0, bleed + safe + 26, _spaced(spec.author.upper()))
    c.setFont(dreg, max(7.5, size * 0.18))
    c.setFillColor(Color(0.62, 0.61, 0.60))
    c.drawString(fx0, bleed + safe + 10, _spaced(spec.imprint.upper()))

    # ---- spine ---------------------------------------------------------
    if g.house_spine_text_allowed:
        sw = g.spine * PT
        cx = spine_x + sw / 2
        c.saveState()
        c.translate(cx, bleed + trim_h / 2)
        c.rotate(90)
        s_size = min(sw * 0.42, 13.0)
        c.setFillColor(PAPER)
        c.setFont(disp, s_size)
        c.drawCentredString(0, -s_size * 0.36, spec.title.upper())
        c.setFont(dreg, s_size * 0.66)
        c.setFillColor(Color(0.66, 0.65, 0.64))
        c.drawRightString(trim_h / 2 - safe, -s_size * 0.36, spec.author.upper())
        c.restoreState()

    # ---- back ----------------------------------------------------------
    bx0, bx1 = back_x + safe, back_x + trim_w - safe
    bw = bx1 - bx0
    by = bleed + trim_h - safe - 34
    hook = (spec.raw.get("back_cover_hook") or spec.promise).strip()
    c.setFillColor(ACCENT)
    c.rect(bx0, by + 24, bw * 0.16, 3.0, stroke=0, fill=1)
    c.setFillColor(PAPER)
    hsize = 13.0
    for ln in _wrap(hook, disp, hsize, bw):
        c.setFont(disp, hsize)
        c.drawString(bx0, by, ln)
        by -= hsize * 1.28
    by -= 10
    c.setFillColor(Color(0.80, 0.79, 0.77))
    for para in (spec.raw.get("back_cover_copy") or "").strip().split("\n\n"):
        if not para.strip():
            continue
        for ln in _wrap(para.strip(), serif, 10.0, bw):
            c.setFont(serif, 10.0)
            c.drawString(bx0, by, ln)
            by -= 14.0
        by -= 7.0

    # barcode clear zone: KDP prints the barcode here, so nothing else may be
    bc_x, bc_y = g.barcode_x0 * PT, g.barcode_y0 * PT
    bc_w, bc_h = g.barcode_w * PT, g.barcode_h * PT
    c.setFillColor(white)
    c.rect(bc_x, bc_y, bc_w, bc_h, stroke=0, fill=1)
    if proof:
        c.setFillColor(Color(0.55, 0.55, 0.55))
        c.setFont(dreg, 7)
        c.drawString(bc_x + 6, bc_y + bc_h / 2, "KDP BARCODE ZONE 2.0 x 1.2 in")

    # ---- proof guides --------------------------------------------------
    if proof:
        c.setStrokeColor(Color(0.95, 0.35, 0.15))
        c.setLineWidth(0.6)
        c.setDash(4, 3)
        c.rect(bleed, bleed, W - bleed * 2, trim_h, stroke=1, fill=0)   # trim
        c.line(spine_x, 0, spine_x, H)
        c.line(spine_x + g.spine * PT, 0, spine_x + g.spine * PT, H)
        c.setStrokeColor(Color(0.35, 0.75, 0.95))
        c.rect(front_x + safe, bleed + safe, trim_w - safe * 2, trim_h - safe * 2,
               stroke=1, fill=0)
        c.rect(back_x + safe, bleed + safe, trim_w - safe * 2, trim_h - safe * 2,
               stroke=1, fill=0)
        c.setDash()
        c.setFillColor(Color(0.95, 0.35, 0.15))
        c.setFont(dreg, 7.5)
        c.drawString(6, 6, f"PROOF - wrap {g.wrap_w:.4f} x {g.wrap_h:.4f} in | "
                           f"spine {g.spine:.4f} in @ {g.pages} pp {g.paper} | "
                           f"rate table {g.rate_table} | NOT FOR UPLOAD")
    c.showPage()
    c.save()


def run(ctx: Run) -> None:
    spec = ctx.spec
    typography.register(pdfmetrics, TTFont)
    interior = ctx.read_json("interior", "interior.json")   # from disk, not memory
    pages = int(interior["page_count"])

    g = kdp.cover_geometry(spec.trim[0], spec.trim[1], pages, spec.paper, ctx.rates)

    prod = ctx.path("cover", f"{spec.slug}_cover_wrap_{g.wrap_w:.4f}x{g.wrap_h:.4f}in.pdf")
    proof = ctx.path("cover", f"{spec.slug}_cover_PROOF.pdf")
    prod.parent.mkdir(parents=True, exist_ok=True)
    _draw(prod, spec, g, proof=False)
    _draw(proof, spec, g, proof=True)
    ctx.adopt(prod)
    ctx.adopt(proof)

    geom = g.as_dict()
    geom.update({
        "production_pdf": prod.name,
        "proof_pdf": proof.name,
        "page_count_source": "03_interior/interior.json",
        "spine_formula": f"({pages} x {kdp.paper_caliper(spec.paper, ctx.rates)}) + "
                         f"{ctx.rates['spine_cover_allowance_in']} = {g.spine:.6f} in",
        "spine_text_printed": g.house_spine_text_allowed,
    })
    ctx.write_json("cover", "cover_geometry.json", geom)

    brief = f"""# Cover art brief - {spec.full_title}

The engine ships a typographic wrap that is print-legal today. Art direction is
Chris's call, not the engine's. If art replaces the flat field, it has to fit
this geometry exactly:

- Full wrap canvas: **{g.wrap_w:.4f} x {g.wrap_h:.4f} in** at 300 DPI
  = **{round(g.wrap_w * 300)} x {round(g.wrap_h * 300)} px**
- Spine: **{g.spine:.4f} in** starting {g.spine_x0:.4f} in from the left edge
- Front cover panel starts at {g.front_x0:.4f} in
- Keep type 0.25 in inside every trim edge
- Barcode zone stays clear: 2.0 x 1.2 in at ({g.barcode_x0:.2f}, {g.barcode_y0:.2f}) in
- Spine text is {'allowed' if g.house_spine_text_allowed else
  'NOT allowed at this page count under house rule (min '
  f"{ctx.rates['house_spine_text_min_pages']} pages)"}

Thumbnail test before anything else: at 160 px tall the title has to be
readable and the book has to look unlike every other book in the category.

Brand marks: none applied. {spec.imprint} wordmark is white on black when Chris
says to use it.
"""
    ctx.write("cover", "cover_art_brief.md", brief)
    ctx.say(f"cover: spine {g.spine:.4f}\" for {pages} pp, wrap "
            f"{g.wrap_w:.4f}x{g.wrap_h:.4f}\"")
