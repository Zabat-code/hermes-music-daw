"""Regresiones ejecutables de los defectos históricos y del aborto de entrega."""
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest

import mido

SCRIPTS = Path(__file__).resolve().parents[1] / 'scripts'
sys.path.insert(0, str(SCRIPTS))
from audit_arrangement import audit, format_report, ArrangementError, require_arrangement
from composition_guard import main as guarded_main, verify_delivery
from example_dense_arrangement import save_midi, decision_plan
from hermesmusic import build_track, render_song




class ArrangementGuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.TemporaryDirectory(prefix='test-arrangement-')
        cls.root = Path(cls.work.name)
        cls.reference = cls.root / 'reference.mid'
        save_midi(cls.reference)
        cls.song = mido.MidiFile(cls.reference)
        # Portable regression fixture: recreate the measured v1 failure classes,
        # rather than depending on the author's private historical MIDI files.
        cls.bad = cls.root / 'v1_failure_classes.mid'
        bad = copy.deepcopy(cls.song)
        bad.tracks[1] = build_track('drums', [
            (b * 4 + i * .5, .1, pitch, 90)
            for b in range(120) for i in range(8) for pitch in (36, 42, 49)], 0, 9, is_drum=True)
        for tr in bad.tracks[2:]:
            for msg in tr:
                if msg.type == 'note_on' and msg.velocity:
                    msg.velocity = 90
        for msg in bad.tracks[-1]:
            if hasattr(msg, 'note'):
                msg.note += 14
        bad.save(cls.bad)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def mutated(self, transform):
        song = copy.deepcopy(self.song)
        transform(song)
        path = self.root / 'mutated.mid'
        song.save(path)
        return audit(path)

    def gate(self, report, name):
        return next(g['ok'] for g in report['gates'] if g['gate'] == name)

    def test_reference_passes(self):
        self.assertTrue(audit(self.reference)['ok'])

    def test_historical_v1_failure_classes_fail(self):
        report = audit(self.bad)
        for name in ('dinámica', 'registro', 'solapamiento', 'patrones', 'densidad'):
            self.assertFalse(self.gate(report, name))

    def test_corrected_reference_passes(self):
        # El ejemplo interno conserva la corrección; no requiere archivos privados.
        report = audit(self.reference)
        self.assertTrue(report['ok'], format_report(report))

    def test_flat_velocities_fail(self):
        def flatten(song):
            for tr in song.tracks:
                for msg in tr:
                    if msg.type == 'note_on' and msg.velocity:
                        msg.velocity = 90
        self.assertFalse(self.gate(self.mutated(flatten), 'dinámica'))

    def test_high_lead_fails(self):
        def high(song):
            for msg in song.tracks[-1]:
                if hasattr(msg, 'note'):
                    msg.note += 14
        self.assertFalse(self.gate(self.mutated(high), 'registro'))

    def test_held_harmony_is_not_silence(self):
        def held(song):
            song.tracks[5] = build_track('synth_piano', [(0, 480, 64, 80)], 4, 3)
        self.assertFalse(self.gate(self.mutated(held), 'espacio'))

    def test_pedal_extends_occupancy(self):
        def held(song):
            song.tracks[5] = mido.MidiTrack([
                mido.MetaMessage('track_name', name='synth_piano'),
                mido.Message('program_change', program=4, channel=3),
                mido.Message('control_change', control=64, value=127, channel=3),
                mido.Message('note_on', note=64, velocity=80, channel=3),
                mido.Message('note_off', note=64, channel=3, time=480),
            ])
        self.assertFalse(self.gate(self.mutated(held), 'espacio'))

    def test_triples_across_tracks_fail(self):
        def triple(song):
            song.tracks.append(build_track('extra_drums', [(0, .1, 47, 80)], 0, 9, is_drum=True))
        self.assertFalse(self.gate(self.mutated(triple), 'solapamiento'))

    def test_jitter_cannot_hide_triple(self):
        def triple(song):
            song.tracks.append(build_track('extra_drums', [(.01, .1, 47, 80)], 0, 9, is_drum=True))
        self.assertFalse(self.gate(self.mutated(triple), 'solapamiento'))

    def test_repetition_and_fixed_density_fail(self):
        def repeated(song):
            ns = [(b * 4 + off, .1, p, 70 + (b % 15))
                  for b in range(120) for off, p in ((0, 36), (1, 38), (2, 36), (3, 38))]
            song.tracks[1] = build_track('drums', ns, 0, 9, is_drum=True)
        report = self.mutated(repeated)
        self.assertFalse(self.gate(report, 'patrones'))
        self.assertFalse(self.gate(report, 'densidad'))

    def test_periodic_fills_fail(self):
        def periodic(song):
            ns = [(b * 4 + 3 + i * .25, .1, p, 70 + i * 4)
                  for b in range(3, 120, 4) for i, p in enumerate((47, 45, 43, 41))]
            song.tracks[1] = build_track('drums', ns, 0, 9, is_drum=True)
        self.assertFalse(self.gate(self.mutated(periodic), 'fills'))

    def test_gate_raises(self):
        with self.assertRaises(ArrangementError):
            require_arrangement(self.bad)

    def test_engine_rejects_grid_before_overwriting_target(self):
        out = self.root / 'protected.mid'
        out.write_bytes(b'original intacto')
        spec = {'sections': [{'name': 'A', 'bars': 8}], 'tracks': [
            {'role': 'drums', 'pattern': 'drum_grid',
             'grid': {'kick': [1], 'snare': [1], 'hihat': [1]}}]}
        with self.assertRaisesRegex(ValueError, 'drum_grid rechazado'):
            render_song(spec, str(out))
        self.assertEqual(out.read_bytes(), b'original intacto')

    def test_engine_rejects_grid_offset_collisions(self):
        out = self.root / 'offset.mid'
        spec = {'sections': [{'name': 'A', 'bars': 8}], 'tracks': [
            {'role': 'drums', 'pattern': 'drum_grid', 'grid': {
                'kick': [1], 'snare': [0, [1, -.25]],
                'hihat': [0, 0, [1, -.5]]}}]}
        with self.assertRaisesRegex(ValueError, 'tick efectivo'):
            render_song(spec, str(out))
        self.assertFalse(out.exists())

    def test_direct_engine_cannot_publish_repetitive_grid(self):
        out = self.root / 'repetitive.mid'
        spec = {'sections': [{'name': 'A', 'bars': 16}], 'tracks': [
            {'role': 'drums', 'pattern': 'drum_grid', 'grid': {'kick': [1]}}]}
        with self.assertRaises(ArrangementError):
            render_song(spec, str(out))
        self.assertFalse(out.exists())

    def test_basic_api_can_still_publish_valid_non_drum_piece(self):
        out = self.root / 'piano.mid'
        spec = {'humanize': {'seed': 12, 'velocity': .2},
                'sections': [{'name': 'A', 'bars': 8}], 'tracks': [
                    {'role': 'piano', 'pattern': 'arpeggio_up', 'octave': 3}]}
        render_song(spec, str(out))
        self.assertTrue(out.is_file())

    def test_entry_aborts_and_never_publishes_bad_score(self):
        plan = self.root / 'plan.json'
        plan.write_text(json.dumps(decision_plan()))
        composer = self.root / 'bad_composer.py'
        composer.write_text("import shutil,sys\nshutil.copyfile(" +
                            repr(str(self.bad)) + ",sys.argv[1])\n")
        out = self.root / 'must_not_exist.mid'
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = guarded_main([str(plan), '--out', str(out), '--', str(composer), '{draft}'])
        self.assertEqual(code, 1)
        self.assertFalse(out.exists())
        self.assertFalse(Path(str(out) + '.audit.json').exists())

    def test_entry_certifies_and_detects_later_edits(self):
        plan = self.root / 'good_plan.json'
        plan.write_text(json.dumps(decision_plan()))
        out = self.root / 'certified.mid'
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            code = guarded_main([str(plan), '--out', str(out), '--',
                                 str(SCRIPTS / 'example_dense_arrangement.py'), '--out', '{draft}'])
        self.assertEqual(code, 0)
        self.assertTrue(verify_delivery(out)['ok'])
        edited = mido.MidiFile(out)
        edited.tracks[0][0].name = 'Editado después de certificar'
        edited.save(out)
        with self.assertRaisesRegex(ValueError, 'certificado inválido'):
            verify_delivery(out)


if __name__ == '__main__':
    unittest.main()
