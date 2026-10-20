#!/usr/bin/env python3
"""Gates de arreglo denso, versión 1. No certifican timbre ni gusto musical.

Contrato deliberadamente estricto: ningún ataque de batería con 3+ piezas;
5 velocidades y amplitud >=10 en pistas con >=16 notas; ningún groove en
>50% de compases activos; contraste de densidad >=2 golpes entre secciones;
un instrumento armónico con >=1 compás realmente silencioso; registro por rol.
Los fills se INFIEREN de >=3 toms o >=4 cajas en el último pulso: es heurística.
La firma rítmica ignora velocidad/duración y redondea a semicorcheas, para que
añadir jitter o velocidades aleatorias no disfrace una rejilla repetida.

API: audit(path, profile='dense') -> informe; require_arrangement(path) aborta.
CLI: audit_arrangement.py archivo.mid [--json informe.json]
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
NAMES = {35: 'bombo35', 36: 'bombo36', 38: 'caja38', 40: 'caja40',
         42: 'hat42', 44: 'hat44', 46: 'hat46', 49: 'crash49', 51: 'ride51'}


class ArrangementError(ValueError):
    """El arreglo no puede publicarse como composición terminada."""


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
    if 'bass' in n or 'bajo' in n or 32 <= program <= 39:
        return 'bass'
    if any(x in n for x in ('lead', 'melody', 'melodia', 'solo')):
        return 'lead'
    if any(x in n for x in ('guitar', 'guitarra')) or 24 <= program <= 31:
        return 'rhythm_guitar'
    if any(x in n for x in ('piano', 'keyboard', 'teclado')) or 0 <= program <= 7:
        return 'piano'
    if 'choir' in n or 'coro' in n or program in (52, 53, 54):
        return 'choir'
    if 'pad' in n or 88 <= program <= 95:
        return 'pad'
    if 40 <= program <= 51:
        return 'strings'
    if 80 <= program <= 87:
        return 'lead'
    return 'unknown'


def load_notes(mid):
    """Une pistas por canal para programas, sustain y off que cruzan pistas."""
    events = []
    end = 0
    names = {}
    for i, track in enumerate(mid.tracks):
        tick = 0
        names[i] = track.name or f'pista_{i}'
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
                problems.append(f're-disparo abierto canal {msg.channel}, nota {msg.note}, tick {tick}')
            note = Note(tick, end, msg.note, msg.velocity, msg.channel, programs[msg.channel])
            notes[i].append(note)
            opened[key].append(note)
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            key = (msg.channel, msg.note)
            if not opened[key]:
                problems.append(f'note_off huérfano canal {msg.channel}, nota {msg.note}, tick {tick}')
                continue
            note = opened[key].popleft()
            note.end = tick
            if pedals[msg.channel] and msg.channel != 9:
                note.end = end
                sustained[msg.channel].append(note)
            if tick <= note.start:
                problems.append(f'duración no positiva: nota {msg.note}, tick {tick}')
    for (ch, pitch), pending in opened.items():
        if pending:
            problems.append(f'{len(pending)} notas sin cerrar canal {ch}, nota {pitch}')
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
            raise ValueError('compás no positivo')
        stop = pos + length
        if any(pos < t < stop for t in changes):
            raise ValueError('cambio de compás fuera de borde: no verificable con este perfil')
        bars.append((float(pos), float(min(stop, end))))
        pos = stop
    return bars


def bad_drum_group(pitches):
    if len(pitches) >= 3:
        return '3+ piezas'
    if len(pitches) == 2:
        a, b = pitches
        if a == b or (a in KICKS and b in KICKS):
            return 'golpe duplicado'
        if a in CYMBALS and b in CYMBALS:
            return 'dos platillos/hat simultáneos'
        if (a in SNARES and b in TOMS) or (b in SNARES and a in TOMS):
            return 'caja+tom simultáneos (contrato de claridad)'
    return None


def audit(path, profile='dense'):
    """dense es el contrato solicitado; basic solo para piezas SIN batería."""
    path = Path(path)
    mid = mido.MidiFile(path)
    tracks, names, end, meters, markers, structural = load_notes(mid)
    if mid.type == 2:
        structural.append('MIDI tipo 2: secuencias independientes')
    if mid.ticks_per_beat <= 0:
        raise ValueError('división SMPTE no soportada')
    bars = make_bars(end, mid.ticks_per_beat, meters)
    if not bars or not tracks:
        structural.append('pieza vacía')
    drums = [n for ns in tracks.values() for n in ns if n.channel == 9]
    if profile == 'auto':
        profile = 'dense' if drums else 'basic'
    if profile not in ('basic', 'dense'):
        raise ValueError('perfil desconocido')
    if profile == 'basic' and drums:
        raise ValueError('el perfil basic NO permite eludir los gates de batería')
    gates = []

    def gate(name, ok, detail):
        gates.append({'gate': name, 'ok': bool(ok), 'detail': detail})

    gate('estructura', not structural, '; '.join(structural[:8]) or 'notas cerradas y duración positiva')
    stats, dynamic_bad, register_bad, harmonic_silence = [], [], [], []
    for i, ns in sorted(tracks.items()):
        # Una pista tipo 0 puede contener múltiples canales/programas/roles.
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
                register_bad.append(f'{name}: rol desconocido, requiere perfil específico')
            elif role != 'drums':
                floor, ceiling = RANGES[role]
                if lo < floor or hi > ceiling:
                    register_bad.append(f'{name}={lo}..{hi}, permitido {floor}..{ceiling}')
            if role in HARMONIC and silent >= 1:
                harmonic_silence.append(f'{name}:{silent}')
    gate('dinámica', not dynamic_bad, 'mínimo 5 velocidades y amplitud 10; fallan: ' +
         ', '.join(dynamic_bad) if dynamic_bad else '>=5 velocidades y amplitud >=10 en pistas con >=16 notas')
    gate('registro', not register_bad, '; '.join(register_bad) or 'rangos por rol dentro del contrato')
    if profile == 'dense':
        gate('espacio', bool(harmonic_silence), 'compases completos sin notas ni sustain: ' +
             (', '.join(harmonic_silence) or 'ningún instrumento armónico calla'))
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
    # Agrupar ataques separados por <=1/48 de negra (~8 ms a 160 BPM).
    # Cada grupo queda anclado al primer ataque: no encadena golpes distantes.
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
        gate('solapamiento', not violation_ticks and not near_collisions,
             f'{sum(collisions.values())} instantes con 2+; {len(violation_ticks)} prohibidos; '
             f'{sum(near_collisions.values())} grupos próximos prohibidos; '
             f'primeros ticks prohibidos={violation_ticks[:8]}')
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
        gate('patrones', len(counts) >= 3 and dominance <= .5,
             f'{len(counts)} patrones/{len(signatures)} compases activos; máximo {most} '
             f'({dominance:.1%}); límites >=3 patrones y <=50%')
    sections = []
    if markers:
        for idx, (tick, label) in enumerate(markers):
            stop = markers[idx + 1][0] if idx + 1 < len(markers) else end
            indices = [b for b, (s, e) in enumerate(bars) if tick <= s < stop]
            # El contraste debe sobrevivir sin el ataque inicial ni el fill.
            body = [b for b in indices[1:-1] if b not in fill_bars]
            if not body:
                body = [b for b in indices if b not in fill_bars] or indices
            if body:
                sections.append((label, round(sum(density[b] for b in body) / len(body), 2)))
    else:
        # Sin marcadores no se pueden afirmar secciones: solo bloques de 8.
        for b in range(0, len(bars), 8):
            values = density[b:b + 8]
            sections.append((f'bloque{b + 1}', round(sum(values) / len(values), 2)))
    contrast = max((d for s, d in sections), default=0) - min((d for s, d in sections), default=0)
    if profile == 'dense':
        gate('densidad', len(set(density)) >= 3 and contrast >= 2,
             f'min={min(density, default=0)}, max={max(density, default=0)}, '
             f'{len(set(density))} niveles; contraste entre secciones/bloques={contrast:.2f} (mínimo 2)')
    gaps = [b - a for a, b in zip(fill_bars, fill_bars[1:])]
    periodic = len(fill_bars) >= 4 and gaps.count(4) / len(gaps) >= .75
    boundaries = {b for b, (s, e) in enumerate(bars) if any(t == e for t, label in markers) or e == end}
    outside = [b + 1 for b in fill_bars if markers and b not in boundaries]
    if profile == 'dense':
        gate('fills', not periodic and not outside,
             f'candidatos (heurística)={[b + 1 for b in fill_bars]}; '
             f'intervalos={gaps}; fuera de bordes={outside}; periódico cada 4={periodic}')
    return {'version': VERSION, 'file': str(path.resolve()),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'profile': profile, 'bars': len(bars), 'seconds': round(mid.length, 6),
            'tracks': stats, 'gates': gates, 'ok': all(g['ok'] for g in gates),
            'collisions': [{'pitches': list(ps), 'count': count,
                            'reason': bad_drum_group(ps)} for ps, count in sorted(collisions.items())],
            'near_collisions': [{'pitches': list(ps), 'count': count} for ps, count in near_collisions.items()],
            'fill_bars': [b + 1 for b in fill_bars],
            'density_sections': sections,
            'limits': 'Contrato de arreglo denso; no prueba timbre, enmascaramiento acústico, '
                      'palm mute, armonía correcta ni calidad musical. Fills inferidos, no todos detectables.'}


def format_report(report):
    lines = [f"AUDITORÍA {report['version']} | {report['file']}",
             f"Perfil={report['profile']} | {report['bars']} compases | {report['seconds']:.3f} s"]
    for s in report['tracks']:
        lines.append(f"PISTA {s['name']}: rol={s['role']}, velocidades={s['velocities']}, "
                     f"amplitud={s['spread']}, registro={s['range'][0]}..{s['range'][1]}, "
                     f"silencios={s['silent_bars']} compases")
    for g in report['gates']:
        lines.append(f"{'PASA' if g['ok'] else 'FALLA'} {g['gate']}: {g['detail']}")
    for c in report['collisions']:
        combo = '+'.join(NAMES.get(p, f'GM{p}') for p in c['pitches'])
        lines.append(f"  {combo}: {c['count']} instantes [{c['reason'] or 'permitido'}]")
    lines.append('Densidad por sección/bloque: ' + ', '.join(f'{s}={d:g}' for s, d in report['density_sections']))
    lines.append('LÍMITES: ' + report['limits'])
    lines.append('RESULTADO: ' + ('PASA (exit 0)' if report['ok'] else 'ABORTAR (exit 1)'))
    return '\n'.join(lines)


def require_arrangement(path, profile='auto'):
    report = audit(path, profile)
    if not report['ok']:
        raise ArrangementError(format_report(report))
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('midi', type=Path)
    parser.add_argument('--json', type=Path, help='guardar métricas y hash del MIDI auditado')
    args = parser.parse_args(argv)
    try:
        report = audit(args.midi)
        print(format_report(report))
        if args.json:
            if args.json.resolve() == args.midi.resolve():
                raise ValueError('el informe no puede sobrescribir el MIDI')
            args.json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        return 0 if report['ok'] else 1
    except Exception as exc:
        print(f'ABORTAR (exit 1): {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
