"""KDP print arithmetic. Every countable thing about a physical book lives here.

Nothing in this module guesses. Values come from a dated rate table on disk
(factory/rates/kdp_rates_<version>.json) and anything the table marks
"unverified" refuses to produce a price unless the caller explicitly accepts
the risk. Rates change; the table is versioned so a build can be reproduced.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

RATES_DIR = Path(__file__).resolve().parent.parent / "rates"
DEFAULT_RATE_VERSION = "2026-09"


class RateError(RuntimeError):
    """Raised when a price cannot be computed from verified inputs."""


class SpecError(ValueError):
    """Raised when a physical book configuration is outside KDP limits."""


def load_rates(version: str = DEFAULT_RATE_VERSION) -> dict:
    path = RATES_DIR / f"kdp_rates_{version}.json"
    if not path.exists():
        raise RateError(f"no rate table for version {version!r} at {path}")
    return json.loads(path.read_text())


# --------------------------------------------------------------------------
# trim
# --------------------------------------------------------------------------

def trim_class(width_in: float, height_in: float, rates: dict) -> str:
    """'regular' or 'large' -- drives both print cost and margin rules."""
    key = (round(width_in, 2), round(height_in, 2))
    for w, h in rates["regular_trim_sizes_in"]:
        if (round(w, 2), round(h, 2)) == key:
            return "regular"
    for w, h in rates["large_trim_sizes_in"]:
        if (round(w, 2), round(h, 2)) == key:
            return "large"
    raise SpecError(
        f"trim {width_in}x{height_in} is not a KDP paperback trim size in rate "
        f"table {rates['table_version']}"
    )


# --------------------------------------------------------------------------
# margins
# --------------------------------------------------------------------------

def gutter_min(pages: int, rates: dict) -> float:
    for band in rates["gutter_minimums_in"]:
        if band["min_pages"] <= pages <= band["max_pages"]:
            return band["gutter"]
    raise SpecError(f"{pages} pages is outside every KDP gutter band (24-828)")


def outer_min(bleed: bool, rates: dict) -> float:
    return rates["outer_margin_min_in"]["with_bleed" if bleed else "no_bleed"]


@dataclass(frozen=True)
class Margins:
    gutter: float
    outer: float
    top: float
    bottom: float

    def as_dict(self) -> dict:
        return asdict(self)


def margins_for(pages: int, rates: dict, bleed: bool = False,
                gutter_pad: float = 0.125, edge_pad: float = 0.375) -> Margins:
    """House margins: KDP minimum plus deliberate padding.

    KDP minimums are the point at which a book is *rejected*, not the point at
    which it reads well. A2A house style pads the gutter and edges so the text
    block does not crowd the binding on a book people actually hold open.
    """
    g = round(gutter_min(pages, rates) + gutter_pad, 4)
    o = round(outer_min(bleed, rates) + edge_pad, 4)
    return Margins(gutter=g, outer=o, top=o, bottom=o)


# --------------------------------------------------------------------------
# spine + cover wrap
# --------------------------------------------------------------------------

def paper_caliper(paper: str, rates: dict) -> float:
    try:
        return rates["paper_caliper_in_per_page"][paper]["value"]
    except KeyError as exc:
        raise SpecError(f"unknown paper type {paper!r}") from exc


def spine_width(pages: int, paper: str, rates: dict) -> float:
    """KDP paperback spine = (pages x caliper) + cover allowance."""
    assert_page_count(pages, paper, rates)
    return round(pages * paper_caliper(paper, rates) + rates["spine_cover_allowance_in"], 6)


def assert_page_count(pages: int, paper: str, rates: dict) -> None:
    limits = rates["page_count_limits"]
    if pages < limits["min_pages"]:
        raise SpecError(f"{pages} pages is below the KDP paperback minimum of {limits['min_pages']}")
    key = {
        "white": "max_pages_bw_white",
        "cream": "max_pages_bw_cream",
        "premium_color": "max_pages_premium_color",
        "standard_color": "max_pages_standard_color",
    }[paper]
    if pages > limits[key]:
        raise SpecError(f"{pages} pages exceeds the KDP maximum of {limits[key]} for {paper} paper")


@dataclass(frozen=True)
class CoverGeometry:
    trim_w: float
    trim_h: float
    pages: int
    paper: str
    spine: float
    bleed: float
    wrap_w: float
    wrap_h: float
    front_x0: float
    spine_x0: float
    back_x0: float
    barcode_w: float
    barcode_h: float
    barcode_x0: float
    barcode_y0: float
    spine_text_allowed: bool
    house_spine_text_allowed: bool
    rate_table: str

    def as_dict(self) -> dict:
        return asdict(self)


def cover_geometry(trim_w: float, trim_h: float, pages: int, paper: str,
                   rates: dict) -> CoverGeometry:
    """Full paperback wrap, flat, in inches, origin at bottom-left of the bleed.

    wrap width  = bleed + back trim + spine + front trim + bleed
    wrap height = bleed + trim height + bleed
    """
    trim_class(trim_w, trim_h, rates)  # validates the trim
    spine = spine_width(pages, paper, rates)
    bleed = rates["bleed_in"]
    wrap_w = round(bleed * 2 + trim_w * 2 + spine, 6)
    wrap_h = round(trim_h + rates["cover_height_allowance_in"], 6)
    back_x0 = bleed
    spine_x0 = round(bleed + trim_w, 6)
    front_x0 = round(spine_x0 + spine, 6)
    # KDP reserves a 2" x 1.2" white barcode block, 0.25" up from the trim
    # bottom and 0.25" in from the back cover's outer trim edge.
    barcode_w, barcode_h = 2.0, 1.2
    barcode_x0 = round(back_x0 + 0.25, 6)
    barcode_y0 = round(bleed + 0.25, 6)
    return CoverGeometry(
        trim_w=trim_w, trim_h=trim_h, pages=pages, paper=paper, spine=spine,
        bleed=bleed, wrap_w=wrap_w, wrap_h=wrap_h,
        front_x0=front_x0, spine_x0=spine_x0, back_x0=back_x0,
        barcode_w=barcode_w, barcode_h=barcode_h,
        barcode_x0=barcode_x0, barcode_y0=barcode_y0,
        spine_text_allowed=pages >= rates["spine_text_min_pages"],
        house_spine_text_allowed=pages >= rates["house_spine_text_min_pages"],
        rate_table=rates["table_version"],
    )


# --------------------------------------------------------------------------
# money
# --------------------------------------------------------------------------

def _cost_key(ink: str, tclass: str) -> str:
    return {
        ("bw", "regular"): "bw_regular_trim",
        ("bw", "large"): "bw_large_trim",
        ("premium_color", "regular"): "premium_color_regular_trim",
        ("premium_color", "large"): "premium_color_large_trim",
        ("standard_color", "regular"): "standard_color_regular_trim",
        ("standard_color", "large"): "standard_color_large_trim",
    }[(ink, tclass)]


def print_cost(pages: int, ink: str, trim_w: float, trim_h: float, rates: dict,
               market: str = "US", allow_unverified: bool = False) -> float:
    tclass = trim_class(trim_w, trim_h, rates)
    try:
        band = rates["print_cost"][market][_cost_key(ink, tclass)]
    except KeyError as exc:
        raise RateError(f"no print cost band for ink={ink} trim_class={tclass} market={market}") from exc
    if band["confidence"] != "verified" and not allow_unverified:
        raise RateError(
            f"print cost band {_cost_key(ink, tclass)} in rate table "
            f"{rates['table_version']} is marked '{band['confidence']}'. "
            "Confirm the figure in KDP title setup, update the rate table, then "
            "re-run. Pass allow_unverified=True only for scratch estimates."
        )
    flat_max = band.get("flat_max_pages") or 0
    if pages <= flat_max and band.get("flat_cost") is not None:
        return round(float(band["flat_cost"]), 2)
    return round(band["fixed_cost"] + band["per_page"] * pages, 2)


def min_list_price(cost: float, rates: dict) -> float:
    """Lowest list price KDP will accept at the 60% paperback rate."""
    rate = rates["royalty"]["paperback_rate"]
    return math.ceil((cost / rate) * 100) / 100


def royalty(list_price: float, cost: float, rates: dict) -> float:
    rate = rates["royalty"]["paperback_rate"]
    return round(list_price * rate - cost, 2)


def charm_price(floor: float) -> float:
    """Round a floor price up to the next .99 -- the only price shape A2A uses."""
    whole = math.floor(floor)
    candidate = whole + 0.99
    if candidate < floor - 1e-9:
        candidate = whole + 1.99
    return round(candidate, 2)


@dataclass(frozen=True)
class Economics:
    pages: int
    ink: str
    paper: str
    trim: str
    print_cost: float
    min_list_price: float
    list_price: float
    royalty_per_copy: float
    royalty_rate: float
    rate_table: str
    verified: bool

    def as_dict(self) -> dict:
        return asdict(self)


def economics(pages: int, ink: str, paper: str, trim_w: float, trim_h: float,
              rates: dict, list_price: Optional[float] = None,
              market: str = "US", allow_unverified: bool = False) -> Economics:
    cost = print_cost(pages, ink, trim_w, trim_h, rates, market, allow_unverified)
    floor = min_list_price(cost, rates)
    price = list_price if list_price is not None else charm_price(floor)
    if price < floor - 1e-9:
        raise SpecError(
            f"list price ${price:.2f} is below the KDP floor of ${floor:.2f} for a "
            f"{pages}-page {ink} book (print cost ${cost:.2f})"
        )
    band = rates["print_cost"][market][_cost_key(ink, trim_class(trim_w, trim_h, rates))]
    return Economics(
        pages=pages, ink=ink, paper=paper, trim=f"{trim_w}x{trim_h}",
        print_cost=cost, min_list_price=floor, list_price=round(price, 2),
        royalty_per_copy=royalty(price, cost, rates),
        royalty_rate=rates["royalty"]["paperback_rate"],
        rate_table=rates["table_version"],
        verified=band["confidence"] == "verified",
    )


def breakeven_units(fixed_spend: float, royalty_per_copy: float) -> int:
    if royalty_per_copy <= 0:
        raise SpecError("royalty per copy is zero or negative; the title cannot break even")
    return math.ceil(fixed_spend / royalty_per_copy)
