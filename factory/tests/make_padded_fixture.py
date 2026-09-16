"""Build the padded-book fixture the substance gate is supposed to reject.

This exists so the gate can be proven to still bite. If a future change makes
the fixture build cleanly, the gate has been weakened and the test says so.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / "factory" / "manuscripts" / "_fixture-padded"

FILLER_PARA = (
    "In today's world it is important to remember that our journey is a personal "
    "one. When it comes to growth, the truth is that we all have a path. At the "
    "end of the day, what matters is that we continue to move forward with "
    "intention and purpose in all that we do."
)
ABSTRACT_PARA = (
    "Faith is a posture of the heart rather than a set of actions. When we learn "
    "to release control, we begin to experience a deeper sense of peace that is "
    "not dependent on circumstances. This is the invitation that is offered to "
    "each of us."
)
REPEATED_PARA = (
    "Surrender is not weakness. Surrender is the beginning of strength, because "
    "it releases the weight we were never meant to carry alone, and it opens us "
    "to a peace that does not depend on our circumstances or our performance."
)

TITLES = [
    "The Journey Begins", "A Season of Waiting", "The Quiet Voice", "Letting Go",
    "The Path Ahead", "Trusting the Process", "A New Perspective", "The Inner Work",
    "Moments of Stillness", "Finding Your Center", "The Deeper Call", "Learning to Receive",
    "A Posture of Openness", "The Gift of Presence", "Walking in Light",
    "The Space Between", "Choosing Gratitude", "The Long Obedience",
    "Becoming Who You Are", "The Final Invitation",
]


def build() -> Path:
    DEST.mkdir(parents=True, exist_ok=True)
    for old in DEST.glob("*.md"):
        old.unlink()
    for i, title in enumerate(TITLES, start=1):
        slug = title.lower().replace(" ", "-")
        body = [f"# {title}", "", "> Be still and know. -- Psalm 46:10", ""]
        body += [ABSTRACT_PARA, "", FILLER_PARA, ""]
        if i % 3 == 0:                      # the same paragraph, over and over
            body += [REPEATED_PARA, ""]
        if i == 4:                          # a placeholder nobody filled in
            body += ["[INSERT PERSONAL STORY HERE]", ""]
        if i % 5 != 0:                      # most entries keep the drill
            body += ["## THE DRILL", "", "Take a moment to reflect on this today.", ""]
        body += ["::: prayer", "God, meet me here today. Amen.", ":::", ""]
        (DEST / f"{i:03d}-{slug}.md").write_text("\n".join(body), encoding="utf-8")
    return DEST


if __name__ == "__main__":
    print(build())
