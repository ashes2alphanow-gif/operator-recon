"""Config, paths, and the ledger. The ledger is one JSON file: every video and
clip the team has touched, with status. No database."""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MEDIA = ROOT / "media"
READY = ROOT / "ready"


def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.yaml") as f:
        return yaml.safe_load(f)


def slug(s: str, n: int = 40) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:n] or "x"


# Clip status flow:
#   picked -> packaged -> rendered -> (needs_vo) -> ready -> posted
#   rejected (brand / rights) at any point
@dataclass
class Ledger:
    path: Path = DATA / "ledger.json"

    def __post_init__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = json.loads(self.path.read_text()) if self.path.exists() else {"videos": {}, "clips": {}}

    def save(self):
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.db, indent=2))
        tmp.replace(self.path)

    # videos -----------------------------------------------------------------
    def has_video(self, vid: str) -> bool:
        return vid in self.db["videos"]

    def put_video(self, v: dict):
        v.setdefault("added", time.strftime("%Y-%m-%d %H:%M"))
        v.setdefault("status", "scouted")
        self.db["videos"][v["id"]] = v

    def videos(self, status: str | None = None) -> list[dict]:
        vs = self.db["videos"].values()
        return [v for v in vs if status is None or v["status"] == status]

    # clips ------------------------------------------------------------------
    def put_clip(self, c: dict):
        self.db["clips"][c["id"]] = c

    def clip(self, cid: str) -> dict:
        return self.db["clips"][cid]

    def clips(self, status: str | None = None) -> list[dict]:
        cs = self.db["clips"].values()
        return [c for c in cs if status is None or c["status"] == status]
