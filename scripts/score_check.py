#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""score_check.py — Analiza un MIDI como PARTITURA, sin audio.

La idea del usuario: en MuseScore se ve a primera vista cuándo una canción va a
sonar rara. Este script reproduce esa lectura de forma programática:

1. Densidad vertical (cuántas notas suenan a la vez) — "se ve apretado"
2. Registro agudo por pista (notas por encima de E5) — "se ve arriba"
3. Ligaduras / retrigger (nota repetida antes de cerrar) — "se ve mal escrito"
4. Distribución por octava — "se ve desconectado"
5. Haces (clústeres de notas simultáneas) — "se ve enredado"

NO necesita oír nada. Es lectura de partitura.

Uso:
    python3 score_check.py pieza.mid
    python3 score_check.py pieza.mid --threshold 76   # E5 por defecto
"""
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import mido

NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']


def nm(pitch: int) -> str:
    return f"{NAMES[pitch % 12]}{pitch // 12 - 1}"


def load_tracks(mid):
    """-> {nombre: [(start_tick, dur, pitch, vel)]}"""
    out = {}
    for i, tr in enumerate(mid.tracks):
        if i == 0:
            continue
        tick = 0
        open_notes = {}
        notes = []
        for msg in tr:
            tick += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                open_notes[(msg.note, msg.channel)] = tick
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                k = (msg.note, msg.channel)
                if k in open_notes:
                    start = open_notes.pop(k)
                    notes.append((start, tick - start, msg.note, 0))
        out[tr.name or f'track_{i}'] = notes
    return out


def density_vertical(mid, tracks):
    """Cuántas notas suenan a la vez, en cada instante."""
    events = []
    for i, tr in enumerate(mid.tracks):
        if i == 0:
            continue
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == 'note_on' and msg.velocity > 0:
                events.append((t, 1))
            elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                events.append((t, -1))
    hist = Counter()
    active = 0
    for _t, delta in sorted(events):
        active += delta
        hist[max(active, 0)] += 1
    return hist


def report(path, threshold):
    mid = mido.MidiFile(str(path))
    tracks = load_tracks(mid)
    total_notes = sum(len(v) for v in tracks.values())

    print(f"=== LECTURA DE PARTITURA: {Path(path).name} ===")
    print(f"    {len(tracks)} pistas | {total_notes} notas | "
          f"{mid.ticks_per_beat} TPB | {mid.length:.2f}s")
    print()

    # 1) Densidad vertical
    hist = density_vertical(mid, tracks)
    tot = sum(hist.values()) or 1
    peak = max(hist) if hist else 0
    print("1) DENSIDAD VERTICAL  (cuántas notas suenan a la vez)")
    for k in sorted(hist):
        bar = '#' * int(hist[k] * 30 / tot)
        print(f"   {k:2d} notas: {hist[k]:6d} ({hist[k]*100/tot:5.1f}%) {bar}")
    mean = sum(k * v for k, v in hist.items()) / tot
    print(f"   pico={peak}  media={mean:.1f}")
    if mean > 6:
        print("   -> SE VE APRETADO: demasiadas notas sonando a la vez.")
    elif mean < 2.5:
        print("   -> SE VE VACÍO: muy pocas notas a la vez.")
    else:
        print("   -> densidad razonable.")
    print()

    # 2) Registro agudo
    print(f"2) REGISTRO AGUDO  (notas por encima de {nm(threshold)})")
    worst = []
    for name, notes in tracks.items():
        if not notes:
            continue
        hi = [n for n in notes if n[2] >= threshold]
        pct = len(hi) * 100 / len(notes)
        top = max(n[2] for n in notes)
        flag = '  <-- SE VE ARRIBA' if pct > 40 else ''
        print(f"   {name:20s} {len(hi):5d}/{len(notes):5d} ({pct:5.1f}%)  max={nm(top)}{flag}")
        if pct > 40:
            worst.append((name, pct, top))
    if worst:
        print("   -> ESTAS PISTAS SUENAN AGUDAS: baja el registro o cambia el timbre.")
    print()

    # 3) Ligaduras
    print("3) LIGADURAS / RETRIGGER  (nota repetida antes de cerrar)")
    any_lig = False
    for name, notes in tracks.items():
        by_start = {}
        for start, dur, pitch, _v in notes:
            by_start.setdefault(pitch, []).append((start, dur))
        lig = 0
        for _p, evs in by_start.items():
            evs.sort()
            for (s1, d1), (s2, d2) in zip(evs, evs[1:]):
                if s2 < s1 + d1:
                    lig += 1
        if lig:
            any_lig = True
            print(f"   {name:20s} {lig:5d} ligaduras  <-- SE VE MAL ESCRITO")
    if not any_lig:
        print("   ninguna — limpio.")
    print()

    # 4) Distribución por octava
    print("4) DISTRIBUCIÓN POR OCTAVA")
    for name, notes in tracks.items():
        if not notes:
            continue
        octs = Counter((n[2] // 12) - 1 for n in notes)
        parts = '  '.join(f"{o}:{octs[o]}" for o in sorted(octs))
        print(f"   {name:20s} {parts}")
    print()

    # 5) Haces (clústeres simultáneos)
    print("5) HACES  (cuántas notas atacan en el mismo instante)")
    onset = Counter()
    for name, notes in tracks.items():
        for start, dur, pitch, _v in notes:
            onset[start] += 1
    max_h = max(onset.values()) if onset else 0
    print(f"   ataque máximo simultáneo: {max_h} notas")
    if max_h > 6:
        print("   -> SE VE ENREDADO: un instante con demasiadas notas nuevas.")
    else:
        print("   -> ataques claros.")
    print()
    print("LÍMITE: esto es lectura de partitura. Detecta problemas VISUALES de")
    print("escritura, no sustituye la escucha ni garantiza calidad musical.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("midi", help="archivo MIDI a analizar")
    ap.add_argument("--threshold", type=int, default=76,
                    help="umbral de agudez en nota MIDI (defecto 76 = E5)")
    args = ap.parse_args()

    if not Path(args.midi).is_file():
        print(f"ERROR: no existe {args.midi}")
        return 1
    report(args.midi, args.threshold)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
