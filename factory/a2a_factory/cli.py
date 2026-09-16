"""a2a - one spec in, one title package out."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import kdp, spec as specmod
from .pipeline import build

ROOT = Path(__file__).resolve().parent.parent.parent


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="a2a", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="run the full pipeline on one title spec")
    b.add_argument("spec", type=Path)
    b.add_argument("--rates", default=kdp.DEFAULT_RATE_VERSION)
    b.add_argument("--keep-going", action="store_true",
                   help="record gate failures but do not stop (diagnostics only)")

    q = sub.add_parser("quote", help="page math and money for a hypothetical book")
    q.add_argument("--pages", type=int, required=True)
    q.add_argument("--trim", default="6x9")
    q.add_argument("--paper", default="cream")
    q.add_argument("--ink", default="bw")
    q.add_argument("--price", type=float, default=None)
    q.add_argument("--rates", default=kdp.DEFAULT_RATE_VERSION)

    v = sub.add_parser("validate", help="check a spec without building anything")
    v.add_argument("spec", type=Path)

    a = ap.parse_args(argv)

    if a.cmd == "build":
        s = specmod.load(a.spec)
        state = build(s, ROOT, a.rates, keep_going=a.keep_going)
        return 0 if state["status"] == "OK" else 2

    if a.cmd == "validate":
        s = specmod.load(a.spec)
        print(json.dumps(s.as_dict(), indent=2, default=str))
        return 0

    if a.cmd == "quote":
        rates = kdp.load_rates(a.rates)
        w, h = (float(x) for x in a.trim.lower().split("x"))
        g = kdp.cover_geometry(w, h, a.pages, a.paper, rates)
        e = kdp.economics(a.pages, a.ink, a.paper, w, h, rates, list_price=a.price)
        m = kdp.margins_for(a.pages, rates)
        print(json.dumps({"geometry": g.as_dict(), "economics": e.as_dict(),
                          "margins": m.as_dict()}, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
