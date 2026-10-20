"""A short, explicitly arranged excerpt of the in-repo reference, not a new genre engine."""
from pathlib import Path
import sys

import mido

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from example_dense_arrangement import BPM, TPB, PROGRAMS, compose
from hermesmusic import build_track

SECTIONS = [('intro', 0, 4, 6), ('verse', 12, 4, 15), ('chorus', 32, 4, 16)]


def plan():
    roles = {'rhythm_guitar_L': ('rhythm_guitar', 48, 71, 0),
             'rhythm_guitar_R': ('rhythm_guitar', 48, 71, 0),
             'electric_bass': ('bass', 24, 47, 0),
             'synth_piano': ('piano', 60, 84, 4),
             'lead_guitar': ('lead', 76, 88, 4)}
    return {'profile': 'dense', 'intent': '18-second GM structural demo: three contrasting grooves, '
            'power chords and piano silence; listening quality not certified.',
            'sections': [{'name': n, 'bars': bars, 'groove': n, 'density': d}
                         for n, source, bars, d in SECTIONS],
            'instruments': [{'name': 'drums', 'role': 'drums', 'silent_bars': 0}] +
                [{'name': name, 'role': r, 'min': lo, 'max': hi, 'silent_bars': silent}
                 for name, (r, lo, hi, silent) in roles.items()], 'fill_bars': []}


def save(path):
    song = mido.MidiFile(type=1, ticks_per_beat=TPB)
    meta = mido.MidiTrack([mido.MetaMessage('track_name', name='Hermes short structural demo'),
                          mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)),
                          mido.MetaMessage('time_signature', numerator=4, denominator=4)])
    previous = target = 0
    for name, source, bars, density in SECTIONS:
        meta.append(mido.MetaMessage('marker', text=name, time=(target - previous) * 4 * TPB))
        previous = target
        target += bars
    meta.append(mido.MetaMessage('end_of_track', time=(target - previous) * 4 * TPB))
    song.tracks.append(meta)
    for name, notes in compose().items():
        excerpt = []
        target = 0
        for section, source, bars, density in SECTIONS:
            for start, duration, pitch, velocity in notes:
                if source * 4 <= start < (source + bars) * 4:
                    excerpt.append((start - source * 4 + target * 4,
                                    min(duration, (source + bars) * 4 - start), pitch, velocity))
            target += bars
        program, channel = (0, 9) if name == 'drums' else PROGRAMS[name]
        song.tracks.append(build_track(name, excerpt, program, channel, TPB, name == 'drums'))
    song.save(path)
