#!/usr/bin/env python3
"""
Reggaeton Dembow Pattern Generator
===================================

Experimental legacy generator inspired by Jaime Altozano's MOTOMAMI analysis.
It does not implement a validated dembow arrangement or isolated drum stems.
Fixes applied: delta timing, one instrument per track, GM percussion channel 9,
recipe BPM, and safe handling of recipes without an 808 entry.
Recipe labels such as 808 do not establish GM sounds. See
references/effects_mapper.md for implementation limits.

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

def create_dembow_track(title, pattern, bars=8, bpm=None, ticks_per_beat=480,
                        channel_base=9):
    """Build one dembow instrument track on the correct GM percussion channel.

    Fixed defects: deltas instead of absolute ticks; one instrument per track;
    GM channel 9 (not 0-3); the recipe BPM is applied.
    """
    if bpm is None:
        bpm = pattern['bpm']
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=title, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm), time=0))
    track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))

    events = []  # (tick, kind_order, channel, note, velocity)

    for bar in range(bars):
        bar_start = bar * 4 * ticks_per_beat
        # Kick: on beats 0 and 2 (the "1" and "3" of each bar)
        for beat in (0, 2):
            t = bar_start + beat * ticks_per_beat
            kicks = pattern['pitches'].get('kick', [])
            kvel = pattern['velocities'].get('kick', [])
            if kicks:
                idx = beat // 2 % len(kicks)
                events.append((t, 2, channel_base, kicks[idx],
                               kvel[idx % len(kvel)] if kvel else 100))
        # Snare: the "&" of 2 and the "&" of 4
        for beat in (1.5, 3.5):
            t = int(bar_start + beat * ticks_per_beat)
            snares = pattern['pitches'].get('snare', [])
            svel = pattern['velocities'].get('snare', [])
            if snares:
                idx = int(beat) % len(snares)
                events.append((t, 2, channel_base, snares[idx],
                               svel[idx % len(svel)] if svel else 100))
        # Hi-hat: eighth notes across the bar
        for sub in range(8):
            t = bar_start + sub * ticks_per_beat // 2
            hats = pattern['pitches'].get('hihat', [])
            hvel = pattern['velocities'].get('hihat', [])
            if hats:
                idx = sub % len(hats)
                events.append((t, 2, channel_base, hats[idx],
                               hvel[idx % len(hvel)] if hvel else 70))
        # 808: quarter-note pulse
        for sub in range(4):
            t = bar_start + sub * ticks_per_beat
            bass = pattern['pitches'].get('808', [])
            bvel = pattern['velocities'].get('808', [])
            if bass:
                idx = sub % len(bass)
                events.append((t, 2, channel_base, bass[idx],
                               bvel[idx % len(bvel)] if bvel else 50))

    events.sort(key=lambda e: (e[0], e[1]))

    last_tick = [0]  # mutable cursor so note_off closes each note correctly

    # Emit note_on at each event tick; close it with note_off on the next tick.
    for i, (tick, _order, channel, note, vel) in enumerate(events):
        nxt = events[i + 1][0] if i + 1 < len(events) else tick + ticks_per_beat // 2
        dur = max(nxt - tick, 1)
        track.append(mido.Message('note_on', channel=channel, note=note,
                                  velocity=vel, time=tick - last_tick[0]))
        track.append(mido.Message('note_off', channel=channel, note=note,
                                  velocity=0, time=dur))
        last_tick[0] = nxt

    return track


def create_dembow_midi(pattern_name, output_file, bars=8, bpm=None):
    """Create a complete MIDI file with one track per instrument.

    Fixed: applies --bpm and --bars, uses GM channel 9, and does not duplicate
    the same pattern across four tracks.
    """
    if pattern_name not in DEMBO_PATTERNS:
        print(f'ERROR: Pattern "{pattern_name}" does not exist', file=sys.stderr)
        print('   Available: ' + ', '.join(DEMBO_PATTERNS.keys()), file=sys.stderr)
        return 1

    pattern = DEMBO_PATTERNS[pattern_name]
    bpm = bpm or pattern['bpm']
    print(f'Generating: {pattern_name}')
    print(f'   BPM: {bpm}')
    print(f'   Description: {pattern["description"]}')
    print(f'   {len(pattern["pitches"].get("kick", []))} kicks, '
          f'{len(pattern["pitches"].get("snare", []))} snares, '
          f'{len(pattern["pitches"].get("hihat", []))} hi-hats')

    tracks = []
    for instrument in ('kick', 'snare', 'hihat', '808'):
        if pattern['pitches'].get(instrument):
            tracks.append(create_dembow_track(instrument.capitalize(), pattern,
                                              bars=bars, bpm=bpm))

    mid = mido.MidiFile()
    mid.ticks_per_beat = 480
    mid.tracks = tracks
    mid.save(output_file)
    print(f'   Saved: {output_file}')
    return 0


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
