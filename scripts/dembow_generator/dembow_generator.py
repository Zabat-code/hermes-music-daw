#!/usr/bin/env python3
"""
Reggaeton Dembow Pattern Generator
===================================

Experimental legacy generator inspired by Jaime Altozano's MOTOMAMI analysis.
It does not implement a validated dembow arrangement or isolated drum stems.
Known defects: absolute ticks are written as deltas; four tracks duplicate the
same multichannel pattern; channels 0-3 are not GM percussion channel 9.
Tempo is fixed at 120 BPM and generation loops over eight bars; CLI --bpm and
--bars are not applied. The latin_cumbia recipe accesses a missing 808 entry.
Recipe labels such as 808 do not establish GM sounds. See
references/effects_mapper.md for legacy implementation limits.

Usage:
    python3 dembow_generator.py --genre reggaeton_basic --out out.mid

    # List recipes
    python3 dembow_generator.py --genre list

Output:
    - out.mid: four named tracks, each containing the same combined pattern
    - No pattern-description text file is written.
"""

import argparse
import json
import sys
import os
from pathlib import Path
import mido


# ---------- Pattern recipes ----------

# The classic dembow pattern at 92-96 BPM
DEMBO_PATTERNS = {
    'reggaeton_basic': {
        'bpm': 92,
        'description': 'Basic reggaeton dembow, standard pattern',
        'pitches': {
            'kick': [36, 38, 40, 41],      # 1 e & a with kick
            'snare': [38, 41],             # "&" of 2 and "&" of 4
            'hihat': [42, 44, 46, 48],     # eighth-note zeros
            '808': [41, 43, 45, 47],       # 808 pulse
        },
        'velocities': {
            'kick': [100, 90, 80, 70],
            'snare': [110, 100],
            'hihat': [80, 70, 60, 50],
            '808': [50, 45, 40, 35],
        },
        'effects': {
            'filter': {'cutoff_low': 60, 'cutoff_high': 150},
            'eq': {'low': 0, 'mid': 0, 'high': -3},
        },
    },
    'reggaeton_dembow_v2': {
        'bpm': 94,
        'description': 'Dembow v2 with more groove',
        'pitches': {
            'kick': [36, 38, 40, 41, 43],
            'snare': [38, 41],
            'hihat': [42, 43, 44, 48],
            '808': [42, 44, 46],
        },
        'velocities': {
            'kick': [105, 85, 75, 80, 65],
            'snare': [115, 105],
            'hihat': [85, 75, 60, 55],
            '808': [55, 45, 38],
        },
    },
    'reggaeton_melodic': {
        'bpm': 90,
        'description': 'Dembow with an accompanying melody',
        'pitches': {
            'kick': [36, 38, 40, 41],
            'snare': [38, 41],
            'hihat': [42, 44, 46, 48],
            '808': [41, 43, 45, 47],
            'melody': [72, 74, 76, 79, 81, 83],
        },
        'velocities': {
            'kick': [100, 90, 80, 70],
            'snare': [110, 100],
            'hihat': [80, 70, 60, 50],
            '808': [50, 45, 40, 35],
            'melody': [85, 90, 85, 95, 80, 90],
        },
    },
    'trap_fast': {
        'bpm': 140,
        'description': 'Fast trap with varied dembow',
        'pitches': {
            'kick': [36, 38, 40],
            'snare': [38, 41],
            'hihat': [42, 43, 44, 45, 46, 48],
            '808': [41, 43],
        },
        'velocities': {
            'kick': [105, 90, 80],
            'snare': [115, 105],
            'hihat': [90, 75, 65, 60, 55, 50],
            '808': [60, 45],
        },
    },
    'latin_cumbia': {
        'bpm': 100,
        'description': 'Cumbia with an accompaniment pattern',
        'pitches': {
            'kick': [36, 38, 40],
            'snare': [38],
            'hihat': [42, 44, 46, 48],
            'timbale': [44, 46],
        },
        'velocities': {
            'kick': [100, 90, 80],
            'snare': [110],
            'hihat': [80, 70, 60, 50],
            'timbale': [75, 70],
        },
    },
}


# ---------- MIDI conversion ----------

def create_dembow_track(title, pattern):
    """Create a MIDI track with a dembow pattern."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=title, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))

    bpm = pattern['bpm']
    # Four quarter-note beats per bar, 4/4; recipe BPM is not applied.
    # Ticks per beat = 480 (standard)
    ticks_per_beat = 480

    # Create events
    events = []

    # Calculate event times
    # Intended grid: 8 bars = 32 quarter-note beats in 4/4.
    # Each beat = 480 ticks = 1 quarter note

    for bar in range(8):  # 8 bars
        for beat in range(4):  # 4 beats per bar
            beat_time = (bar * 4 + beat) * ticks_per_beat

            # Event on each quarter-note beat (0, 1, 2, 3).
            if beat in [0, 1, 2, 3]:
                kick_idx = beat % len(pattern['pitches']['kick'])
                kick_pitch = pattern['pitches']['kick'][kick_idx]
                kick_vel = pattern['velocities']['kick'][kick_idx]
                events.append((beat_time, 'note_on', 0, kick_pitch, kick_vel))

            # Events on zero-based beats 2 and 3, not eighth-note offbeats.
            if beat in [2, 3]:
                snare_idx = (beat // 2) % len(pattern['pitches']['snare'])
                snare_pitch = pattern['pitches']['snare'][snare_idx]
                snare_vel = pattern['velocities']['snare'][snare_idx]
                events.append((beat_time, 'note_on', 1, snare_pitch, snare_vel))

            # Eight subdivisions per quarter note (thirty-second-note spacing).
            for i in range(8):
                hihat_time = beat_time + (i * ticks_per_beat // 8)
                hihat_idx = i % len(pattern['pitches']['hihat'])
                hihat_pitch = pattern['pitches']['hihat'][hihat_idx]
                hihat_vel = pattern['velocities']['hihat'][hihat_idx]
                events.append((hihat_time, 'note_on', 2, hihat_pitch, hihat_vel))

            # 808 persistent
            for i, pitch in enumerate(pattern['pitches'].get('808', [])):
                if i < 8:  # 8 pulses
                    pulse_time = beat_time + (i * ticks_per_beat // 4)
                    events.append((pulse_time, 'note_on', 3, pitch, pattern['velocities']['808'][i]))

    # Sort events by time
    events.sort(key=lambda x: x[0])

    # Legacy defect: time is absolute here, but MIDI message.time is a delta.
    for time, msg_type, channel, note, vel in events:
        track.append(mido.Message(msg_type, channel=channel, note=note, velocity=vel, time=time))
        # Add note_off for each note
        track.append(mido.Message('note_off', channel=channel, note=note, velocity=60, time=10))

    return track


def create_dembow_midi(pattern_name, output_file):
    """Create a complete MIDI file with a dembow pattern."""
    if pattern_name not in DEMBO_PATTERNS:
        print(f'ERROR: Pattern "{pattern_name}" does not exist', file=sys.stderr)
        print(f'   Available: {", ".join(DEMBO_PATTERNS.keys())}', file=sys.stderr)
        return 1

    pattern = DEMBO_PATTERNS[pattern_name]

    print(f'Generating: {pattern_name}')
    print(f'   BPM: {pattern["bpm"]}')
    print(f'   Description: {pattern["description"]}')
    print(f'   Notes: {len(pattern["pitches"]["kick"])} kicks, {len(pattern["pitches"]["snare"])} snares, {len(pattern["pitches"]["hihat"])} hi-hats')

    # Create tracks
    tracks = []
    tracks.append(create_dembow_track('Kick', pattern))
    tracks.append(create_dembow_track('Snare', pattern))
    tracks.append(create_dembow_track('Hi-hat', pattern))
    tracks.append(create_dembow_track('808', pattern))

    # Create MIDI file
    mid = mido.MidiFile()
    mid.ticks_per_beat = 480
    mid.tracks = tracks

    # Save
    mid.save(output_file)

    print(f'   Saved: {output_file}')
    return 0


def list_patterns():
    """List available patterns."""
    print('Available dembow patterns:')
    for name, data in DEMBO_PATTERNS.items():
        print(f'  {name:25s} | BPM: {data["bpm"]:3d} | {data["description"]}')

    print(f'\n   MIDI notes (GM Drum Map):')
    print(f'   Kick: 36, Snare: 38, Hi-hat: 42, 808: 41')


def main():
    parser = argparse.ArgumentParser(
        description='Reggaeton Dembow Pattern Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
    python3 dembow_generator.py --genre reggaeton_basic --bpm 92 --bars 8 --out reggaeton.mid
    python3 dembow_generator.py --genre list
        '''
    )
    parser.add_argument('--genre', '-g', help='Pattern name (reggaeton_basic, reggaeton_dembow_v2, reggaeton_melodic, trap_fast, latin_cumbia)')
    parser.add_argument('--bpm', '-b', type=int, help='Tempo in BPM (overrides the recipe)')
    parser.add_argument('--bars', '-n', type=int, default=8, help='Number of bars (default: 8)')
    parser.add_argument('--out', '-o', help='Output file')

    args = parser.parse_args()

    if args.genre == 'list':
        list_patterns()
        return

    if not args.genre:
        print('ERROR: --genre is required', file=sys.stderr)
        print('   Use --genre list to view available patterns', file=sys.stderr)
        sys.exit(1)

    if args.out is None:
        args.out = f'reggaeton_{args.genre}.mid'

    # Create MIDI
    sys.exit(create_dembow_midi(args.genre, args.out))


if __name__ == '__main__':
    main()
