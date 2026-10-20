"""All ten tools process generated media, including a real stdio MCP session."""
import asyncio
import json
import os
from pathlib import Path
import sys

import mido
import numpy as np
import pytest

import daw_mcp as daw
from audio_utils import executable, find_soundfont, load_audio, write_audio


def audio_dependencies():
    try:
        executable('fluidsynth')
        executable('ffmpeg')
        if not find_soundfont():
            raise RuntimeError('No SoundFont')
    except (RuntimeError, ValueError) as exc:
        pytest.skip(str(exc))


def test_analysis_measures_signal_and_mono(make_wav):
    result = daw.analyze_audio(str(make_wav(mono=True, amplitude=.25)))
    assert result['channels'] == 1 and result['seconds'] == 1
    assert result['peak'] == pytest.approx(.25, abs=1e-4)
    assert result['rms_db'] == pytest.approx(-15.05, abs=.05)
    assert result['stereo_correlation'] == 1
    assert result['octave_bands_db']['500Hz'] > result['octave_bands_db']['8000Hz']


def test_masking_and_reference_comparison(make_wav, tmp_path):
    a = make_wav('stems/a.wav')
    b = make_wav('stems/b.wav', amplitude=.1)
    result = daw.analyze_masking(str(a.parent), top=1)
    assert len(result['top_overlaps']) == 1
    assert result['top_overlaps'][0]['overlap'] > .99
    compared = daw.compare_to_reference(str(a), str(b))
    assert compared['rms_delta_db'] == pytest.approx(-6.02, abs=.02)
    assert compared['band_delta_db']['500Hz'] == pytest.approx(-6.02, abs=.02)
    with pytest.raises(ValueError, match='top'):
        daw.analyze_masking(str(a.parent), 0)


@pytest.mark.parametrize('band', ['peak', 'low_shelf', 'high_shelf', 'highpass'])
def test_eq_writes_processed_audio(make_wav, tmp_path, band):
    source = make_wav(frequency=1000)
    result = daw.apply_eq(str(source), str(tmp_path / 'eq.wav'), band, 1000, 6)
    assert result['after']['seconds'] == result['before']['seconds']
    assert result['applied']['band'] == band
    if band == 'peak':
        assert result['after']['rms_db'] > result['before']['rms_db'] + 4


def test_compressor_reduces_hot_signal(make_wav, tmp_path):
    result = daw.apply_comp(str(make_wav(amplitude=.8)), str(tmp_path / 'comp.wav'), -24, 6)
    assert result['after']['rms_db'] < result['before']['rms_db'] - 5


@pytest.mark.integration
def test_master_uses_lufs_target_and_release_measures_true_peak(make_wav, tmp_path):
    executable('ffmpeg')
    source = str(make_wav(seconds=2))
    outputs = [daw.master(source, str(tmp_path / f'master{i}.wav'), target, 'balanced')
               for i, target in enumerate([-16, -20])]
    for target, result in zip([-16, -20], outputs):
        assert result['target_met']
        assert result['loudness']['integrated_lufs'] == pytest.approx(target, abs=.3)
        assert result['loudness']['true_peak_dbfs'] <= -.9
    check = daw.release_check(outputs[0]['out'], 'balanced')
    assert check['verdict'] == 'ready'
    assert check['loudness']['integrated_lufs'] == outputs[0]['loudness']['integrated_lufs']


@pytest.mark.parametrize('profile', ['does-not-exist'])
def test_unknown_profiles_are_clear(make_wav, tmp_path, profile):
    source = str(make_wav())
    for call in (lambda: daw.master(source, str(tmp_path / 'out.wav'), profile=profile),
                 lambda: daw.release_check(source, profile)):
        with pytest.raises(ValueError, match='Unknown profile'):
            call()


@pytest.mark.parametrize('kind', ['missing', 'corrupt', 'empty', 'silent'])
def test_bad_audio_errors(make_wav, tmp_path, kind):
    path = make_wav(seconds=0 if kind == 'empty' else 1, silent=kind == 'silent')
    if kind == 'corrupt':
        path.write_bytes(b'not audio')
    if kind == 'missing':
        path.unlink()
    for call in (lambda: daw.analyze_audio(str(path)),
                 lambda: daw.apply_eq(str(path), str(tmp_path / 'eq.wav')),
                 lambda: daw.apply_comp(str(path), str(tmp_path / 'comp.wav')),
                 lambda: daw.master(str(path), str(tmp_path / 'master.wav')),
                 lambda: daw.release_check(str(path)),
                 lambda: daw.compare_to_reference(str(path), str(path))):
        with pytest.raises(ValueError, match='does not exist|decode|Empty|Silent'):
            call()


def test_invalid_processing_arguments(make_wav, tmp_path):
    path, out = str(make_wav()), str(tmp_path / 'out.wav')
    for kwargs in ({'freq': -1}, {'freq': 30000}, {'band': 'bad'}, {'q': 0}, {'gain_db': float('nan')}):
        with pytest.raises(ValueError):
            daw.apply_eq(path, out, **kwargs)
    for kwargs in ({'ratio': .5}, {'attack_ms': 0}, {'release_ms': -1}):
        with pytest.raises(ValueError):
            daw.apply_comp(path, out, **kwargs)
    with pytest.raises(ValueError, match='target_lufs'):
        daw.master(path, out, target_lufs=0)
    with pytest.raises(ValueError, match='differ from input'):
        daw.apply_eq(path, path)


def test_midi_errors_are_clear(midi_file, tmp_path):
    with pytest.raises(ValueError, match='does not exist'):
        daw.render_stems(str(tmp_path / 'missing.mid'), str(tmp_path / 'stems'))
    bad = tmp_path / 'corrupt.mid'
    bad.write_bytes(b'not midi')
    with pytest.raises(ValueError, match='Cannot decode MIDI'):
        daw.render_stems(str(bad), str(tmp_path / 'stems'))
    midi = mido.MidiFile(midi_file)
    midi.tracks[1].name = '../../escape'
    midi.save(bad)
    with pytest.raises(ValueError, match='safe filenames'):
        daw.render_stems(str(bad), str(tmp_path / 'stems'))


def test_render_failure_is_not_success(midi_file, tmp_path, monkeypatch):
    monkeypatch.setattr(daw, 'find_soundfont', lambda: '/test/font.sf2')
    monkeypatch.setattr(daw, 'executable', lambda name: name)
    def fail(argv):
        raise RuntimeError('fluidsynth failed (exit 1): invalid SoundFont')
    monkeypatch.setattr(daw, 'run_process', fail)
    with pytest.raises(RuntimeError, match='fluidsynth failed'):
        daw.render_stems(str(midi_file), str(tmp_path / 'stems'))
    assert not (tmp_path / 'stems').exists()


def test_render_preserves_tempo_map_and_late_notes(midi_file, tmp_path, monkeypatch):
    midi = mido.MidiFile(midi_file)
    midi.tracks[0] = mido.MidiTrack([
        mido.MetaMessage('marker', text='not copied', time=240),
        mido.MetaMessage('set_tempo', tempo=600000, time=240),
        mido.MetaMessage('end_of_track', time=480)])
    midi.tracks[1][2].time = 480
    midi.save(midi_file)
    monkeypatch.setattr(daw, 'find_soundfont', lambda: '/test/font.sf2')
    monkeypatch.setattr(daw, 'executable', lambda name: name)
    def inspect_render(argv):
        rendered = mido.MidiFile(argv[-1])
        tick = 0
        tempos = []
        for msg in rendered.tracks[0]:
            tick += msg.time
            if msg.type == 'set_tempo':
                tempos.append(tick)
        assert tempos == [480]
        assert next(msg.time for msg in rendered.tracks[1] if msg.type == 'note_on') == 480
        t = np.arange(44100) / 44100
        write_audio(argv[argv.index('-F') + 1], np.array([.1 * np.sin(2 * np.pi * 440 * t)], dtype=np.float32), 44100)
    monkeypatch.setattr(daw, 'run_process', inspect_render)
    assert daw.render_stems(str(midi_file), str(tmp_path / 'stems'))['count'] == 1


@pytest.mark.integration
def test_all_ten_tools_over_real_stdio_mcp(make_wav, midi_file, tmp_path):
    audio_dependencies()
    from fastmcp import Client
    from fastmcp.client.transports import PythonStdioTransport
    source = str(make_wav('input.wav', seconds=2))
    stems = tmp_path / 'mix_stems'
    make_wav('mix_stems/electric_bass.wav', seconds=2)
    calls = [
        ('list_profiles', {}),
        ('render_stems', {'midi_path': str(midi_file), 'out_dir': str(tmp_path / 'rendered')}),
        ('analyze_audio', {'path': source}),
        ('analyze_masking', {'stems_dir': str(stems)}),
        ('auto_mix', {'stems_dir': str(stems), 'out': str(tmp_path / 'mix.wav'), 'duration': 2}),
        ('apply_eq', {'path': source, 'out': str(tmp_path / 'eq.wav'), 'gain_db': 3}),
        ('apply_comp', {'path': source, 'out': str(tmp_path / 'comp.wav')}),
        ('master', {'path': source, 'out': str(tmp_path / 'master.wav'), 'target_lufs': -16}),
        ('compare_to_reference', {'a': source, 'b': str(tmp_path / 'eq.wav')}),
        ('release_check', {'path': str(tmp_path / 'master.wav')}),
    ]
    async def run():
        # This test also runs in a sandbox that denies socketpair.send(). Keep
        # the client and server loops awake there; wire traffic is still real MCP.
        async def tick():
            while True:
                await asyncio.sleep(.05)
        heartbeat = asyncio.create_task(tick())
        env = dict(os.environ, HERMES_DAW_STDIO_POLL='1')
        transport = PythonStdioTransport(Path(daw.__file__), python_cmd=sys.executable,
                                         cwd=str(tmp_path), env=env)
        async with Client(transport, timeout=120) as client:
            listed = await client.list_tools()
            assert {t.name for t in listed} == {fn.__name__ for fn in daw.TOOLS}
            assert all(t.description and len(t.description) > 60 for t in listed)
            for name, args in calls:
                result = await client.call_tool(name, args)
                assert not result.is_error, (name, result)
                data = result.data
                assert isinstance(data, dict) and data, (name, result)
                if name == 'render_stems':
                    assert data['count'] == 1
                    assert (tmp_path / 'rendered/electric_bass.wav').is_file()
                if name == 'master':
                    assert data['target_met']
            error = await client.call_tool('analyze_audio', {'path': str(tmp_path / 'missing.wav')}, raise_on_error=False)
            assert error.is_error
            assert 'does not exist' in str(error.content)
        heartbeat.cancel()
    asyncio.run(run())
