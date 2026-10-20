"""Exercise actual Pedalboard chains, channel handling and trimming."""
import numpy as np
from pedalboard.io import AudioFile
import pytest

from mix_engine import PROFILES, SR, load_stem, mix, pan


@pytest.mark.parametrize('profile', sorted(PROFILES))
def test_profiles_mix_all_stems(make_wav, tmp_path, profile):
    stems = tmp_path / 'stems'
    for i, role in enumerate(PROFILES[profile]['roles']):
        make_wav(f'stems/{role}.wav', frequency=110 * (i + 1), amplitude=.04)
    out = tmp_path / 'mix.wav'
    result = mix(stems, out, profile)
    assert result['stems_used'] == sorted(PROFILES[profile]['roles'])
    assert result['stems_ignored'] == []
    assert result['seconds'] == 1
    assert result['peak'] < 1
    with AudioFile(str(out)) as f:
        assert f.samplerate == SR and f.num_channels == 2 and f.frames == SR
        assert np.abs(f.read(f.frames)).max() > .001


def test_pan_direction_and_center():
    data = np.ones((2, 32), dtype=np.float32)
    np.testing.assert_array_equal(pan(data, 0), data)
    np.testing.assert_array_equal(pan(data, -1), np.array([np.ones(32), np.zeros(32)]))
    assert pan(data, .6)[0].mean() < pan(data, .6)[1].mean()
    with pytest.raises(ValueError, match='pan'):
        pan(data, 1.1)


def test_mono_and_resampling_preserve_duration(make_wav, tmp_path):
    path = make_wav('stems/electric_bass.wav', sr=22050, mono=True)
    loaded = load_stem(path, SR)
    assert loaded.shape == (2, SR)
    np.testing.assert_array_equal(loaded[0], loaded[1])
    result = mix(path.parent, tmp_path / 'mix.wav')
    assert result['seconds'] == 1


@pytest.mark.parametrize('duration', [.25, 1.5])
def test_trim_and_pad(make_wav, tmp_path, duration):
    make_wav('stems/electric_bass.wav')
    result = mix(tmp_path / 'stems', tmp_path / 'mix.wav', duration=duration)
    assert result['seconds'] == duration
    with AudioFile(str(tmp_path / 'mix.wav')) as f:
        assert f.frames == round(duration * SR)


def test_load_stem_padding_is_silent(make_wav):
    path = make_wav(seconds=.2)
    data = load_stem(path, SR)
    assert np.all(data[:, SR // 5:] == 0)


def test_bad_profile(tmp_path):
    with pytest.raises(ValueError, match='perfil desconocido'):
        mix(tmp_path, tmp_path / 'out.wav', 'unlisted')


def test_empty_and_missing_directory(tmp_path):
    with pytest.raises(ValueError, match='No WAV'):
        mix(tmp_path, tmp_path / 'out.wav')
    with pytest.raises(ValueError, match='directory does not exist'):
        mix(tmp_path / 'missing', tmp_path / 'out.wav')


def test_unmatched_and_partially_matched_stems_abort(make_wav, tmp_path):
    make_wav('stems/unknown.wav')
    with pytest.raises(ValueError, match='ningún stem coincide'):
        mix(tmp_path / 'stems', tmp_path / 'out.wav')
    make_wav('stems/drums.wav')
    with pytest.raises(ValueError, match='not in profile'):
        mix(tmp_path / 'stems', tmp_path / 'out.wav')
    assert not (tmp_path / 'out.wav').exists()


@pytest.mark.parametrize('duration', [0, -1, float('nan'), float('inf')])
def test_invalid_duration(make_wav, tmp_path, duration):
    make_wav('stems/electric_bass.wav')
    with pytest.raises(ValueError, match='duration'):
        mix(tmp_path / 'stems', tmp_path / 'out.wav', duration=duration)


@pytest.mark.parametrize('kind', ['corrupt', 'empty', 'silent'])
def test_bad_stem(make_wav, tmp_path, kind):
    path = make_wav('stems/electric_bass.wav', seconds=0 if kind == 'empty' else 1,
                    silent=kind == 'silent')
    if kind == 'corrupt':
        path.write_bytes(b'this is not a WAV')
    with pytest.raises(ValueError, match='decode|Empty|Silent'):
        mix(path.parent, tmp_path / 'out.wav', duration=1)
    with pytest.raises(ValueError, match='decode|Empty|Silent'):
        mix(path.parent, tmp_path / 'out.wav')


def test_output_cannot_destroy_input(make_wav):
    path = make_wav('stems/electric_bass.wav')
    original = path.read_bytes()
    with pytest.raises(ValueError, match='differ from input'):
        mix(path.parent, path)
    assert path.read_bytes() == original
