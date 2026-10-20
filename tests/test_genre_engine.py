"""Contract tests for the genre metadata and harmonic-form planner."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE / "scripts"))
import genre_engine as ge


class GenreProfilesTests(unittest.TestCase):
    def test_every_catalogue_genre_has_a_differentiated_profile(self):
        profiles = ge.load_profiles()
        catalogue = json.loads((BASE / "references" / "genre_configs.json").read_text())
        self.assertEqual(set(profiles), set(catalogue))
        for name, profile in profiles.items():
            with self.subTest(name=name):
                self.assertEqual(profile["id"], name)
                self.assertGreaterEqual(len(profile["minimum_identity"]), 1)
                self.assertTrue(profile["required_roles"] or profile["requires_choice"])
                self.assertIn(profile["harmony_strategy"], ge.STRATEGIES)
                self.assertIn(profile["evidence_level"], {"direct", "family", "provisional"})
                self.assertIn("meter", profile)
                if profile["requires_choice"]:
                    self.assertTrue(profile["variants"], f"{name}: requiere variante pero no ofrece ninguna")
                self.assertGreaterEqual(len(profile["differentiator"]), 12)

    def test_umbrella_labels_fail_closed(self):
        for name in ("folk", "electronic", "classical", "alternative", "experimental", "comedy_music", "spoken_word"):
            self.assertTrue(ge.get_profile(name)["requires_choice"], name)
            with self.assertRaises(ValueError):
                ge.plan_song(name, key="C", seed=1)

    def test_metal_subvariant_tree(self):
        for name in ("power_metal", "death_metal", "black_metal", "thrash_metal", "doom_metal", "prog_rock"):
            p = ge.get_profile(name)
            self.assertGreaterEqual(len(p["variants"]), 2, name)
            self.assertTrue(all(v["minimum_identity"] for v in p["variants"].values()))
        p = ge.get_profile("power_metal", "symphonic")
        self.assertIn("symphonic", p["variant"])
        self.assertTrue(any("orquest" in x.lower() for x in p["minimum_identity"]))

    def test_non_pop_meters_and_percussion(self):
        self.assertEqual(ge.get_profile("waltz")["meter"], [3, 4])
        self.assertEqual(ge.get_profile("jig")["meter"], [6, 8])
        self.assertNotIn("drum_kit", ge.get_profile("baroque")["required_roles"])
        self.assertNotIn("drum_kit", ge.get_profile("ambient")["required_roles"])


class HarmonicPlannerTests(unittest.TestCase):
    def test_reproducible_and_keyed(self):
        a = ge.plan_song("power_metal", key="D", seed=17)
        b = ge.plan_song("power_metal", key="D", seed=17)
        self.assertEqual(a, b)
        self.assertNotEqual(a, ge.plan_song("power_metal", key="E", seed=17))
        self.assertIn("sections", a)
        self.assertGreaterEqual(len(a["sections"]), 5)
        self.assertEqual(a["profile_id"], "power_metal")
        self.assertFalse(a["verified_audio"])

    def test_motif_returns_with_controlled_variation(self):
        a = ge.plan_song("power_metal", key="A", seed=23)
        motifs = [s for s in a["sections"] if s["motif"] == "A"]
        self.assertGreaterEqual(len(motifs), 3)
        first = [b["degree"] for b in motifs[0]["bars"]]
        for s in motifs[1:]:
            seq = [b["degree"] for b in s["bars"]]
            self.assertEqual(len(first), len(seq))
            self.assertGreaterEqual(sum(x == y for x, y in zip(first, seq)), len(first) - 1)
        self.assertTrue(any("permut" in b["origin"] for s in motifs[1:] for b in s["bars"]))

    def test_user_motif_is_anchor_and_no_fake_cadence_in_loop(self):
        a = ge.plan_song("pop", key="C", seed=4, motif=["C", "G", "Am", "F"])
        self.assertEqual([b["symbol"] for b in a["sections"][1]["bars"]], ["C", "G", "Am", "F"])
        self.assertEqual(a["strategy"], "loop")
        self.assertFalse(any(s["cadence_forced"] for s in a["sections"]))
        with self.assertRaises(ValueError):
            ge.plan_song("pop", key="C", seed=4, motif=["C", "not-a-chord"])

    def test_blues_is_twelve_bar_and_functional_cadence(self):
        a = ge.plan_song("blues", key="C", seed=8)
        motif = [s for s in a["sections"] if s["motif"] == "A"][0]
        self.assertEqual(len(motif["bars"]), 12)
        degrees = [b["degree"] for b in motif["bars"]]
        self.assertEqual(degrees[:4], ["I7"] * 4)
        self.assertIn("IV7", degrees)
        self.assertIn("V7", degrees)
        functional = ge.plan_song("baroque", key="D", seed=10)
        self.assertTrue(any(s["cadence_forced"] for s in functional["sections"]))

    def test_meters_and_direct_midi_export_are_honest(self):
        song = ge.plan_song("waltz", key="F", seed=12)
        self.assertEqual(song["meter"], [3, 4])
        import mido
        with tempfile.TemporaryDirectory() as work:
            p = Path(work) / 'waltz.mid'
            ge.export_harmony_midi(song, p)
            midi = mido.MidiFile(p)
            self.assertEqual(midi.tracks[0][1].numerator, 3)
            self.assertGreater(sum(msg.type == "note_on" and msg.velocity > 0 for track in midi.tracks for msg in track), 10)

    def test_scored_permutations_expose_form_and_vary_seed(self):
        plans = [ge.plan_song("power_metal", key="A", seed=i) for i in range(12)]
        assert len({tuple(x["degree"] for x in p["sections"][3]["bars"]) for p in plans}) >= 3
        for p in plans:
            section = p["sections"][3]
            self.assertIn("score", section)
            self.assertIn("score_components", section)
            self.assertIn("motif_similarity", section["score_components"])
            self.assertGreaterEqual(section["score_components"]["motif_similarity"], .75)
            self.assertTrue(section["transformations"])

    def test_bridge_and_b_have_real_contrast_and_reprise(self):
        for genre, variant in [("power_metal", None), ("pop", None), ("jazz", "bebop")]:
            p = ge.plan_song(genre, variant=variant, key="C", seed=3)
            a = [x["degree"] for x in p["sections"][1]["bars"]]
            b = [x["degree"] for x in p["sections"][2]["bars"]]
            self.assertGreaterEqual(sum(x != y for x, y in zip(a, b)), 2)
            self.assertEqual(p["sections"][3]["bars"][0]["degree"], a[0])

    def test_odd_meter_and_no_spurious_v_to_i_in_drone(self):
        a = ge.plan_song("drone", key="C", seed=1)
        self.assertEqual(a["strategy"], "drone")
        self.assertTrue(all(not s["cadence_forced"] for s in a["sections"]))
        self.assertLessEqual(len({b["symbol"] for s in a["sections"] for b in s["bars"]}), 2)
        with self.assertRaises(ValueError):
            ge.plan_song("power_metal", key="H", seed=1)


if __name__ == "__main__":
    unittest.main()
