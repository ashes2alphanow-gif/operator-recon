"""Regression tests. Run: python3 factory/tests/test_factory.py"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "factory"))

from a2a_factory import kdp, lanes, pdfinspect, spec as specmod, textmetrics as tm  # noqa: E402
from a2a_factory.stages.listing import pick_keywords  # noqa: E402

RATES = kdp.load_rates()
OUT = ROOT / "output"


class PageMath(unittest.TestCase):
    def test_spine_white_200pp(self):
        self.assertAlmostEqual(kdp.spine_width(200, "white", RATES), 0.5104, places=4)

    def test_spine_cream_is_thicker_than_white(self):
        self.assertGreater(kdp.spine_width(300, "cream", RATES),
                           kdp.spine_width(300, "white", RATES))

    def test_wrap_is_two_trims_plus_spine_plus_bleed(self):
        g = kdp.cover_geometry(6, 9, 200, "white", RATES)
        self.assertAlmostEqual(g.wrap_w, 0.125 * 2 + 6 * 2 + g.spine, places=6)
        self.assertAlmostEqual(g.wrap_h, 9 + 0.25, places=6)
        self.assertAlmostEqual(g.front_x0, 0.125 + 6 + g.spine, places=6)

    def test_gutter_bands(self):
        self.assertEqual(kdp.gutter_min(100, RATES), 0.375)
        self.assertEqual(kdp.gutter_min(151, RATES), 0.5)
        self.assertEqual(kdp.gutter_min(301, RATES), 0.625)
        self.assertEqual(kdp.gutter_min(828, RATES), 0.875)

    def test_page_bounds_reject_short_and_long(self):
        with self.assertRaises(kdp.SpecError):
            kdp.spine_width(20, "white", RATES)
        with self.assertRaises(kdp.SpecError):
            kdp.spine_width(800, "cream", RATES)   # cream tops out lower than white

    def test_unknown_trim_is_refused(self):
        with self.assertRaises(kdp.SpecError):
            kdp.trim_class(6.5, 9.5, RATES)


class Money(unittest.TestCase):
    def test_flat_tier_and_per_page_tier(self):
        self.assertEqual(kdp.print_cost(96, "bw", 5.5, 8.5, RATES), 2.30)
        self.assertEqual(kdp.print_cost(108, "bw", 5.5, 8.5, RATES), 2.30)
        self.assertEqual(kdp.print_cost(200, "bw", 6, 9, RATES), round(1.00 + 0.012 * 200, 2))

    def test_unverified_rates_refuse_to_price(self):
        with self.assertRaises(kdp.RateError):
            kdp.print_cost(200, "premium_color", 6, 9, RATES)
        self.assertGreater(
            kdp.print_cost(200, "premium_color", 6, 9, RATES, allow_unverified=True), 0)

    def test_price_below_floor_is_refused(self):
        with self.assertRaises(kdp.SpecError):
            kdp.economics(300, "bw", "white", 6, 9, RATES, list_price=3.00)

    def test_royalty_and_breakeven(self):
        e = kdp.economics(96, "bw", "cream", 5.5, 8.5, RATES, list_price=13.99)
        self.assertAlmostEqual(e.royalty_per_copy, round(13.99 * 0.6 - 2.30, 2), places=2)
        self.assertEqual(kdp.breakeven_units(150.0, e.royalty_per_copy), 25)


class SpecRules(unittest.TestCase):
    def _write(self, tmp: Path, **over) -> Path:
        base = {
            "title": "Test Title", "subtitle": "A Subtitle", "lane": "devotional",
            "reader": "r", "reader_problem": "p", "promise": "q", "transformation": "t",
            "units": [{"title": f"Entry {i}", "thesis": f"Thesis number {i} about a thing"}
                      for i in range(1, 21)],
        }
        base.update(over)
        import yaml
        p = tmp / "s.yml"
        p.write_text(yaml.safe_dump(base))
        return p

    def test_byline_is_locked(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = self._write(Path(d), author="Somebody Else")
            with self.assertRaises(specmod.SpecError):
                specmod.load(p)

    def test_placeholder_is_refused(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = self._write(Path(d), promise="[PROMISE TO BE ADDED]")
            with self.assertRaises(specmod.SpecError):
                specmod.load(p)

    def test_unit_count_must_fit_the_lane(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            p = self._write(Path(d), units=[{"title": "Only One", "thesis": "not enough"}])
            with self.assertRaises(specmod.SpecError):
                specmod.load(p)


class Keywords(unittest.TestCase):
    def test_filters_and_takes_seven(self):
        seeds = ["devotional for police", "devotional for police", "best devotional",
                 "x" * 60, "test title", "a", "b", "c", "d", "e", "f", "g"]
        chosen, spare, rejected = pick_keywords(seeds, "Test Title", "")
        self.assertEqual(len(chosen), 7)
        reasons = {r["keyword"]: r["reason"] for r in rejected}
        self.assertIn("duplicate", reasons["devotional for police"])
        self.assertIn("disallows", reasons["best devotional"])
        self.assertIn("50-char", reasons["x" * 60])
        self.assertIn("already appears", reasons["test title"])


class TextMetrics(unittest.TestCase):
    ABSTRACT = ("Faith is a posture of the heart. When we release control we begin to "
                "experience peace that is not dependent on circumstances. This is the "
                "invitation offered to each of us in every season of life.")
    CONCRETE = ("The alarm went at 1730 for a shift that starts at 1900. He checked the "
                "radio battery, keyed the mic twice, and walked the fence line at 0300 "
                "with a flashlight dimmer than it was last month.")

    def test_abstract_scores_near_zero_and_concrete_scores_high(self):
        self.assertLess(tm.concrete_density(self.ABSTRACT), 1.0)
        self.assertGreater(tm.concrete_density(self.CONCRETE), 3.0)

    def test_scripture_citations_do_not_count_as_concrete(self):
        self.assertEqual(tm.concrete_density("Psalm 46:10 Be still and know."), 0.0)

    def test_near_duplicate_pairs_are_found(self):
        a = ("Surrender is not weakness. It is the beginning of strength because it "
             "releases the weight you were never meant to carry alone in the first place.")
        b = ("Surrender is not weakness at all. It is the start of strength, since it "
             "releases weight you were never meant to carry alone in the first place.")
        c = ("The alarm went at 1730 and the truck needed fuel before the shift started, "
             "so he stopped at the pump on the way in and lost eleven minutes doing it.")
        pairs = tm.near_duplicate_pairs([("a", a), ("b", b), ("c", c)])
        self.assertEqual(len(pairs), 1)
        self.assertEqual({pairs[0]["a"], pairs[0]["b"]}, {"a", "b"})

    def test_filler_is_detected(self):
        self.assertIn("in today's world", tm.filler_hits("In today's world we must adapt."))


class Lanes(unittest.TestCase):
    def test_every_lane_has_a_usable_profile(self):
        for key, lane in lanes.LANES.items():
            self.assertLess(lane.min_units, lane.max_units, key)
            self.assertLess(lane.min_words_per_unit, lane.max_words_per_unit, key)
            self.assertTrue(lane.required_unit_sections, key)
            self.assertIn(lane.claim_risk, ("low", "elevated", "high"), key)

    def test_high_risk_lanes_demand_evidence(self):
        self.assertTrue(lanes.TECHNICAL.source_ledger_required)
        self.assertTrue(lanes.TECHNICAL.professional_review_required)


class BuiltArtifacts(unittest.TestCase):
    """These read the last pilot build. Skipped if it has not been run."""

    SLUG = "warriors-code-of-prayer-v1"

    def setUp(self):
        self.out = OUT / self.SLUG
        if not (self.out / "run_state.json").exists():
            self.skipTest("pilot has not been built in this tree")
        self.state = json.loads((self.out / "run_state.json").read_text())

    def test_pilot_build_completed_and_every_gate_passed(self):
        self.assertEqual(self.state["status"], "OK")
        for gate, res in self.state["gates"].items():
            self.assertEqual(res["result"], "PASS", gate)

    def test_interior_file_matches_what_the_builder_claimed(self):
        claim = json.loads((self.out / "03_interior" / "interior.json").read_text())
        facts = pdfinspect.inspect(self.out / "03_interior" / claim["pdf"], want_text=True)
        self.assertEqual(facts.page_count, claim["page_count"])
        self.assertEqual(facts.page_count % 2, 0)
        self.assertTrue(facts.uniform_page_size)
        self.assertEqual(facts.unembedded_fonts, [])
        self.assertGreater(facts.embedded_font_streams, 0)
        self.assertIn("watchman", facts.text_sample.lower())

    def test_cover_geometry_matches_the_final_page_count(self):
        claim = json.loads((self.out / "04_cover" / "cover_geometry.json").read_text())
        interior = json.loads((self.out / "03_interior" / "interior.json").read_text())
        expect = kdp.cover_geometry(claim["trim_w"], claim["trim_h"],
                                    interior["page_count"], claim["paper"], RATES)
        self.assertAlmostEqual(claim["spine"], expect.spine, places=6)
        facts = pdfinspect.inspect(self.out / "04_cover" / claim["production_pdf"])
        self.assertEqual(facts.page_count, 1)
        w, h = facts.media_boxes_in[0]
        self.assertAlmostEqual(w, expect.wrap_w, places=2)
        self.assertAlmostEqual(h, expect.wrap_h, places=2)


class PaddedFixture(unittest.TestCase):
    """The gate has to keep rejecting a book that is padding."""

    def setUp(self):
        self.out = OUT / "fixture-padded"
        if not (self.out / "run_state.json").exists():
            self.skipTest("padded fixture has not been built in this tree")

    def test_padded_book_is_halted_at_the_substance_gate(self):
        state = json.loads((self.out / "run_state.json").read_text())
        self.assertEqual(state["status"], "HALTED")
        self.assertEqual(state["halted_at"], "substance")
        codes = {f["code"] for f in
                 json.loads((self.out / "gates" / "substance.json").read_text())["findings"]}
        for expected in ("thin-unit", "repetition", "filler", "placeholder",
                         "missing-section", "abstract-unit"):
            self.assertIn(expected, codes)

    def test_nothing_downstream_was_produced(self):
        self.assertFalse((self.out / "03_interior").glob("*.pdf").__iter__().__next__()
                         if list((self.out / "03_interior").glob("*.pdf")) else False)
        self.assertTrue((self.out / "BUILD_HALTED.md").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
