#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""hermesmusic — motor unificado de composición y render MIDI.

Una sola regla de timing: los eventos se construyen en TICKS ABSOLUTOS, se
ordenan (meta < program < note_off < note_on) y se convierten a DELTA por pista.
Nunca se usa ``max(0, delta)``: un delta negativo es un ERROR, no se oculta.

Dependencias:
  - ``mido`` (obligatoria).
  - ``fluidsynth`` + ``ffmpeg`` + un SoundFont (solo para exportar audio).

CLI:
  hermesmusic.py recipes
  hermesmusic.py gen --recipe love_theme --key F --title Reencuentro -o r.mid
  hermesmusic.py compose r.spec.json -o r.mid [--audio r.mp3]
  hermesmusic.py validate r.mid
  hermesmusic.py render r.mid r.mp3

Compatibilidad con las skills antiguas: ``deg``, ``acorde_desde_grado``,
``eventos_a_pista`` y ``validar_seccion`` se mantienen como envoltorios.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile

import mido
from mido import Message, MetaMessage, MidiFile, MidiTrack

TPB = 480  # ticks por negra

# ============================================================================
# PITCH  —  notas, escalas, acordes
# ============================================================================

NOTE_PC = {
    "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
    "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10,
    "B": 11,
}
_PC_NAMES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]

SCALES = {
    "mayor":            [0, 2, 4, 5, 7, 9, 11],
    "menor_natural":    [0, 2, 3, 5, 7, 8, 10],
    "menor_armonica":   [0, 2, 3, 5, 7, 8, 11],
    "menor_melodica":   [0, 2, 3, 5, 7, 9, 11],
    "dorico":           [0, 2, 3, 5, 7, 9, 10],
    "frigio":           [0, 1, 3, 5, 7, 8, 10],
    "frigio_dominante": [0, 1, 4, 5, 7, 8, 10],
    "lidico":           [0, 2, 4, 6, 7, 9, 11],
    "mixolidio":        [0, 2, 4, 5, 7, 9, 10],
    "locrio":           [0, 1, 3, 5, 6, 8, 10],
    "alterada":         [0, 1, 3, 4, 6, 8, 10],
    "pentatonica_menor":[0, 3, 5, 7, 10],
    "pentatonica_mayor":[0, 2, 4, 7, 9],
    "blues":            [0, 3, 5, 6, 7, 10],
}

MOOD_SCALE = {
    "aventura": "dorico", "folk_epico": "dorico", "victoria": "mayor",
    "pueblo": "mayor", "calma": "mayor", "tristeza": "menor_natural",
    "perdida": "menor_natural", "amor": "mayor", "villano": "frigio",
    "mazmorra": "frigio", "tension": "frigio", "boss_final": "menor_armonica",
    "dramatico": "menor_armonica", "simple": "pentatonica_menor",
}


def name_to_midi(name: str) -> int:
    """'F4' -> 65 ; 'Bb3' -> 58  (C4 = 60, Do central)."""
    m = re.match(r"^([A-Ga-g])([#b]?)(-?\d+)$", name.strip())
    if not m:
        raise ValueError(f"nota inválida: {name!r}")
    pitch = m.group(1).upper() + m.group(2)
    octave = int(m.group(3))
    return 12 * (octave + 1) + NOTE_PC[pitch]


def midi_to_name(note: int) -> str:
    octave, pc = divmod(int(note), 12)
    return f"{_PC_NAMES[pc]}{octave - 1}"


def build_scale(tonic: str, scale_name: str = "mayor", octave: int = 4) -> list:
    """Escala de una octava en notas MIDI (semántica compatible con deg())."""
    if scale_name not in SCALES:
        raise ValueError(f"escala desconocida: {scale_name!r}")
    base = 12 * (octave + 1) + NOTE_PC[tonic]
    return [base + s for s in SCALES[scale_name]]


def scale_pcs(tonic: str, scale_name: str = "mayor") -> list:
    return [(NOTE_PC[tonic] + s) % 12 for s in SCALES[scale_name]]


def deg(scale: list, degree: int, transpose: int = 0) -> int:
    """Grado de escala -> nota MIDI. Usar SIEMPRE para melodía procedural."""
    length = len(scale)
    return scale[degree % length] + 12 * (degree // length) + transpose


def transcribe_to_midi(name: str) -> int:
    return name_to_midi(name)


# ---- acordes por cifrado: Fmaj7, Am7, C/E, Dm7, G7sus4, Bb, C6 ... ----------
_QUAL = {
    "": [0, 4, 7], "maj": [0, 4, 7], "major": [0, 4, 7],
    "min": [0, 3, 7], "m": [0, 3, 7], "minor": [0, 3, 7],
    "dim": [0, 3, 6], "o": [0, 3, 6], "aug": [0, 4, 8], "+": [0, 4, 8],
    "maj7": [0, 4, 7, 11], "M7": [0, 4, 7, 11],
    "min7": [0, 3, 7, 10], "m7": [0, 3, 7, 10], "-7": [0, 3, 7, 10],
    "7": [0, 4, 7, 10], "dom7": [0, 4, 7, 10],
    "m7b5": [0, 3, 6, 10], "dim7": [0, 3, 6, 9],
    "sus2": [0, 2, 7], "sus4": [0, 5, 7], "7sus4": [0, 5, 7, 10],
    "6": [0, 4, 7, 9], "m6": [0, 3, 7, 9],
    "add9": [0, 4, 7, 14], "9": [0, 4, 7, 10, 14],
    "maj9": [0, 4, 7, 11, 14], "m9": [0, 3, 7, 10, 14],
}
# 'M7' -> maj7 y séptima mayor por defecto para símbolo desnudo + 7 ya está en '7'
_QUAL["maj7"] = [0, 4, 7, 11]
_CHORD_RE = re.compile(r"^([A-Ga-g])([#b]?)(.*)$")


def parse_chord(symbol: str):
    """-> (root_pc, intervals, bass_pc|None)."""
    symbol = symbol.strip()
    bass_pc = None
    if "/" in symbol:
        symbol, bass = symbol.split("/", 1)
        bass_pc = NOTE_PC[bass.strip().capitalize().replace("B", "B")] if bass.strip() in NOTE_PC else None
        if bass_pc is None:
            bass_pc = NOTE_PC.get(bass.strip()[:1].upper() + bass.strip()[1:], None)
    m = _CHORD_RE.match(symbol)
    if not m:
        raise ValueError(f"acorde inválido: {symbol!r}")
    root = (m.group(1).upper() + m.group(2))
    if root not in NOTE_PC:
        raise ValueError(f"raíz inválida: {root!r}")
    quality = m.group(3).strip()
    if quality not in _QUAL:
        for k in sorted(_QUAL, key=len, reverse=True):
            if k and quality.startswith(k):
                quality = k
                break
        else:
            raise ValueError(f"calidad desconocida {quality!r} en {symbol!r}")
    return NOTE_PC[root], _QUAL[quality], bass_pc


def chord_midis(symbol: str, octave: int = 4, inversion: int = 0) -> list:
    """Notas MIDI del acorde, con inversión y bajo opcional una octava abajo."""
    root_pc, intervals, bass_pc = parse_chord(symbol)
    base = 12 * (octave + 1) + root_pc
    notes = [base + i for i in intervals]
    for _ in range(inversion % len(notes)):
        notes.append(notes.pop(0) + 12)
    if bass_pc is not None:
        notes = [12 * octave + bass_pc] + notes
    return notes


def _chord_degree_index(pcs: list, root_pc: int) -> int:
    """Índice del grado de la escala más cercano a la raíz del acorde."""
    root_pc %= 12
    for i, pc in enumerate(pcs):
        if pc == root_pc:
            return i
    return min(range(len(pcs)),
               key=lambda i: min((pcs[i] - root_pc) % 12, (root_pc - pcs[i]) % 12))


# ============================================================================
# PATRONES — melódicos (grados relativos al acorde) y de acompañamiento
# ============================================================================

# Melódicos: 8 corcheas por compás, offsets de grado relativos a la raíz.
MELODIC_PATTERNS = {
    "arpegio_confiado":  [0, 2, 4, 7, 6, 5, 4, 2],
    "escala_ascendente": [0, 1, 2, 3, 4, 3, 2, 0],
    "giro_ornacional":   [0, 2, 1, 0, -1, 0, 2, 4],
    "nota_repetida":     [0, 0, 1, 2, 0, 0, -1, 0],
    "salto_climax":      [0, 4, 7, 9, 7, 4, 2, 0],
    "descenso_cadencia": [4, 3, 2, 1, 0, -1, 0, 2],
    "swagger":           [0, 2, 4, 2, 0, -1, -3, 0],
    "balada":            [0, 1, 2, 4, 3, 2, 1, 0],
}
HOOK_DEFAULT = "salto_climax"

DYNAMICS = {"pp": 20, "p": 35, "mp": 50, "mf": 70, "f": 90, "ff": 110}
REGISTER_OCTAVE = {"low": 3, "mid": 4, "high": 5}


def _arp(symbol, octave, direction="up"):
    notes = chord_midis(symbol, octave)
    pool = notes + [n + 12 for n in notes]
    seq = pool if direction == "up" else list(reversed(pool))
    if direction == "updown":
        seq = pool + list(reversed(pool))
    out = (seq * 4)[:8]
    return [(i * 0.5, 0.5, p, 0) for i, p in enumerate(out)]


def _block(symbol, octave):
    notes = chord_midis(symbol, octave)
    steps = []
    for beat in (0.0, 2.0):
        for i, p in enumerate(notes):
            steps.append((beat + i * 0.04, 1.8, p, 0))
    return steps


def _bass_root(symbol, octave):
    root = chord_midis(symbol, octave)[0] - 12
    return [(0.0, 4.0, root, 0)]


def _bass_pulse(symbol, octave):
    root = chord_midis(symbol, octave)[0] - 12
    return [(b, 0.9, root, 0) for b in (0.0, 1.0, 2.0, 3.0)]


def _alberti(symbol, octave):
    notes = chord_midis(symbol, octave)
    lo = notes[0] - 12
    mid = notes[1] if len(notes) > 1 else notes[0] + 4
    hi = notes[2] if len(notes) > 2 else notes[0] + 7
    pattern = [lo, hi, mid, hi, lo, hi, mid, hi]
    return [(i * 0.5, 0.5, p, 0) for i, p in enumerate(pattern)]


def _waltz(symbol, octave):
    notes = chord_midis(symbol, octave)
    root = notes[0] - 12
    steps = [(0.0, 1.0, root, 0)]
    for b in (1.0, 2.0):
        for i, p in enumerate(notes):
            steps.append((b + i * 0.03, 0.95, p, 0))
    return steps


def _pad(symbol, octave):
    notes = chord_midis(symbol, octave)
    return [(0.0, 4.0, p, 0) for p in notes]


def _drum_metal(symbol, octave=None, tpb=TPB):
    """Batería power-metal: kick en 1/8, snare en 2&4, ride en corcheas.
    Devuelve (beat_offset, dur, pitch_midi, velocity) — channel 9 (batería)."""
    steps = []
    for beat in range(4):
        # ride/crash on every corchea
        for s in range(2):
            b = beat + s * 0.5
            steps.append((b, 0.25, 51, 100))  # ride (51)
        # hi-hat suave en corcheas (mas bajo)
        for s in range(2):
            b = beat + s * 0.5
            if s == 1:  # offbeat hi-hat mas suave
                steps.append((b, 0.15, 42, 70))  # closed hi-hat (42)
        # kick en 1 y 3 (y offbeat)
        steps.append((beat, 0.4, 36, 110))  # kick (36) fuerte
        steps.append((beat + 0.5, 0.3, 36, 90))  # kick offbeat
        # snare en 2 y 4
        if beat % 2 == 1:
            steps.append((beat, 0.4, 38, 115))  # snare (38) fuerte
            steps.append((beat + 0.5, 0.3, 38, 100))  # snare offbeat
        else:
            steps.append((beat + 0.5, 0.35, 38, 95))  # snare ghost
    return steps


def _choir_pad(symbol, octave):
    """Voz coro: acorde pad sostenido con movimiento de arpa en capas vocales."""
    root_pc, intervals, bass_pc = parse_chord(symbol)
    notes = chord_midis(symbol, octave)
    steps = []
    # voz principal (alto)
    for n in notes:
        steps.append((0.0, 4.0, n, 60))
    # voz segunda un 3ra/5ta arriba
    steps.append((0.0, 4.0, notes[0] + 4, 55))
    # voz tercera un 6ta arriba (armonía de 3 voces)
    steps.append((0.0, 4.0, notes[0] + 7, 55))
    # movimiento arpegiado suave en voces altas
    pool = notes + [n + 12 for n in notes]
    for i, p in enumerate(pool[:8]):
        steps.append((i * 0.5, 0.4, p, 65))
    return steps


ACCOMPANIMENT = {
    "arpeggio_up": lambda s, o: _arp(s, o, "up"),
    "arpeggio_down": lambda s, o: _arp(s, o, "down"),
    "arpeggio_updown": lambda s, o: _arp(s, o, "updown"),
    "block_chords": _block,
    "bass_root": _bass_root,
    "bass_pulse": _bass_pulse,
    "alberti": _alberti,
    "waltz": _waltz,
    "pad": _pad,
    "choir_pad": _choir_pad,
    "drum_metal": _drum_metal,
}


# ============================================================================
# TRACK BUILDER — el único lugar que convierte absoluto -> delta
# ============================================================================

def ticks(beats: float, tpb: int = TPB) -> int:
    return int(round(beats * tpb))


def build_track(name: str, notes, program: int, channel: int,
                tpb: int = TPB, is_drum: bool = False) -> MidiTrack:
    """notes: lista de (start_beats, dur_beats, pitch, velocity).

    Orden en el mismo tick: note_off antes que note_on (evita notas pegadas y
    permite re-disparar el mismo pitch). Un delta negativo levanta error.
    """
    track = MidiTrack()
    track.append(MetaMessage("track_name", name=name, time=0))
    if not is_drum:
        if not 0 <= program <= 127:
            raise ValueError(f"programa fuera de rango: {program}")
        track.append(Message("program_change", program=program,
                             channel=channel, time=0))

    events = []
    for (start, dur, pitch, vel) in notes:
        pitch, vel = int(round(pitch)), int(round(vel))
        if not 0 <= pitch <= 127:
            raise ValueError(f"pitch fuera de rango MIDI: {pitch}")
        if not 0 <= vel <= 127:
            raise ValueError(f"velocity fuera de rango MIDI: {vel}")
        on, off = ticks(start, tpb), ticks(start + dur, tpb)
        if off < on:
            raise ValueError(f"duración negativa en {name}: {dur}")
        events.append((on, 3, "on", pitch, vel))
        events.append((off, 2, "off", pitch, 0))

    events.sort(key=lambda e: (e[0], e[1]))
    last = 0
    open_pitches = set()

    def emit(kind, pitch, vel, tick):
        nonlocal last
        delta = tick - last
        if delta < 0:
            raise ValueError(f"delta negativo en {name} ({tick} < {last})")
        last = tick
        if kind == "on":
            track.append(Message("note_on", note=pitch, velocity=vel,
                                 channel=channel, time=delta))
        else:
            track.append(Message("note_off", note=pitch, velocity=0,
                                 channel=channel, time=delta))

    for (tick, _order, kind, pitch, vel) in events:
        if kind == "on":
            if pitch in open_pitches:  # re-disparo del mismo pitch: cerrar antes
                emit("off", pitch, 0, tick)
            open_pitches.add(pitch)
            emit("on", pitch, vel, tick)
        else:
            if pitch not in open_pitches:  # off sobrante (jitter): se descarta
                continue
            open_pitches.discard(pitch)
            emit("off", pitch, 0, tick)
    track.append(MetaMessage("end_of_track", time=0))
    return track


# ---- envoltorios de compatibilidad con las skills antiguas ------------------
def eventos_a_pista(nombre_pista, notas, program, channel, tpb=TPB):
    """Compat: notas = (tick_inicio, pitch, dur_ticks, velocity)."""
    beats = [(s / tpb, d / tpb, p, v) for (s, d, p, v) in notas]
    return build_track(nombre_pista, beats, program, channel, tpb,
                       is_drum=(channel == 9))


def acorde_desde_grado(scale, grado_raiz, transpose=0):
    return [deg(scale, grado_raiz + i, transpose) for i in (0, 2, 4)]


def validar_seccion(nombre, chords, patts, patterns_dict=None):
    assert len(chords) == len(patts), (
        f"{nombre}: {len(chords)} acordes vs {len(patts)} patrones")
    if patterns_dict is not None:
        for p in patts:
            if isinstance(p, str) and p not in patterns_dict:
                raise AssertionError(f"{nombre}: patrón '{p}' no existe")
    return True


# ============================================================================
# RENDER — SongSpec -> MidiFile
# ============================================================================

def _humanize(vel, tick, rng, hum):
    if not hum:
        return vel, tick
    vj = int(round(vel * hum.get("velocity", 0.0) * rng.uniform(-1, 1)))
    tj = int(round(hum.get("ticks", 0) * rng.uniform(-1, 1))) if hum.get("ticks") else 0
    return max(1, min(127, vel + vj)), max(0, tick + tj)


def render_song(spec: dict, out_path: str, tpb: int = TPB) -> str:
    title = spec.get("title", "Sin Título")
    key = spec.get("key", "C")
    scale_name = spec.get("scale", "mayor")
    tempo = int(round(spec.get("tempo", spec.get("tempo_bpm", 120))))
    num, den = spec.get("meter", spec.get("time_signature", [4, 4]))
    bar_beats = num * (4.0 / den)
    scale = build_scale(key, scale_name, 4)
    pcs = scale_pcs(key, scale_name)
    hum = spec.get("humanize") or {}
    rng = random.Random(hum.get("seed", 0))

    sections = spec.get("sections", [])
    spans, start = [], 0.0
    for sec in sections:
        length = sec.get("bars", 4) * bar_beats
        spans.append((sec, start, length))
        start += length
    total = start

    # ---- melodías (por pista nombrada) ----
    melody = {}  # track_name -> {"instrument","channel","notes":[...]}
    for sec, sec_start, _len in spans:
        # una sección puede llevar "melody" (una voz) y/o "melodies" (varias voces
        # simultáneas: p. ej. violín + flauta). Retrocompatible con "melody".
        mels = []
        if sec.get("melody"):
            mels.append(sec["melody"])
        mels.extend(sec.get("melodies") or [])
        for mel in mels:
            tname = mel.get("track", "melody")
            slot = melody.setdefault(tname, {
                "instrument": mel.get("instrument", 40),
                "channel": mel.get("channel"),
                "notes": [],
            })
            oct_shift = mel.get("octave", 0) * 12
            dyn = DYNAMICS.get(sec.get("dynamics", mel.get("dynamics", "mf")), 70)
            if "notes" in mel:
                for n in mel["notes"]:
                    when = sec_start + n["bar"] * bar_beats + n.get("beat", 0.0)
                    slot["notes"].append((when, n.get("dur", 1.0),
                                          name_to_midi(n["note"]) + oct_shift,
                                          DYNAMICS.get(n.get("dynamics", ""), dyn)))
            elif "pattern" in mel:
                pat = MELODIC_PATTERNS.get(mel["pattern"])
                if pat is None:
                    raise ValueError(f"patrón melódico desconocido: {mel['pattern']!r}")
                prog = sec.get("progression", [key])
                for b in range(sec.get("bars", 4)):
                    chord = prog[b % len(prog)]
                    root_pc, _, _ = parse_chord(chord)
                    cdeg = _chord_degree_index(pcs, root_pc)
                    base = sec_start + b * bar_beats
                    for i, off in enumerate(pat):
                        when = base + i * 0.5
                        slot["notes"].append((when, 0.5,
                                              deg(scale, cdeg + off, oct_shift), dyn))

    # ---- tracks de acompañamiento (por pista) ----
    accomp = {}  # name -> {"instrument","channel","notes":[], "is_drum"}
    # tracks_global aplica a TODAS las secciones
    all_track_entries = list(spec.get("tracks_global", [])) + list(spec.get("tracks", []))
    for t in all_track_entries:
        patname = t.get("pattern")
        if not patname:
            continue
        # --- patrón de batería por rejilla (16 pasos/compás) ---
        # t["grid"] = {"kick":[...16], "snare":[...], "hihat":[...], ...} fracciones 0..1
        if patname == "drum_grid":
            grid = t.get("grid") or {}
            thr = float(t.get("grid_threshold", 0.4))
            dyn = DYNAMICS.get(t.get("dynamics", "mp"), 50)
            dmap = [("kick", 36), ("snare", 38), ("hihat", 42),
                    ("cymbal", 49), ("ride", 51), ("tom", 45)]
            # Gate ANTES de humanizar: el jitter no puede ocultar 3 piezas.
            # Comprobar pasos y ticks efectivos (los offsets pueden colisionar).
            grid_steps, grid_ticks = {}, {}
            for cls, _pitch in dmap:
                for i, val in enumerate((grid.get(cls) or [])[:16]):
                    on, offb = val if isinstance(val, (list, tuple)) and len(val) >= 2 else ((val or 0.0), 0.0)
                    if on is not None and on >= thr:
                        grid_steps.setdefault(i, []).append(cls)
                        at = ticks(i * bar_beats / 16.0 + offb, tpb)
                        grid_ticks.setdefault(at, []).append(cls)
            for kind, positions in (("paso", grid_steps), ("tick efectivo", grid_ticks)):
                for position, pieces in positions.items():
                    if len(pieces) >= 3:
                        raise ValueError(
                            f"drum_grid rechazado: {len(pieces)} piezas en {kind} "
                            f"{position}: {'+'.join(pieces)}. Máximo 2; redistribuye "
                            "los ataques y ejecuta audit_arrangement.py.")
            want = t.get("sections")          # opcional: limitar a secciones por nombre
            dyn_map = t.get("dyn_map") or {}  # opcional: dinámica por sección
            dnotes = []
            for sec, sec_start, _l in spans:
                if want and sec.get("name") not in want:
                    continue
                sdyn = DYNAMICS.get(dyn_map.get(sec.get("name", ""), dyn), dyn)
                for b in range(sec.get("bars", 4)):
                    base = sec_start + b * bar_beats
                    for cls, pitch in dmap:
                        steps = grid.get(cls) or []
                        for i, val in enumerate(steps[:16]):
                            # val puede ser: (intensity, offset_beats) o solo intensity
                            if isinstance(val, (list, tuple)) and len(val) >= 2:
                                on, offb = val
                            else:
                                on, offb = (val or 0.0), 0.0
                            if on is not None and on >= thr:
                                dnotes.append((base + i * (bar_beats / 16.0) + offb,
                                               0.1, pitch, sdyn))
            accomp[t.get("role", "drums")] = {
                "instrument": 0, "channel": 9, "notes": dnotes, "is_drum": True}
            continue
        # --- patrón de género: auto-configura drum_grid + instruments ---
        # t["genre"] = "jazz" | "rock" | "reggae" | ... (ver genre_configs.json)
        if patname == "genre_grid":
            genre_name = t.get("genre", "").lower().replace("-", "_").replace(" ", "_")
            # Cargar config de género
            _gc_path = os.path.join(os.path.dirname(__file__), "..", "references", "genre_configs.json")
            try:
                with open(os.path.normpath(_gc_path), "r", encoding="utf-8") as _f:
                    _gc = json.load(_f)
            except (FileNotFoundError, json.JSONDecodeError) as _e:
                raise ValueError(f"No se pudo cargar genre_configs.json: {_e}")
            if genre_name not in _gc:
                raise ValueError(f"Género desconocido: {genre_name!r}. Géneros disponibles: {sorted(_gc.keys())}")
            gcfg = _gc[genre_name]
            # Configurar drum_grid desde el género
            _grid = gcfg["drum_grid"]
            thr = float(t.get("grid_threshold", 0.4))
            dyn_lo, dyn_hi = gcfg.get("dyn_range", [50, 90])
            # Escalar dinámica al rango del género
            _base_dyn = DYNAMICS.get(t.get("dynamics", "mp"), 50)
            _scale = (dyn_hi - dyn_lo) / 40.0  # normalizar
            _sdyn = max(dyn_lo, min(dyn_hi, int(_base_dyn * _scale + dyn_lo * 0.5)))
            dmap = [("kick", 36), ("snare", 38), ("hihat", 42),
                    ("cymbal", 49), ("ride", 51), ("tom", 45)]
            want = t.get("sections")
            dyn_map = t.get("dyn_map") or {}
            dnotes = []
            for sec, sec_start, _l in spans:
                if want and sec.get("name") not in want:
                    continue
                _sdyn2 = DYNAMICS.get(dyn_map.get(sec.get("name", ""), ""), _sdyn)
                _sdyn2 = max(dyn_lo, min(dyn_hi, _sdyn2))
                for b in range(sec.get("bars", 4)):
                    base = sec_start + b * bar_beats
                    for cls, pitch in dmap:
                        steps = _grid.get(cls) or []
                        # Determine swing offset: if genre has swing > 0.3 and
                        # grid cells are simple 0/1 (no explicit offsets),
                        # apply swing to offbeat positions (odd 16th steps)
                        # so the rhythm sounds genuinely swung.
                        # Fórmula: offset_beats = (swing - 0.5) * 0.34
                        _sw = gcfg.get("swing", 0.0)
                        _apply_swing = _sw > 0.3 and (not steps or isinstance(steps[0], (int, float)))
                        _swing_off = (_sw - 0.5) * 0.34 if _apply_swing else 0.0
                        for i, val in enumerate(steps[:16]):
                            if isinstance(val, (list, tuple)) and len(val) >= 2:
                                on, offb = val
                            else:
                                on = (val or 0.0)
                                # Apply swing offset to offbeat positions (odd steps: 1,3,5,...)
                                offb = _swing_off if _apply_swing and (i % 2 == 1) and on >= thr else 0.0
                            if on is not None and on >= thr:
                                dnotes.append((base + i * (bar_beats / 16.0) + offb,
                                               0.1, pitch, _sdyn2))
            accomp[t.get("role", "drums")] = {
                "instrument": 0, "channel": 9, "notes": dnotes, "is_drum": True}
            # Auto-configurar instruments si no se especificaron
            if not t.get("instruments") and gcfg.get("instruments"):
                # Los instruments se usan a nivel de spec, no de track
                # Guardar referencia para que el spec los use
                t["_genre_instruments"] = gcfg["instruments"]
            continue
        gen = ACCOMPANIMENT.get(patname)
        if gen is None:
            raise ValueError(f"patrón de acompañamiento desconocido: {patname!r}")
        octv = t.get("octave", REGISTER_OCTAVE.get(t.get("register", "mid"), 4))
        dyn = DYNAMICS.get(t.get("dynamics", "mp"), 50)
        notes = []
        want = t.get("sections")          # opcional: limitar a secciones por nombre
        dyn_map = t.get("dyn_map") or {}  # opcional: dinámica por sección
        for sec, sec_start, _len in spans:
            if want and sec.get("name") not in want:
                continue
            sdyn = DYNAMICS.get(dyn_map.get(sec.get("name"), ""), dyn)
            prog = sec.get("progression", [key])
            for b in range(sec.get("bars", 4)):
                chord = prog[b % len(prog)]
                base = sec_start + b * bar_beats
                for (offb, dur, pitch, _v) in gen(chord, octv):
                    notes.append((base + offb, dur, pitch, sdyn))
        accomp[t.get("role", patname)] = {
            "instrument": t.get("instrument", 0),
            "channel": t.get("channel"),
            "notes": notes,
            "is_drum": t.get("is_drum", False),
        }

    # ---- ensamblar ----
    mid = MidiFile(type=1, ticks_per_beat=tpb)
    meta = MidiTrack()
    meta.append(MetaMessage("track_name", name=title, time=0))
    meta.append(MetaMessage("set_tempo", tempo=mido.bpm2tempo(tempo), time=0))
    meta.append(MetaMessage("time_signature", numerator=num, denominator=den, time=0))
    # La auditoría compara densidades por sección real, no por ventanas supuestas.
    previous_marker = 0
    for index, (section, section_start, _length) in enumerate(spans):
        at = ticks(section_start, tpb)
        meta.append(MetaMessage("marker", text=section.get("name", f"seccion_{index + 1}"),
                                time=at - previous_marker))
        previous_marker = at
    meta.append(MetaMessage("end_of_track", time=ticks(total, tpb) - previous_marker))
    mid.tracks.append(meta)

    used_channels = set()
    next_ch = 0

    def pick_channel(pref):
        nonlocal next_ch
        if pref is not None and pref != 9:
            used_channels.add(pref)
            return pref
        while next_ch in used_channels or next_ch == 9:
            next_ch += 1
        used_channels.add(next_ch)
        return next_ch

    for group in list(accomp.items()) + list(melody.items()):
        name, slot = group
        is_drum = slot.get("is_drum", False)
        ch = 9 if is_drum else pick_channel(slot.get("channel"))
        notes = []
        for (when, dur, pitch, vel) in slot["notes"]:
            t = ticks(when, tpb)
            v, t2 = _humanize(vel, t, rng, hum)
            notes.append((t2 / tpb, dur, pitch, v))
        mid.tracks.append(build_track(name, notes, slot["instrument"], ch,
                                      tpb, is_drum))

    # Toda composición del motor se audita antes de publicar el archivo.
    # Mantiene la firma pública; las composiciones defectuosas ahora ABORTAN.
    # No afecta a render_performance (reconstrucción fiel de material ajeno).
    if __package__:
        from .audit_arrangement import require_arrangement
    else:
        from audit_arrangement import require_arrangement
    target_dir = os.path.dirname(os.path.abspath(out_path))
    with tempfile.TemporaryDirectory(prefix=".hermes-audit-", dir=target_dir) as tmp:
        candidate = os.path.join(tmp, "candidate.mid")
        mid.save(candidate)
        require_arrangement(candidate)
        os.replace(candidate, out_path)
    return out_path


# ============================================================================
# VALIDACIÓN (solo mido)
# ============================================================================

def validate_midi(path: str, expected_duration=None, tol=0.5):
    mid = MidiFile(path)
    problems = []
    if mid.type == 2:
        problems.append("Type 2: secuencias independientes, no una canción")
    for i, tr in enumerate(mid.tracks):
        name = tr.name or f"pista {i}"
        tick, open_notes, notes = 0, {}, 0
        has_ctl = False
        for msg in tr:
            tick += msg.time
            # La clave incluye el canal: en MIDI dos notas del mismo pitch en
            # canales distintos pueden solaparse sin ser un error. Con clave
            # solo por pitch esto daba falsos positivos "re-disparo".
            # Los MetaMessage no tienen .channel/.note: solo aplica a notas.
            key = (msg.channel, msg.note) if msg.is_meta is False and hasattr(msg, "note") else None
            if key is not None and msg.type == "note_on" and msg.velocity > 0:
                if open_notes.get(key):
                    problems.append(f"[{name}] re-disparo sin note_off ({msg.note})")
                open_notes[key] = open_notes.get(key, 0) + 1
                notes += 1
            elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
                if open_notes.get(key, 0) <= 0:
                    problems.append(f"[{name}] note_off sin note_on ({msg.note})")
                else:
                    open_notes[key] -= 1
                    if open_notes[key] == 0:
                        del open_notes[key]
            elif msg.type in ("control_change", "pitchwheel", "program_change"):
                has_ctl = True
        if open_notes:
            pend = sorted({n for (_ch, n) in open_notes})
            problems.append(f"[{name}] notas sin cerrar: {pend}")
        if notes == 0 and i > 0 and not has_ctl:
            problems.append(f"[{name}] no tiene notas")
    duration = mid.length
    if expected_duration is not None and abs(duration - expected_duration) > tol:
        problems.append(f"duración {duration:.2f}s != esperada {expected_duration:.2f}s")
    return problems, duration


# ============================================================================
# AUDIO — fluidsynth -> wav -> mp3/ogg
# ============================================================================

def find_soundfont():
    if __package__:
        from .audio_utils import find_soundfont as discover
    else:
        from audio_utils import find_soundfont as discover
    return discover()


def render_audio(mid_path: str, out_path: str, soundfont: str = None,
                 gain: float = 0.8) -> str:
    if __package__:
        from .audio_utils import executable, positive, run_process
    else:
        from audio_utils import executable, positive, run_process
    positive(gain, 'gain')
    sf = soundfont or find_soundfont()
    if not sf or not os.path.isfile(sf):
        raise RuntimeError("Missing SoundFont; install fluid-soundfont-gm or set MIDI_SOUNDFONT")
    if not os.path.isfile(mid_path):
        raise ValueError(f'MIDI file does not exist: {mid_path}')
    if os.path.abspath(mid_path) == os.path.abspath(out_path):
        raise ValueError('Audio output must differ from MIDI input')
    synth = executable('fluidsynth')
    ffmpeg = executable('ffmpeg')
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "out.wav")
        run_process([synth, "-ni", "-g", str(gain), "-F", wav,
                     "-r", "44100", str(sf), str(mid_path)])
        ext = os.path.splitext(out_path)[1].lower()
        if ext == ".mp3":
            codec = ["-codec:a", "libmp3lame", "-qscale:a", "2"]
        elif ext == ".ogg":
            codec = ["-c:a", "libvorbis", "-q:a", "5"]
        elif ext == ".wav":
            codec = ["-c:a", "pcm_s16le"]
        else:
            raise ValueError('Supported audio outputs: .wav, .ogg, .mp3')
        run_process([ffmpeg, "-nostdin", "-y", "-i", wav, "-ar", "44100", "-ac", "2",
                     *codec, str(out_path)])
    return out_path


# ============================================================================
# PERFORMANCE — reconstrucción FIEL de un MIDI real (sin pérdida)
# ============================================================================
# A diferencia de `render_song` (SongSpec: composición nueva), aquí se reescribe
# una `performance` extraída con miditrack_extract.py conservando TODO:
# mapa de tempo, mapa de compás, por pista: programa, notas+velocidad y CC7.

def render_performance(perf: dict, out_path: str, tpb: int = None) -> str:
    """Reconstruye un MIDI fiel desde un dict 'performance' (sin pérdida)."""
    tpb = tpb or perf.get("tpb", TPB)
    mid = MidiFile(type=1, ticks_per_beat=tpb)

    # ---- pista meta: tempo_map + meter_map + key_signature ----
    meta = MidiTrack()
    meta.append(MetaMessage("track_name", name=perf.get("filename", "performance"),
                            time=0))
    mevents = []
    for e in perf.get("tempo_map") or [[0, 500000]]:
        mevents.append((int(e[0]), 1, "tempo", int(e[1])))
    for e in perf.get("meter_map") or [[0, 4, 4]]:
        mevents.append((int(e[0]), 2, "meter", (int(e[1]), int(e[2]))))
    if perf.get("key_signature"):
        mevents.append((0, 3, "key", perf["key_signature"]))
    mevents.sort(key=lambda x: (x[0], x[1]))
    last = 0
    for tick, _order, kind, data in mevents:
        d = tick - last
        if d < 0:
            continue
        last = tick
        if kind == "tempo":
            meta.append(MetaMessage("set_tempo", tempo=data, time=d))
        elif kind == "meter":
            meta.append(MetaMessage("time_signature", numerator=data[0],
                                    denominator=data[1], time=d))
        else:
            meta.append(MetaMessage("key_signature", key=data, time=d))
    meta.append(MetaMessage("end_of_track", time=0))
    mid.tracks.append(meta)

    # ---- pistas reales ----
    for t in perf.get("tracks", []):
        ch = int(t.get("channel", 0))
        is_drum = bool(t.get("is_drum")) or ch == 9
        tr = MidiTrack()
        tr.append(MetaMessage("track_name",
                              name=str(t.get("name") or t.get("gm_name") or "track"),
                              time=0))
        ev = []  # (tick, order, kind, a, b)
        if not is_drum:
            ev.append((0, 1, "prog", int(t.get("program", 0)), 0))
        cc = t.get("cc")
        if cc:  # TODOS los controladores (CC1, CC7, CC10, CC11, CC64...) [str|int keys]
            for ctrl, evs in cc.items():
                for ctick, cval in evs:
                    ev.append((int(ctick), 2, "cc", int(ctrl), int(cval)))
        else:   # performances antiguas: solo CC7
            for ctick, cval in t.get("cc7") or []:
                ev.append((int(ctick), 2, "cc", 7, int(cval)))
        for btick, bval in t.get("bend") or []:
            ev.append((int(btick), 2, "bend", int(bval), 0))
        for n in t.get("notes", []):
            st, en, pitch, vel = int(n[0]), int(n[1]), int(n[2]), int(n[3])
            if not 0 <= pitch <= 127 or vel <= 0:
                continue
            ev.append((st, 4, "on", pitch, min(127, vel)))
            ev.append((max(en, st + 1), 3, "off", pitch, 0))
        ev.sort(key=lambda x: (x[0], x[1]))

        last, openp = 0, set()
        for tick, _order, kind, a, b in ev:
            d = tick - last
            if d < 0:
                d = 0
            if kind == "prog":
                tr.append(Message("program_change", program=a, channel=ch, time=d))
                last = tick
            elif kind == "cc":
                tr.append(Message("control_change", control=a, value=b,
                                  channel=ch, time=d))
                last = tick
            elif kind == "bend":
                tr.append(Message("pitchwheel", pitch=a, channel=ch, time=d))
                last = tick
            elif kind == "off":
                if a not in openp:
                    continue
                openp.discard(a)
                tr.append(Message("note_off", note=a, velocity=0, channel=ch,
                                  time=d))
                last = tick
            else:  # on
                if a in openp:  # re-disparo: cerrar en el mismo tick
                    tr.append(Message("note_off", note=a, velocity=0, channel=ch,
                                      time=d))
                    openp.discard(a)
                    last = tick
                    d = 0
                else:
                    last = tick
                openp.add(a)
                tr.append(Message("note_on", note=a, velocity=b, channel=ch,
                                  time=d))
        for pitch in sorted(openp):  # cerrar colgadas
            tr.append(Message("note_off", note=pitch, velocity=0, channel=ch,
                              time=0))
        tr.append(MetaMessage("end_of_track", time=0))
        mid.tracks.append(tr)

    mid.save(out_path)
    return out_path


# ============================================================================
# RECETAS — devuelven un SongSpec
# ============================================================================

def _love_theme_spec(key="F", tempo=72):
    """Tema de amor estilo FF4 (Rosa y Cecil). 24 compases = 1:20 a 72 BPM."""
    intro = ["Fmaj7", "Am7", "Bb", "C"]
    a = ["F", "C/E", "Dm7", "Bb", "Gm7", "C7", "F", "C"]
    b = ["Dm", "Bb", "F", "C", "Dm", "Gm7", "Bb", "C"]
    outro = ["F", "Bb", "Gm7", "F"]
    a_mel = [
        (0, 0, 1, "C5"), (0, 1, 1, "D5"), (0, 2, 2, "F5"),
        (1, 0, 2, "E5"), (1, 2, 1, "C5"), (1, 3, 1, "G4"),
        (2, 0, 1, "A4"), (2, 1, 1, "C5"), (2, 2, 2, "D5"),
        (3, 0, 2, "F5"), (3, 2, 1, "D5"), (3, 3, 1, "Bb4"),
        (4, 0, 1, "G4"), (4, 1, 1, "A4"), (4, 2, 2, "Bb4"),
        (5, 0, 1, "A4"), (5, 1, 1, "G4"), (5, 2, 2, "E4"),
        (6, 0, 2, "F4"), (6, 2, 2, "A4"),
        (7, 0, 2, "C5"), (7, 2, 2, "G4"),
    ]
    b_mel = [
        (0, 0, 2, "D5"), (0, 2, 2, "F5"), (1, 0, 2, "F5"), (1, 2, 2, "D5"),
        (2, 0, 1, "C5"), (2, 1, 1, "D5"), (2, 2, 2, "F5"), (3, 0, 4, "E5"),
        (4, 0, 2, "F5"), (4, 2, 2, "A5"), (5, 0, 2, "G5"), (5, 2, 2, "D5"),
        (6, 0, 2, "F5"), (6, 2, 2, "D5"), (7, 0, 4, "C5"),
    ]
    out_mel = [
        (0, 0, 2, "C5"), (0, 2, 2, "A4"), (1, 0, 2, "Bb4"), (1, 2, 2, "D5"),
        (2, 0, 2, "A4"), (2, 2, 2, "G4"), (3, 0, 4, "F4"),
    ]

    def mel(notes, instrument, dyn, oct_shift=0):
        return {"instrument": instrument, "octave": oct_shift, "dynamics": dyn,
                "notes": [{"bar": ba, "beat": be, "dur": du, "note": no}
                          for (ba, be, du, no) in notes]}

    return {
        "title": "Reencuentro", "key": key, "scale": "mayor",
        "tempo": tempo, "meter": [4, 4],
        "humanize": {"seed": 42, "velocity": 0.08, "ticks": 4},
        "sections": [
            {"name": "intro", "bars": 4, "progression": intro, "dynamics": "p"},
            {"name": "A", "bars": 8, "progression": a, "dynamics": "mp",
             "melody": mel(a_mel, 40, "mp")},
            {"name": "B", "bars": 8, "progression": b, "dynamics": "mf",
             "melody": mel(b_mel, 40, "mf")},
            {"name": "outro", "bars": 4, "progression": outro, "dynamics": "p",
             "melody": mel(out_mel, 40, "p")},
        ],
        "tracks": [
            {"role": "harp", "instrument": 46, "pattern": "arpeggio_up",
             "register": "high", "dynamics": "p"},
            {"role": "piano", "instrument": 0, "pattern": "bass_root",
             "register": "low", "dynamics": "mp"},
            {"role": "piano_chords", "instrument": 0, "pattern": "block_chords",
             "register": "mid", "dynamics": "mp"},
        ],
    }


def _battle_spec(key="A", tempo=160):
    return {
        "title": "Batalla", "key": key, "scale": "menor_armonica",
        "tempo": tempo, "meter": [4, 4],
        "humanize": {"seed": 7, "velocity": 0.1, "ticks": 6},
        "sections": [
            {"name": "intro", "bars": 4, "progression": ["Am", "F", "G", "Am"],
             "dynamics": "mf"},
            {"name": "A", "bars": 8, "progression": ["Am", "F", "G", "Am", "Dm", "E", "Am", "E"],
             "dynamics": "f", "melody": {"pattern": "salto_climax",
                                         "instrument": 61, "track": "lead"}},
        ],
        "tracks": [
            {"role": "bass", "instrument": 34, "pattern": "bass_pulse",
             "register": "low", "dynamics": "f"},
            {"role": "pad", "instrument": 48, "pattern": "pad",
             "register": "mid", "dynamics": "mp"},
            {"role": "timpani", "instrument": 47, "pattern": "bass_root",
             "register": "low", "dynamics": "mf", "is_drum": True, "channel": 9},
        ],
    }


def _game_spec(title, key, scale, tempo, progression, lead, accomp, bars=16, seed=11):
    """Constructor compacto de piezas de juego (melodía procedural por patrón)."""
    lead_instr, lead_pattern, lead_dyn = lead
    return {
        "title": title, "key": key, "scale": scale, "tempo": tempo, "meter": [4, 4],
        "humanize": {"seed": seed, "velocity": 0.08, "ticks": 5},
        "sections": [
            {"name": "intro", "bars": 4, "progression": progression, "dynamics": "mp"},
            {"name": "tema", "bars": bars, "progression": progression, "dynamics": lead_dyn,
             "melody": {"pattern": lead_pattern, "instrument": lead_instr, "track": "lead"}},
        ],
        "tracks": accomp,
    }


# Recetas de género: parámetros -> spec. Añade aquí para exponer en `gen --recipe`.
_GAME = {
    "fanfarria": dict(t="Fanfarria", k="A", s="mixolidio", bpm=132, seed=3,
        prog=["A", "E", "F#m", "D", "A", "D", "E", "A"],
        lead=(56, "salto_climax", "f"),
        acc=[{"role": "brass", "instrument": 61, "pattern": "block_chords", "register": "mid", "dynamics": "f"},
             {"role": "strings", "instrument": 48, "pattern": "pad", "register": "high", "dynamics": "mf"},
             {"role": "bass", "instrument": 32, "pattern": "bass_pulse", "register": "low", "dynamics": "f"},
             {"role": "timpani", "instrument": 47, "pattern": "bass_root", "register": "low", "dynamics": "mf", "is_drum": True, "channel": 9}]),
    "taverna": dict(t="Taverna", k="G", s="dorico", bpm=120, seed=5,
        prog=["G", "Em", "C", "D", "G", "C", "D", "G"],
        lead=(73, "giro_ornacional", "mf"),
        acc=[{"role": "guitar", "instrument": 24, "pattern": "block_chords", "register": "mid", "dynamics": "mf"},
             {"role": "pluck", "instrument": 45, "pattern": "arpeggio_up", "register": "high", "dynamics": "mp"},
             {"role": "bass", "instrument": 32, "pattern": "bass_root", "register": "low", "dynamics": "mf"}]),
    "mazmorra": dict(t="Mazmorra", k="D", s="frigio", bpm=80, seed=13,
        prog=["Dm", "Bb", "Gm", "A", "Dm", "Bb", "A", "Dm"],
        lead=(42, "descenso_cadencia", "mp"),
        acc=[{"role": "strings", "instrument": 48, "pattern": "pad", "register": "low", "dynamics": "mp"},
             {"role": "choir", "instrument": 52, "pattern": "pad", "register": "mid", "dynamics": "p"},
             {"role": "bass", "instrument": 32, "pattern": "bass_root", "register": "low", "dynamics": "mp"}]),
    "misterio": dict(t="Misterio", k="A", s="menor_natural", bpm=70, seed=17,
        prog=["Am", "Dm", "E", "Am", "F", "Dm", "E", "Am"],
        lead=(11, "giro_ornacional", "mp"),
        acc=[{"role": "pad", "instrument": 89, "pattern": "pad", "register": "mid", "dynamics": "p"},
             {"role": "harp", "instrument": 46, "pattern": "arpeggio_updown", "register": "high", "dynamics": "p"},
             {"role": "bass", "instrument": 32, "pattern": "bass_root", "register": "low", "dynamics": "p"}]),
    "pueblo": dict(t="Pueblo", k="C", s="mayor", bpm=100, seed=19,
        prog=["C", "G", "Am", "F", "C", "F", "G", "C"],
        lead=(68, "escala_ascendente", "mf"),
        acc=[{"role": "guitar", "instrument": 24, "pattern": "block_chords", "register": "mid", "dynamics": "mf"},
             {"role": "pluck", "instrument": 45, "pattern": "arpeggio_up", "register": "high", "dynamics": "mp"},
             {"role": "bass", "instrument": 32, "pattern": "bass_root", "register": "low", "dynamics": "mf"}]),
    "epica": dict(t="Epica", k="D", s="dorico", bpm=90, seed=23,
        prog=["Dm", "Bb", "F", "C", "Dm", "Gm", "Bb", "C"],
        lead=(60, "salto_climax", "f"),
        acc=[{"role": "strings", "instrument": 48, "pattern": "pad", "register": "high", "dynamics": "mf"},
             {"role": "brass", "instrument": 61, "pattern": "block_chords", "register": "mid", "dynamics": "mf"},
             {"role": "bass", "instrument": 32, "pattern": "bass_pulse", "register": "low", "dynamics": "f"},
             {"role": "timpani", "instrument": 47, "pattern": "bass_root", "register": "low", "dynamics": "mf", "is_drum": True, "channel": 9}]),
    "funebre": dict(t="Funebre", k="D", s="menor_natural", bpm=60, seed=29,
        prog=["Dm", "Gm", "A", "Dm", "Bb", "Gm", "A", "Dm"],
        lead=(42, "descenso_cadencia", "p"),
        acc=[{"role": "strings", "instrument": 48, "pattern": "pad", "register": "mid", "dynamics": "p"},
             {"role": "organ", "instrument": 19, "pattern": "pad", "register": "low", "dynamics": "mp"},
             {"role": "bass", "instrument": 32, "pattern": "bass_root", "register": "low", "dynamics": "p"}]),
}


def _make_game_recipe(params):
    def fn(key=None, tempo=None):
        return _game_spec(params["t"], key or params["k"], params["s"], tempo or params["bpm"],
                          params["prog"], params["lead"], params["acc"],
                          params.get("bars", 16), params.get("seed", 11))
    return fn


RECIPES = {
    "love_theme": _love_theme_spec,
    "battle": _battle_spec,
}
for _name, _params in _GAME.items():
    RECIPES[_name] = _make_game_recipe(_params)


# ============================================================================
# CLI
# ============================================================================

def _cmd_recipes(_args):
    print("Recetas disponibles:")
    for name in RECIPES:
        print(f"  - {name}")


def _cmd_gen(args):
    recipe = RECIPES.get(args.recipe)
    if recipe is None:
        sys.exit(f"receta desconocida: {args.recipe} (usa 'recipes')")
    spec = recipe(key=args.key, tempo=args.tempo) if args.tempo else recipe(key=args.key)
    if args.title:
        spec["title"] = args.title
    out = args.out or (spec["title"].replace(" ", "_") + ".mid")
    _finish(spec, out, args.audio)


def _cmd_compose(args):
    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    out = args.out or (spec.get("title", "salida").replace(" ", "_") + ".mid")
    _finish(spec, out, args.audio)


def _finish(spec, out, audio):
    render_song(spec, out)
    problems, duration = validate_midi(out)
    if problems:
        print("PROBLEMAS:")
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print(f"OK MIDI y arreglo auditados -> {out}  ({duration:.2f}s, {len(spec['sections'])} secciones)")
    if audio:
        render_audio(out, audio)
        print(f"Audio -> {audio}")


def _cmd_validate(args):
    problems, duration = validate_midi(args.midi, args.expect)
    print(f"{args.midi}: {duration:.2f}s")
    if problems:
        for p in problems:
            print("  -", p)
        sys.exit(1)
    print("  sin problemas")


def _cmd_render(args):
    render_audio(args.midi, args.audio)
    print(f"OK -> {args.audio}")


def _cmd_rebuild(args):
    with open(args.perf, encoding="utf-8") as fh:
        perf = json.load(fh)
    render_performance(perf, args.out)
    problems, duration = validate_midi(args.out)
    print(f"OK -> {args.out}  ({duration:.2f}s, {len(perf.get('tracks', []))} pistas)")
    for p in problems:
        print("  -", p)
    if args.audio:
        render_audio(args.out, args.audio)
        print(f"OK -> {args.audio}")


def main(argv=None):
    p = argparse.ArgumentParser(prog="hermesmusic",
                                description="Motor unificado de composición MIDI")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("recipes").set_defaults(func=_cmd_recipes)

    g = sub.add_parser("gen", help="generar desde una receta")
    g.add_argument("--recipe", required=True)
    g.add_argument("--key", default="C")
    g.add_argument("--title", default=None)
    g.add_argument("--tempo", type=int, default=None)
    g.add_argument("-o", "--out", default=None)
    g.add_argument("--audio", default=None)
    g.set_defaults(func=_cmd_gen)

    c = sub.add_parser("compose", help="generar desde un SongSpec JSON")
    c.add_argument("spec")
    c.add_argument("-o", "--out", default=None)
    c.add_argument("--audio", default=None)
    c.set_defaults(func=_cmd_compose)

    v = sub.add_parser("validate")
    v.add_argument("midi")
    v.add_argument("--expect", type=float, default=None)
    v.set_defaults(func=_cmd_validate)

    r = sub.add_parser("render")
    r.add_argument("midi")
    r.add_argument("audio")
    r.set_defaults(func=_cmd_render)

    rb = sub.add_parser("rebuild", help="reconstruir fiel desde una performance JSON")
    rb.add_argument("perf", help="JSON de performance (miditrack_extract)")
    rb.add_argument("-o", "--out", required=True)
    rb.add_argument("--audio", default=None)
    rb.set_defaults(func=_cmd_rebuild)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
