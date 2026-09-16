"""The single input to the engine: one title spec.

One YAML file in, one finished title package out. The spec is the only place a
human decides anything before the human approval stop at the end.
"""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml

from . import lanes

# Identity is locked. The engine will not publish under any other name.
LOCKED_AUTHOR = "Chris G. Stewart"
LOCKED_IMPRINT = "Ashes to Alpha"


class SpecError(ValueError):
    pass


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return re.sub(r"-{2,}", "-", text)


@dataclass
class Unit:
    """One chapter / entry / session. The architecture, not the prose."""
    number: int
    title: str
    thesis: str
    anchor: str = ""
    sections: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class TitleSpec:
    title: str
    subtitle: str
    lane: str
    reader: str
    reader_problem: str
    promise: str
    transformation: str
    units: list
    raw: dict = field(default_factory=dict, repr=False)

    series: str = ""
    volume: str = ""
    edition: str = "First Edition"
    year: int = 2026
    isbn: str = ""                 # blank means "use the free KDP ASIN"
    trim: tuple = ()
    paper: str = ""
    ink: str = ""
    list_price: float = 0.0
    keywords_seed: list = field(default_factory=list)
    categories: list = field(default_factory=list)
    bisac: list = field(default_factory=list)
    compliance: dict = field(default_factory=dict)
    companion_products: list = field(default_factory=list)
    manuscript_dir: str = ""
    slug_override: str = ""

    # ---- derived -------------------------------------------------------
    @property
    def lane_profile(self) -> lanes.Lane:
        return lanes.get(self.lane)

    @property
    def slug(self) -> str:
        if self.slug_override:
            return slugify(self.slug_override)
        base = self.title if not self.volume else f"{self.title} {self.volume}"
        return slugify(base)

    @property
    def author(self) -> str:
        return LOCKED_AUTHOR

    @property
    def imprint(self) -> str:
        return LOCKED_IMPRINT

    @property
    def full_title(self) -> str:
        return f"{self.title}: {self.subtitle}" if self.subtitle else self.title

    def fingerprint(self) -> str:
        payload = json.dumps(self.raw, sort_keys=True, default=str).encode()
        return hashlib.sha256(payload).hexdigest()[:16]

    def as_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw", None)
        d["slug"] = self.slug
        d["author"] = self.author
        d["imprint"] = self.imprint
        d["full_title"] = self.full_title
        d["fingerprint"] = self.fingerprint()
        d["units"] = [u.as_dict() if isinstance(u, Unit) else u for u in self.units]
        return d


REQUIRED = ("title", "lane", "reader", "reader_problem", "promise", "transformation")
PLACEHOLDER = re.compile(r"\[[A-Z][A-Z \-_/]{2,}\]|TBD|TODO|XXX|LOREM IPSUM", re.I)


def load(path: str | Path) -> TitleSpec:
    path = Path(path)
    raw: dict[str, Any] = yaml.safe_load(path.read_text()) or {}

    missing = [k for k in REQUIRED if not raw.get(k)]
    if missing:
        raise SpecError(f"{path.name}: missing required field(s): {', '.join(missing)}")

    lane = lanes.get(raw["lane"])

    units = []
    for i, u in enumerate(raw.get("units") or [], start=1):
        if not u.get("title") or not u.get("thesis"):
            raise SpecError(f"{path.name}: unit {i} needs both a title and a thesis")
        units.append(Unit(
            number=int(u.get("number", i)),
            title=u["title"].strip(),
            thesis=u["thesis"].strip(),
            anchor=(u.get("anchor") or "").strip(),
            sections=u.get("sections") or {},
        ))
    if not units:
        raise SpecError(f"{path.name}: a spec with no units is a wish, not a book")

    numbers = [u.number for u in units]
    if sorted(numbers) != list(range(1, len(units) + 1)):
        raise SpecError(f"{path.name}: unit numbers must run 1..{len(units)} with no gaps or repeats")

    titles = [u.title.lower() for u in units]
    dupes = {t for t in titles if titles.count(t) > 1}
    if dupes:
        raise SpecError(f"{path.name}: duplicate unit titles: {', '.join(sorted(dupes))}")

    if not (lane.min_units <= len(units) <= lane.max_units):
        raise SpecError(
            f"{path.name}: lane '{lane.key}' expects {lane.min_units}-{lane.max_units} "
            f"{lane.unit_type}s; spec has {len(units)}"
        )

    for k, v in raw.items():
        if isinstance(v, str) and PLACEHOLDER.search(v):
            raise SpecError(f"{path.name}: field '{k}' still carries a placeholder: {v!r}")

    author = (raw.get("author") or LOCKED_AUTHOR).strip()
    if author != LOCKED_AUTHOR:
        raise SpecError(
            f"{path.name}: byline is locked to {LOCKED_AUTHOR!r}; spec asked for {author!r}. "
            "Change it in spec.py if the imprint policy ever changes."
        )

    trim = tuple(raw.get("trim") or lane.default_trim)
    spec = TitleSpec(
        title=raw["title"].strip(),
        subtitle=(raw.get("subtitle") or "").strip(),
        lane=lane.key,
        reader=raw["reader"].strip(),
        reader_problem=raw["reader_problem"].strip(),
        promise=raw["promise"].strip(),
        transformation=raw["transformation"].strip(),
        units=units,
        raw=raw,
        series=(raw.get("series") or "").strip(),
        volume=(raw.get("volume") or "").strip(),
        edition=(raw.get("edition") or "First Edition").strip(),
        year=int(raw.get("year", 2026)),
        isbn=(raw.get("isbn") or "").strip(),
        trim=(float(trim[0]), float(trim[1])),
        paper=(raw.get("paper") or lane.default_paper),
        ink=(raw.get("ink") or lane.default_ink),
        list_price=float(raw.get("list_price") or 0.0),
        keywords_seed=list(raw.get("keywords_seed") or []),
        categories=list(raw.get("categories") or []),
        bisac=list(raw.get("bisac") or []),
        compliance=dict(raw.get("compliance") or {}),
        companion_products=list(raw.get("companion_products") or []),
        manuscript_dir=(raw.get("manuscript_dir") or "").strip(),
        slug_override=(raw.get("slug") or "").strip(),
    )
    return spec
