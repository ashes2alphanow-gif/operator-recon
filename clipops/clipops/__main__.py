"""CLIPOPS command line.

  python -m clipops daily            scout -> analyze -> render -> show queue
  python -m clipops scout            find new source videos
  python -m clipops analyze          Analyst + Packager on scouted videos
  python -m clipops render [ID]      render clips (all pending if no ID)
  python -m clipops queue            what's ready, what needs your VO
  python -m clipops post [-n 3]      schedule ready clips into the next slots
  python -m clipops posted ID YTID   log a manual upload
  python -m clipops reject ID        kill a clip
  python -m clipops stats            pull views for posted clips, by pillar
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict

from .core import MEDIA, Ledger, load_config


def clip_dir(c: dict):
    return MEDIA / c["video_id"] / c["id"]


def cmd_scout(cfg, L, a):
    from .scout import scout_own, scout_youtube
    n_own = scout_own(cfg, L)
    print(f"scout: {n_own} own-footage files")
    L.save()
    if not a.own_only:
        scout_youtube(cfg, L, max_new=a.max)
        L.save()


def cmd_analyze(cfg, L, a):
    from .agents import Team
    from .transcript import get_words, slice_words
    team = Team(cfg)
    todo = sorted(L.videos("scouted"), key=lambda v: v.get("score", 0), reverse=True)[: a.limit]
    for v in todo:
        print(f"analyze: {v['title'][:70]}")
        try:
            words = get_words(v)
            picks = team.analyze(v, words)
        except Exception as e:
            print(f"  fail: {e}")
            v["status"], v["error"] = "failed", str(e)[:200]
            L.save()
            continue
        v["status"] = "analyzed"
        print(f"  {len(picks)} clip(s) cleared the bar")
        for p in picks:
            cid = f"{v['id'][:16]}-{int(p['start'])}"
            text = " ".join(w["w"] for w in slice_words(words, p["start"], p["end"]))
            try:
                pkg = team.package(v, p, text)
            except Exception as e:
                print(f"  package fail {cid}: {e}")
                continue
            L.put_clip({**p, "id": cid, "video_id": v["id"], "status": "packaged", "package": pkg})
            d = MEDIA / v["id"] / cid
            d.mkdir(parents=True, exist_ok=True)
            (d / "vo_script.txt").write_text(
                f"VO OPEN  (save as vo_open.m4a — optional)\n{pkg['vo_open']}\n\n"
                f"VO CLOSE (save as vo_close.m4a — required for non-own footage)\n{pkg['vo_close']}\n")
            print(f"  + {cid}  {p['score']}  [{p['pillar']}]  {pkg['title']}")
        L.save()


def cmd_render(cfg, L, a):
    from .editor import render_clip
    from .publisher import gate
    from .transcript import get_words, slice_words
    targets = [L.clip(a.id)] if a.id else L.clips("packaged") + L.clips("needs_vo")
    for c in targets:
        v = L.db["videos"][c["video_id"]]
        d = clip_dir(c)
        try:
            words = slice_words(get_words(v), c["start"], c["end"])
            final = render_clip(v, c, words, cfg, d)
        except Exception as e:
            print(f"render fail {c['id']}: {e}")
            continue
        block = gate(v, d, cfg)
        c["final"] = str(final)
        c["status"] = "ready" if block is None else ("needs_vo" if block == "needs_vo" else "rejected")
        c["block"] = block
        print(f"render {c['id']}: {c['status']}{'  (' + block + ')' if block else ''}")
        L.save()


def cmd_queue(cfg, L, a):
    by = defaultdict(list)
    for c in L.clips():
        by[c["status"]].append(c)
    for st in ["ready", "needs_vo", "packaged", "scheduled", "posted"]:
        cs = by.get(st, [])
        print(f"\n== {st.upper()} ({len(cs)})")
        for c in sorted(cs, key=lambda c: -c["score"]):
            print(f"  {c['id']}  {c['score']}  [{c['pillar']}]  {c['package']['title']}")
            if st == "needs_vo":
                print(f"      record VO -> {clip_dir(c)}/vo_close.m4a   (script: vo_script.txt)")
            if st == "scheduled":
                print(f"      {c.get('slot')}  {c.get('kit') or c.get('yt_id')}")


def cmd_post(cfg, L, a):
    from datetime import datetime
    from pathlib import Path
    from .publisher import build_kit, next_slot, upload
    taken = {c["slot"] for c in L.clips() if c.get("slot")}
    ready = sorted(L.clips("ready"), key=lambda c: -c["score"])[: a.n]
    if not ready:
        print("nothing ready. run: python -m clipops queue")
    for c in ready:
        v = L.db["videos"][c["video_id"]]
        when = next_slot(cfg, taken)
        taken.add(when.isoformat())
        if cfg["publish"]["mode"] == "api":
            c["yt_id"] = upload(v, c, Path(c["final"]), when, cfg)
            print(f"uploaded {c['id']} -> https://youtu.be/{c['yt_id']}  publishes {when:%a %H:%M}")
        else:
            c["kit"] = str(build_kit(v, c, Path(c["final"]), when))
            print(f"kit {c['id']} -> {c['kit']}  post {when:%a %b %d %H:%M}")
        c["slot"], c["status"] = when.isoformat(), "scheduled"
        L.save()


def cmd_posted(cfg, L, a):
    c = L.clip(a.id)
    c["yt_id"], c["status"] = a.yt_id, "posted"
    L.save()
    print(f"logged {a.id} -> https://youtube.com/shorts/{a.yt_id}")


def cmd_reject(cfg, L, a):
    L.clip(a.id)["status"] = "rejected"
    L.save()
    print(f"rejected {a.id}")


def cmd_stats(cfg, L, a):
    from .publisher import fetch_stats
    live = [c for c in L.clips() if c.get("yt_id")]
    if not live:
        print("no posted clips with a YouTube id yet")
        return
    st = fetch_stats([c["yt_id"] for c in live])
    agg = defaultdict(lambda: [0, 0])
    for c in live:
        s = st.get(c["yt_id"], {})
        c["stats"] = s
        agg[c["pillar"]][0] += 1
        agg[c["pillar"]][1] += s.get("viewCount", 0)
        print(f"  {s.get('viewCount', 0):>9,} views  {s.get('likeCount', 0):>6,} likes  [{c['pillar']}]  {c['package']['title'][:60]}")
    L.save()
    print("\nby pillar (clips / total views / avg):")
    for p, (n, views) in sorted(agg.items(), key=lambda kv: -kv[1][1]):
        print(f"  {p:<16} {n:>3}  {views:>10,}  {views // max(n, 1):>8,}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="clipops")
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("scout"); s.add_argument("--max", type=int, default=15); s.add_argument("--own-only", action="store_true")
    s = sub.add_parser("analyze"); s.add_argument("--limit", type=int, default=5)
    s = sub.add_parser("render"); s.add_argument("id", nargs="?")
    sub.add_parser("queue")
    s = sub.add_parser("post"); s.add_argument("-n", type=int, default=3)
    s = sub.add_parser("posted"); s.add_argument("id"); s.add_argument("yt_id")
    s = sub.add_parser("reject"); s.add_argument("id")
    sub.add_parser("stats")
    s = sub.add_parser("daily"); s.add_argument("--max", type=int, default=10); s.add_argument("--limit", type=int, default=5)
    a = ap.parse_args(argv)

    cfg, L = load_config(), Ledger()
    if a.cmd == "daily":
        a.own_only, a.id = False, None
        for f in (cmd_scout, cmd_analyze, cmd_render, cmd_queue):
            f(cfg, L, a)
        return
    {"scout": cmd_scout, "analyze": cmd_analyze, "render": cmd_render, "queue": cmd_queue, "post": cmd_post,
     "posted": cmd_posted, "reject": cmd_reject, "stats": cmd_stats}[a.cmd](cfg, L, a)


if __name__ == "__main__":
    sys.exit(main())
