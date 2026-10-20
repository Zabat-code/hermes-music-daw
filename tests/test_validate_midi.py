"""Tests de regresión para validate_midi en hermesmusic.py.

Caso histórico: validate_midi usaba como clave de notas abiertas solo el
pitch (msg.note), sin canal. Dos notas del mismo pitch en CANALES distintos
solapadas (legal en MIDI) se reportaban como "re-disparo sin note_off".
Corregido el 2026-10-19: la clave es (channel, note).
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

mido = pytest.importorskip("mido")
from mido import Message, MidiFile, MidiTrack  # noqa: E402

from hermesmusic import validate_midi  # noqa: E402


def _save(msgs, path):
    mid = MidiFile(type=1, ticks_per_beat=480)
    tr = MidiTrack()
    mid.tracks.append(tr)
    for m in msgs:
        tr.append(m)
    mid.save(path)
    return path


def test_mismo_pitch_en_canales_distintos_no_es_error(tmp_path):
    """Solape del mismo pitch en canales distintos es legal: sin problemas."""
    p = _save(
        [
            Message("note_on", note=60, velocity=80, channel=0, time=0),
            Message("note_on", note=60, velocity=80, channel=1, time=0),
            Message("note_off", note=60, velocity=0, channel=0, time=480),
            Message("note_off", note=60, velocity=0, channel=1, time=480),
        ],
        str(tmp_path / "twoch.mid"),
    )
    problems, _ = validate_midi(p)
    assert problems == [], f"falso positivo: {problems}"


def test_mismo_pitch_mismo_canal_solapado_si_es_error(tmp_path):
    """Solape del mismo pitch en el MISMO canal debe seguir detectándose."""
    p = _save(
        [
            Message("note_on", note=60, velocity=80, channel=0, time=0),
            Message("note_on", note=60, velocity=80, channel=0, time=0),
            Message("note_off", note=60, velocity=0, channel=0, time=480),
            Message("note_off", note=60, velocity=0, channel=0, time=480),
        ],
        str(tmp_path / "samech.mid"),
    )
    problems, _ = validate_midi(p)
    assert any("re-disparo" in x for x in problems), problems


def test_archivo_con_metaeventos_no_revienta(tmp_path):
    """MetaMessage no tiene .channel/.note: no debe lanzar AttributeError."""
    p = _save(
        [
            Message("note_on", note=64, velocity=90, channel=0, time=0),
            Message("note_off", note=64, velocity=0, channel=0, time=480),
        ],
        str(tmp_path / "meta.mid"),
    )
    problems, duration = validate_midi(p)
    assert problems == [], problems
    assert duration >= 0
