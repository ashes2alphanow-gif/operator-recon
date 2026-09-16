"""Front and back matter. Generated, never hand-maintained per title."""
from __future__ import annotations

from .spec import TitleSpec

DISCLAIMER = {
    "technical": (
        "This book is general information written from operational experience. "
        "It is not financial, legal, medical, or tax advice, and it does not "
        "create a professional relationship of any kind. Your situation has "
        "details this book cannot see. Before you act on anything in here that "
        "moves money, affects your health, or carries legal weight, take it to a "
        "licensed professional who can look at your actual numbers."
    ),
    "practice": (
        "This book is a structured practice, not treatment. It is not therapy "
        "and it is not a substitute for care from a licensed clinician. If you "
        "are in crisis, stop reading and call or text 988 in the United States, "
        "or your local emergency number. Working through hard material can bring "
        "things up. Do it with support."
    ),
}


def ai_disclosure_line(spec: TitleSpec) -> str:
    c = spec.compliance.get("ai_origin") or {}
    generated = [k for k, v in c.items() if str(v).lower() == "ai-generated"]
    assisted = [k for k, v in c.items() if str(v).lower() == "ai-assisted"]
    if generated:
        return ("Portions of this book (" + ", ".join(sorted(generated)) +
                ") were produced with generative AI and edited by the author. "
                "This has been disclosed to Amazon KDP as required.")
    if assisted:
        return ("This book was written by the author. AI tools were used for "
                "editing and research support only.")
    return "This book was written by the author without generative AI."


def front_blocks(spec: TitleSpec, lane_keys: tuple) -> list:
    b: list = []
    for key in lane_keys:
        if key == "half_title":
            b += [{"t": "center", "v": "upper", "lines": [
                {"text": spec.title.upper(), "style": "display_sm"}]},
                {"t": "pagebreak"}, {"t": "pagebreak"}]
        elif key == "title":
            lines = [{"text": spec.title.upper(), "style": "display_lg"}]
            if spec.subtitle:
                lines.append({"text": spec.subtitle, "style": "body_it"})
            if spec.volume:
                lines.append({"text": spec.volume, "style": "small_caps"})
            lines += [{"text": "", "style": "gap"}, {"text": spec.author, "style": "display_sm"},
                      {"text": spec.imprint.upper(), "style": "small_caps"}]
            b += [{"t": "center", "v": "upper", "lines": lines}, {"t": "pagebreak"}]
        elif key == "copyright":
            fine = [
                f"{spec.full_title}",
                f"Copyright (c) {spec.year} {spec.author}. All rights reserved.",
                "",
                "No part of this book may be reproduced or distributed in any form "
                "without written permission from the author, except brief quotations "
                "in a review.",
                "",
                f"Published by {spec.imprint}.",
                f"{spec.edition}.",
                f"ISBN: {spec.isbn}" if spec.isbn else
                "Identifier: Amazon KDP ASIN (no ISBN assigned).",
                "",
                ai_disclosure_line(spec),
            ]
            src = spec.compliance.get("scripture_translation")
            if src:
                fine += ["", f"Scripture quotations are taken from the {src}."]
            b += [{"t": "fineprint", "lines": fine}, {"t": "pagebreak"}]
        elif key == "disclaimer":
            text = DISCLAIMER.get(spec.lane, DISCLAIMER["technical"])
            b += [{"t": "subhead", "text": "READ THIS FIRST"}, {"t": "p", "text": text},
                  {"t": "pagebreak"}]
        elif key == "contents":
            b += [{"t": "toc"}, {"t": "pagebreak"}]
        elif key in ("authors_note", "how_to_use"):
            key_text = spec.raw.get(key)
            if key_text:
                head = "A NOTE BEFORE YOU START" if key == "authors_note" else "HOW TO USE THIS BOOK"
                b += [{"t": "subhead", "text": head}]
                b += [{"t": "p", "text": p.strip()} for p in key_text.strip().split("\n\n")]
                b += [{"t": "pagebreak"}]
    b.append({"t": "recto_break"})
    return b


def back_blocks(spec: TitleSpec, lane_keys: tuple) -> list:
    """Back matter. Each section opens on a recto; nothing trails a blank leaf."""
    sections: list = []
    for key in lane_keys:
        blocks: list = []
        if key == "closing" and spec.raw.get("closing"):
            blocks += [{"t": "subhead", "text": "LAST THING"}]
            blocks += [{"t": "p", "text": p.strip()}
                       for p in spec.raw["closing"].strip().split("\n\n")]
        elif key == "index_of_anchors":
            blocks += [{"t": "subhead", "text": "INDEX OF ANCHORS"}, {"t": "anchor_index"}]
        elif key == "sources":
            blocks += [{"t": "subhead", "text": "SOURCES"}, {"t": "source_list"}]
        elif key == "about_the_author" and spec.raw.get("about_the_author"):
            blocks += [{"t": "subhead", "text": "ABOUT THE AUTHOR"}]
            blocks += [{"t": "p", "text": p.strip()}
                       for p in spec.raw["about_the_author"].strip().split("\n\n")]
        elif key == "also_by" and spec.companion_products:
            blocks += [{"t": "subhead", "text": f"ALSO FROM {spec.imprint.upper()}"}]
            blocks += [{"t": "p", "text": str(c)} for c in spec.companion_products]
        elif key == "review_request":
            blocks += [{"t": "subhead", "text": "ONE ASK"},
                       {"t": "p", "text":
                        "If this book did what it said it would do, say so where the next "
                        "reader will see it. A review on Amazon takes ninety seconds and it "
                        "is the only thing that decides whether a book like this reaches the "
                        "man who needs it. If it did not do what it said, say that too. I "
                        "would rather know."}]
        if blocks:
            sections.append(blocks)

    out: list = [{"t": "head", "text": ""}]
    for blocks in sections:
        out.append({"t": "recto_break"})
        out += blocks
    return out
