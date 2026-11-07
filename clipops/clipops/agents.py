"""The two Claude agents on the team.

ANALYST   reads a full transcript, finds the moments that stand alone, hook in
          the first two seconds, and fit the brand. Scores them. Kills hard-no.
PACKAGER  writes the copy for one approved clip in the channel voice: title,
          on-screen hook, the closing take, and the voice-over script that
          makes the clip yours.

Scoring math and hard-no enforcement happen in code, not in the model.
"""
from __future__ import annotations

from typing import Literal

import anthropic
from pydantic import BaseModel

from .transcript import to_lines

Pillar = Literal["pressure", "field_truth", "k9", "dark_humor", "earned_doctrine", "none"]
WEIGHTS = {"hook": 0.35, "brand_fit": 0.30, "standalone": 0.20, "payoff": 0.15}


class Scores(BaseModel):
    hook: int
    brand_fit: int
    standalone: int
    payoff: int


class Pick(BaseModel):
    start_s: float
    end_s: float
    pillar: Pillar
    first_line: str
    why: str
    scores: Scores
    hard_no: bool
    risk_flags: list[str]


class Picks(BaseModel):
    picks: list[Pick]


class Package(BaseModel):
    title: str
    on_screen_hook: str
    close_take: str
    vo_open: str
    vo_close: str
    description: str
    hashtags: list[str]
    pinned_comment: str


VOICE = """VOICE RULES (non-negotiable):
- Direct, calm, credible. Short controlled sentences. Sounds like a man who has lived hard things.
- Dry, dark humor allowed when it is sharp and earned.
- Never: hype, influencer tone, "alpha male", "warrior mindset", "sheepdog", "built different",
  "one percent", "rise and grind", "game changer", "you won't believe", emoji walls, ALL-CAPS shouting.
- Titles tell the truth about the clip. Curiosity is fine. Lies are not.
- If a line sounds like something an internet influencer would say, rewrite it."""


def _system_analyst(cfg: dict) -> str:
    b = cfg["brand"]
    pillars = "\n".join(f"- {k}: {v}" for k, v in b["pillars"].items())
    hard = "\n".join(f"- {h}" for h in b["hard_no"])
    lo, hi = b["clip_len_s"]
    return f"""You are the Analyst on a short-form clip team for the YouTube channel "{cfg['channel']['name']}".
The channel is run by a career federal agent, SAR/K-9 operator, Army veteran, and father.
Audience: law enforcement, military and veterans, first responders, K-9 handlers, SAR, blue-collar men, fathers.

Your job: read a timestamped transcript and pick the moments that will hold a scrolling thumb
AND fit the brand. Most transcripts have zero to three real clips. Returning nothing is a valid answer.

BRAND PILLARS:
{pillars}

HARD NO (set hard_no=true if the moment touches any of these, even partly):
{hard}

WHAT A CLIP NEEDS:
- Hook: the first spoken line lands in under 2 seconds with no setup. Start mid-thought if that is where it hits.
- Standalone: a stranger with zero context understands it.
- Payoff: it ends on the punch, the turn, or the lesson. Cut right after it lands.
- Length {lo}-{hi} seconds. Start and end on sentence boundaries using the transcript timestamps.

SCORING (integers 0-10, be stingy; a 7 is good, a 9 is rare):
hook, brand_fit, standalone, payoff.
risk_flags: anything an editor should check (profanity density, a named private person, music in background,
a claim that needs verification, needs context the clip lacks).
first_line: the exact first words spoken in the clip."""


def _system_packager(cfg: dict) -> str:
    return f"""You are the Packager on the clip team for "{cfg['channel']['name']}".
The host adds his own voice-over around every clip he did not film. That commentary is what makes the
channel original and monetizable, so the VO script carries weight. It is his perspective as a
career agent, K-9/SAR operator, veteran, and father. Not a summary of the clip.

{VOICE}

Deliver:
- title: <= 70 characters. No hashtags in the title.
- on_screen_hook: <= 8 words. Sits on screen for the first seconds. Makes the viewer stay.
- vo_open: 1-2 sentences, ~5 seconds spoken. Frames why this clip matters to men who carry weight. Does not spoil the payoff.
- vo_close: 2-3 sentences, ~10 seconds spoken. His take. One idea he would actually say. Ends clean.
- close_take: the single strongest line from vo_close, <= 14 words, for the end card.
- description: 2-3 short lines. Do not add the source credit; code appends it.
- hashtags: 3-5, lowercase, include #shorts.
- pinned_comment: one line that starts a real conversation with this audience. A question they have an answer to."""


class Team:
    def __init__(self, cfg: dict, client: anthropic.Anthropic | None = None):
        self.cfg = cfg
        self.model = cfg["model"]["name"]
        self.effort = cfg["model"]["effort"]
        self.client = client or anthropic.Anthropic()

    def _ask(self, system: str, user: str, schema):
        r = self.client.messages.parse(
            model=self.model,
            max_tokens=16000,
            system=system,
            output_config={"effort": self.effort},
            messages=[{"role": "user", "content": user}],
            output_format=schema,
        )
        if r.stop_reason == "refusal":
            raise RuntimeError("model declined this source")
        return r.parsed_output

    # ANALYST ----------------------------------------------------------------
    def analyze(self, video: dict, words: list[dict]) -> list[dict]:
        user = (f"SOURCE: {video.get('title','')} — {video.get('channel','')}\n"
                f"Pick up to {self.cfg['brand']['max_clips_per_video']} clips.\n\n"
                f"TRANSCRIPT:\n{to_lines(words)}")
        picks = self._ask(_system_analyst(self.cfg), user, Picks).picks
        return select(picks, self.cfg, duration=video.get("duration") or (words[-1]["e"] if words else 0))

    # PACKAGER ---------------------------------------------------------------
    def package(self, video: dict, clip: dict, clip_text: str) -> dict:
        user = (f"SOURCE: {video.get('title','')} — {video.get('channel','')} (rights: {video['rights']})\n"
                f"PILLAR: {clip['pillar']}\nWHY IT WORKS: {clip['why']}\n\nCLIP TRANSCRIPT:\n{clip_text}")
        return self._ask(_system_packager(self.cfg), user, Package).model_dump()


def weighted(s: Scores) -> float:
    return round(sum(getattr(s, k) * w for k, w in WEIGHTS.items()), 2)


def select(picks: list[Pick], cfg: dict, duration: float) -> list[dict]:
    """Code-side gate: hard-no, score floor, length clamp, no overlaps."""
    b = cfg["brand"]
    lo, hi = b["clip_len_s"]
    out: list[dict] = []
    for p in sorted(picks, key=lambda p: weighted(p.scores), reverse=True):
        score = weighted(p.scores)
        if p.hard_no or p.pillar == "none" or score < b["min_score"]:
            continue
        start = max(0.0, p.start_s)
        end = min(p.end_s, start + hi, duration or p.end_s)
        if end - start < lo:
            continue
        if any(start < o["end"] and end > o["start"] for o in out):
            continue
        out.append({"start": round(start, 2), "end": round(end, 2), "pillar": p.pillar, "score": score,
                    "first_line": p.first_line, "why": p.why, "risk_flags": p.risk_flags,
                    "scores": p.scores.model_dump()})
        if len(out) >= b["max_clips_per_video"]:
            break
    return out
