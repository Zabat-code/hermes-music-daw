"""Discovery overrides and guard repair messages must work without Hermes home."""
import pytest

from audio_utils import executable, find_soundfont
from composition_guard import READINGS, SKILL, validate_plan
from example_dense_arrangement import decision_plan


def test_guard_readings_are_bundled():
    assert all(p.is_relative_to(SKILL) and p.is_file() for p in READINGS)


def test_soundfont_override_is_checked_at_call_time(tmp_path, monkeypatch):
    sf = tmp_path / 'font.sf2'
    sf.write_bytes(b'test')
    monkeypatch.setenv('MIDI_SOUNDFONT', str(sf))
    assert find_soundfont() == str(sf)
    monkeypatch.setenv('MIDI_SOUNDFONT', str(tmp_path / 'missing.sf2'))
    with pytest.raises(ValueError, match='MIDI_SOUNDFONT'):
        find_soundfont()


def test_invalid_binary_override_explains_repair(monkeypatch):
    monkeypatch.setenv('FLUIDSYNTH', '/nonexistent/fluidsynth')
    with pytest.raises(RuntimeError, match='Install fluidsynth or set FLUIDSYNTH'):
        executable('fluidsynth')


def test_missing_silence_message_explains_actual_score_change():
    plan = decision_plan()
    for instrument in plan['instruments']:
        instrument['silent_bars'] = 0
    with pytest.raises(ValueError, match='silent_bars>=1.*sin notas ni sustain'):
        validate_plan(plan)


def test_fill_message_reports_valid_one_based_borders():
    plan = decision_plan()
    plan['fill_bars'] = [7]
    with pytest.raises(ValueError, match='numerados desde 1.*8, 24, 32'):
        validate_plan(plan)
