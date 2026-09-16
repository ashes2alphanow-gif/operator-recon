"""The assembly line.

Producers and approvers are different modules. A gate reads only files that are
already on disk, so nothing can be waved through on the strength of what the
builder believed it had done.
"""
from __future__ import annotations

import json
import traceback
from pathlib import Path

from . import kdp
from .context import Run, BuildHalted
from .gates import (compliance_gate, cover_gate, interior_gate, listing_gate,
                    structure_gate, substance_gate)
from .spec import TitleSpec
from .stages import (blueprint, compliance, cover, intake, interior, listing,
                     manuscript, package)

STEPS = [
    ("stage", "G0 intake", intake.run),
    ("stage", "G1 blueprint", blueprint.run),
    ("gate", "G2 structure gate", structure_gate),
    ("stage", "G3 manuscript", manuscript.run),
    ("gate", "G4 substance gate", substance_gate),
    ("stage", "G5 interior", interior.run),
    ("gate", "G6 interior spec gate", interior_gate),
    ("stage", "G7 cover", cover.run),
    ("gate", "G8 cover spec gate", cover_gate),
    ("stage", "G9 listing", listing.run),
    ("gate", "G10 listing gate", listing_gate),
    ("stage", "G11 compliance", compliance.run),
    ("gate", "G12 compliance gate", compliance_gate),
    ("stage", "G13 package", package.run),
]


def build(spec: TitleSpec, root: Path, rate_version: str = kdp.DEFAULT_RATE_VERSION,
          keep_going: bool = False) -> dict:
    rates = kdp.load_rates(rate_version)
    ctx = Run(spec=spec, root=root, rates=rates)
    ctx.reset()
    print(f"\n  BUILD {spec.full_title}  [{spec.slug}]")
    print(f"  lane={spec.lane} rates={rates['table_version']} out={ctx.out}\n")

    state = {"slug": spec.slug, "status": "OK", "halted_at": None,
             "gates": {}, "steps": []}

    for kind, label, thing in STEPS:
        try:
            if kind == "stage":
                thing(ctx)
                state["steps"].append({"step": label, "kind": kind, "result": "done"})
            else:
                verdict = thing.check(ctx)
                ctx.write_json("gates", f"{thing.NAME}.json", verdict.as_dict())
                state["gates"][thing.NAME] = verdict.as_dict()["counts"] | {
                    "result": "PASS" if verdict.passed else "FAIL"}
                state["steps"].append({"step": label, "kind": kind,
                                       "result": "PASS" if verdict.passed else "FAIL"})
                ctx.say(f"{thing.NAME} gate: "
                        f"{'PASS' if verdict.passed else 'FAIL'} "
                        f"(P0 {len(verdict.blockers)}, "
                        f"P1 {sum(1 for f in verdict.findings if f.severity == 'P1')}, "
                        f"P2 {sum(1 for f in verdict.findings if f.severity == 'P2')})")
                if not verdict.passed and not keep_going:
                    _halt(ctx, thing.NAME, verdict)
                    state["status"] = "HALTED"
                    state["halted_at"] = thing.NAME
                    _write_state(ctx, state)
                    return state
        except manuscript.NeedsContent as exc:
            ctx.say(f"STOP: {exc}. Authoring packs written to "
                    f"{exc.pack_dir.relative_to(ctx.out)}")
            _needs_content(ctx, exc)
            state["status"] = "NEEDS_CONTENT"
            state["halted_at"] = label
            _write_state(ctx, state)
            return state
        except Exception as exc:                     # noqa: BLE001
            ctx.say(f"ERROR in {label}: {exc}")
            (ctx.out / "BUILD_ERROR.md").write_text(
                f"# Build error at {label}\n\n```\n{traceback.format_exc()}\n```\n")
            state["status"] = "ERROR"
            state["halted_at"] = label
            state["error"] = str(exc)
            _write_state(ctx, state)
            raise

    _write_state(ctx, state)
    print(f"\n  BUILD COMPLETE - human approval required: "
          f"{ctx.out / '07_package' / 'APPROVAL_REQUIRED.md'}\n")
    return state


def _write_state(ctx: Run, state: dict) -> None:
    (ctx.out / "run_state.json").write_text(json.dumps(state, indent=2) + "\n")
    (ctx.out / "run_log.txt").write_text("\n".join(ctx.log) + "\n")


def _halt(ctx: Run, gate: str, verdict) -> None:
    lines = [f"# BUILD HALTED at the {gate} gate", "",
             f"**{ctx.spec.full_title}** did not get past `{gate}`. "
             "Nothing downstream was built.", "",
             "## Blockers (P0)", ""]
    for f in verdict.blockers:
        lines.append(f"### {f.code}")
        lines.append(f.message)
        if f.evidence:
            lines.append(f"\n> {f.evidence}")
        if f.fix:
            lines.append(f"\n**Fix:** {f.fix}")
        lines.append("")
    others = [f for f in verdict.findings if f.severity != "P0"]
    if others:
        lines += ["## Also found", ""]
        lines += [f"- **{f.severity}** `{f.code}` {f.message}" for f in others]
    lines += ["", "## Measurements", "", "```",
              json.dumps(verdict.measurements, indent=2), "```", "",
              "Fix the blockers and run the build again. The engine does not have a "
              "flag to publish past this.", ""]
    (ctx.out / "BUILD_HALTED.md").write_text("\n".join(lines))
    print(f"\n  BUILD HALTED at {gate}: {len(verdict.blockers)} blocker(s). "
          f"See {ctx.out / 'BUILD_HALTED.md'}\n")


def _needs_content(ctx: Run, exc) -> None:
    lines = [f"# NEEDS CONTENT - {ctx.spec.full_title}", "",
             f"{len(exc.missing)} {ctx.spec.lane_profile.unit_type}(s) have no source file.",
             "", "| # | title | expected file |", "| --- | --- | --- |"]
    for m in exc.missing:
        lines.append(f"| {m['number']} | {m['title']} | `{m['expected_file']}` |")
    lines += ["", f"Authoring packs are in `02_manuscript/authoring/`. "
              "Run them, save the files, re-run the build.", ""]
    (ctx.out / "NEEDS_CONTENT.md").write_text("\n".join(lines))
