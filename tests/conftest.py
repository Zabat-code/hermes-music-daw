"""Self-contained audio fixtures; no desktop projects or downloaded media."""
from pathlib import Path
import sys

import numpy as np
from pedalboard.io import AudioFile
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))


@pytest.fixture
def make_wav(tmp_path):
    def make(name='tone.wav', *, seconds=1.0, sr=44100, mono=False, amplitude=.2,
             frequency=440, silent=False):
        t = np.arange(round(seconds * sr)) / sr
        left = amplitude * np.sin(2 * np.pi * frequency * t)
        right = .8 * left + amplitude * .5 * np.sin(2 * np.pi * (frequency * 1.5) * t)
        data = left[None, :] if mono else np.array([left, right])
        if silent:
            data[:] = 0
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with AudioFile(str(path), 'w', sr, data.shape[0], bit_depth=32) as f:
            f.write(data.astype(np.float32))
        return path
    return make


@pytest.fixture
def midi_file(tmp_path):
    import mido
    path = tmp_path / 'test.mid'
    midi = mido.MidiFile()
    midi.tracks.append(mido.MidiTrack([
        mido.MetaMessage('set_tempo', tempo=500000),
        mido.MetaMessage('end_of_track', time=960)]))
    midi.tracks.append(mido.MidiTrack([
        mido.MetaMessage('track_name', name='electric_bass'),
        mido.Message('program_change', channel=0, program=34),
        mido.Message('note_on', channel=0, note=40, velocity=85),
        mido.Message('note_off', channel=0, note=40, time=480)]))
    midi.save(path)
    return path
