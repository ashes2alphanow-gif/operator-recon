"""The four A2A production lanes.

A lane is not a genre. It is a risk-and-structure profile: it decides how much
evidence a claim needs, what a finished unit of content has to contain, and
which gates are allowed to be advisory instead of blocking.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass(frozen=True)
class Lane:
    key: str
    name: str
    description: str
    unit_type: str                 # what one countable piece of the book is called
    min_units: int
    max_units: int
    min_words_per_unit: int
    max_words_per_unit: int
    required_unit_sections: tuple  # every unit must contain these, by name
    claim_risk: str                # low | elevated | high
    source_ledger_required: bool
    professional_review_required: bool
    review_discipline: str
    front_matter: tuple
    back_matter: tuple
    default_trim: tuple
    default_paper: str
    default_ink: str
    max_repetition_ratio: float    # share of near-duplicate paragraphs tolerated
    min_concrete_density: float    # concrete markers per 100 words (anti-fluff)
    notes: str = ""

    @property
    def unit_plural(self) -> str:
        return (self.unit_type[:-1] + "ies") if self.unit_type.endswith("y") \
            else self.unit_type + "s"

    def as_dict(self) -> dict:
        d = asdict(self)
        d["unit_plural"] = self.unit_plural
        return d


DOCTRINE = Lane(
    key="doctrine",
    name="Doctrine and transformation",
    description=(
        "Argued books that change how a reader operates. FORGED, Battlefield "
        "Relationships, Smarter Than You Think."
    ),
    unit_type="chapter",
    min_units=8, max_units=40,
    min_words_per_unit=1400, max_words_per_unit=4500,
    required_unit_sections=("opening", "doctrine", "drill"),
    claim_risk="elevated",
    source_ledger_required=True,
    professional_review_required=False,
    review_discipline="developmental edit",
    front_matter=("half_title", "title", "copyright", "contents", "authors_note"),
    back_matter=("closing", "about_the_author", "also_by", "review_request"),
    default_trim=(6.0, 9.0), default_paper="cream", default_ink="bw",
    max_repetition_ratio=0.03,
    min_concrete_density=2.5,
    notes="Every chapter ends in an action the reader can take before they sleep.",
)

TECHNICAL = Lane(
    key="technical",
    name="Technical and high-stakes",
    description=(
        "Material where being wrong costs money, health, or a life. Money "
        "Manual, Survival Is a Decision, retirement and safety work."
    ),
    unit_type="chapter",
    min_units=8, max_units=40,
    min_words_per_unit=1200, max_words_per_unit=5000,
    required_unit_sections=("opening", "doctrine", "drill", "sources"),
    claim_risk="high",
    source_ledger_required=True,
    professional_review_required=True,
    review_discipline="licensed professional in the subject domain",
    front_matter=("half_title", "title", "copyright", "disclaimer", "contents", "how_to_use"),
    back_matter=("closing", "worksheets", "sources", "about_the_author", "review_request"),
    default_trim=(6.0, 9.0), default_paper="white", default_ink="bw",
    max_repetition_ratio=0.02,
    min_concrete_density=3.5,
    notes="No number reaches print without a source line and a worked example.",
)

PRACTICE = Lane(
    key="practice",
    name="Guided practice",
    description=(
        "The reader does the work in the book. The Healing Games, journals, "
        "workbooks, puzzle-assisted reflection."
    ),
    unit_type="session",
    min_units=12, max_units=120,
    min_words_per_unit=150, max_words_per_unit=1200,
    required_unit_sections=("prompt", "practice"),
    claim_risk="elevated",
    source_ledger_required=False,
    professional_review_required=True,
    review_discipline="licensed clinician if the book touches trauma or grief",
    front_matter=("half_title", "title", "copyright", "disclaimer", "contents", "how_to_use"),
    back_matter=("closing", "resources", "about_the_author", "review_request"),
    default_trim=(6.0, 9.0), default_paper="white", default_ink="bw",
    max_repetition_ratio=0.05,
    min_concrete_density=1.5,
    notes="Write space is a feature. Padding is still padding -- blank pages are counted, not hidden.",
)

DEVOTIONAL = Lane(
    key="devotional",
    name="Devotional and legacy",
    description=(
        "Short-form daily material and father-to-son legacy products. "
        "A Warrior's Code of Prayer, Unbreakable."
    ),
    unit_type="entry",
    min_units=20, max_units=366,
    min_words_per_unit=200, max_words_per_unit=900,
    required_unit_sections=("anchor", "body", "drill", "prayer"),
    claim_risk="low",
    source_ledger_required=True,
    professional_review_required=False,
    review_discipline="scripture citation and translation licensing check",
    front_matter=("half_title", "title", "copyright", "contents", "how_to_use"),
    back_matter=("closing", "index_of_anchors", "about_the_author", "review_request"),
    default_trim=(5.5, 8.5), default_paper="cream", default_ink="bw",
    max_repetition_ratio=0.04,
    min_concrete_density=2.0,
    notes="Scripture translation licensing is a blocking check, not a footnote.",
)

LANES = {l.key: l for l in (DOCTRINE, TECHNICAL, PRACTICE, DEVOTIONAL)}


def get(key: str) -> Lane:
    try:
        return LANES[key]
    except KeyError as exc:
        raise ValueError(
            f"unknown lane {key!r}; known lanes: {', '.join(sorted(LANES))}"
        ) from exc
