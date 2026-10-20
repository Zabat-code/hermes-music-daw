#!/usr/bin/env python3
"""
Harmonic Circle Progressions MIDI Generator
===========================================

Generate MIDI chord progressions based on the Circle of Fifths,
based on Jaime Altozano's video "An INCREDIBLE TRICK FOR UNDERSTANDING CHORDS AND SCALES:
The Circle of Fifths" (with millions of views).

Experimental legacy utility, not a validated harmony engine. Known defects:
pitch-class offsets are doubled, per-chord chord_types are ignored and growing
absolute positions are written as MIDI deltas. Ninth, eleventh and thirteenth
chords and an automatic substitution system are not implemented. See
references/effects_mapper.md for implementation limits.

MIDI output:
  - Track 0: Voice (octave harmonies)
  - Track 1: Bass (root note)
  - Track 2: Melody arpeggio

Usage:
    python3 harmonic_circle.py --genre pop --names "I-vi-IV-V" --out pop.mid

    # List progressions
    python3 harmonic_circle.py --list
"""

import argparse
import json
import sys
import os
from pathlib import Path
import mido


# ---------- Semitones per scale degree ----------

# Degree of each scale note (MIDI 0-127)
# C major = 0
SCALE_DEGREES = {
    # Strong notes
    'I': 0,    # Tonic
    'II': 2,   # Supertonic
    'III': 4,  # Third
    'IV': 5,   # Subdominant
    'V': 7,    # Dominant
    'VI': 9,   # Submediant
    'VII': 11, # Leading tone
    # Minor notes (same relative pattern)
    'ii': 2,   # Minor supertonic
    'iii': 4,  # Minor third
    'vi': 9,   # Minor submediant
    'vii': 11, # Minor leading tone
}

# Semitone intervals for each chord quality
QUALITIES = {
    'maj': [0, 4, 7],          # Major
    'min': [0, 3, 7],          # Minor
    'dom7': [0, 4, 7, 10],     # Dominant 7th
    'maj7': [0, 4, 7, 11],     # Major 7th
    'min7': [0, 3, 7, 10],     # Minor 7th
    'dim7': [0, 3, 6, 9],      # Diminished 7th
    'aug': [0, 4, 8],          # Augmented
    '5': [0, 7],               # Perfect 5th
}

# Grammar notation for progressions
# E.g.: "I-vi-IV-V" = Tonic, Submediant, Subdominant, Dominant
#     "I-V-vi-IV" = Classic pop progression
#     "ii-V-I" = Classical function
#     "I-V-vi-III-IV-I-V" = Song structure

# Predefined progressions (scale notes + quality)
POP_PROGRESSIONS = [
    {
        'name': 'I-V-vi-IV',
        'progression': ['I', 'V', 'vi', 'IV'],
        'quality': 'maj',
        'description': 'Classic pop progression',
        'chord_types': ['maj', 'maj', 'min', 'maj'],
    },
    {
        'name': 'I-vi-IV-V',
        'progression': ['I', 'vi', 'IV', 'V'],
        'quality': 'maj',
        'description': 'Progression from the song "Let It Be"',
        'chord_types': ['maj', 'min', 'maj', 'maj'],
    },
    {
        'name': 'I-V-vi-III-IV-I-V',
        'progression': ['I', 'V', 'vi', 'III', 'IV', 'I', 'V'],
        'quality': 'maj',
        'description': 'Flagship progression (The Sing-Along)',
        'chord_types': ['maj', 'maj', 'min', 'min', 'maj', 'maj', 'maj'],
    },
    {
        'name': 'I-V-IV-vi',
        'progression': ['I', 'V', 'IV', 'vi'],
        'quality': 'maj',
        'description': '1980s progression',
        'chord_types': ['maj', 'maj', 'maj', 'min'],
    },
]

REGGAE_PROGRESSIONS = [
    {
        'name': 'I-vi-IV-V',
        'progression': ['I', 'vi', 'IV', 'V'],
        'quality': 'maj',
        'description': 'Bachata/reggae progression',
        'chord_types': ['maj', 'min', 'maj', 'maj'],
    },
    {
        'name': 'I-VII-I-VI',
        'progression': ['I', 'VII', 'I', 'VI'],
        'quality': 'maj',
        'description': 'Latin club progression',
        'chord_types': ['maj', 'min', 'maj', 'min'],
    },
]

CLASSICAL_PROGRESSIONS = [
    {
        'name': 'ii-V-I',
        'progression': ['ii', 'V', 'I'],
        'quality': 'dom7',
        'description': 'Tonic in musical function',
        'chord_types': ['min7', 'dom7', 'maj'],
    },
    {
        'name': 'I-IV-V-I',
        'progression': ['I', 'IV', 'V', 'I'],
        'quality': 'maj',
        'description': 'Classical tonic of the song',
        'chord_types': ['maj', 'maj', 'maj', 'maj'],
    },
    {
        'name': 'I-vi-IV-V',
        'progression': ['I', 'vi', 'IV', 'V'],
        'quality': 'maj',
        'description': 'Circle progression mechanics',
        'chord_types': ['maj', 'min', 'maj', 'maj'],
    },
]


# ---------- Chord calculation ----------

def get_scale_notes(root, quality='maj'):
    """Get chord notes from the root and quality."""
    root_semi = SCALE_DEGREES.get(root, 0)
    intervals = QUALITIES[quality]

    # C3 = MIDI 48 as the bass octave; degrees map to proper semitones.
    notes = []
    for interval in intervals:
        pitch = 48 + root_semi + interval
        notes.append(pitch)

    return notes


def get_chord(root, quality='maj'):
    """Return the chord notes."""
    return get_scale_notes(root, quality)


# ---------- MIDI generation ----------

def create_harmony_track(title, notes, channel=0):
    """Create a MIDI track with a harmony."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=title, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))

    if not notes:
        return track

    ticks_per_beat = 480
    ticks_per_chord = 4 * ticks_per_beat  # 4 beats (1 bar) per chord

    last_tick = 0
    for i, note in enumerate(notes):
        chord_time = i * ticks_per_chord
        delta = chord_time - last_tick
        track.append(mido.Message('note_on', channel=channel, note=note, velocity=80, time=delta))
        track.append(mido.Message('note_off', channel=channel, note=note, velocity=60, time=ticks_per_beat))
        last_tick = chord_time + ticks_per_beat

    return track


def create_bass_track(title, progressions):
    """Create one bass note per degree; legacy pitch/timing defects remain."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=title, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))

    bass_notes = []
    for prog in progressions:
        for chord in prog['progression']:
            root_name = chord if isinstance(chord, str) else chord.get('root', 'I')
            root_semi = SCALE_DEGREES.get(root_name, 0)
            bass_note = 36 + root_semi  # one octave below C3
            bass_notes.append((bass_note, root_name))

    ticks_per_beat = 480
    ticks_per_chord = 4 * ticks_per_beat
    last_tick = 0
    for i, (note, root) in enumerate(bass_notes):
        chord_time = i * ticks_per_chord
        delta = chord_time - last_tick
        track.append(mido.Message('note_on', channel=1, note=note, velocity=70, time=delta))
        track.append(mido.Message('note_off', channel=1, note=note, velocity=50, time=ticks_per_beat))
        last_tick = chord_time + ticks_per_beat

    return track


def create_harmony_midi(progressions, output_file):
    """Create a MIDI file with harmonic progressions."""
    if not progressions:
        print('ERROR: No progressions provided', file=sys.stderr)
        return 1

    print(f'Generating harmonic MIDI progressions')
    print(f'   Progressions: {len(progressions)}')

    for i, prog in enumerate(progressions):
        print(f'   Progression {i+1}: {prog["name"]}')

    # Create tracks
    tracks = []

    # Track 0: Harmonic voice
    voice_notes = []
    arpeggio_notes = []
    chord_index = 0
    for prog in progressions:
        chord_types = prog.get('chord_types', [])
        for chord in prog['progression']:
            quality = chord_types[chord_index % len(chord_types)] if chord_types else prog.get('quality', 'maj')
            notes = get_chord(chord, quality)
            voice_notes.extend(notes)
            arpeggio = notes + notes[::-1]
            arpeggio_notes.extend(arpeggio[::2])
            chord_index += 1

    tracks.append(create_harmony_track('Voice', voice_notes))
    tracks.append(create_bass_track('Bass', progressions))
    tracks.append(create_harmony_track('Arpeggio', arpeggio_notes))

    # Create file
    mid = mido.MidiFile()
    mid.ticks_per_beat = 480
    mid.tracks = tracks

    mid.save(output_file)

    print(f'   Saved: {output_file}')
    return 0


def list_progressions():
    """List available progressions."""
    print('Available harmonic progressions:')
    all_progs = POP_PROGRESSIONS + REGGAE_PROGRESSIONS + CLASSICAL_PROGRESSIONS
    for i, prog in enumerate(all_progs):
        print(f'  {i+1:2d}. {prog["name"]:30s} | {prog["description"]}')


def main():
    parser = argparse.ArgumentParser(
        description='Harmonic Circle Progressions MIDI Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python3 harmonic_circle.py --genre pop --out pop.mid
    python3 harmonic_circle.py --names "I-V-vi-IV" --out my_progression.mid
    python3 harmonic_circle.py --list
        '''
    )
    parser.add_argument('--genre', '-g', help='Genre (pop, reggae, classical)')
    parser.add_argument('--names', '-n', nargs='+', help='Specific progressions (e.g.: I-V-vi-IV, I-V-VI-IV)')
    parser.add_argument('--out', '-o', help='Output file')
    parser.add_argument('--list', '-l', action='store_true', help='List available progressions')

    args = parser.parse_args()

    if args.list or args.genre == 'list':
        list_progressions()
        return

    if not args.genre and not args.names:
        print('ERROR: -n or -g is required', file=sys.stderr)
        print('   Options: --list to view available progressions', file=sys.stderr)
        sys.exit(1)

    if args.out is None:
        args.out = f'harmonic_{args.genre}.mid'

    # Select progressions
    all_progs = POP_PROGRESSIONS + REGGAE_PROGRESSIONS + CLASSICAL_PROGRESSIONS

    if args.names:
        # Specific progressions
        progressions = []
        for name in args.names:
            for prog in all_progs:
                if prog['name'] == name:
                    progressions.append(prog)
                    break
            else:
                print(f'   WARNING: Progression not found: {name}', file=sys.stderr)

    elif args.genre:
        genre_map = {
            'pop': POP_PROGRESSIONS,
            'reggae': REGGAE_PROGRESSIONS,
            'classical': CLASSICAL_PROGRESSIONS,
        }
        progressions = genre_map.get(args.genre.lower(), POP_PROGRESSIONS)

    # Create MIDI
    sys.exit(create_harmony_midi(progressions, args.out))


if __name__ == '__main__':
    main()
