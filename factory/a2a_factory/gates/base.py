"""Gate vocabulary. A gate reads finished files and returns findings."""
from __future__ import annotations

from dataclasses import dataclass, asdict, field

P0 = "P0"   # stops the build
P1 = "P1"   # must be fixed before publish, does not stop the build
P2 = "P2"   # advisory


@dataclass
class Finding:
    severity: str
    code: str
    message: str
    evidence: str = ""
    fix: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class Verdict:
    gate: str
    findings: list = field(default_factory=list)
    measurements: dict = field(default_factory=dict)

    def add(self, severity, code, message, evidence="", fix="") -> None:
        self.findings.append(Finding(severity, code, message, evidence, fix))

    @property
    def blockers(self) -> list:
        return [f for f in self.findings if f.severity == P0]

    @property
    def passed(self) -> bool:
        return not self.blockers

    def as_dict(self) -> dict:
        return {
            "gate": self.gate,
            "result": "PASS" if self.passed else "FAIL",
            "counts": {s: sum(1 for f in self.findings if f.severity == s)
                       for s in (P0, P1, P2)},
            "measurements": self.measurements,
            "findings": [f.as_dict() for f in self.findings],
        }
