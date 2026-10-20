#!/usr/bin/env python3
"""Headless mixing engine - foundation of the DAW MCP.

Takes WAV stems and applies a configurable mixing chain per role (HPF, EQ,
compression), stereo balance, and a master bus with tonal EQ + bus
compression + sample limiter. All using Pedalboard (Spotify), 100% headless.

Usage:
    python3 mix_engine.py --stems <dir> --out mix.wav [--profile power_metal]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from pedalboard import (Compressor, Gain, HighShelfFilter, HighpassFilter,
                        Limiter, LowShelfFilter, PeakFilter, Pedalboard)
from pedalboard.io import AudioFile

if __package__:
    from .audio_utils import load_audio, output_path, positive, wav_files, write_audio
else:
    from audio_utils import load_audio, output_path, positive, wav_files, write_audio

SR = 44100

# --- genre profiles: engineering starting points, not absolute truth ---
# Based on common practice: HPF per role to avoid masking, guitar
# presence, gentle bus compression, sample limiter at -1 dBFS.
PROFILES = {
    'power_metal': {
        'roles': {
            'drums':      {'hpf': 35,  'comp': (-12, 3.0, 5, 80),   'gain': 1.5, 'pan': 0.0,  'lvl': 0.95},
            'electric_bass': {'hpf': 40, 'low_shelf': (120, 3.0), 'comp': (-14, 4.0, 8, 100), 'pan': 0.0, 'lvl': 0.90},
            'rhythm_guitar_L': {'hpf': 90, 'presence': (2400, 2.5), 'comp': (-16, 2.5, 10, 120), 'pan': -0.55, 'lvl': 0.72},
            'rhythm_guitar_R': {'hpf': 90, 'presence': (2400, 2.5), 'comp': (-16, 2.5, 10, 120), 'pan': 0.55,  'lvl': 0.72},
            'lead_guitar_L': {'hpf': 200, 'presence': (3200, 3.0), 'comp': (-18, 3.0, 6, 90), 'pan': -0.30, 'lvl': 0.60},
            'lead_guitar_R': {'hpf': 200, 'presence': (3200, 3.0), 'comp': (-18, 3.0, 6, 90), 'pan': 0.30,  'lvl': 0.60},
            'lead_guitar': {'hpf': 200, 'presence': (3200, 3.0), 'comp': (-18, 3.0, 6, 90), 'pan': 0.0, 'lvl': 0.60},
            'synth_piano': {'hpf': 180, 'presence': (1800, 1.0), 'comp': (-20, 2.0, 12, 130), 'pan': 0.15, 'lvl': 0.45},
        },
        'master': {'hpf': 28, 'mud': (300, -1.5), 'air': (8000, 1.5),
                   'comp': (-10, 2.0, 20, 200), 'limiter': -1.0},
    },
    'balanced': {
        'roles': {
            'drums':      {'hpf': 30,  'comp': (-14, 2.5, 8, 90),  'gain': 0.0, 'pan': 0.0, 'lvl': 0.90},
            'electric_bass': {'hpf': 38, 'low_shelf': (100, 2.0), 'comp': (-16, 3.0, 10, 110), 'pan': 0.0, 'lvl': 0.85},
            'rhythm_guitar_L': {'hpf': 80, 'presence': (2000, 1.5), 'comp': (-18, 2.0, 12, 130), 'pan': -0.50, 'lvl': 0.68},
            'rhythm_guitar_R': {'hpf': 80, 'presence': (2000, 1.5), 'comp': (-18, 2.0, 12, 130), 'pan': 0.50,  'lvl': 0.68},
            'lead_guitar_L': {'hpf': 180, 'presence': (2800, 2.0), 'comp': (-20, 2.5, 8, 100), 'pan': -0.25, 'lvl': 0.58},
            'lead_guitar_R': {'hpf': 180, 'presence': (2800, 2.0), 'comp': (-20, 2.5, 8, 100), 'pan': 0.25,  'lvl': 0.58},
            'lead_guitar': {'hpf': 180, 'presence': (2800, 2.0), 'comp': (-20, 2.5, 8, 100), 'pan': 0.0, 'lvl': 0.58},
            'synth_piano': {'hpf': 150, 'presence': (1800, 0.5), 'comp': (-22, 1.8, 15, 150), 'pan': 0.10, 'lvl': 0.48},
        },
        'master': {'hpf': 25, 'mud': (250, -1.0), 'air': (9000, 1.0),
                   'comp': (-12, 1.8, 25, 220), 'limiter': -1.0},
    },
}


def load_stem(path: Path, n: int) -> np.ndarray:
    data, _ = load_audio(path, SR)
    if data.shape[0] == 1:
        data = np.repeat(data, 2, axis=0)
    if data.shape[1] < n:
        data = np.pad(data, ((0, 0), (0, n - data.shape[1])))
    return data[:, :n].astype(np.float32)


def build_role_chain(cfg: dict) -> Pedalboard:
    fx = [HighpassFilter(cutoff_frequency_hz=cfg['hpf'])]
    if 'low_shelf' in cfg:
        f, g = cfg['low_shelf']
        fx.append(LowShelfFilter(cutoff_frequency_hz=f, gain_db=g, q=0.7))
    if 'presence' in cfg:
        f, g = cfg['presence']
        fx.append(PeakFilter(cutoff_frequency_hz=f, gain_db=g, q=1.1))
    t, r, a, rel = cfg['comp']
    fx.append(Compressor(threshold_db=t, ratio=r, attack_ms=a, release_ms=rel))
    if cfg.get('gain'):
        fx.append(Gain(gain_db=cfg['gain']))
    return Pedalboard(fx)


def build_master_chain(cfg: dict) -> Pedalboard:
    mf, mg = cfg['mud']
    af, ag = cfg['air']
    t, r, a, rel = cfg['comp']
    return Pedalboard([
        HighpassFilter(cutoff_frequency_hz=cfg['hpf']),
        PeakFilter(cutoff_frequency_hz=mf, gain_db=mg, q=0.8),
        HighShelfFilter(cutoff_frequency_hz=af, gain_db=ag),
        Compressor(threshold_db=t, ratio=r, attack_ms=a, release_ms=rel),
        # Headroom before the limiter; the floating-point sum can exceed 0 dBFS.
        Gain(gain_db=cfg.get('trim', -3.0)),
        Limiter(threshold_db=cfg['limiter'], release_ms=80),
    ])


def pan(sig: np.ndarray, pos: float) -> np.ndarray:
    """Linear stereo balance: negative attenuates right, positive attenuates left."""
    if not np.isfinite(pos) or not -1 <= pos <= 1:
        raise ValueError('pan must be between -1 and 1')
    l = sig[0] * (1.0 - max(0.0, pos))
    r = sig[1] * (1.0 - max(0.0, -pos))
    return np.stack([l, r])


def mix(stems_dir: Path, out_path: Path, profile: str = 'power_metal',
        duration: float | None = None) -> dict:
    prof = PROFILES.get(profile)
    if prof is None:
        raise ValueError(f'unknown profile: {profile!r}; available profiles: {sorted(PROFILES)}')

    files = {p.stem: p for p in wav_files(stems_dir)}
    known = [n for n in prof['roles'] if n in files]
    unknown = [n for n in files if n not in prof['roles']]
    if not known:
        raise ValueError(f'no stems match the profile; available stems: {sorted(files)}')
    if unknown:
        raise ValueError(f'Stems not in profile {profile!r}: {sorted(unknown)}; '
                         f'expected roles: {sorted(prof["roles"])}. Rename or define a profile; no stems are silently dropped.')
    output_path(out_path, *files.values())

    # shared duration
    if duration is None:
        lengths = []
        for path in files.values():
            try:
                with AudioFile(str(path)) as f:
                    if not f.frames:
                        raise ValueError(f'Empty audio (zero frames): {path}')
                    lengths.append(f.frames / f.samplerate)
            except Exception as exc:
                raise ValueError(f'Cannot decode audio file {path}: {exc}') from exc
        duration = max(lengths)
    n = int(positive(duration, 'duration') * SR)
    if n < 1:
        raise ValueError('duration must contain at least one sample')
    mix_bus = np.zeros((2, n), dtype=np.float32)
    applied = {}
    for name in known:
        cfg = prof['roles'][name]
        sig = build_role_chain(cfg)(load_stem(files[name], n), SR)
        mix_bus += pan(sig, cfg['pan']) * cfg['lvl']
        applied[name] = {'hpf': cfg['hpf'], 'pan': cfg['pan'], 'lvl': cfg['lvl']}

    final = build_master_chain(prof['master'])(mix_bus, SR)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    write_audio(out_path, final, SR)

    peak = float(np.abs(final).max())
    rms = float(np.sqrt(np.mean(final ** 2)))
    return {
        'out': str(out_path), 'profile': profile,
        'stems_used': sorted(known), 'stems_ignored': sorted(unknown),
        'seconds': round(final.shape[1] / SR, 3),
        'peak': round(peak, 5),
        'peak_db': round(20 * np.log10(peak + 1e-12), 2),
        'rms_db': round(20 * np.log10(rms + 1e-12), 2),
        'chain': applied,
        'note': 'The profile provides engineering starting points, not an absolute '
                'truth. The final decision requires human listening.',
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stems', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--profile', default='power_metal', choices=sorted(PROFILES))
    ap.add_argument('--duration', type=float, default=None, help='seconds; default: longest stem')
    a = ap.parse_args()
    try:
        print(json.dumps(mix(Path(a.stems), Path(a.out), a.profile, a.duration),
                         ensure_ascii=False, indent=2))
    except (ValueError, RuntimeError, OSError) as exc:
        ap.exit(1, f'ERROR: {exc}\n')


if __name__ == '__main__':
    main()
