"""House typography. One place decides how an A2A page looks."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path

FONT_DIR = Path("/usr/share/fonts/truetype/liberation")
FONTS = {
    "body": ("A2ASerif", FONT_DIR / "LiberationSerif-Regular.ttf"),
    "body_bold": ("A2ASerif-Bold", FONT_DIR / "LiberationSerif-Bold.ttf"),
    "body_italic": ("A2ASerif-Italic", FONT_DIR / "LiberationSerif-Italic.ttf"),
    "display": ("A2ADisplay", FONT_DIR / "LiberationSans-Bold.ttf"),
    "display_reg": ("A2ADisplay-Reg", FONT_DIR / "LiberationSans-Regular.ttf"),
}
FONT_LICENSE = "Liberation fonts, SIL Open Font License 1.1 - embedding and print use permitted."


@dataclass(frozen=True)
class Style:
    body_size: float
    body_leading: float
    para_indent: float          # points
    space_after_para: float
    unit_number_size: float
    unit_title_size: float
    subhead_size: float
    anchor_size: float
    folio_size: float
    running_head_size: float
    drop_from_top: float        # points of air above a unit opener title

    def as_dict(self) -> dict:
        return asdict(self)


POCKET = Style(          # 5.5 x 8.5 -- devotional, legacy
    body_size=10.5, body_leading=15.0, para_indent=13.0, space_after_para=0.0,
    unit_number_size=9.0, unit_title_size=17.0, subhead_size=9.5,
    anchor_size=10.0, folio_size=9.0, running_head_size=8.0, drop_from_top=54.0,
)
TRADE = Style(           # 6 x 9 -- doctrine, technical, practice
    body_size=11.0, body_leading=16.0, para_indent=15.0, space_after_para=0.0,
    unit_number_size=9.5, unit_title_size=20.0, subhead_size=10.5,
    anchor_size=10.5, folio_size=9.5, running_head_size=8.5, drop_from_top=66.0,
)


def style_for(trim: tuple) -> Style:
    return POCKET if float(trim[0]) <= 5.6 else TRADE


def register(pdfmetrics, TTFont) -> None:
    for _, (name, path) in FONTS.items():
        if not path.exists():
            raise FileNotFoundError(
                f"house font missing: {path}. Install the Liberation font family "
                "(apt: fonts-liberation) or point typography.FONT_DIR at it."
            )
        pdfmetrics.registerFont(TTFont(name, str(path)))
