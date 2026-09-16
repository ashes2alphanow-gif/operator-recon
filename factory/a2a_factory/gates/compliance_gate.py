"""Gate F - evidence control. The gate that keeps the catalogue defensible."""
from __future__ import annotations

from ..context import Run
from .base import Verdict, P0, P1, P2

NAME = "compliance"
PUBLIC_DOMAIN = ("KJV", "KING JAMES", "WEB", "WORLD ENGLISH", "ASV", "AMERICAN STANDARD")


def check(ctx: Run) -> Verdict:
    v = Verdict(NAME)
    L = ctx.read_json("compliance", "ledgers.json")
    spec = ctx.read_json("intake", "spec.resolved.json")
    lane = spec["lane_profile"]
    risk = L["claim_risk"]
    hard = risk in ("high", "elevated")

    v.measurements = {
        "claim_risk": risk,
        "sources": len(L["sources"]),
        "claims_declared": len(L["claims_declared"]),
        "claims_detected": len(L["claims_detected"]),
        "claims_unresolved": len(L["claims_unresolved"]),
        "stories": len(L["stories"]),
        "ai_generated_components": L["kdp_disclosure_required_for"],
    }

    if lane["source_ledger_required"] and not L["sources"]:
        v.add(P0, "no-source-ledger",
              f"the {lane['key']} lane requires a source ledger and the spec carries none",
              fix="Add a `sources:` block with id, citation, url and access date.")

    for c in L["claims_declared"]:
        if not c["source_resolved"]:
            v.add(P0 if hard else P1, "dangling-claim",
                  f"claim '{c['id']}' points at source '{c['source_id']}' which is not in "
                  "the source ledger", evidence=c["claim"])
        if c["status"] not in ("verified", "author-experience", "opinion"):
            v.add(P0 if hard else P1, "unverified-claim",
                  f"claim '{c['id']}' is marked '{c['status']}'", evidence=c["claim"])

    for u in L["claims_unresolved"][:25]:
        v.add(P0 if hard else P2, "untracked-claim",
              f"{lane['unit_type']} {u['unit']} states a {'/'.join(u['kinds'])} with no "
              "claim-ledger entry",
              evidence=u["sentence"][:200],
              fix="Tag it in the manuscript as [c:some-id] and add the entry, or cut the "
                  "number.")

    for s in L["stories"]:
        if s["provenance"] == "unstated":
            v.add(P0, "story-provenance",
                  f"story '{s['id']}' has no provenance",
                  evidence=s["summary"][:160],
                  fix="Mark it first-hand, composite, or sourced. A fabricated operational "
                      "story is the one mistake this brand does not survive.")
        if s["provenance"] in ("third-party", "sourced") and not s["consent"]:
            v.add(P1, "story-consent",
                  f"story '{s['id']}' involves someone else and records no consent")

    ai = L["ai_origin"]
    for field in ("text", "images", "translation"):
        val = str(ai.get(field, "")).lower()
        if val not in ("ai-generated", "ai-assisted", "none"):
            v.add(P0, "ai-origin-unresolved",
                  f"AI origin for '{field}' is '{ai.get(field, 'missing')}'",
                  fix="KDP asks this at upload. Answer it here first: ai-generated, "
                      "ai-assisted, or none.")

    if lane["professional_review_required"]:
        rev = L["professional_review"]
        if not rev.get("reviewer") or not rev.get("date"):
            v.add(P0, "no-professional-review",
                  f"the {lane['key']} lane requires review by a "
                  f"{lane['review_discipline']} and none is recorded",
                  fix="Record reviewer, credential, date and scope in the spec under "
                      "compliance.professional_review.")

    trans = (L.get("scripture_translation") or "").upper()
    if trans:
        if not any(trans.startswith(p) for p in PUBLIC_DOMAIN):
            v.add(P0, "scripture-licence",
                  f"scripture translation '{L['scripture_translation']}' is not public "
                  "domain",
                  fix="Use KJV, WEB or ASV, or put the publisher's written permission on "
                      "file and record it here.")
    return v
