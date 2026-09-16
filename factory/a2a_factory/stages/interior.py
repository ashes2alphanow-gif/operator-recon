"""G3 - interior. Blocks in, print-ready PDF out.

Margins depend on page count and page count depends on margins, so the build
iterates until the gutter band it used is the gutter band the finished book
actually needs. It does not guess and move on.
"""
from __future__ import annotations

from reportlab.lib.colors import Color, black, white
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas

from .. import kdp, typography
from ..context import Run
from ..frontmatter import front_blocks, back_blocks

PT = 72.0
RULE_GREY = Color(0.55, 0.55, 0.55)


def _wrap(text: str, font: str, size: float, width: float) -> list:
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if pdfmetrics.stringWidth(trial, font, size) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


class Interior:
    def __init__(self, spec, style, margins, out_path, blocks_doc):
        self.spec, self.st, self.mg = spec, style, margins
        self.doc = blocks_doc
        self.w, self.h = spec.trim[0] * PT, spec.trim[1] * PT
        self.c = rl_canvas.Canvas(str(out_path), pagesize=(self.w, self.h),
                                  initialFontName=typography.FONTS['body'][0])
        self.c.setTitle(spec.full_title)
        self.c.setAuthor(spec.author)
        self.c.setSubject(spec.promise)
        self.c.setCreator(f"A2A Publishing Factory / {spec.imprint}")
        self.page = 1
        self.in_body = False
        self.body_first_page = None
        self.opener_page = False
        self.running_head = ""
        self.unit_pages = {}
        self.bodyfont = typography.FONTS["body"][0]
        self.boldfont = typography.FONTS["body_bold"][0]
        self.italfont = typography.FONTS["body_italic"][0]
        self.dispfont = typography.FONTS["display"][0]
        self.dispreg = typography.FONTS["display_reg"][0]
        self._frame()

    # ---- geometry ------------------------------------------------------
    def _frame(self) -> None:
        recto = self.page % 2 == 1
        left = (self.mg.gutter if recto else self.mg.outer) * PT
        right = (self.mg.outer if recto else self.mg.gutter) * PT
        self.x0 = left
        self.x1 = self.w - right
        self.measure = self.x1 - self.x0
        self.top = self.h - self.mg.top * PT
        self.bottom = self.mg.bottom * PT
        self.y = self.top
        self.page_dirty = False

    def _room(self, need: float) -> None:
        if self.y - need < self.bottom:
            self.new_page()

    def new_page(self) -> None:
        self._decorate()
        self.c.showPage()
        self.page += 1
        self.opener_page = False
        self._frame()

    def _decorate(self) -> None:
        if not self.in_body or not self.page_dirty:
            return
        folio = self.page - (self.body_first_page or self.page) + 1
        self.c.setFont(self.bodyfont, self.st.folio_size)
        self.c.setFillColor(black)
        self.c.drawCentredString(self.w / 2, self.mg.bottom * PT / 2 + 2, str(folio))
        if self.opener_page or not self.running_head:
            return
        recto = self.page % 2 == 1
        head = self.running_head if recto else self.spec.title.upper()
        self.c.setFont(self.dispreg, self.st.running_head_size)
        self.c.setFillColor(Color(0.35, 0.35, 0.35))
        y = self.h - self.mg.top * PT + self.st.running_head_size * 1.6
        text = _spaced(head.upper())
        if recto:
            self.c.drawRightString(self.x1, y, text)
        else:
            self.c.drawString(self.x0, y, text)
        self.c.setFillColor(black)

    def recto_break(self) -> None:
        if self.y < self.top - 0.5:          # page has content on it
            self.new_page()
        while self.page % 2 == 0:
            self.new_page()

    # ---- drawing -------------------------------------------------------
    def para(self, text: str, font=None, size=None, leading=None, indent=0.0,
             align="left", space_before=0.0, space_after=0.0, color=black) -> None:
        font = font or self.bodyfont
        size = size or self.st.body_size
        leading = leading or self.st.body_leading
        self.y -= space_before
        lines, cur, first, avail = [], "", True, self.measure - indent
        for w in text.split():
            trial = f"{cur} {w}".strip()
            if pdfmetrics.stringWidth(trial, font, size) <= avail or not cur:
                cur = trial
            else:
                lines.append((indent if first else 0.0, cur))
                first, avail, cur = False, self.measure, w
        if cur:
            lines.append((indent if first else 0.0, cur))
        self.c.setFillColor(color)
        for off, ln in lines:
            self._room(leading)
            self.page_dirty = True
            self.c.setFont(font, size)
            if align == "center":
                self.c.drawCentredString(self.w / 2, self.y - size, ln)
            else:
                self.c.drawString(self.x0 + off, self.y - size, ln)
            self.y -= leading
        self.c.setFillColor(black)
        self.y -= space_after

    def rule_line(self, width_frac: float = 0.18) -> None:
        self._room(self.st.body_leading * 2)
        self.y -= self.st.body_leading * 0.8
        self.page_dirty = True
        self.c.setStrokeColor(RULE_GREY)
        self.c.setLineWidth(0.7)
        half = self.measure * width_frac / 2
        self.c.line(self.w / 2 - half, self.y, self.w / 2 + half, self.y)
        self.c.setStrokeColor(black)
        self.y -= self.st.body_leading * 0.8

    def write_lines(self, n: int) -> None:
        gap = self.st.body_leading * 1.6
        for _ in range(n):
            self._room(gap)
            self.page_dirty = True
            self.y -= gap
            self.c.setStrokeColor(Color(0.70, 0.70, 0.70))
            self.c.setLineWidth(0.6)
            self.c.line(self.x0, self.y + 3, self.x1, self.y + 3)
            self.c.setStrokeColor(black)

    # ---- block stream --------------------------------------------------
    def render(self, blocks: list) -> None:
        for b in blocks:
            t = b["t"]
            if t == "pagebreak":
                self.new_page()
            elif t == "recto_break":
                self.recto_break()
            elif t == "head":
                self.running_head = b.get("text", "")
            elif t == "center":
                self._center(b)
            elif t == "fineprint":
                self._fineprint(b["lines"])
            elif t == "toc":
                self._toc()
            elif t == "anchor_index":
                self._anchor_index()
            elif t == "source_list":
                self._source_list()
            elif t == "unit_open":
                self._unit_open(b)
            elif t == "anchor":
                self._anchor(b)
            elif t == "subhead":
                self.para(_spaced(b["text"].upper()), font=self.dispfont,
                          size=self.st.subhead_size, leading=self.st.subhead_size * 1.4,
                          space_before=self.st.body_leading * 1.1,
                          space_after=self.st.body_leading * 0.35)
            elif t == "p":
                indent = self.st.para_indent if b.get("_cont") else 0.0
                self.para(b["text"], indent=indent)
            elif t == "prayer":
                self._fenced(b["text"], self.italfont)
            elif t == "callout":
                self._fenced(b["text"], self.bodyfont, bar=True)
            elif t == "lines":
                self.write_lines(int(b["n"]))
            elif t == "rule":
                self.rule_line()
            else:
                raise ValueError(f"unknown block type {t!r}")

    def _center(self, b) -> None:
        top_pad = self.h * (0.22 if b.get("v") == "upper" else 0.38)
        self.y = self.h - top_pad
        for ln in b["lines"]:
            s = ln["style"]
            if s == "gap":
                self.y -= self.st.body_leading * 2.2
                continue
            font, size = {
                "display_lg": (self.dispfont, self.st.unit_title_size * 1.55),
                "display_sm": (self.dispfont, self.st.unit_title_size * 0.85),
                "body_it": (self.italfont, self.st.body_size * 1.15),
                "small_caps": (self.dispreg, self.st.body_size * 0.85),
            }[s]
            text = _spaced(ln["text"]) if s in ("display_lg", "display_sm", "small_caps") else ln["text"]
            for line in _wrap(text, font, size, self.measure):
                self.page_dirty = True
                self.c.setFont(font, size)
                self.c.drawCentredString(self.w / 2, self.y - size, line)
                self.y -= size * 1.35
            self.y -= size * 0.5

    def _fineprint(self, lines) -> None:
        body = sum(1 for ln in lines if ln)
        gaps = sum(0.5 for ln in lines if not ln)
        need = self.st.body_leading * 0.82 * (body + gaps)
        self.y = min(self.bottom + need + self.st.body_leading * 2, self.top)
        for ln in lines:
            if not ln:
                self.y -= self.st.body_leading * 0.5
                continue
            self.para(ln, size=self.st.body_size * 0.82,
                      leading=self.st.body_leading * 0.82)

    def _toc(self) -> None:
        self.para(_spaced("CONTENTS"), font=self.dispfont, size=self.st.subhead_size * 1.25,
                  leading=self.st.subhead_size * 2.0, align="center",
                  space_after=self.st.body_leading * 1.2)
        size = self.st.body_size * 0.95
        for num, title, page in self.doc["toc"]:
            self._room(self.st.body_leading)
            self.page_dirty = True
            self.c.setFont(self.bodyfont, size)
            label = f"{num}.  {title}"
            self.c.drawString(self.x0, self.y - size, label[:64])
            if page:
                self.c.drawRightString(self.x1, self.y - size, str(page))
            self.y -= self.st.body_leading

    def _anchor_index(self) -> None:
        size = self.st.body_size * 0.9
        for cite, num, title in self.doc["anchors"]:
            self._room(self.st.body_leading)
            self.page_dirty = True
            self.c.setFont(self.bodyfont, size)
            self.c.drawString(self.x0, self.y - size, f"{cite}")
            self.c.drawRightString(self.x1, self.y - size, str(num))
            self.y -= self.st.body_leading

    def _source_list(self) -> None:
        for s in self.doc.get("sources", []):
            self.para(s, size=self.st.body_size * 0.9,
                      leading=self.st.body_leading * 0.92,
                      space_after=self.st.body_leading * 0.25)

    def _unit_open(self, b) -> None:
        self.in_body = True
        if self.body_first_page is None:
            self.body_first_page = self.page
        if self.spec.lane_profile.unit_type == "chapter":
            self.recto_break()
        elif self.y < self.top - 0.5:
            self.new_page()
        self.opener_page = True
        self.running_head = b["title"]
        self.unit_pages[b["number"]] = self.page
        self.y = self.top - self.st.drop_from_top
        label = f"{self.spec.lane_profile.unit_type.upper()} {b['number']}"
        self.para(_spaced(label), font=self.dispreg, size=self.st.unit_number_size,
                  leading=self.st.unit_number_size * 2.0)
        self.para(b["title"], font=self.dispfont, size=self.st.unit_title_size,
                  leading=self.st.unit_title_size * 1.22,
                  space_after=self.st.body_leading * 0.9)

    def _anchor(self, b) -> None:
        self.y -= self.st.body_leading * 0.3
        self.para(b["text"], font=self.italfont, size=self.st.anchor_size,
                  leading=self.st.anchor_size * 1.4, indent=self.st.para_indent)
        if b.get("cite"):
            self.para(_spaced(b["cite"].upper()), font=self.dispreg,
                      size=self.st.anchor_size * 0.76,
                      leading=self.st.anchor_size * 1.2, indent=self.st.para_indent,
                      color=Color(0.35, 0.35, 0.35))
        self.y -= self.st.body_leading * 0.55

    def _fenced(self, text: str, font, bar: bool = False) -> None:
        self.y -= self.st.body_leading * 0.5
        y_start = self.y
        self.para(text, font=font, size=self.st.body_size,
                  leading=self.st.body_leading, indent=self.st.para_indent * 1.4)
        if bar and self.y < y_start:
            self.c.setStrokeColor(RULE_GREY)
            self.c.setLineWidth(1.2)
            self.c.line(self.x0, y_start - 2, self.x0, self.y + 6)
            self.c.setStrokeColor(black)
        self.y -= self.st.body_leading * 0.5

    def finish(self) -> int:
        self._decorate()
        self.c.showPage()
        total = self.page
        if total % 2:                      # books print on leaves, not pages
            self.c.showPage()
            total += 1
        self.c.save()
        return total


def _spaced(s: str) -> str:
    """Letter-spacing for display type, done the cheap reliable way.

    Words keep a wider gap so a spaced-out running head still reads as words.
    """
    return "   ".join(" ".join(w) for w in s.split())


def _blocks_for(ctx: Run, unit_blocks: list) -> list:
    out = []
    for u in unit_blocks:
        prev_was_text = False
        for b in u["blocks"]:
            b = dict(b)
            if b["t"] == "p":
                b["_cont"] = prev_was_text
                prev_was_text = True
            elif b["t"] in ("subhead", "unit_open", "anchor", "rule", "lines"):
                prev_was_text = False
            out.append(b)
    return out


def run(ctx: Run) -> None:
    spec = ctx.spec
    lane = spec.lane_profile
    style = typography.style_for(spec.trim)
    typography.register(pdfmetrics, TTFont)

    src = ctx.read_json("manuscript", "blocks.json")
    plan = ctx.read_json("blueprint", "blueprint.json")
    body = _blocks_for(ctx, src["units"])

    anchors = []
    for u in src["units"]:
        for b in u["blocks"]:
            if b["t"] == "anchor" and b.get("cite"):
                anchors.append((b["cite"], u["number"], u["title"]))
    sources = [s if isinstance(s, str) else s.get("citation", "")
               for s in (spec.raw.get("sources") or [])]

    out_path = ctx.path("interior", f"{spec.slug}_interior_"
                                    f"{spec.trim[0]}x{spec.trim[1]}.pdf")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    assumed = plan["estimated_pages"]
    history = []
    for attempt in range(1, 6):
        margins = kdp.margins_for(max(assumed, 24), ctx.rates, bleed=False)
        doc = {"toc": [(u["number"], u["title"], None) for u in src["units"]],
               "anchors": anchors, "sources": sources}
        # pass 1 computes where each unit lands, pass 2 prints the real numbers
        for _pass in (1, 2):
            iv = Interior(spec, style, margins, out_path, doc)
            iv.render(front_blocks(spec, lane.front_matter))
            iv.render(body)
            iv.render(back_blocks(spec, lane.back_matter))
            pages = iv.finish()
            first = iv.body_first_page or 1
            doc["toc"] = [(u["number"], u["title"],
                           iv.unit_pages.get(u["number"], 0) - first + 1)
                          for u in src["units"]]
        history.append({"attempt": attempt, "gutter_assumed_pages": assumed,
                        "gutter": margins.gutter, "pages_rendered": pages})
        if kdp.gutter_min(max(assumed, 24), ctx.rates) == kdp.gutter_min(pages, ctx.rates):
            break
        assumed = pages
    else:
        raise RuntimeError("interior margins did not converge in 5 attempts")

    ctx.adopt(out_path)
    econ = kdp.economics(pages, spec.ink, spec.paper, spec.trim[0], spec.trim[1],
                         ctx.rates, list_price=spec.list_price or None)
    ctx.write_json("interior", "interior.json", {
        "pdf": out_path.name,
        "page_count": pages,
        "trim": [spec.trim[0], spec.trim[1]],
        "paper": spec.paper,
        "ink": spec.ink,
        "margins": margins.as_dict(),
        "margin_convergence": history,
        "words": src["total_words"],
        "words_per_page_actual": round(src["total_words"] / pages, 1),
        "body_first_page": first,
        "unit_start_pages": {str(k): v for k, v in iv.unit_pages.items()},
        "fonts_embedded": [n for n, _ in typography.FONTS.values()],
        "font_licence": typography.FONT_LICENSE,
        "economics": econ.as_dict(),
    })
    ctx.say(f"interior: {pages} pages, {src['total_words']:,} words, "
            f"gutter {margins.gutter}\", print ${econ.print_cost:.2f}")
