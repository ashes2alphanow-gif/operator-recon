"""An independent look at a finished PDF.

Deliberately does not import reportlab. The tool that builds the file must not
be the tool that approves it, so this reads the bytes on disk and reports what
is actually in them.
"""
from __future__ import annotations

import base64
import re
import zlib
from dataclasses import dataclass, asdict, field
from pathlib import Path

PT = 72.0

RE_PAGE = re.compile(rb"/Type\s*/Page(?![a-zA-Z])")
RE_PAGES = re.compile(rb"/Type\s*/Pages\b")
RE_COUNT = re.compile(rb"/Count\s+(\d+)")
RE_MEDIABOX = re.compile(rb"/MediaBox\s*\[\s*([\d.\-\s]+?)\s*\]")
RE_BASEFONT = re.compile(rb"/BaseFont\s*/([#A-Za-z0-9+\-_,.]+)")
RE_FONTFILE2 = re.compile(rb"/FontFile2\b")
RE_FONTFILE3 = re.compile(rb"/FontFile3\b")
RE_FONTFILE = re.compile(rb"/FontFile\b(?!\d)")
RE_OBJSTM = re.compile(rb"/Type\s*/ObjStm\b")
RE_IMAGE = re.compile(rb"/Subtype\s*/Image\b")
RE_COLORSPACE_RGB = re.compile(rb"/DeviceRGB\b")
RE_COLORSPACE_CMYK = re.compile(rb"/DeviceCMYK\b")


@dataclass
class PdfFacts:
    path: str
    bytes: int
    page_count: int
    pages_count_entry: int
    media_boxes_pt: list
    media_boxes_in: list
    uniform_page_size: bool
    base_fonts: list
    embedded_font_streams: int
    unembedded_fonts: list
    has_object_streams: bool
    image_count: int
    uses_rgb: bool
    uses_cmyk: bool
    text_sample: str = ""
    notes: list = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


STANDARD_14 = {
    "Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic",
    "Helvetica", "Helvetica-Bold", "Helvetica-Oblique", "Helvetica-BoldOblique",
    "Courier", "Courier-Bold", "Courier-Oblique", "Courier-BoldOblique",
    "Symbol", "ZapfDingbats",
}


RE_OBJ = re.compile(rb"(\d+)\s+0\s+obj\b(.*?)\bendobj", re.S)
RE_FONTRES = re.compile(rb"/Font\s*<<(.*?)>>", re.S)
RE_FONTIND = re.compile(rb"/Font\s+(\d+)\s+0\s+R")
RE_FONTREF = re.compile(rb"/([A-Za-z][\w+.\-]*)\s+(\d+)\s+0\s+R")
RE_TOUNICODE = re.compile(rb"/ToUnicode\s+(\d+)\s+0\s+R")
RE_TF = re.compile(rb"/([A-Za-z][\w+.\-]*)\s+[\d.]+\s+Tf")


def _objects(raw: bytes) -> dict:
    return {int(m.group(1)): m.group(2) for m in RE_OBJ.finditer(raw)}


def _decode_stream(chunk: bytes) -> bytes:
    """Undo whatever filters a writer stacked on a stream.

    reportlab ships ASCII85 over Flate by default; other writers use Flate
    alone or nothing. Try the combinations rather than assuming one.
    """
    candidate = chunk.strip()
    if candidate[:2] in (b"<~",):
        candidate = candidate[2:]
    for attempt in ("a85+flate", "flate", "a85", "raw"):
        try:
            data = candidate
            if attempt.startswith("a85"):
                end = data.find(b"~>")
                data = base64.a85decode(data if end < 0 else data[:end + 2], adobe=True)
            if attempt.endswith("flate"):
                data = zlib.decompress(data)
            if attempt == "raw":
                data = chunk
            return data
        except Exception:                                  # noqa: BLE001
            continue
    return chunk


def _inflate(body: bytes) -> bytes:
    m = re.search(rb"stream\r?\n(.*?)endstream", body, re.S)
    return _decode_stream(m.group(1)) if m else b""


def _streams(raw: bytes):
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        yield _decode_stream(m.group(1))


def _utf16be(hexbytes: bytes) -> str:
    try:
        return bytes.fromhex(hexbytes.decode()).decode("utf-16-be", "replace")
    except ValueError:
        return ""


def _parse_cmap(data: bytes) -> dict:
    table: dict = {}
    for block in re.findall(rb"beginbfchar(.*?)endbfchar", data, re.S):
        for src, dst in re.findall(rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            table[int(src, 16)] = _utf16be(dst)
    for block in re.findall(rb"beginbfrange(.*?)endbfrange", data, re.S):
        for lo, hi, dst in re.findall(
                rb"<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>\s*<([0-9A-Fa-f]+)>", block):
            base = int(dst, 16)
            for i, code in enumerate(range(int(lo, 16), int(hi, 16) + 1)):
                table[code] = chr(base + i)
    return table


def _font_tables(raw: bytes) -> dict:
    """Resource name (/F1, /F2 ...) -> its own ToUnicode table.

    Subset fonts reuse the same CID numbers, so one shared table turns text into
    noise. Each font gets read against its own CMap.
    """
    objs = _objects(raw)
    tables: dict = {}
    dicts = [m.group(1) for m in RE_FONTRES.finditer(raw)]
    # the font dictionary is often an indirect reference rather than inline
    dicts += [objs[int(m.group(1))] for m in RE_FONTIND.finditer(raw)
              if int(m.group(1)) in objs]
    for chunk in dicts:
        for name, num in RE_FONTREF.findall(chunk):
            num = int(num)
            if name in tables or num not in objs:
                continue
            tu = RE_TOUNICODE.search(objs[num])
            if not tu:
                continue
            cmap_obj = int(tu.group(1))
            if cmap_obj in objs:
                tables[name.decode()] = _parse_cmap(_inflate(objs[cmap_obj]))
    return tables


def _extract_text(raw: bytes, limit: int = 6000) -> str:
    """Pull drawn text back out, whether it was written as a literal string or
    as two-byte CIDs against an embedded subset font."""
    tables = _font_tables(raw)
    default = {}
    for t in tables.values():
        default.update(t)
    out: list = []
    size = 0
    token = re.compile(rb"/([A-Za-z][\w+.\-]*)\s+[\d.]+\s+Tf"
                       rb"|<([0-9A-Fa-f]+)>"
                       rb"|\((?:\\.|[^\\()])*\)")
    for data in _streams(raw):
        if b"Tj" not in data and b"TJ" not in data:
            continue
        current = default
        for m in token.finditer(data):
            if m.group(1):
                current = tables.get(m.group(1).decode(), default)
                continue
            if m.group(2):
                h = m.group(2)
                if len(h) % 4:
                    continue
                piece = "".join(current.get(int(h[i:i + 4], 16), "")
                                for i in range(0, len(h), 4))
            else:
                tok = m.group(0)
                body = re.sub(rb"\\([()\\])", rb"\1", tok[1:-1])
                if current and max(current) < 256:
                    piece = "".join(current.get(b, "") for b in body)
                else:
                    piece = body.decode("latin-1", "replace")
            if piece.strip():
                out.append(piece)
                size += len(piece)
        if size > limit:
            break
    return " ".join(out)[:limit]


def inspect(path: str | Path, want_text: bool = False,
            text_limit: int = 6000) -> PdfFacts:
    p = Path(path)
    raw = p.read_bytes()
    if not raw.startswith(b"%PDF-"):
        raise ValueError(f"{p.name} is not a PDF")

    pages = len(RE_PAGE.findall(raw))
    count_entries = [int(m.group(1)) for m in RE_COUNT.finditer(raw)] or [0]
    boxes_pt = []
    for m in RE_MEDIABOX.finditer(raw):
        nums = [float(x) for x in m.group(1).split()]
        if len(nums) == 4:
            boxes_pt.append([round(nums[2] - nums[0], 4), round(nums[3] - nums[1], 4)])
    uniq = sorted({tuple(b) for b in boxes_pt})
    boxes_in = [[round(w / PT, 4), round(h / PT, 4)] for w, h in uniq]

    fonts = sorted({m.group(1).decode("latin-1") for m in RE_BASEFONT.finditer(raw)})
    stripped = [f.split("+", 1)[-1] for f in fonts]
    embedded = (len(RE_FONTFILE2.findall(raw)) + len(RE_FONTFILE3.findall(raw))
                + len(RE_FONTFILE.findall(raw)))
    unembedded = [f for f in stripped if f in STANDARD_14]

    return PdfFacts(
        path=str(p),
        bytes=len(raw),
        page_count=pages,
        pages_count_entry=max(count_entries),
        media_boxes_pt=[list(b) for b in uniq],
        media_boxes_in=boxes_in,
        uniform_page_size=len(uniq) == 1,
        base_fonts=fonts,
        embedded_font_streams=embedded,
        unembedded_fonts=unembedded,
        has_object_streams=bool(RE_OBJSTM.search(raw)),
        image_count=len(RE_IMAGE.findall(raw)),
        uses_rgb=bool(RE_COLORSPACE_RGB.search(raw)),
        uses_cmyk=bool(RE_COLORSPACE_CMYK.search(raw)),
        text_sample=_extract_text(raw, text_limit) if want_text else "",
    )
