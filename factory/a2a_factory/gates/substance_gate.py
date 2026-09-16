"""Gate B - padded or thin, the run halts here.

This is the gate that makes the difference between a catalogue and a content
mill. It does not ask whether the prose is nice. It asks whether there is
anything in it.
"""
from __future__ import annotations

import re

from .. import textmetrics as tm
from ..context import Run
from .base import Verdict, P0, P1, P2

NAME = "substance"

PLACEHOLDER = re.compile(
    r"\[[A-Z][A-Z \-_/]{2,}\]|\bTBD\b|\bTODO\b|\bXXX\b|lorem ipsum|"
    r"\bINSERT [A-Z]+\b|\bPLACEHOLDER\b", re.I)
SECTION_ALIASES = {
    "opening": ("p",), "doctrine": ("p",), "body": ("p",),
    "drill": ("subhead",), "prayer": ("prayer",), "anchor": ("anchor",),
    "prompt": ("p", "subhead"), "practice": ("lines", "subhead"),
    "sources": ("subhead",),
}


def _unit_text(u: dict, skip=("anchor",)) -> str:
    """The author's own words. Quoted anchors are somebody else's."""
    return " ".join(b.get("text", "") for b in u["blocks"]
                    if b.get("text") and b["t"] not in skip)


def _has_section(u: dict, name: str) -> bool:
    kinds = SECTION_ALIASES.get(name, (name,))
    for b in u["blocks"]:
        if b["t"] in kinds:
            if b["t"] == "subhead" and name in ("drill", "practice", "sources", "prompt"):
                if name.upper() not in b.get("text", "").upper():
                    continue
            return True
    return False


def check(ctx: Run) -> Verdict:
    v = Verdict(NAME)
    src = ctx.read_json("manuscript", "blocks.json")
    spec = ctx.read_json("intake", "spec.resolved.json")
    lane = spec["lane_profile"]
    units = src["units"]

    full = " ".join(_unit_text(u) for u in units)
    sents = tm.sentences(full)
    density = tm.concrete_density(full)
    stats = tm.sentence_stats(full)
    fillers = tm.filler_hits(full)

    paras = []
    for u in units:
        for i, b in enumerate(u["blocks"]):
            if b["t"] in ("p", "prayer", "callout") and b.get("text"):
                paras.append((f"{lane['unit_type']} {u['number']} para {i}", b["text"]))
    dupes = tm.near_duplicate_pairs(paras, threshold=0.55)
    # share of paragraphs caught in at least one near-duplicate pair, so the
    # number stays between 0 and 1 and means something to a human
    involved = {d["a"] for d in dupes} | {d["b"] for d in dupes}
    ratio = len(involved) / max(len(paras), 1)

    v.measurements = {
        "total_words": src["total_words"],
        "units": len(units),
        "concrete_density_per_100w": density,
        "sentence_mean_words": stats["mean"],
        "sentence_stdev": stats["stdev"],
        "filler_hits": len(fillers),
        "paragraphs": len(paras),
        "near_duplicate_pairs": len(dupes),
        "paragraphs_involved_in_a_duplicate": len(involved),
        "near_duplicate_ratio": round(ratio, 4),
    }

    for u in units:
        text = _unit_text(u)
        n = len(tm.words(text))
        label = f"{lane['unit_type']} {u['number']} '{u['title']}'"
        if n < lane["min_words_per_unit"]:
            v.add(P0, "thin-unit",
                  f"{label} runs {n} words against a {lane['min_words_per_unit']} floor",
                  fix="Write it or cut it. Padding it out is the third option and it is banned.")
        elif n > lane["max_words_per_unit"]:
            v.add(P1, "long-unit",
                  f"{label} runs {n} words over the {lane['max_words_per_unit']} ceiling",
                  fix="It is two units, or it has a tangent in it.")
        for s in lane["required_unit_sections"]:
            if not _has_section(u, s):
                v.add(P0, "missing-section",
                      f"{label} has no '{s}' section",
                      fix=f"Every {lane['unit_type']} in this lane carries: "
                          f"{', '.join(lane['required_unit_sections'])}.")
        ud = tm.concrete_density(text)
        if ud < lane["min_concrete_density"] * 0.6:
            v.add(P0, "abstract-unit",
                  f"{label} scores {ud} concrete markers per 100 words against a lane "
                  f"floor of {lane['min_concrete_density']}",
                  fix="Name the thing. A time, a number, a piece of gear, a decision "
                      "someone actually made.")
        m = PLACEHOLDER.search(text)
        if m:
            v.add(P0, "placeholder", f"{label} still contains a placeholder",
                  evidence=m.group(0), fix="Fill it or delete it before the build runs.")

    if density < lane["min_concrete_density"]:
        v.add(P0, "abstract-book",
              f"whole book scores {density} concrete markers per 100 words against a "
              f"floor of {lane['min_concrete_density']}",
              fix="This reads like advice about advice. Put the field back in it.")

    if ratio > lane["max_repetition_ratio"]:
        v.add(P0, "repetition",
              f"{len(involved)} of {len(paras)} paragraphs ({ratio:.1%}) are caught in "
              f"{len(dupes)} near-duplicate pairs, over the "
              f"{lane['max_repetition_ratio']:.0%} ceiling",
              evidence="; ".join(f"{d['a']} ~ {d['b']} ({d['similarity']:.0%})"
                                 for d in dupes[:6]),
              fix="The reader notices before you do. Cut one side of each pair.")
    elif dupes:
        for d in dupes[:8]:
            v.add(P1, "repeated-passage",
                  f"{d['a']} and {d['b']} are {d['similarity']:.0%} the same",
                  evidence=f"{d['a_text']} || {d['b_text']}")

    per_1k = len(fillers) / max(len(tm.words(full)) / 1000, 1)
    if per_1k > 1.5:
        v.add(P0, "filler",
              f"{len(fillers)} filler phrases = {per_1k:.1f} per thousand words",
              evidence=", ".join(sorted(set(fillers))[:10]),
              fix="Every one of these is a sentence that says nothing. Delete, do not rewrite.")
    elif fillers:
        v.add(P1, "filler", f"{len(fillers)} filler phrases present",
              evidence=", ".join(sorted(set(fillers))[:10]))

    if stats["stdev"] < 4.0 and stats["count"] > 40:
        v.add(P1, "monotone",
              f"sentence length barely varies (stdev {stats['stdev']}) - reads machine-made",
              fix="Break the rhythm. One long sentence, then three words.")

    openers = tm.repeated_openers(sents)
    for o in openers[:5]:
        v.add(P2, "repeated-opening",
              f"'{o['opening']}...' opens {o['count']} sentences")

    dashes = full.count("—")
    if dashes:
        v.add(P2, "em-dash", f"{dashes} em dashes against house style",
              fix="Period or comma.")
    return v
