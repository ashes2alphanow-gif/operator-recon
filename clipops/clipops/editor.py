"""EDITOR — cuts the segment and renders a 1080x1920 Short.

Layout:
  [open card: hook text + your VO]   only if vo_open.* exists in the clip folder
  [the clip: hook banner 3s, burned captions, loudness-normalized]
  [end card: your closing take + your VO]   silent card if no vo_close.*

Drop voice memos named vo_open.m4a / vo_close.m4a (mp3/wav fine) into the
clip folder and re-run `render`. That VO is the commentary layer.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

W, H, FPS = 1080, 1920, 30
ENC = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(FPS),
       "-video_track_timescale", "15360", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
AUDIO_EXT = (".m4a", ".mp3", ".wav", ".aac", ".ogg")


def run(cmd: list[str], cwd: Path | None = None):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{cmd[0]} failed:\n{r.stderr[-1500:]}")
    return r


def duration(path: Path) -> float:
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(path)])
    return float(json.loads(r.stdout)["format"]["duration"])


def find_vo(clip_dir: Path, name: str) -> Path | None:
    for ext in AUDIO_EXT:
        p = clip_dir / f"{name}{ext}"
        if p.exists():
            return p
    return None


# ---- ASS subtitle building -------------------------------------------------
def _ts(t: float) -> str:
    t = max(t, 0)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def _esc(s: str) -> str:
    return s.replace("\\", "").replace("{", "(").replace("}", ")").replace("\n", " ").strip()


def ass_header(font: str) -> str:
    return f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Hook,{font},70,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,3,18,0,8,80,80,250,1
Style: Cap,{font},84,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,1,0,0,0,100,100,0,0,1,6,2,2,70,70,560,1
Style: Card,{font},76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,0,0,1,0,0,5,110,110,0,1
Style: Mark,{font},34,&H99FFFFFF,&H99FFFFFF,&H00000000,&H00000000,1,0,0,0,100,100,2,0,1,0,0,2,40,40,90,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def caption_chunks(words: list[dict], per: int = 3, max_gap: float = 0.6) -> list[tuple[float, float, str]]:
    chunks, cur = [], []
    for w in words:
        if cur and (len(cur) >= per or w["s"] - cur[-1]["e"] > max_gap):
            chunks.append(cur)
            cur = []
        cur.append(w)
    if cur:
        chunks.append(cur)
    out = []
    for i, c in enumerate(chunks):
        end = c[-1]["e"]
        if i + 1 < len(chunks):
            end = min(max(end, c[0]["s"] + 0.35), chunks[i + 1][0]["s"])
        out.append((c[0]["s"], end, " ".join(x["w"] for x in c)))
    return out


def clip_ass(words: list[dict], hook: str, dur: float, font: str, per: int, mark: str = "") -> str:
    lines = [ass_header(font)]
    if hook:
        lines.append(f"Dialogue: 1,{_ts(0)},{_ts(min(3.0, dur))},Hook,,0,0,0,,{_esc(hook).upper()}")
    for s, e, txt in caption_chunks(words, per):
        if s >= dur:
            break
        lines.append(f"Dialogue: 0,{_ts(s)},{_ts(min(e, dur))},Cap,,0,0,0,,{_esc(txt).upper()}")
    if mark:
        lines.append(f"Dialogue: 0,{_ts(0)},{_ts(dur)},Mark,,0,0,0,,{_esc(mark)}")
    return "\n".join(lines) + "\n"


def card_ass(text: str, dur: float, font: str, mark: str = "") -> str:
    lines = [ass_header(font), f"Dialogue: 0,{_ts(0)},{_ts(dur)},Card,,0,0,0,,{_esc(text)}"]
    if mark:
        lines.append(f"Dialogue: 0,{_ts(0)},{_ts(dur)},Mark,,0,0,0,,{_esc(mark)}")
    return "\n".join(lines) + "\n"


# ---- source segment ------------------------------------------------------
def fetch_segment(video: dict, start: float, end: float, out: Path):
    if out.exists():
        return
    if video.get("source") == "local":
        run(["ffmpeg", "-y", "-ss", f"{start}", "-to", f"{end}", "-i", video["path"], *ENC, str(out)])
        return
    from yt_dlp import YoutubeDL
    from yt_dlp.utils import download_range_func
    opts = {
        "quiet": True, "no_warnings": True,
        "format": "bv*[height<=1080][ext=mp4]+ba[ext=m4a]/bv*[height<=1080]+ba/b",
        "merge_output_format": "mp4",
        "download_ranges": download_range_func(None, [(start, end)]),
        "force_keyframes_at_cuts": True,
        "outtmpl": str(out.with_suffix(".%(ext)s")),
    }
    with YoutubeDL(opts) as y:
        y.download([video["url"]])
    if not out.exists():
        cands = list(out.parent.glob(out.stem + ".*"))
        if not cands:
            raise RuntimeError("segment download failed")
        cands[0].rename(out)


# ---- render ----------------------------------------------------------------
def _frame_filter(mode: str) -> str:
    if mode == "crop":
        return f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1[base]"
    return (f"[0:v]split=2[a][b];"
            f"[a]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},boxblur=24:4,eq=brightness=-0.12[bg];"
            f"[b]scale={W}:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2,setsar=1[base]")


def render_main(src: Path, words: list[dict], hook: str, cfg: dict, out: Path, mark: str = ""):
    r = cfg["render"]
    dur = duration(src)
    (out.parent / "main.ass").write_text(clip_ass(words, hook, dur, r["font"], r["caption_words"], mark))
    fc = f"{_frame_filter(r['frame'])};[base]ass=main.ass[v];[0:a]loudnorm=I={r['loudness_lufs']}:TP=-1.5:LRA=11[a]"
    run(["ffmpeg", "-y", "-i", src.name, "-filter_complex", fc, "-map", "[v]", "-map", "[a]", *ENC, out.name],
        cwd=out.parent)


def render_card(text: str, vo: Path | None, cfg: dict, out: Path, mark: str = ""):
    r = cfg["render"]
    dur = (duration(vo) + 0.4) if vo else float(r["card_seconds"])
    ass_name = out.stem + ".ass"
    (out.parent / ass_name).write_text(card_ass(text, dur, r["font"], mark))
    audio = ["-i", str(vo.resolve())] if vo else ["-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo"]
    afilt = f"[1:a]loudnorm=I={r['loudness_lufs']}:TP=-1.5:LRA=11,apad[a]" if vo else "[1:a]anull[a]"
    run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x0b0b0b:s={W}x{H}:r={FPS}:d={dur:.2f}", *audio,
         "-filter_complex", f"[0:v]ass={ass_name}[v];{afilt}", "-map", "[v]", "-map", "[a]",
         "-t", f"{dur:.2f}", *ENC, out.name], cwd=out.parent)


def render_clip(video: dict, clip: dict, words: list[dict], cfg: dict, clip_dir: Path) -> Path:
    """Full render. Returns path to final.mp4."""
    clip_dir.mkdir(parents=True, exist_ok=True)
    pkg = clip["package"]
    mark = cfg["channel"].get("watermark") or ""
    src = clip_dir / "src.mp4"
    fetch_segment(video, clip["start"], clip["end"], src)

    parts = []
    vo_open, vo_close = find_vo(clip_dir, "vo_open"), find_vo(clip_dir, "vo_close")
    if vo_open:
        render_card(pkg["on_screen_hook"], vo_open, cfg, clip_dir / "p0_open.mp4", mark)
        parts.append("p0_open.mp4")
    render_main(src, words, pkg["on_screen_hook"], cfg, clip_dir / "p1_main.mp4", mark)
    parts.append("p1_main.mp4")
    render_card(pkg["close_take"], vo_close, cfg, clip_dir / "p2_close.mp4", mark)
    parts.append("p2_close.mp4")

    (clip_dir / "parts.txt").write_text("".join(f"file '{p}'\n" for p in parts))
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "parts.txt", "-c", "copy",
         "-movflags", "+faststart", "final.mp4"], cwd=clip_dir)
    return clip_dir / "final.mp4"
