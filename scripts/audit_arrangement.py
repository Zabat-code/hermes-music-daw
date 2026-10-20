#!/usr/bin/env python3
"""Dense arrangement gates, version 1. Do not certify timbre or musical taste.

Deliberately strict contract: no drum attacks with 3+ kit pieces;
5 velocities and spread >=10 on tracks with >=16 notes; no groove in
>50% of active bars; density contrast >=2 hits between sections;
one harmonic instrument with >=1 truly silent bar; register per role.
Fills are INFERRED from >=3 toms or >=4 snares in the last beat: a heuristic.
The rhythm signature ignores velocity/duration and rounds to sixteenth notes,
so adding jitter or random velocities cannot disguise a repeated grid.

API: audit(path, profile='dense') -> report; require_arrangement(path) aborts.
CLI: audit_arrangement.py piece.mid [--json report.json]
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys

import mido

VERSION = '2026-10-19.1'
RANGES = {'bass': (24, 60), 'rhythm_guitar': (40, 84), 'lead': (48, 90),
          'piano': (36, 84), 'pad': (36, 90), 'strings': (36, 90),
          'choir': (36, 84)}
HARMONIC = {'rhythm_guitar', 'piano', 'pad', 'strings', 'choir'}
KICKS = {35, 36}
SNARES = {38, 40}
TOMS = {41, 43, 45, 47, 48, 50}
CYMBALS = {42, 44, 46, 49, 51, 52, 53, 55, 57, 59}
NAMES = {35: 'kick35', 36: 'kick36', 38: 'snare38', 40: 'snare40',
         42: 'hat42', 44: 'hat44', 46: 'hat46', 49: 'crash49', 51: 'ride51'}


class ArrangementError(ValueError):
    """The arrangement cannot be published as a finished composition."""


@dataclass
class Note:
    start: int
    end: int
    pitch: int
    velocity: int
    channel: int
    program: int


def infer_role(name, program, channel):
    n = name.lower()
    if channel == 9:
        return 'drums'
    if 'bass' in n or 32 <= program <= 39:
        return 'bass'
    if any(x in n for x in ('lead', 'melody', 'solo')):
        return 'lead'
    if any(x in n for x in ('guitar',)) or 24 <= program <= 31:
        return 'rhythm_guitar'
    if any(x in n for x in ('piano', 'keyboard')) or 0 <= program <= 7:
        return 'piano'
    if 'choir' in n or program in (52, 53, 54):
        return 'choir'
    if 'pad' in n or 88 <= program <= 95:
        return 'pad'
    if 40 <= program <= 51:
        return 'strings'
    if 80 <= program <= 87:
        return 'lead'
    return 'unknown'


def load_notes(mid):
    """Merge tracks by channel for programs, sustain and note-offs spanning tracks."""
    events = []
    end = 0
    names = {}
    for i, track in enumerate(mid.tracks):
        tick = 0
        names[i] = track.name or f'track_{i}'
        for j, msg in enumerate(track):
            tick += msg.time
            events.append((tick, i, j, msg))
        end = max(end, tick)
    notes, problems, meters, markers = defaultdict(list), [], [], []
    opened = defaultdict(deque)
    sustained = defaultdict(list)
    pedals = defaultdict(bool)
    programs = defaultdict(int)
    for tick, i, j, msg in sorted(events, key=lambda e: e[:3]):
        if msg.type == 'time_signature':
            meters.append((tick, msg.numerator, msg.denominator))
        elif msg.type == 'marker':
            markers.append((tick, msg.text))
        elif msg.type == 'program_change':
            programs[msg.channel] = msg.program
        elif msg.type == 'control_change' and msg.control == 64:
            pedals[msg.channel] = msg.value >= 64
            if msg.value < 64:
                for note in sustained.pop(msg.channel, []):
                    note.end = tick
        elif msg.type == 'note_on' and msg.velocity > 0:
            key = (msg.channel, msg.note)
            if opened[key]:
                problems.append(f'retrigger while note is open on channel {msg.channel}, note {msg.note}, tick {tick}')
            note = Note(tick, end, msg.note, msg.velocity, msg.channel, programs[msg.channel])
            notes[i].append(note)
            opened[key].append(note)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if not opened[key]:
                problems.append(f'orphan note_off on channel {msg.channel}, note {msg.note}, tick {tick}')
                continue
            note = opened[key].popleft()
            note.end = tick
            if pedals[msg.channel] and msg.channel != 9:
                note.end = end
                sustained[msg.channel].append(note)
            if tick <= note.start:
                problems.append(f'nonpositive duration: note {msg.note}, tick {tick}')
    for (ch, pitch), pending in opened.items():
        if pending:
            problems.append(f'{len(pending)} unclosed notes on channel {ch}, note {pitch}')
    return notes, names, end, sorted(set(meters)), sorted(set(markers)), problems


def make_bars(end, tpb, meters):
    changes = dict((t, (n, d)) for t, n, d in meters)
    changes.setdefault(0, (4, 4))
    bars = []
    pos = Fraction(0)
    meter = changes[0]
    while pos < end:
        if pos in changes:
            meter = changes[pos]
        length = Fraction(tpb * meter[0] * 4, meter[1])
        if length <= 0:
            raise ValueError('nonpositive bar length')
        stop = pos + length
        if any(pos < t < stop for t in changes):
            raise ValueError('time signature change outside a bar boundary: cannot verify with this profile')
        bars.append((float(pos), float(min(stop, end))))
        pos = stop
    return bars


def bad_drum_group(pitches):
    if len(pitches) >= 3:
        return '3+ kit pieces'
    if len(pitches) == 2:
        a, b = pitches
        if a == b or (a in KICKS and b in KICKS):
            return 'duplicate hit'
        if a in CYMBALS and b in CYMBALS:
            return 'two simultaneous cymbals/hi-hats'
        if (a in SNARES and b in TOMS) or (b in SNARES and a in TOMS):
            return 'simultaneous snare+tom (clarity contract)'
    return None


def audit(path, profile='dense'):
    """dense is the requested contract; basic is only for pieces WITHOUT drums."""
    path = Path(path)
    mid = mido.MidiFile(path)
    tracks, names, end, meters, markers, structural = load_notes(mid)
    if mid.type == 2:
        structural.append('MIDI type 2: independent sequences')
    if mid.ticks_per_beat <= 0:
        raise ValueError('SMPTE division is not supported')
    bars = make_bars(end, mid.ticks_per_beat, meters)
    if not bars or not tracks:
        structural.append('empty piece')
    drums = [n for ns in tracks.values() for n in ns if n.channel == 9]
    if profile == 'auto':
        profile = 'dense' if drums else 'basic'
    if profile not in ('basic', 'dense'):
        raise ValueError('unknown profile')
    if profile == 'basic' and drums:
        raise ValueError('the basic profile does NOT allow bypassing the drum gates')
    gates = []

    def gate(name, ok, detail):
        gates.append({'gate': name, 'ok': bool(ok), 'detail': detail})

    gate('structure', not structural, '; '.join(structural[:8]) or 'closed notes and positive duration')
    stats, dynamic_bad, register_bad, harmonic_silence = [], [], [], []
    for i, ns in sorted(tracks.items()):
        # A type 0 track can contain multiple channels/programs/roles.
        parts = defaultdict(list)
        for n in ns:
            parts[(n.channel, n.program)].append(n)
        for (ch, program), part in sorted(parts.items()):
            name = names[i] + (f'/ch{ch}/GM{program}' if len(parts) > 1 else '')
            role = infer_role(names[i], program, ch)
            velocities = {n.velocity for n in part}
            spread = max(velocities) - min(velocities)
            active = {b for b, (start, stop) in enumerate(bars)
                      if any(n.start < stop and n.end > start for n in part)}
            silent = len(bars) - len(active)
            lo, hi = min(n.pitch for n in part), max(n.pitch for n in part)
            stats.append({'name': name, 'role': role, 'notes': len(part),
                          'velocities': len(velocities), 'spread': spread,
                          'range': [lo, hi], 'silent_bars': silent})
            if len(part) >= 16 and (len(velocities) < 5 or spread < 10):
                dynamic_bad.append(name)
            if role == 'unknown':
                register_bad.append(f'{name}: unknown role, requires a specific profile')
            elif role != 'drums':
                floor, ceiling = RANGES[role]
                if lo < floor or hi > ceiling:
                    register_bad.append(f'{name}={lo}..{hi}, allowed {floor}..{ceiling}')
            if role in HARMONIC and silent >= 1:
                harmonic_silence.append(f'{name}:{silent}')
    gate('dynamics', not dynamic_bad, 'minimum 5 velocities and amplitude 10; failing: ' +
         ', '.join(dynamic_bad) if dynamic_bad else '>=5 velocities and spread >=10 on tracks with >=16 notes')
    gate('register', not register_bad, '; '.join(register_bad) or 'ranges per role within the contract')
    if profile == 'dense':
        gate('space', bool(harmonic_silence), 'complete measures with no notes or sustain: ' +
             (', '.join(harmonic_silence) or 'no harmonic instrument goes silent'))
    collisions, near_collisions = Counter(), Counter()
    violation_ticks = []
    groups = defaultdict(list)
    for n in drums:
        groups[n.start].append(n.pitch)
    for tick, pitches in sorted(groups.items()):
        if len(pitches) >= 2:
            collisions[tuple(sorted(pitches))] += 1
        if bad_drum_group(pitches):
            violation_ticks.append(tick)
    # Group attacks separated by <=1/48 of a quarter note (~8 ms at 160 BPM).
    # Each group is anchored to its first attack: distant hits are not chained together.
    cluster, anchor = [], None
    for tick, pitches in sorted(groups.items()):
        if anchor is not None and tick - anchor > mid.ticks_per_beat / 48:
            if len({t for t, p in cluster}) > 1 and bad_drum_group([p for t, p in cluster]):
                near_collisions[tuple(sorted(p for t, p in cluster))] += 1
            cluster, anchor = [], None
        if anchor is None:
            anchor = tick
        cluster.extend((tick, p) for p in pitches)
    if len({t for t, p in cluster}) > 1 and bad_drum_group([p for t, p in cluster]):
        near_collisions[tuple(sorted(p for t, p in cluster))] += 1
    if profile == 'dense':
        gate('overlap', not violation_ticks and not near_collisions,
             f'{sum(collisions.values())} instants with 2+; {len(violation_ticks)} prohibited; '
             f'{sum(near_collisions.values())} prohibited nearby groups; '
             f'first prohibited ticks={violation_ticks[:8]}')
    signatures, density, fill_bars = [], [], []
    for b, (start, stop) in enumerate(bars):
        ns = [n for n in drums if start <= n.start < stop]
        density.append(len(ns))
        if ns:
            signatures.append(tuple(sorted((round((n.start - start) * 4 / mid.ticks_per_beat), n.pitch)
                                           for n in ns)))
        tail = [n for n in ns if n.start >= stop - mid.ticks_per_beat]
        if sum(n.pitch in TOMS for n in tail) >= 3 or sum(n.pitch in SNARES for n in tail) >= 4:
            fill_bars.append(b)
    counts = Counter(signatures)
    most = max(counts.values(), default=0)
    dominance = most / len(signatures) if signatures else 1
    if profile == 'dense':
        gate('patterns', len(counts) >= 3 and dominance <= .5,
             f'{len(counts)} patterns/{len(signatures)} active bars; maximum {most} '
             f'({dominance:.1%}); limits >=3 patterns and <=50%')
    sections = []
    if markers:
        for idx, (tick, label) in enumerate(markers):
            stop = markers[idx + 1][0] if idx + 1 < len(markers) else end
            indices = [b for b, (s, e) in enumerate(bars) if tick <= s < stop]
            # Contrast must remain without the initial attack or the fill.
            body = [b for b in indices[1:-1] if b not in fill_bars]
            if not body:
                body = [b for b in indices if b not in fill_bars] or indices
            if body:
                sections.append((label, round(sum(density[b] for b in body) / len(body), 2)))
    else:
        # Without markers, sections cannot be established: only blocks of 8.
        for b in range(0, len(bars), 8):
            values = density[b:b + 8]
            sections.append((f'block{b + 1}', round(sum(values) / len(values), 2)))
    contrast = max((d for s, d in sections), default=0) - min((d for s, d in sections), default=0)
    if profile == 'dense':
        gate('density', len(set(density)) >= 3 and contrast >= 2,
             f'min={min(density, default=0)}, max={max(density, default=0)}, '
             f'{len(set(density))} levels; contrast between sections/blocks={contrast:.2f} (minimum 2)')
    gaps = [b - a for a, b in zip(fill_bars, fill_bars[1:])]
    periodic = len(fill_bars) >= 4 and gaps.count(4) / len(gaps) >= .75
    boundaries = {b for b, (s, e) in enumerate(bars) if any(t == e for t, label in markers) or e == end}
    outside = [b + 1 for b in fill_bars if markers and b not in boundaries]
    if profile == 'dense':
        gate('fills', not periodic and not outside,
             f'candidates (heuristic)={[b + 1 for b in fill_bars]}; '
             f'intervals={gaps}; outside boundaries={outside}; periodic every 4={periodic}')
    return {'version': VERSION, 'file': str(path.resolve()),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'profile': profile, 'bars': len(bars), 'seconds': round(mid.length, 6),
            'tracks': stats, 'gates': gates, 'ok': all(g['ok'] for g in gates),
            'collisions': [{'pitches': list(ps), 'count': count,
                            'reason': bad_drum_group(ps)} for ps, count in sorted(collisions.items())],
            'near_collisions': [{'pitches': list(ps), 'count': count} for ps, count in near_collisions.items()],
            'fill_bars': [b + 1 for b in fill_bars],
            'density_sections': sections,
            'limits': 'Dense arrangement contract; does not establish timbre, acoustic masking, '
                      'palm muting, correct harmony or musical quality. Fills are inferred; not all are detectable.'}


def format_report(report):
    lines = [f"AUDIT {report['version']} | {report['file']}",
             f"Profile={report['profile']} | {report['bars']} bars | {report['seconds']:.3f} s"]
    for s in report['tracks']:
        lines.append(f"TRACK {s['name']}: role={s['role']}, velocities={s['velocities']}, "
                     f"spread={s['spread']}, register={s['range'][0]}..{s['range'][1]}, "
                     f"silence={s['silent_bars']} bars")
    for g in report['gates']:
        lines.append(f"{'PASS' if g['ok'] else 'FAIL'} {g['gate']}: {g['detail']}")
    for c in report['collisions']:
        combo = '+'.join(NAMES.get(p, f'GM{p}') for p in c['pitches'])
        lines.append(f"  {combo}: {c['count']} instants [{c['reason'] or 'allowed'}]")
    lines.append('Density per section/block: ' + ', '.join(f'{s}={d:g}' for s, d in report['density_sections']))
    lines.append('LIMITS: ' + report['limits'])
    lines.append('RESULT: ' + ('PASS (exit 0)' if report['ok'] else 'ABORT (exit 1)'))
    return '\n'.join(lines)


def require_arrangement(path, profile='auto'):
    report = audit(path, profile)
    if not report['ok']:
        raise ArrangementError(format_report(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('midi', type=Path)
    parser.add_argument('--json', type=Path, help='save metrics and hash of the audited MIDI')
    args = parser.parse_args(argv)
    try:
        report = audit(args.midi)
        print(format_report(report))
        if args.json:
            if args.json.resolve() == args.midi.resolve():
                raise ValueError('the report cannot overwrite the MIDI')
            args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        return 0 if report['ok'] else 1
    except Exception as exc:
        print(f'ABORT (exit 1): {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
