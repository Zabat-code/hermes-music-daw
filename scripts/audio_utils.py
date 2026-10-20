"""Shared offline audio validation and dependency discovery (no MCP imports)."""
from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import numpy as np
from pedalboard.io import AudioFile


def executable(name: str) -> str:
    override = os.environ.get(name.upper())
    found = shutil.which(override or name)
    if not found:
        raise RuntimeError(f"Missing executable: {override or name}. Install {name} or set {name.upper()}.")
    return found


def find_soundfont() -> str | None:
    override = os.environ.get('MIDI_SOUNDFONT')
    if override:
        path = Path(override).expanduser()
        if not path.is_file():
            raise ValueError(f"MIDI_SOUNDFONT does not point to a file: {path}")
        return str(path.resolve())
    candidates = [Path(p) for p in (
        '/usr/share/sounds/sf2/FluidR3_GM.sf2',
        '/usr/share/sounds/sf2/TimGM6mb.sf2',
        '/usr/share/sounds/sf2/default-GM.sf2',
        '/usr/local/share/soundfonts/FluidR3_GM.sf2',
    )]
    for directory in (Path('/usr/share/sounds/sf2'), Path('/usr/share/soundfonts'),
                      Path.home() / '.local/share/soundfonts'):
        candidates.extend(sorted(directory.glob('*.sf2')))
    return next((str(p.resolve()) for p in candidates if p.is_file()), None)


def positive(value: float, name: str) -> float:
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and greater than zero')
    return value


def load_audio(path: str | Path, target_sr: int | None = None) -> tuple[np.ndarray, int]:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f'Audio file does not exist: {path}')
    try:
        with AudioFile(str(path)) as f:
            if target_sr and f.samplerate != target_sr:
                with f.resampled_to(target_sr) as resampled:
                    data, sr = resampled.read(resampled.frames), target_sr
            else:
                data, sr = f.read(f.frames), int(f.samplerate)
    except Exception as exc:
        raise ValueError(f'Cannot decode audio file {path}: {exc}') from exc
    if data.size == 0:
        raise ValueError(f'Empty audio (zero frames): {path}')
    if not np.isfinite(data).all():
        raise ValueError(f'Audio contains NaN or infinity: {path}')
    if not np.any(np.abs(data) > 1e-10):
        raise ValueError(f'Silent audio (no signal): {path}')
    if data.shape[0] not in (1, 2):
        raise ValueError(f'Only mono/stereo audio is supported: {path}')
    return data.astype(np.float32), int(sr)


def wav_files(directory: str | Path) -> list[Path]:
    directory = Path(directory)
    if not directory.is_dir():
        raise ValueError(f'Stems directory does not exist: {directory}')
    files = sorted(directory.glob('*.wav'))
    if not files:
        raise ValueError(f'No WAV stems in {directory}')
    return files


def output_path(out: str | Path, *inputs: str | Path) -> Path:
    path = Path(out)
    if path.suffix.lower() != '.wav':
        raise ValueError(f'Output must be a .wav file: {path}')
    if any(path.resolve() == Path(p).resolve() for p in inputs):
        raise ValueError(f'Output must differ from input: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def write_audio(out: str | Path, data: np.ndarray, sr: int) -> None:
    out = output_path(out)
    with tempfile.TemporaryDirectory(prefix='.audio-', dir=out.parent) as work:
        tmp = Path(work) / 'output.wav'
        with AudioFile(str(tmp), 'w', sr, data.shape[0], bit_depth=32) as f:
            f.write(data)
        os.replace(tmp, out)


def run_process(argv: list[str]) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    # FluidSynth enumerates SDL devices even for -F/--version. Avoid contacting
    # PulseAudio in an offline render (can hang in containers without audio IPC).
    if Path(argv[0]).name == 'fluidsynth':
        env.setdefault('SDL_AUDIODRIVER', 'dummy')
    try:
        return subprocess.run(argv, capture_output=True, text=True, check=True, timeout=300, env=env)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f'{Path(argv[0]).name} failed (exit {exc.returncode}): '
                           f'{(exc.stderr or exc.stdout)[-2000:]}') from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f'{Path(argv[0]).name} timed out after 300 seconds') from exc


def loudness(path: str | Path, target: float = -12.0) -> dict:
    """Measure EBU R128 integrated LUFS, oversampled true peak and LRA via FFmpeg."""
    result = run_process([executable('ffmpeg'), '-hide_banner', '-nostdin', '-i', str(path),
                          '-af', f'loudnorm=I={target}:TP=-1:LRA=11:print_format=json',
                          '-f', 'null', '-'])
    matches = re.findall(r'\{\s*"input_i".*?\}', result.stderr, re.S)
    if not matches:
        raise RuntimeError('FFmpeg did not return loudnorm measurements')
    raw = json.loads(matches[-1])
    if not all(math.isfinite(float(raw[k])) for k in ('input_i', 'input_tp', 'input_lra')):
        raise ValueError(f'Audio too short or quiet to measure integrated loudness: {path}')
    return {'integrated_lufs': float(raw['input_i']), 'true_peak_dbfs': float(raw['input_tp']),
            'lra_lu': float(raw['input_lra']), 'raw': raw}
