"""G6 - ledgers. Where every claim, source, story and AI decision is written down.

A claim with no source is not a style problem. It is the thing that gets a
title pulled, or gets a reader hurt. The ledgers are built here; the gate that
reads them and can stop the build lives in gates/compliance_gate.py.
"""
from __future__ import annotations

import re

from ..context import Run

SENTENCE = re.compile(r"(?<=[.!?])\s+")
TAG = re.compile(r"\[c:([a-z0-9\-]+)\]", re.I)

RISKY = [
    (re.compile(r"\$\s?\d"), "dollar figure"),
    (re.compile(r"\b\d+(\.\d+)?\s?%"), "percentage"),
    (re.compile(r"\b\d{2,}\b"), "quantity"),
    (re.compile(r"\b(stud(?:y|ies)|research|data|survey|report)\s+(?:show|shows|found|says)", re.I),
     "appeal to research"),
    (re.compile(r"\b(always|never|every time|guaranteed|proven)\b", re.I), "absolute"),
    (re.compile(r"\b(IRS|FDIC|TSP|401\s?\(?k\)?|Roth|VA|OSHA|FAA|DOT)\b"), "named authority"),
]
SAFE_CONTEXT = re.compile(r"^\s*(entry|chapter|session)\s+\d+", re.I)


def scan_claims(units: list) -> list:
    found = []
    for u in units:
        for b in u["blocks"]:
            text = b.get("text", "")
            if not text or b["t"] in ("anchor",):
                continue
            for sent in SENTENCE.split(text):
                s = sent.strip()
                if not s or SAFE_CONTEXT.match(s):
                    continue
                kinds = [name for rx, name in RISKY if rx.search(s)]
                if not kinds:
                    continue
                tags = TAG.findall(s)
                found.append({
                    "unit": u["number"], "unit_title": u["title"],
                    "sentence": TAG.sub("", s).strip(),
                    "kinds": kinds,
                    "claim_ids": [t.lower() for t in tags],
                })
    return found


def run(ctx: Run) -> None:
    spec = ctx.spec
    lane = spec.lane_profile
    src = ctx.read_json("manuscript", "blocks.json")
    interior = ctx.read_json("interior", "interior.json")

    sources = []
    for s in spec.raw.get("sources") or []:
        sources.append({
            "id": str(s.get("id", "")).lower(),
            "citation": s.get("citation", ""),
            "url": s.get("url", ""),
            "accessed": str(s.get("accessed", "")),
            "type": s.get("type", ""),
        })
    source_ids = {s["id"] for s in sources if s["id"]}

    declared = []
    for cl in spec.raw.get("claims") or []:
        cid = str(cl.get("id", "")).lower()
        declared.append({
            "id": cid,
            "claim": cl.get("claim", ""),
            "source_id": str(cl.get("source_id", "")).lower(),
            "source_resolved": str(cl.get("source_id", "")).lower() in source_ids,
            "status": cl.get("status", "unverified"),
            "reviewed_by": cl.get("reviewed_by", ""),
        })
    declared_ids = {c["id"] for c in declared}

    detected = scan_claims(src["units"])
    unresolved = [d for d in detected
                  if not d["claim_ids"] or
                  any(t not in declared_ids for t in d["claim_ids"])]

    stories = []
    for st in spec.raw.get("stories") or []:
        stories.append({
            "id": str(st.get("id", "")).lower(),
            "summary": st.get("summary", ""),
            "provenance": st.get("provenance", "unstated"),
            "consent": st.get("consent", ""),
            "identifying_details_changed": bool(st.get("identifying_details_changed", False)),
        })

    ai = dict(spec.compliance.get("ai_origin") or {})
    disclosure_needed = {k: v for k, v in ai.items() if str(v).lower() == "ai-generated"}
    review = dict(spec.compliance.get("professional_review") or {})

    ledgers = {
        "slug": spec.slug,
        "lane": lane.key,
        "claim_risk": lane.claim_risk,
        "sources": sources,
        "claims_declared": declared,
        "claims_detected": detected,
        "claims_unresolved": unresolved,
        "stories": stories,
        "ai_origin": ai,
        "kdp_disclosure_required_for": sorted(disclosure_needed),
        "professional_review": review,
        "professional_review_required": lane.professional_review_required,
        "review_discipline": lane.review_discipline,
        "scripture_translation": spec.compliance.get("scripture_translation", ""),
        "scripture_translation_public_domain": str(
            spec.compliance.get("scripture_translation", "")).upper().split()[0] in
            ("KJV", "WEB", "ASV", "KING", "WORLD", "AMERICAN") if
            spec.compliance.get("scripture_translation") else None,
    }
    ctx.write_json("compliance", "ledgers.json", ledgers)

    decisions = [
        {"decision": "rate table", "value": ctx.rates["table_version"],
         "why": "prices and spine come from a dated table, not from memory"},
        {"decision": "page count", "value": interior["page_count"],
         "why": "measured from the rendered interior, not estimated"},
        {"decision": "byline", "value": spec.author, "why": "locked in spec.py"},
        {"decision": "trim/paper/ink",
         "value": f"{spec.trim[0]}x{spec.trim[1]} / {spec.paper} / {spec.ink}",
         "why": "lane default unless the spec overrode it"},
    ]
    ctx.write_json("compliance", "decision_ledger.json", decisions)

    lines = [f"# KDP disclosure sheet - {spec.full_title}", "",
             "Answer the KDP content questions exactly this way:", ""]
    for field in ("text", "images", "translation"):
        val = str(ai.get(field, "none")).lower()
        answer = {"ai-generated": "YES - AI-generated",
                  "ai-assisted": "NO - AI-assisted only, no disclosure required",
                  "none": "NO - no AI involvement"}.get(val, f"UNRESOLVED ({val})")
        lines.append(f"- **{field.title()}**: {answer}")
    lines += ["",
              "KDP distinguishes AI-generated content (an AI produced the draft, even if "
              "you edited it afterwards) from AI-assisted content (you wrote it, AI helped "
              "edit or brainstorm). Only AI-generated content is disclosed. The disclosure "
              "is internal to Amazon and is not shown on the product page.", "",
              "Source: KDP Content Guidelines, AI-generated content section.", ""]
    ctx.write("compliance", "kdp_disclosure.md", "\n".join(lines))
    ctx.say(f"compliance: {len(detected)} risky sentences, {len(unresolved)} unresolved, "
            f"{len(sources)} sources, AI-generated: {sorted(disclosure_needed) or 'none'}")
