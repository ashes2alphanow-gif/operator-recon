"""G2 - manuscript assembly.

The engine does not invent prose here. It takes authored unit files, validates
them against the architecture, and turns them into a typed block stream the
interior renderer can lay out. If the files are not there, it writes the
authoring packs and stops -- an empty book is a stop, not a silent pass.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..context import Run

FENCE = re.compile(r"^:::\s*(\w+)?\s*$")
LINES = re.compile(r"^\[\[lines:(\d+)\]\]$")


class NeedsContent(RuntimeError):
    def __init__(self, missing: list, pack_dir: Path):
        self.missing = missing
        self.pack_dir = pack_dir
        super().__init__(f"{len(missing)} unit file(s) not authored yet")


def unit_filename(number: int, title: str) -> str:
    from ..spec import slugify
    return f"{number:03d}-{slugify(title)}.md"


def parse_unit(text: str, number: int) -> list:
    """A2A markdown dialect -> blocks.

    # Title              unit opener
    > quote -- source    anchor line
    ## SUBHEAD           section subhead
    ::: prayer ... :::   fenced special block
    [[lines:8]]          8 ruled write-lines
    ---                  ornamental break
    """
    blocks, para, fence, buf = [], [], None, []
    def flush_para():
        if para:
            blocks.append({"t": "p", "text": " ".join(para).strip()})
            para.clear()

    for raw in text.splitlines():
        line = raw.rstrip()
        m = FENCE.match(line.strip())
        if m:
            if fence is None:
                flush_para()
                fence = (m.group(1) or "callout").lower()
                buf = []
            else:
                blocks.append({"t": fence, "text": " ".join(buf).strip()})
                fence, buf = None, []
            continue
        if fence is not None:
            if line.strip():
                buf.append(line.strip())
            continue
        if not line.strip():
            flush_para()
            continue
        if line.startswith("# "):
            flush_para()
            blocks.append({"t": "unit_open", "number": number, "title": line[2:].strip()})
        elif line.startswith("## "):
            flush_para()
            blocks.append({"t": "subhead", "text": line[3:].strip()})
        elif line.startswith("> "):
            flush_para()
            body, _, cite = line[2:].partition(" -- ")
            blocks.append({"t": "anchor", "text": body.strip(), "cite": cite.strip()})
        elif LINES.match(line.strip()):
            flush_para()
            blocks.append({"t": "lines", "n": int(LINES.match(line.strip()).group(1))})
        elif line.strip() == "---":
            flush_para()
            blocks.append({"t": "rule"})
        else:
            para.append(line.strip())
    if fence is not None:
        raise ValueError(f"unit {number}: unclosed ':::' fence")
    flush_para()
    return blocks


def run(ctx: Run) -> None:
    spec = ctx.spec
    lane = spec.lane_profile
    if spec.manuscript_dir:
        src = Path(spec.manuscript_dir)
        if not src.is_absolute():
            src = (ctx.root / src).resolve()
    else:
        src = ctx.root / "factory" / "manuscripts" / spec.slug

    missing, units = [], []
    for u in spec.units:
        f = src / unit_filename(u.number, u.title)
        if not f.exists():
            missing.append({"number": u.number, "title": u.title, "expected_file": str(f)})
            continue
        blocks = parse_unit(f.read_text(encoding="utf-8"), u.number)
        heads = [b for b in blocks if b["t"] == "unit_open"]
        if len(heads) != 1:
            raise ValueError(f"{f.name}: expected exactly one '# Title' line, found {len(heads)}")
        if heads[0]["title"].strip().lower() != u.title.strip().lower():
            raise ValueError(
                f"{f.name}: title drift -- spec says {u.title!r}, file says {heads[0]['title']!r}"
            )
        words = sum(len(b.get("text", "").split()) for b in blocks)
        units.append({"number": u.number, "title": u.title, "thesis": u.thesis,
                      "source_file": str(f), "words": words,
                      "blocks": blocks})

    if missing:
        pack = write_authoring_packs(ctx, missing)
        raise NeedsContent(missing, pack)

    units.sort(key=lambda x: x["number"])
    total = sum(u["words"] for u in units)
    ctx.write_json("manuscript", "blocks.json", {
        "slug": spec.slug, "lane": lane.key, "unit_type": lane.unit_type,
        "total_words": total, "units": units,
    })

    md = [f"# {spec.full_title}", f"_{spec.author} / {spec.imprint}_", ""]
    for u in units:
        f = src / unit_filename(u["number"], u["title"])
        md += [f.read_text(encoding="utf-8").strip(), "", "---", ""]
    ctx.write("manuscript", "manuscript.md", "\n".join(md))
    ctx.say(f"manuscript: {len(units)} {lane.unit_plural}, {total:,} words assembled")


def write_authoring_packs(ctx: Run, missing: list) -> Path:
    """Write one ready-to-run authoring prompt per missing unit."""
    from ..promptpack import unit_prompt
    d = ctx.out / "02_manuscript" / "authoring"
    d.mkdir(parents=True, exist_ok=True)
    for m in missing:
        unit = next(u for u in ctx.spec.units if u.number == m["number"])
        (d / f"{m['number']:03d}-prompt.md").write_text(
            unit_prompt(ctx.spec, unit), encoding="utf-8")
    (d / "README.md").write_text(
        f"# Authoring packs - {ctx.spec.full_title}\n\n"
        f"{len(missing)} {ctx.spec.lane_profile.unit_type}(s) have no source file.\n"
        "Run each prompt, save the result to the path named at the top of the prompt, "
        "then re-run the build.\n", encoding="utf-8")
    return d
