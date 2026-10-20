"""Regression tests for validate_midi in hermesmusic.py.

Historical case: validate_midi keyed open notes only by
pitch (msg.note), without the channel. Two overlapping notes of the same pitch
on different CHANNELS (legal in MIDI) were reported as "retrigger without note_off".
Fixed on 2026-10-19: the key is (channel, note).
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
    """Overlapping notes of the same pitch on different channels are legal: no problems."""
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
    assert problems == [], f"false positive: {problems}"


def test_mismo_pitch_mismo_canal_solapado_si_es_error(tmp_path):
    """Overlapping notes of the same pitch on the SAME channel must still be detected."""
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
    assert any("retrigger" in x for x in problems), problems


def test_archivo_con_metaeventos_no_revienta(tmp_path):
    """MetaMessage has no .channel/.note: must not raise AttributeError."""
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
