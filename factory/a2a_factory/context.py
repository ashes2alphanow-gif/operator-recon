"""Run context. Every stage writes real files; nothing is passed in memory
from a producer to its approver."""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from .spec import TitleSpec


class BuildHalted(RuntimeError):
    """A gate refused the build. The run stops here."""

    def __init__(self, gate: str, findings: list):
        self.gate = gate
        self.findings = findings
        blockers = [f for f in findings if f.get("severity") == "P0"]
        super().__init__(f"{gate} FAILED with {len(blockers)} P0 blocker(s)")


STAGE_DIRS = {
    "intake": "00_intake",
    "blueprint": "01_blueprint",
    "manuscript": "02_manuscript",
    "interior": "03_interior",
    "cover": "04_cover",
    "listing": "05_listing",
    "compliance": "06_compliance",
    "package": "07_package",
    "gates": "gates",
}


@dataclass
class Run:
    spec: TitleSpec
    root: Path
    rates: dict
    started: float = field(default_factory=time.time)
    log: list = field(default_factory=list)
    artifacts: dict = field(default_factory=dict)

    @property
    def out(self) -> Path:
        return self.root / "output" / self.spec.slug

    def reset(self) -> None:
        if self.out.exists():
            shutil.rmtree(self.out)
        for d in STAGE_DIRS.values():
            (self.out / d).mkdir(parents=True, exist_ok=True)

    def path(self, stage: str, name: str) -> Path:
        return self.out / STAGE_DIRS[stage] / name

    # ---- writing -------------------------------------------------------
    def write(self, stage: str, name: str, content: str | bytes) -> Path:
        p = self.path(stage, name)
        p.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(content, str):
            p.write_text(content, encoding="utf-8")
        else:
            p.write_bytes(content)
        self._record(p)
        return p

    def write_json(self, stage: str, name: str, payload) -> Path:
        return self.write(stage, name, json.dumps(payload, indent=2, default=str) + "\n")

    def adopt(self, path: Path) -> Path:
        """Register a file a stage wrote through a third-party library."""
        self._record(path)
        return path

    def _record(self, p: Path) -> None:
        data = p.read_bytes()
        rel = str(p.relative_to(self.out))
        self.artifacts[rel] = {
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        }

    # ---- reading (gates only) ------------------------------------------
    def read(self, stage: str, name: str) -> str:
        return self.path(stage, name).read_text(encoding="utf-8")

    def read_json(self, stage: str, name: str):
        return json.loads(self.read(stage, name))

    def say(self, line: str) -> None:
        stamp = f"{time.time() - self.started:6.2f}s"
        self.log.append(f"[{stamp}] {line}")
        print(f"  {line}", flush=True)
