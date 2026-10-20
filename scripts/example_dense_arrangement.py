#!/usr/bin/env python3
"""STANDALONE dense arrangement reference, adapted from Iron Determination v2.

Note-by-note event authoring: explicit form, grooves, registers and rests.
Short durations approximate articulation; GM does NOT establish palm muting or metal.
Audit corrections: voicing capped at two kit pieces per attack, actual cymbal
replacement with crash, spaced toms, no duplicated chord in the coda,
no solo duplicates and minor thirds where the chord symbol specifies minor.
Does not write the original MIDIs or use modules from external projects.

1) --plan plan.json writes decisions without generating notes.
2) composition_guard.py plan.json --out final.mid -- este_script.py --out {draft}
"""
import argparse
import json
import re
import random
import sys
from pathlib import Path

import mido

if __package__:
    from .hermesmusic import build_track, validate_midi
    from .audit_arrangement import require_arrangement
else:
    from hermesmusic import build_track, validate_midi
    from audit_arrangement import require_arrangement

BPM = 160
TPB = 480
BARS = 120
OUT_MID = Path('example_dense_reference.mid')

PCS = {'C': 0, 'C#': 1, 'Db': 1, 'D': 2, 'D#': 3, 'Eb': 3, 'E': 4, 'F': 5,
       'F#': 6, 'Gb': 6, 'G': 7, 'G#': 8, 'Ab': 8, 'A': 9, 'A#': 10, 'Bb': 10, 'B': 11}


def root_midi(sym: str, octave: int) -> int:
    m = re.match(r'([A-G](?:#|b)?)', sym)
    if not m:
        raise ValueError(f'unsupported chord: {sym!r}')
    return 12 * (octave + 1) + PCS[m.group(1)]


# --- structure: exactly 120 bars -------------------------------------
# (name, bars, chords 1/bar, energy 0-1, drum style)
SECTIONS = (
    ('intro',     8,  ('Em', 'Em', 'C', 'D', 'Em', 'Em', 'C', 'D'), 0.35, 'intro'),
    ('verse1',    16, ('Em', 'C', 'G', 'D') * 4,                     0.62, 'verse'),
    ('prechorus', 8,  ('Am', 'C', 'B', 'B', 'Am', 'C', 'B', 'B'),    0.78, 'prechorus'),
    ('chorus1',   16, ('G', 'D', 'Em', 'C') * 4,                     0.95, 'chorus'),
    ('verse2',    16, ('Em', 'C', 'G', 'D') * 4,                     0.66, 'verse'),
    ('chorus2',   16, ('G', 'D', 'Em', 'C') * 4,                     0.97, 'chorus'),
    ('solo',      16, ('Em', 'C', 'D', 'B') * 4,                     0.92, 'solo'),
    ('chorus3',   16, ('G', 'D', 'Em', 'C') * 4,                     1.00, 'chorus'),
    ('outro',     8,  ('Em', 'C', 'D', 'Em', 'Em', 'C', 'B', 'Em'),  0.85, 'outro'),
)
assert sum(s[1] for s in SECTIONS) == BARS


def clamp(v):
    return int(max(1, min(127, v)))


# ==========================================================================
# DRUMS - grooves per function, separate velocities, fills only at boundaries
# ==========================================================================
def arrange_drums(rng):
    notes = []

    def hit(bar, off, pitch, vel, dur=0.12):
        notes.append((round(bar * 4 + off, 5), dur, pitch, clamp(vel + rng.randint(-3, 3))))

    gbar = 0
    for name, bars, chords, energy, style in SECTIONS:
        for local in range(bars):
            bar = gbar
            phrase = (local // 4) % 4
            boundary = (local == bars - 1)
            hats_off = ()          # positions to omit to make room for the fill

            if style == 'intro':
                # build: minimal first 4 bars, then the band enters
                if local < 4:
                    for off in (0, 2):
                        hit(bar, off, 36, 92)
                    for off in (0, 1, 2, 3):
                        hit(bar, off, 42, 56)
                    if local == 0:
                        hit(bar, 0, 49, 98, 0.30)
                else:
                    for off in (0, 1, 2, 3):
                        hit(bar, off, 36, 96)
                    for off in (1, 3):
                        hit(bar, off, 38, 100)
                    for off in (0, .5, 1, 1.5, 2, 2.5, 3, 3.5):
                        hit(bar, off, 42, 60)
                    if local == 4:
                        hit(bar, 0, 49, 100, 0.30)

            elif style == 'verse':
                kicks = ((0, .75, 1.5, 2, 2.75, 3.5),
                         (0, .5, 1.5, 2, 3, 3.5),
                         (0, .75, 1.5, 2, 2.5, 3.5),
                         (0, .5, 1, 1.5, 2.5, 3.5))[phrase]
                for off in kicks:
                    hit(bar, off, 36, 100 if off in (0, 2) else 84)
                for off in (1, 3):
                    hit(bar, off, 38, 102)
                for i in range(8):
                    off = i * .5
                    hit(bar, off, 42, 64 if off.is_integer() else 52)

            elif style == 'prechorus':
                # increasing tension: hi-hat -> ride, double kick at the end
                for i in range(8):
                    off = i * .5
                    hit(bar, off, 36, 100 if off.is_integer() else 88)
                for off in (1, 3):
                    hit(bar, off, 38, 104)
                use_ride = local >= 4
                for i in range(8):
                    off = i * .5
                    hit(bar, off, 51 if use_ride else 42, 76 if use_ride else 60)
                if local == 0:
                    hit(bar, 0, 49, 104, 0.30)
                if local >= 6:
                    for off in (2.25, 2.75, 3.25, 3.75):
                        hit(bar, off, 36, 92)

            elif style in ('chorus', 'solo'):
                for i in range(8):
                    off = i * .5
                    hit(bar, off, 36, 106 if off in (0, 2) else 90)
                for off in (1, 3):
                    hit(bar, off, 38, 108)
                for i in range(8):
                    off = i * .5
                    hit(bar, off, 51, 82 if off.is_integer() else 72)
                if local % 4 == 0:
                    hit(bar, 0, 49, 106, 0.30)

            elif style == 'outro':
                for i in range(8):
                    hit(bar, i * .5, 36, 104 if i % 2 == 0 else 86)
                for off in (1, 3):
                    hit(bar, off, 38, 108)
                for i in range(8):
                    hit(bar, i * .5, 51, 84)
                if local == 0:
                    hit(bar, 0, 49, 108, 0.30)

            # fills ONLY at section boundaries (not every 4 bars)
            if boundary and style != 'outro':
                hats_off = (3, 3.5)
                for i, p in enumerate((47, 45, 43, 41)):
                    hit(bar, 3 + i * .25, p, 74 + i * 8, 0.14)
                hit(bar, 3.75, 49, 92, 0.20)
            if style == 'outro' and boundary:
                hit(bar, 0, 49, 110, 1.60)
                hit(bar, 2, 49, 102, 1.60)

            # remove cymbals that would clash with the fill
            if hats_off:
                notes[:] = [n for n in notes
                            if not (n[2] in (42, 51) and n[0] in
                                    {round(bar * 4 + off, 5) for off in hats_off})]
            gbar += 1
    # Explicit kit orchestration: choose articulations for each attack.
    # This is not an auditor correction; it is part of this composition recipe.
    # Tom replaces snare, crash replaces hat/ride; retain at most a pair.
    voiced = []
    by_attack = {}
    for event in notes:
        by_attack.setdefault(event[0], []).append(event)
    for attack, events in sorted(by_attack.items()):
        pitches = {e[2] for e in events}
        if pitches & {41, 43, 45, 47, 48, 50}:
            events = [e for e in events if e[2] != 38]
        if 49 in pitches:
            events = [e for e in events if e[2] not in (42, 51)]
        # Retain tom+crash in a fill, kick+snare on a backbeat;
        # the cymbal yields when both hands/foot already carry an accent.
        priority = {47: 0, 45: 0, 43: 0, 41: 0, 38: 1, 49: 2, 36: 3, 51: 4, 42: 5}
        voiced.extend(sorted(events, key=lambda e: priority[e[2]])[:2])
    return voiced


# ==========================================================================
# GUITARS - power chords + palm mute, double-tracked (L/R), NO arpeggios
# ==========================================================================
def arrange_guitars(rng):
    L, R = [], []

    def pchord(beat, dur, root, vel, shift):
        for p in (root, root + 7, root + 12):
            L.append((round(beat, 5), dur, p, clamp(vel + rng.randint(-2, 2))))
            R.append((round(beat + shift, 5), dur, p, clamp(vel - 3 + rng.randint(-2, 2))))

    def mute(beat, root, vel, shift):
        L.append((round(beat, 5), 0.11, root, clamp(vel)))
        R.append((round(beat + shift, 5), 0.11, root, clamp(vel - 4)))

    gbar = 0
    for name, bars, chords, energy, style in SECTIONS:
        for local in range(bars):
            beat = gbar * 4
            # octave 3: power chords 48-64, guitar body (not muddy)
            root = root_midi(chords[local % len(chords)], 3)
            shift = 0.014

            if style == 'outro' and local == bars - 1:
                pchord(beat, 3.6, root, 104, shift)
                gbar += 1
                continue

            if style == 'intro':
                for pos in (0, 2.5):
                    pchord(beat + pos, 0.40, root, 72, shift)
                if local >= 4:
                    for off in (.5, 1, 1.5, 2, 3, 3.5):
                        mute(beat + off, root, 66, shift)

            elif style == 'verse':
                for pos in (0, 1.5, 2.5, 3.5):
                    pchord(beat + pos, 0.28, root, 86, shift)
                for off in (.5, .75, 1, 2, 2.25, 3):
                    mute(beat + off, root, 70, shift)

            elif style == 'prechorus':
                for pos in (0, 1, 2, 3):
                    pchord(beat + pos, 0.26, root, 90, shift)
                for off in (.5, .75, 1.5, 2.5, 3.5):
                    mute(beat + off, root, 74, shift)

            elif style in ('chorus', 'solo'):
                for pos in (0, 1, 1.5, 2, 2.5, 3, 3.5):
                    pchord(beat + pos, 0.26, root, 98, shift)
                for off in (.5, .75, 1.25, 1.75, 2.25, 2.75, 3.25):
                    mute(beat + off, root, 78, shift)

            elif style == 'outro':
                for pos in (0, 1, 2, 3):
                    pchord(beat + pos, 0.26, root, 96, shift)
                for off in (.5, .75, 1.5, 2.5, 3.5):
                    mute(beat + off, root, 76, shift)
            gbar += 1
    return L, R


# ==========================================================================
# BASS - eighth-note root, octave jumps in the chorus
# ==========================================================================
def arrange_bass(rng):
    notes = []
    gbar = 0
    for name, bars, chords, energy, style in SECTIONS:
        for local in range(bars):
            beat = gbar * 4
            root = root_midi(chords[local % len(chords)], 1)   # E1 = 28
            full = style in ('chorus', 'solo', 'outro', 'prechorus')
            if style == 'intro' and local < 4:
                for off in (0, 2):
                    notes.append((round(beat + off, 5), 1.6, root, clamp(78)))
            else:
                for i in range(8):
                    off = i * .5
                    pitch = root
                    if full and i in (3, 7):
                        pitch = root + 12
                    vel = 86 if off in (0, 2) else 72
                    notes.append((round(beat + off, 5), 0.44, pitch, clamp(vel + rng.randint(-2, 2))))
            gbar += 1
    return notes


# ==========================================================================
# SYNTH PIANO (Electric Piano, prog 4) - WITH SPACE: silent in verses/solo
# ==========================================================================
def arrange_piano(rng):
    notes = []
    gbar = 0
    for name, bars, chords, energy, style in SECTIONS:
        for local in range(bars):
            beat = gbar * 4
            sym = chords[local % len(chords)]
            r4 = root_midi(sym, 4)          # octave 4: 60-71
            third = 3 if sym.endswith('m') else 4
            r5 = root_midi(sym, 5)          # octave 5: 72-83 (cap 84)

            if style == 'intro':
                # gentle eighth-note arpeggio
                for i, p in enumerate((r4, r4 + third, r4 + 7, r4 + 12,
                                       r4 + 7, r4 + third, r4, r4 + 7)):
                    notes.append((round(beat + i * .5, 5), 0.46, p, clamp(56 + rng.randint(-3, 3))))
            elif style == 'prechorus':
                # sustained chords, building
                for i in (0, 2):
                    for p in (r4, r4 + third, r4 + 7):
                        notes.append((round(beat + i, 5), 1.8, p, clamp(60 + int(energy * 14))))
            elif style in ('chorus', 'outro'):
                # double the riff in the upper octave + sparkle (strict cap 84)
                for i in (0, 2):
                    for p in (r5, r5 + 7):
                        if p <= 84:
                            notes.append((round(beat + i, 5), 0.9, p,
                                          clamp(66 + int(energy * 12))))
                if r5 + 12 <= 84:
                    notes.append((round(beat + 3.5, 5), 0.4, r5 + 12, clamp(62)))
            # verses and solo: deliberate SILENCE (leave room for guitars)
            gbar += 1
    return notes


# ==========================================================================
# LEAD - register 76-88 (never 102), phrases with breathing room
# ==========================================================================
MOTIFS = {
    'A': [(0, .70, 76), (.75, .25, 79), (1, .45, 81), (1.5, .45, 83),
          (2, .90, 81), (3, .45, 79), (3.5, .45, 76)],
    'B': [(0, .70, 83), (.75, .25, 81), (1, .70, 79), (2, .45, 78), (2.5, 1.40, 76)],
    'C': [(0, .50, 76), (.5, .50, 79), (1, .50, 81), (1.5, .50, 83),
          (2, .90, 88), (3, .45, 83), (3.5, .45, 81)],
    'D': [(0, .70, 88), (.75, .25, 86), (1, .45, 84), (1.5, .45, 83),
          (2, .90, 81), (3, .90, 79)],
}


def arrange_lead(rng):
    notes = []

    def phrase(beat, key, vel):
        for off, dur, pitch in MOTIFS[key]:
            notes.append((round(beat + off, 5), dur, pitch, clamp(vel + rng.randint(-3, 3))))

    gbar = 0
    for name, bars, chords, energy, style in SECTIONS:
        for local in range(bars):
            beat = gbar * 4
            if style == 'verse' and local % 4 in (0, 1):
                phrase(beat, 'A', 92)
            elif style == 'prechorus' and local in (6, 7):
                phrase(beat, 'C', 96)
            elif style in ('chorus',) and local % 4 in (0, 1):
                phrase(beat, 'A', 100)
            elif style == 'chorus' and local % 4 in (2, 3):
                phrase(beat, 'B', 100)
            elif style == 'solo':
                # continuous run: E minor scale, 16 notes per 2 bars
                scale = (76, 78, 79, 81, 83, 84, 86, 88)
                if local % 2 == 0:
                    seq = scale + scale[::-1]
                else:
                    seq = scale[::-1] + scale
                for i, p in enumerate(seq):
                    notes.append((round(beat + i * .25, 5), 0.24, p,
                                  clamp(98 + (i % 4) * 2 + rng.randint(-2, 2))))
            elif style == 'outro':
                if local == 0:
                    phrase(beat, 'D', 102)
                elif local == 4:
                    phrase(beat, 'A', 100)
                elif local == bars - 1:
                    for off, dur, p in ((0, 2.8, 76),):
                        notes.append((round(beat + off, 5), dur, p, 104))
            gbar += 1
    return notes


# ==========================================================================
def compose():
    rng = random.Random(20261019)
    left, right = arrange_guitars(rng)
    return {
        'drums':            arrange_drums(rng),
        'rhythm_guitar_L':  left,
        'rhythm_guitar_R':  right,
        'electric_bass':    arrange_bass(rng),
        'synth_piano':      arrange_piano(rng),
        'lead_guitar':      arrange_lead(rng),
    }


PROGRAMS = {
    'rhythm_guitar_L': (30, 0),   # Overdriven Guitar, pan left
    'rhythm_guitar_R': (30, 1),   # Overdriven Guitar, pan right
    'electric_bass':   (34, 2),   # Electric Bass (pick)
    'synth_piano':     (4,  3),   # Electric Piano 1
    'lead_guitar':     (31, 4),   # Distortion Guitar
}
PANS = {'rhythm_guitar_L': 25, 'rhythm_guitar_R': 102, 'lead_guitar': 64,
        'electric_bass': 64, 'synth_piano': 64}


def save_midi(path=OUT_MID):
    tracks = compose()
    song = mido.MidiFile(type=1, ticks_per_beat=TPB)
    meta = mido.MidiTrack([
        mido.MetaMessage('track_name', name='Audited reference: adaptation of Iron Determination'),
        mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM)),
        mido.MetaMessage('time_signature', numerator=4, denominator=4),
    ])
    cur = prev = 0
    for name, bars, chords, energy, style in SECTIONS:
        meta.append(mido.MetaMessage('marker', text=name, time=(cur - prev) * 4 * TPB))
        prev = cur
        cur += bars
    meta.append(mido.MetaMessage('end_of_track', time=(cur - prev) * 4 * TPB))
    song.tracks.append(meta)

    song.tracks.append(build_track('drums', tracks['drums'], 0, 9, TPB, is_drum=True))
    for name, (program, channel) in PROGRAMS.items():
        tr = build_track(name, tracks[name], program, channel, TPB)
        tr.insert(2, mido.Message('control_change', channel=channel,
                                  control=10, value=PANS[name], time=0))
        song.tracks.append(tr)

    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError(f'Do not overwrite: {path}')
    song.save(path)
    problems, duration = validate_midi(str(path), expected_duration=180.0, tol=0.5)
    if problems:
        raise ValueError(f'Invalid MIDI: {problems}')
    require_arrangement(path)
    return path, duration, tracks


def decision_plan():
    roles = {'rhythm_guitar_L': ('rhythm_guitar', 48, 71, 0),
             'rhythm_guitar_R': ('rhythm_guitar', 48, 71, 0),
             'electric_bass': ('bass', 24, 47, 0),
             'synth_piano': ('piano', 60, 84, 48),
             'lead_guitar': ('lead', 76, 88, 35)}
    densities = {'intro': 10, 'verse': 15, 'prechorus': 17,
                 'chorus': 16, 'solo': 16, 'outro': 16}
    end, fills = 0, []
    for name, bars, chords, energy, style in SECTIONS:
        end += bars
        if style != 'outro':
            fills.append(end)
    return {'profile': 'dense', 'intent': 'Instrumental power metal demo for gym use; '
            'energy contrast, power-chord riffs and piano silence. Sound quality awaits listening.',
            'sections': [{'name': n, 'bars': b, 'groove': style,
                          'density': densities[style]} for n, b, c, e, style in SECTIONS],
            'instruments': [{'name': 'drums', 'role': 'drums', 'silent_bars': 0}] +
            [{'name': n, 'role': r, 'min': lo, 'max': hi, 'silent_bars': silence}
             for n, (r, lo, hi, silence) in roles.items()], 'fill_bars': fills}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=OUT_MID)
    parser.add_argument('--plan', type=Path, help='write only the decisions, without music')
    args = parser.parse_args()
    if args.plan:
        with args.plan.open('x') as f:
            json.dump(decision_plan(), f, ensure_ascii=False, indent=2)
            f.write('\n')
        print(f'Plan written: {args.plan}')
    else:
        path, duration, tracks = save_midi(args.out)
        print(f'AUDITED DRAFT: {path} | {duration:.3f}s; awaiting publication through composition_guard.py')
