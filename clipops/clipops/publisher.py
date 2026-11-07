"""RIGHTS OFFICER + PUBLISHER.

Rights officer: nothing ships without clearing the gate.
Publisher: assigns the next open post slot and either builds a manual post kit
(ready/<date>/<time>_<clip>/) or uploads through the YouTube Data API.
"""
from __future__ import annotations

import shutil
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from .core import DATA, READY, ROOT
from .editor import find_vo

SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]


# ---- RIGHTS ----------------------------------------------------------------
def gate(video: dict, clip_dir: Path, cfg: dict) -> str | None:
    """Return a block reason, or None if clear to publish."""
    r = video["rights"]
    if r == "own":
        return None
    if r == "unlicensed" and not cfg["rights"]["allow_unlicensed_with_commentary"]:
        return "unlicensed source; fair-use lane is off"
    if cfg["rights"]["require_commentary"] and not find_vo(clip_dir, "vo_close"):
        return "needs_vo"
    return None


def credit_line(video: dict) -> str:
    r = video["rights"]
    if r == "own":
        return ""
    tag = " (CC BY)" if r == "cc_by" else ""
    return f"Source: {video.get('credit') or video.get('channel')}{tag} — {video['url']}"


def post_text(video: dict, pkg: dict) -> tuple[str, str, list[str]]:
    tags = [t if t.startswith("#") else f"#{t}" for t in pkg["hashtags"]]
    if "#shorts" not in [t.lower() for t in tags]:
        tags.append("#shorts")
    parts = [pkg["description"].strip(), credit_line(video), " ".join(tags)]
    return pkg["title"][:100], "\n\n".join(p for p in parts if p), [t.lstrip("#") for t in tags]


# ---- SLOTS -----------------------------------------------------------------
def next_slot(cfg: dict, taken: set[str], now: datetime | None = None) -> datetime:
    tz = ZoneInfo(cfg["channel"]["timezone"])
    now = now or datetime.now(tz)
    slots = sorted(cfg["channel"]["post_slots"])
    for day in range(0, 60):
        d = (now + timedelta(days=day)).date()
        for s in slots:
            hh, mm = map(int, s.split(":"))
            t = datetime(d.year, d.month, d.day, hh, mm, tzinfo=tz)
            if t > now + timedelta(minutes=20) and t.isoformat() not in taken:
                return t
    raise RuntimeError("no open slot in 60 days")


# ---- MANUAL KIT ------------------------------------------------------------
def build_kit(video: dict, clip: dict, final: Path, when: datetime) -> Path:
    title, desc, _ = post_text(video, clip["package"])
    kit = READY / when.strftime("%Y-%m-%d") / f"{when.strftime('%H%M')}_{clip['id']}"
    kit.mkdir(parents=True, exist_ok=True)
    shutil.copy2(final, kit / "video.mp4")
    (kit / "post.txt").write_text(
        f"POST AT: {when.strftime('%a %b %d %H:%M %Z')}\n\nTITLE:\n{title}\n\nDESCRIPTION:\n{desc}\n\n"
        f"PINNED COMMENT:\n{clip['package']['pinned_comment']}\n\n"
        f"After posting run:  python -m clipops posted {clip['id']} <youtube_video_id>\n")
    return kit


# ---- API -------------------------------------------------------------------
def _youtube():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    tok = DATA / "token.json"
    creds = Credentials.from_authorized_user_file(str(tok), SCOPES) if tok.exists() else None
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            secret = ROOT / "client_secret.json"
            if not secret.exists():
                raise RuntimeError("client_secret.json missing — see README, YouTube API setup")
            creds = InstalledAppFlow.from_client_secrets_file(str(secret), SCOPES).run_local_server(port=0)
        tok.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload(video: dict, clip: dict, final: Path, when: datetime, cfg: dict) -> str:
    from googleapiclient.http import MediaFileUpload
    title, desc, tags = post_text(video, clip["package"])
    body = {
        "snippet": {"title": title, "description": desc, "tags": tags, "categoryId": cfg["publish"]["category_id"]},
        "status": {"privacyStatus": "private", "publishAt": when.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "selfDeclaredMadeForKids": cfg["publish"]["made_for_kids"], "containsSyntheticMedia": False},
    }
    req = _youtube().videos().insert(part="snippet,status", body=body,
                                     media_body=MediaFileUpload(str(final), chunksize=-1, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    return resp["id"]


def fetch_stats(ids: list[str]) -> dict[str, dict]:
    yt, out = _youtube(), {}
    for i in range(0, len(ids), 50):
        r = yt.videos().list(part="statistics", id=",".join(ids[i:i + 50])).execute()
        for it in r.get("items", []):
            out[it["id"]] = {k: int(v) for k, v in it["statistics"].items() if v.isdigit()}
    return out
