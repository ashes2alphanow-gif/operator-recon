"""Countable things about prose. Used by the gates, never by the writers."""
from __future__ import annotations

import re
from collections import Counter

WORD = re.compile(r"[a-z']+")
SENT = re.compile(r"(?<=[.!?])\s+")

STOP = set("""a an the and or but if then than that this these those of to in on for with
as at by from is are was were be been being it its it's you your yours i me my we our us
he she they them his her their not no so do does did done have has had will would can
could should may might must there here what when where who whom which how why all any
each more most other some such only own same too very just about into over under again
""".split())

FILLER = [
    r"\bin today'?s world\b", r"\bnow more than ever\b", r"\bat the end of the day\b",
    r"\bthe truth is\b", r"\bit is important to (?:note|remember|understand)\b",
    r"\blet'?s be honest\b", r"\bin order to\b", r"\bthe fact of the matter\b",
    r"\bneedless to say\b", r"\bwhen it comes to\b", r"\bunleash\b", r"\blevel up\b",
    r"\bcrush it\b", r"\bgame[- ]chang(?:er|ing)\b", r"\bin conclusion\b",
    r"\bthis (?:book|chapter) will (?:teach|show) you\b", r"\bas we all know\b",
    r"\bdelve into\b", r"\bnavigate the complexit\w+\b", r"\btapestry\b",
    r"\bmultifaceted\b", r"\bin the realm of\b", r"\bit'?s worth noting\b",
]
FILLER_RX = [re.compile(p, re.I) for p in FILLER]

# Things a sentence can contain that prove it is about something real.
# Counting words only. "one", "first" and "half" are left out on purpose: they
# work as pronouns and hedges far more often than as measurements, and counting
# them lets abstract prose score as if it said something.
NUMBER_WORD = (r"\b(?:two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|"
               r"thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|"
               r"twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|"
               r"thousand|dozen)\b")

CONCRETE = [
    re.compile(r"\b\d"),                                        # any digit
    re.compile(NUMBER_WORD, re.I),                              # a spelled-out count
    re.compile(r"\b\d{1,2}:\d{2}\b"),                           # a time
    re.compile(r"\b(?:minute|hour|day|week|month|year|mile|pound|round|round|"
               r"degree|dollar|percent|page|rep|set|shift|mile)s?\b", re.I),
    re.compile(r"\b(?:radio|tourniquet|rifle|truck|leash|harness|boot|pack|"
               r"knife|rope|litter|helmet|glove|light|map|compass|phone|"
               r"kennel|collar|vest|ledger|receipt|statement|account|uniform|"
               r"badge|patch|credential|form|report|log|calendar|casket|flag|"
               r"chapel|graveside|briefing|checklist|mic|battery|channel)s?\b", re.I),
    re.compile(r"\b(?:he|she|they|we|I) (?:said|told|asked|called|wrote|handed|"
               r"walked|drove|carried|pulled|signed)\b", re.I),
]


def words(text: str) -> list:
    return WORD.findall(text.lower())


def sentences(text: str) -> list:
    return [s.strip() for s in SENT.split(text) if s.strip()]


def content_tokens(text: str) -> set:
    return {w for w in words(text) if w not in STOP and len(w) > 2}


def jaccard(a: str, b: str) -> float:
    ta, tb = content_tokens(a), content_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)


def near_duplicate_pairs(items: list, threshold: float = 0.55,
                         min_words: int = 25) -> list:
    """items: list of (label, text). Returns pairs that say the same thing twice."""
    usable = [(lbl, t) for lbl, t in items if len(words(t)) >= min_words]
    idx = {}
    for i, (lbl, t) in enumerate(usable):
        for tok in content_tokens(t):
            idx.setdefault(tok, []).append(i)
    seen, pairs = set(), []
    for bucket in idx.values():
        if len(bucket) > 60:
            continue
        for a in range(len(bucket)):
            for b in range(a + 1, len(bucket)):
                key = (bucket[a], bucket[b])
                if key in seen:
                    continue
                seen.add(key)
                score = jaccard(usable[key[0]][1], usable[key[1]][1])
                if score >= threshold:
                    pairs.append({"a": usable[key[0]][0], "b": usable[key[1]][0],
                                  "similarity": round(score, 3),
                                  "a_text": usable[key[0]][1][:160],
                                  "b_text": usable[key[1]][1][:160]})
    return sorted(pairs, key=lambda p: -p["similarity"])


def filler_hits(text: str) -> list:
    hits = []
    for rx in FILLER_RX:
        for m in rx.finditer(text):
            hits.append(m.group(0).lower())
    return hits


CITATION = re.compile(r"\b\d?\s?[A-Z][a-z]+\s+\d{1,3}:\d{1,3}(?:-\d{1,3})?")


def strip_noise(text: str) -> str:
    """Remove the things that look concrete without being concrete.

    Scripture references carry digits. Filler phrases like "at the end of the
    day" carry a time word. Neither one is the author saying something real, so
    neither one is allowed to raise the score.
    """
    text = CITATION.sub(" ", text)
    for rx in FILLER_RX:
        text = rx.sub(" ", text)
    return text


def concrete_density(text: str) -> float:
    """Concrete markers per 100 words. Padding scores low; field writing scores high."""
    text = strip_noise(text)
    w = words(text)
    if not w:
        return 0.0
    hits = 0
    for s in sentences(text):
        hits += sum(1 for rx in CONCRETE if rx.search(s))
    return round(hits / len(w) * 100, 2)


def sentence_stats(text: str) -> dict:
    lens = [len(words(s)) for s in sentences(text) if words(s)]
    if not lens:
        return {"count": 0, "mean": 0.0, "stdev": 0.0, "max": 0}
    mean = sum(lens) / len(lens)
    var = sum((x - mean) ** 2 for x in lens) / len(lens)
    return {"count": len(lens), "mean": round(mean, 2),
            "stdev": round(var ** 0.5, 2), "max": max(lens)}


def repeated_openers(sents: list, n: int = 3) -> list:
    """Three-word openings used over and over are the tell of generated prose."""
    heads = Counter(" ".join(words(s)[:n]) for s in sents if len(words(s)) >= n)
    return [{"opening": k, "count": v} for k, v in heads.most_common() if v >= 4]
