"""Word-timed transcripts. YouTube captions via yt-dlp (json3), local files via
faster-whisper (optional install). Output: list of {"s","e","w"} in seconds."""
from __future__ import annotations

import json
from pathlib import Path

from .core import MEDIA


def parse_json3(data: dict) -> list[dict]:
    words: list[dict] = []
    for ev in data.get("events", []):
        segs = ev.get("segs")
        if not segs:
            continue
        t0 = ev.get("tStartMs", 0)
        end = t0 + ev.get("dDurationMs", 0)
        toks = [(t0 + s.get("tOffsetMs", 0), s.get("utf8", "")) for s in segs]
        toks = [(t, w.strip()) for t, w in toks if w.strip()]
        if not toks:
            continue
        # Manual captions arrive as one seg of many words: spread evenly.
        if len(toks) == 1 and " " in toks[0][1]:
            parts = toks[0][1].split()
            step = (end - t0) / max(len(parts), 1)
            toks = [(t0 + i * step, p) for i, p in enumerate(parts)]
        for i, (t, w) in enumerate(toks):
            nxt = toks[i + 1][0] if i + 1 < len(toks) else end
            words.append({"s": t / 1000, "e": max(nxt, t + 120) / 1000, "w": w})
    words.sort(key=lambda x: x["s"])
    # clamp overlaps (rolling auto-captions repeat timing)
    for a, b in zip(words, words[1:]):
        a["e"] = min(a["e"], b["s"]) if b["s"] > a["s"] else a["e"]
    return words


def youtube_words(video: dict) -> list[dict]:
    from yt_dlp import YoutubeDL
    out = MEDIA / video["id"]
    out.mkdir(parents=True, exist_ok=True)
    opts = {
        "quiet": True, "no_warnings": True, "skip_download": True,
        "writesubtitles": True, "writeautomaticsub": True,
        "subtitleslangs": ["en", "en-US", "en-orig"], "subtitlesformat": "json3",
        "outtmpl": str(out / "subs.%(ext)s"),
    }
    with YoutubeDL(opts) as y:
        y.download([video["url"]])
    files = sorted(out.glob("subs*.json3"), key=lambda p: ("orig" in p.name, p.name))
    if not files:
        raise RuntimeError("no English captions")
    return parse_json3(json.loads(files[0].read_text()))


def local_words(path: str) -> list[dict]:
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise RuntimeError("pip install faster-whisper to transcribe your own footage") from e
    model = WhisperModel("small.en", compute_type="int8")
    segs, _ = model.transcribe(path, word_timestamps=True, vad_filter=True)
    return [{"s": w.start, "e": w.end, "w": w.word.strip()} for s in segs for w in (s.words or [])]


def get_words(video: dict) -> list[dict]:
    cache = MEDIA / video["id"] / "words.json"
    if cache.exists():
        return json.loads(cache.read_text())
    words = local_words(video["path"]) if video.get("source") == "local" else youtube_words(video)
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(words))
    return words


def to_lines(words: list[dict], every: float = 8.0) -> str:
    """Compact timestamped transcript for the Analyst: '[612.4] text...'"""
    lines, cur, t0 = [], [], None
    for w in words:
        if t0 is None:
            t0 = w["s"]
        cur.append(w["w"])
        if w["e"] - t0 >= every:
            lines.append(f"[{t0:.1f}] {' '.join(cur)}")
            cur, t0 = [], None
    if cur:
        lines.append(f"[{t0:.1f}] {' '.join(cur)}")
    return "\n".join(lines)


def slice_words(words: list[dict], start: float, end: float) -> list[dict]:
    return [{"s": w["s"] - start, "e": min(w["e"], end) - start, "w": w["w"]}
            for w in words if w["s"] >= start - 0.05 and w["s"] < end]
