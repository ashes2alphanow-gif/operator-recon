"""SCOUT — finds source videos worth mining.

Three lanes, in order of value:
  own        your footage in own_footage/            -> rights: own
  allowlist  creators who gave permission             -> rights: permitted
  search     open YouTube search (CC filter default)  -> rights: cc_by / unlicensed

Ranks search hits by outlier signal: views relative to channel size, and
views per day. A small channel with a breakout video is the target.
"""
from __future__ import annotations

import hashlib
import math
import time
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus

from .core import ROOT, Ledger, slug

VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm"}
CC_FILTER = "EgIwAQ%3D%3D"  # YouTube search filter: Creative Commons


def _ydl(**opts):
    from yt_dlp import YoutubeDL
    return YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, **opts})


def classify_rights(info: dict, allow_credit: str | None) -> str:
    if allow_credit:
        return "permitted"
    if "creative commons" in (info.get("license") or "").lower():
        return "cc_by"
    return "unlicensed"


def outlier_score(info: dict, now: float | None = None) -> float:
    views = info.get("view_count") or 0
    subs = max(info.get("channel_follower_count") or 0, 1000)
    ud = info.get("upload_date")
    age = 365.0
    if ud:
        age = max((((now or time.time()) - datetime.strptime(ud, "%Y%m%d").timestamp()) / 86400), 1.0)
    return round(math.log10(1 + views / age) + math.log10(1 + views / subs), 3)


def _video_record(info: dict, rights: str, credit: str | None, proof: str | None) -> dict:
    return {
        "id": info["id"],
        "url": info.get("webpage_url") or f"https://www.youtube.com/watch?v={info['id']}",
        "title": info.get("title", ""),
        "channel": info.get("channel") or info.get("uploader") or "",
        "channel_url": info.get("channel_url", ""),
        "duration": info.get("duration") or 0,
        "views": info.get("view_count") or 0,
        "subs": info.get("channel_follower_count") or 0,
        "upload_date": info.get("upload_date"),
        "license": info.get("license") or "",
        "rights": rights,
        "credit": credit or (info.get("channel") or ""),
        "proof": proof,
        "score": outlier_score(info),
        "source": "youtube",
    }


def scout_own(cfg: dict, ledger: Ledger) -> int:
    d = ROOT / cfg["sources"]["own_footage_dir"]
    d.mkdir(exist_ok=True)
    n = 0
    for p in sorted(d.iterdir()):
        if p.suffix.lower() not in VIDEO_EXT:
            continue
        vid = f"own-{slug(p.stem, 30)}-{hashlib.sha1(str(p).encode()).hexdigest()[:6]}"
        if ledger.has_video(vid):
            continue
        ledger.put_video({"id": vid, "url": str(p), "path": str(p), "title": p.stem, "channel": "self",
                          "rights": "own", "credit": "", "score": 99.0, "source": "local"})
        n += 1
    return n


def _flat(url: str, limit: int) -> list[dict]:
    with _ydl(extract_flat="in_playlist", playlistend=limit) as y:
        res = y.extract_info(url, download=False)
    return [e for e in (res.get("entries") or []) if e and e.get("id")]


def _full(vid: str) -> dict | None:
    try:
        with _ydl() as y:
            return y.extract_info(f"https://www.youtube.com/watch?v={vid}", download=False)
    except Exception as e:  # private, removed, age-gated
        print(f"  skip {vid}: {str(e)[:80]}")
        return None


def scout_youtube(cfg: dict, ledger: Ledger, max_new: int = 15) -> int:
    s = cfg["sources"]
    allow_unlic = cfg["rights"]["allow_unlicensed_with_commentary"]
    min_dur = s["min_duration_min"] * 60
    max_age = s["max_age_days"]
    pool: dict[str, tuple[str | None, str | None]] = {}  # id -> (credit, proof)

    for a in s.get("allowlist") or []:
        for e in _flat(a["url"], 15):
            pool[e["id"]] = (a.get("credit"), a.get("proof"))
    for q in s.get("searches") or []:
        url = f"https://www.youtube.com/results?search_query={quote_plus(q)}"
        if s.get("cc_only", True):
            url += f"&sp={CC_FILTER}"
        for e in _flat(url, s["results_per_search"]):
            if (e.get("duration") or min_dur) < min_dur:
                continue
            pool.setdefault(e["id"], (None, None))

    fresh = [v for v in pool if not ledger.has_video(v)]
    print(f"scout: {len(pool)} hits, {len(fresh)} new")
    found = []
    for vid in fresh:
        info = _full(vid)
        if not info:
            continue
        credit, proof = pool[vid]
        rec = _video_record(info, classify_rights(info, credit), credit, proof)
        age_ok = not rec["upload_date"] or (time.time() - datetime.strptime(rec["upload_date"], "%Y%m%d").timestamp()) / 86400 <= max_age
        if rec["duration"] < min_dur or not age_ok:
            continue
        if rec["rights"] == "unlicensed" and not allow_unlic:
            continue
        found.append(rec)
    found.sort(key=lambda r: r["score"], reverse=True)
    for rec in found[:max_new]:
        ledger.put_video(rec)
        print(f"  + [{rec['rights']}] {rec['score']:>5} {rec['title'][:70]} — {rec['channel']}")
    return len(found[:max_new])
