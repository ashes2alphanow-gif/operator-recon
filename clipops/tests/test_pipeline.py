"""Offline tests: no network, no API key. Run: python -m unittest discover tests"""
import json
import subprocess
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from clipops import agents, core, editor, publisher, transcript
from clipops.core import load_config

CFG = load_config()


def fake_words(n=60, step=0.5):
    return [{"s": i * step, "e": i * step + 0.4, "w": f"word{i}"} for i in range(n)]


class FakeClient:
    """Stands in for anthropic.Anthropic: returns canned Picks / Package."""
    def __init__(self):
        self.messages = SimpleNamespace(parse=self.parse)

    def parse(self, output_format, **kw):
        if output_format is agents.Picks:
            sc = lambda h, b: agents.Scores(hook=h, brand_fit=b, standalone=8, payoff=8)
            picks = [
                agents.Pick(start_s=2, end_s=26, pillar="k9", first_line="x", why="strong", scores=sc(9, 9), hard_no=False, risk_flags=[]),
                agents.Pick(start_s=5, end_s=28, pillar="k9", first_line="x", why="overlap", scores=sc(8, 8), hard_no=False, risk_flags=[]),
                agents.Pick(start_s=0, end_s=25, pillar="pressure", first_line="x", why="politics", scores=sc(10, 10), hard_no=True, risk_flags=[]),
                agents.Pick(start_s=0, end_s=25, pillar="field_truth", first_line="x", why="weak", scores=sc(4, 5), hard_no=False, risk_flags=[]),
            ]
            out = agents.Picks(picks=picks)
        else:
            out = agents.Package(title="The dog found him first", on_screen_hook="Nobody believed the dog",
                                 close_take="Trust the dog. Then trust your training.", vo_open="v1", vo_close="v2",
                                 description="Handler story.", hashtags=["k9", "sar"], pinned_comment="Best find?")
        return SimpleNamespace(stop_reason="end_turn", parsed_output=out)


class TestLogic(unittest.TestCase):
    def test_json3_parse(self):
        data = {"events": [{"tStartMs": 1000, "dDurationMs": 2000,
                            "segs": [{"utf8": "hold"}, {"utf8": " the", "tOffsetMs": 400}, {"utf8": " line", "tOffsetMs": 900}]},
                           {"tStartMs": 3000, "dDurationMs": 1000, "segs": [{"utf8": "\n"}]},
                           {"tStartMs": 4000, "dDurationMs": 1500, "segs": [{"utf8": "manual caption here"}]}]}
        w = transcript.parse_json3(data)
        self.assertEqual([x["w"] for x in w], ["hold", "the", "line", "manual", "caption", "here"])
        self.assertAlmostEqual(w[1]["s"], 1.4)
        self.assertTrue(all(a["e"] <= b["s"] for a, b in zip(w, w[1:])))

    def test_analyst_gate(self):
        team = agents.Team(CFG, client=FakeClient())
        picks = team.analyze({"title": "t", "channel": "c", "duration": 600}, fake_words())
        self.assertEqual(len(picks), 1)            # overlap, hard-no, weak all dropped
        self.assertEqual(picks[0]["pillar"], "k9")
        self.assertGreaterEqual(picks[0]["score"], CFG["brand"]["min_score"])

    def test_rights_gate(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            self.assertIsNone(publisher.gate({"rights": "own"}, d, CFG))
            self.assertEqual(publisher.gate({"rights": "cc_by"}, d, CFG), "needs_vo")
            self.assertIn("unlicensed", publisher.gate({"rights": "unlicensed"}, d, CFG))
            (d / "vo_close.m4a").write_bytes(b"x")
            self.assertIsNone(publisher.gate({"rights": "permitted"}, d, CFG))

    def test_credit_and_post_text(self):
        v = {"rights": "cc_by", "credit": "@Handler", "url": "https://youtu.be/abc"}
        pkg = {"title": "T", "description": "D", "hashtags": ["k9"]}
        title, desc, tags = publisher.post_text(v, pkg)
        self.assertIn("Source: @Handler (CC BY)", desc)
        self.assertIn("#shorts", desc)
        self.assertEqual(tags, ["k9", "shorts"])

    def test_slots(self):
        tz = ZoneInfo(CFG["channel"]["timezone"])
        now = datetime(2026, 11, 7, 12, 0, tzinfo=tz)
        a = publisher.next_slot(CFG, set(), now)
        b = publisher.next_slot(CFG, {a.isoformat()}, now)
        self.assertEqual((a.hour, a.minute), (17, 30))
        self.assertEqual((b.hour, b.minute), (20, 45))

    def test_captions(self):
        ch = editor.caption_chunks(fake_words(7), per=3)
        self.assertEqual(len(ch), 3)
        self.assertEqual(ch[0][2], "word0 word1 word2")


class TestRender(unittest.TestCase):
    """End to end on a synthetic own-footage file: render + post kit."""
    def test_render_and_kit(self):
        with tempfile.TemporaryDirectory() as d:
            d = Path(d)
            src = d / "talk.mp4"
            subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=s=1280x720:r=30:d=40",
                            "-f", "lavfi", "-i", "sine=f=220:d=40", "-shortest", "-c:v", "libx264", "-c:a", "aac",
                            str(src)], check=True, capture_output=True)
            video = {"id": "own-test", "path": str(src), "url": str(src), "source": "local", "rights": "own",
                     "title": "talk", "channel": "self"}
            pkg = FakeClient().parse(agents.Package).parsed_output.model_dump()
            clip = {"id": "own-test-2", "start": 2.0, "end": 26.0, "package": pkg, "score": 9, "pillar": "k9"}
            words = transcript.slice_words(fake_words(80), 2.0, 26.0)
            out = editor.render_clip(video, clip, words, CFG, d / "clip")
            self.assertTrue(out.exists())
            info = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,codec_type",
                                              "-show_entries", "format=duration", "-of", "json", str(out)],
                                             capture_output=True, text=True).stdout)
            v = [s for s in info["streams"] if s["codec_type"] == "video"][0]
            self.assertEqual((v["width"], v["height"]), (1080, 1920))
            dur = float(info["format"]["duration"])
            self.assertAlmostEqual(dur, 24 + CFG["render"]["card_seconds"], delta=0.6)

            # with VO: open card + close card driven by the voice memo
            for name, f in (("vo_open", 330), ("vo_close", 440)):
                subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", f"sine=f={f}:d=3", "-c:a", "aac",
                                str(d / "clip" / f"{name}.m4a")], check=True, capture_output=True)
            out = editor.render_clip(video, clip, words, CFG, d / "clip")
            self.assertAlmostEqual(editor.duration(out), 24 + 3.4 + 3.4, delta=0.8)
            core.READY = publisher.READY = d / "ready"
            kit = publisher.build_kit(video, clip, out, datetime(2026, 11, 8, 11, 30, tzinfo=ZoneInfo("UTC")))
            self.assertTrue((kit / "video.mp4").exists())
            self.assertIn("The dog found him first", (kit / "post.txt").read_text())


if __name__ == "__main__":
    unittest.main()
