#!/usr/bin/env python3
"""hermes-daw-mcp - headless mixing and mastering MCP.

Audio engineering assistant: measure, apply known chains, and MEASURE AGAIN.
Does not judge aesthetics; brings the mix to a measurable, consistent starting point.

Tools:
  list_profiles        available mix profiles
  render_stems         split a MIDI file into a WAV per instrument
  analyze_audio        peak, RMS, spectrum, stereo correlation, octave bands
  analyze_masking      rank spectral similarity between stem pairs (heuristic)
  auto_mix             apply the profile chain and return output metrics
  apply_eq             targeted EQ on a file
  apply_comp           targeted compression on a file
  master               mastering chain with a loudness target
  compare_to_reference compare sample peak, RMS, band energies and stereo metrics
  release_check        ready/needs-work verdict

Usage: python3 daw_mcp.py  (stdio)   |   --selftest (test without MCP)
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
from pedalboard import (Compressor, Gain, HighShelfFilter, HighpassFilter,
                        Limiter, LowShelfFilter, PeakFilter, Pedalboard)

if __package__:
    from .mix_engine import PROFILES, SR, mix as _mix
    from .audio_utils import (executable, find_soundfont, load_audio, loudness,
                              output_path, positive, run_process, wav_files, write_audio)
else:
    from mix_engine import PROFILES, SR, mix as _mix
    from audio_utils import (executable, find_soundfont, load_audio, loudness,
                             output_path, positive, run_process, wav_files, write_audio)


# ---------------------------------------------------------------- measurement ---
def _load(path: str) -> tuple[np.ndarray, int]:
    return load_audio(path)


def _profile(name: str) -> dict:
    if name not in PROFILES:
        raise ValueError(f'Unknown profile {name!r}; choose from {sorted(PROFILES)}')
    return PROFILES[name]


def _octave_bands(data: np.ndarray, sr: int) -> dict:
    """Energy per octave band (center frequency in Hz)."""
    mono = data.mean(axis=0)
    n = len(mono)
    if n == 0:
        return {}
    # Normalize window and length so comparisons do not simply track file duration.
    window = np.hanning(n)
    power = np.abs(np.fft.rfft(mono * window)) ** 2 / max(n * float((window ** 2).sum()), 1e-12)
    freqs = np.fft.rfftfreq(n, 1 / sr)
    centers = [31.25, 62.5, 125, 250, 500, 1000, 2000, 4000, 8000, 16000]
    out = {}
    for c in centers:
        lo, hi = c / math.sqrt(2), c * math.sqrt(2)
        mask = (freqs >= lo) & (freqs < hi)
        e = float(power[mask].sum())
        out[f'{c:g}Hz'] = round(10 * math.log10(e + 1e-24), 2)
    return out


def _stereo_correlation(data: np.ndarray) -> float:
    if data.shape[0] < 2:
        return 1.0
    l, r = data[0], data[1]
    if l.std() < 1e-9 or r.std() < 1e-9:
        return 1.0
    return round(float(np.corrcoef(l, r)[0, 1]), 4)


def analyze_audio(path: str) -> dict:
    """Use before/after processing a WAV: return duration, sample peak, RMS dBFS,
    stereo correlation and normalized octave-band energy. Does not measure LUFS
    or true peak; use release_check for FFmpeg EBU R128 measurements.
    """
    data, sr = _load(path)
    peak = float(np.abs(data).max())
    rms = float(np.sqrt(np.mean(data ** 2)))
    return {
        'file': str(path),
        'seconds': round(data.shape[1] / sr, 3),
        'sample_rate': sr,
        'channels': int(data.shape[0]),
        'peak': round(peak, 5),
        'peak_db': round(20 * math.log10(peak + 1e-12), 2),
        'rms_db': round(20 * math.log10(rms + 1e-12), 2),
        'clipping': peak >= 0.999,
        'stereo_correlation': _stereo_correlation(data),
        'octave_bands_db': _octave_bands(data, sr),
    }


def analyze_masking(stems_dir: str, top: int = 8) -> dict:
    """Use to investigate competing stems. Return names and up to top pairs ranked
    by octave-energy correlation (-1..1). This heuristic cannot prove audibility.
    """
    if type(top) is not int or top < 1:
        raise ValueError('top must be a positive integer')
    files = wav_files(stems_dir)
    bands = {}
    for p in files:
        d, sr = _load(str(p))
        bands[p.stem] = _octave_bands(d, sr)
    names = list(bands)
    pairs = []
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = bands[names[i]], bands[names[j]]
            keys = sorted(a.keys() & b.keys())
            # normalized overlap: how closely the spectral profiles match
            va = np.array([a[k] for k in keys])
            vb = np.array([b[k] for k in keys])
            va = va - va.mean(); vb = vb - vb.mean()
            denom = (np.linalg.norm(va) * np.linalg.norm(vb))
            score = float(np.dot(va, vb) / denom) if denom > 1e-9 else 0.0
            pairs.append({'pair': f'{names[i]} + {names[j]}', 'overlap': round(score, 3)})
    pairs.sort(key=lambda x: -x['overlap'])
    return {
        'stems': names,
        'top_overlaps': pairs[:top],
        'note': 'Spectral overlap heuristic. Does NOT prove that an instrument '
                'is inaudible; indicates where to investigate.',
    }


def render_stems(midi_path: str, out_dir: str, gain: float = 0.5) -> dict:
    """Use after MIDI audit to render one WAV per named single-channel note track
    with FluidSynth. Return out_dir, stem names and count. Preserve the global
    tempo map and original delta times; reject unsafe/duplicate track names,
    multi-channel tracks, empty MIDI, nonempty output directories and render failures.
    """
    import mido
    positive(gain, 'gain')
    if not Path(midi_path).is_file():
        raise ValueError(f'MIDI file does not exist: {midi_path}')
    try:
        mid = mido.MidiFile(midi_path)
    except Exception as exc:
        raise ValueError(f'Cannot decode MIDI {midi_path}: {exc}') from exc
    if mid.type == 2 or mid.ticks_per_beat <= 0:
        raise ValueError('Stem rendering requires synchronous MIDI with beat-based timing')
    tracks = [tr for tr in mid.tracks
              if any(m.type == 'note_on' and m.velocity > 0 for m in tr)]
    if not tracks:
        raise ValueError('Empty MIDI: no note tracks to render')
    names = [tr.name for tr in tracks]
    if any(not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]*', name) for name in names):
        raise ValueError('Track names must be safe filenames: letters, digits, _, - and .; rename unnamed tracks')
    if len(set(names)) != len(names):
        raise ValueError('Duplicate MIDI track names: use a unique name per stem')
    for tr in tracks:
        if len({msg.channel for msg in tr if hasattr(msg, 'channel')}) != 1:
            raise ValueError(f'Track {tr.name!r} has multiple MIDI channels; split it into named instrument tracks')
    sf = find_soundfont()
    if not sf:
        raise RuntimeError('Missing SoundFont: install fluid-soundfont-gm or set MIDI_SOUNDFONT')
    synth = executable('fluidsynth')
    out = Path(out_dir)
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ValueError(f'Stem output directory must be new or empty: {out}')
    out.parent.mkdir(parents=True, exist_ok=True)
    # Collect metadata at absolute ticks, then reconstruct deltas. Filtering delta
    # messages directly would move later tempo changes earlier in the song.
    meta = mido.MidiTrack()
    tick = previous = 0
    for msg in mido.merge_tracks(mid.tracks):
        tick += msg.time
        if msg.type in ('set_tempo', 'time_signature', 'key_signature'):
            meta.append(msg.copy(time=tick - previous))
            previous = tick
    meta.append(mido.MetaMessage('end_of_track', time=tick - previous))
    # Render all files in staging; a failed subprocess never leaves stale WAVs.
    with tempfile.TemporaryDirectory(prefix='.stems-', dir=out.parent) as work:
        staging = Path(work)
        for tr in tracks:
            new = mido.MidiFile(type=1, ticks_per_beat=mid.ticks_per_beat)
            new.tracks.append(mido.MidiTrack(meta))
            part = mido.MidiTrack()
            pending = 0
            for msg in tr:
                pending += msg.time
                if msg.type not in ('set_tempo', 'time_signature', 'key_signature'):
                    part.append(msg.copy(time=pending))
                    pending = 0
            new.tracks.append(part)
            m = staging / f'{tr.name}.mid'
            new.save(str(m))
            wav = staging / f'{tr.name}.wav'
            run_process([synth, '-ni', '-g', str(gain), '-F', str(wav),
                         '-r', str(SR), sf, str(m)])
            _load(str(wav))
        out.mkdir(parents=True, exist_ok=True)
        for wav in staging.glob('*.wav'):
            os.replace(wav, out / wav.name)
    return {'out_dir': str(out), 'stems': names, 'count': len(names)}


# --------------------------------------------------------------- processing ---
def apply_eq(path: str, out: str, band: str = 'peak', freq: float = 1000,
             gain_db: float = 0.0, q: float = 1.0) -> dict:
    """Use for a targeted tonal correction. Write a new WAV and return out,
    before/after metrics and applied settings. Bands: peak, low_shelf,
    high_shelf, highpass. Frequency must lie below the input Nyquist frequency.
    """
    output_path(out, path)
    before = analyze_audio(path)
    data, sr = _load(path)
    if not 0 < freq < sr / 2 or not math.isfinite(freq):
        raise ValueError(f'freq must be above 0 and below Nyquist ({sr / 2:g} Hz)')
    positive(q, 'q')
    if not math.isfinite(gain_db):
        raise ValueError('gain_db must be finite')
    if band == 'peak':
        fx = PeakFilter(cutoff_frequency_hz=freq, gain_db=gain_db, q=q)
    elif band == 'low_shelf':
        fx = LowShelfFilter(cutoff_frequency_hz=freq, gain_db=gain_db, q=q)
    elif band == 'high_shelf':
        fx = HighShelfFilter(cutoff_frequency_hz=freq, gain_db=gain_db, q=q)
    elif band == 'highpass':
        fx = HighpassFilter(cutoff_frequency_hz=freq)
    else:
        raise ValueError("band: peak | low_shelf | high_shelf | highpass")
    out_data = Pedalboard([fx])(data, sr)
    write_audio(out, out_data, sr)
    return {'out': str(out), 'before': before, 'after': analyze_audio(out),
            'applied': {'band': band, 'freq': freq, 'gain_db': gain_db}}


def apply_comp(path: str, out: str, threshold_db: float = -14.0,
               ratio: float = 3.0, attack_ms: float = 8.0,
               release_ms: float = 100.0) -> dict:
    """Use to control a stem's dynamics. Write a compressed WAV and return out,
    before/after metrics and compressor settings. ratio >= 1; attack/release > 0.
    """
    output_path(out, path)
    if not math.isfinite(threshold_db) or not math.isfinite(ratio) or ratio < 1:
        raise ValueError('threshold_db must be finite and ratio must be >= 1')
    positive(attack_ms, 'attack_ms')
    positive(release_ms, 'release_ms')
    before = analyze_audio(path)
    data, sr = _load(path)
    out_data = Pedalboard([Compressor(threshold_db=threshold_db, ratio=ratio,
                                      attack_ms=attack_ms, release_ms=release_ms)])(data, sr)
    write_audio(out, out_data, sr)
    return {'out': str(out), 'before': before, 'after': analyze_audio(out),
            'applied': {'threshold_db': threshold_db, 'ratio': ratio,
                        'attack_ms': attack_ms, 'release_ms': release_ms}}


def master(path: str, out: str, target_lufs: float = -12.0,
           profile: str = 'power_metal', trim_db: float = -3.0) -> dict:
    """Use after mixing. Apply the profile bus chain, then FFmpeg two-pass
    loudnorm targeting integrated LUFS and -1 dBTP. Return before/after audio
    metrics, measured loudness and target_met. Requires FFmpeg; always verify
    the resulting file with release_check and listen before publication.
    """
    output_path(out, path)
    prof = _profile(profile)['master']
    if not math.isfinite(target_lufs) or not -70 <= target_lufs <= -5:
        raise ValueError('target_lufs must be between -70 and -5')
    if not math.isfinite(trim_db):
        raise ValueError('trim_db must be finite')
    before = analyze_audio(path)
    data, sr = _load(path)
    mf, mg = prof['mud']; af, ag = prof['air']
    t, r, a, rel = prof['comp']
    chain = Pedalboard([
        HighpassFilter(cutoff_frequency_hz=prof['hpf']),
        PeakFilter(cutoff_frequency_hz=mf, gain_db=mg, q=0.8),
        HighShelfFilter(cutoff_frequency_hz=af, gain_db=ag),
        Compressor(threshold_db=t, ratio=r, attack_ms=a, release_ms=rel),
        Gain(gain_db=trim_db),
        Limiter(threshold_db=-1.0, release_ms=80),
    ])
    out_data = chain(data, sr)
    with tempfile.TemporaryDirectory(prefix='.master-', dir=Path(out).parent) as work:
        processed = Path(work) / 'processed.wav'
        normalized = Path(work) / 'normalized.wav'
        write_audio(processed, out_data, sr)
        measured = loudness(processed, target_lufs)['raw']
        afilter = (f'loudnorm=I={target_lufs}:TP=-1:LRA=11:'
                   f'measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}:'
                   f'measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}:'
                   f'offset={measured["target_offset"]}:linear=true')
        run_process([executable('ffmpeg'), '-hide_banner', '-nostdin', '-y', '-i', str(processed),
                     '-af', afilter, '-ar', str(sr), '-ac', str(data.shape[0]),
                     '-c:a', 'pcm_f32le', str(normalized)])
        measured_after = loudness(normalized, target_lufs)
        measured_after.pop('raw')
        os.replace(normalized, out)
    after = analyze_audio(out)
    return {'out': str(out), 'target_lufs': target_lufs, 'profile': profile,
            'before': before, 'after': after,
            'loudness': measured_after,
            'target_met': abs(measured_after['integrated_lufs'] - target_lufs) <= 1.0
                          and measured_after['true_peak_dbfs'] <= -0.9,
            'note': 'LUFS and true peak measured by FFmpeg. Target may be constrained '
                    'by dynamics; verify the exported delivery format and listen.'}


def auto_mix(stems_dir: str, out: str, profile: str = 'power_metal',
             duration: float | None = None) -> dict:
    """Use after rendering named WAV stems. Apply role chains, stereo balance
    and the profile bus; return output metrics, roles and settings. Default
    duration is the longest stem; explicit seconds trim/pad. Unknown stems abort.
    """
    return _mix(Path(stems_dir), Path(out), profile, duration)


def compare_to_reference(a: str, b: str) -> dict:
    """Use to compare reference a with candidate b. Return both analyses and
    candidate-minus-reference deltas in sample peak, RMS and octave-band energy.
    Differences are descriptive; they do not establish musical quality.
    """
    ma, mb = analyze_audio(a), analyze_audio(b)
    diff = {}
    for k in ma['octave_bands_db']:
        if k in mb['octave_bands_db']:
            diff[k] = round(mb['octave_bands_db'][k] - ma['octave_bands_db'][k], 2)
    return {'reference': ma, 'compared': mb,
            'band_delta_db': diff,
            'peak_delta_db': round(mb['peak_db'] - ma['peak_db'], 2),
            'rms_delta_db': round(mb['rms_db'] - ma['rms_db'], 2),
            'note': 'Positive delta = the compared file has MORE energy in that band.'}


def release_check(path: str, profile: str = 'power_metal') -> dict:
    """Use on the final export before sharing. Return ready/needs_work, issues,
    sample metrics and FFmpeg LUFS/true peak/LRA. Check clipping, peak margin,
    high RMS and stereo correlation. A ready verdict does not certify taste,
    genre, a chosen LUFS target or absence of audible defects.
    """
    _profile(profile)
    m = analyze_audio(path)
    measured = loudness(path)
    measured.pop('raw')
    issues = []
    if m['clipping']:
        issues.append('CLIPPING: the peak reaches 0 dB')
    if m['peak_db'] > -0.3:
        issues.append(f"peak too high ({m['peak_db']} dB); leave headroom to -1 dBTP")
    if measured['true_peak_dbfs'] > -0.9:
        issues.append(f"true peak too high ({measured['true_peak_dbfs']} dBTP); target <= -1 dBTP")
    if m['rms_db'] > -9:
        issues.append(f"RMS too high ({m['rms_db']} dB): likely overcompression")
    if m['stereo_correlation'] > 0.98:
        issues.append('stereo correlation ~1.0: nearly mono mix')
    if m['stereo_correlation'] < 0.2:
        issues.append('stereo correlation very low: risk of cancellation in mono')
    return {'file': str(path), 'profile': profile, 'metrics': m, 'loudness': measured,
            'verdict': 'needs_work' if issues else 'ready',
            'issues': issues,
            'note': 'Limited technical verdict. Does not assess musical taste.'}


def list_profiles() -> dict:
    """Use first to discover supported mix profiles, exact WAV role names and
    all role/master settings. Return profiles and a note about their limitations.
    """
    return {'profiles': {k: {'roles': list(v['roles']),
                             'role_settings': {r: dict(c) for r, c in v['roles'].items()},
                             'master': v['master']} for k, v in PROFILES.items()},
            'note': 'Engineering starting points, not absolute truth.'}


TOOLS = [list_profiles, render_stems, analyze_audio, analyze_masking, auto_mix,
         apply_eq, apply_comp, master, compare_to_reference, release_check]


def _selftest():
    with tempfile.TemporaryDirectory(prefix='hermes-daw-') as work:
        path = Path(work) / 'tone.wav'
        t = np.arange(SR) / SR
        write_audio(path, np.array([.1 * np.sin(2 * np.pi * 440 * t)], dtype=np.float32), SR)
        print(json.dumps(analyze_audio(str(path)), indent=2))


def build_server():
    from fastmcp import FastMCP
    mcp = FastMCP('hermes-daw')
    for fn in TOOLS:
        mcp.tool(fn)
    return mcp


def main():
    if '--selftest' in sys.argv:
        _selftest()
    elif os.environ.get('HERMES_DAW_STDIO_POLL') == '1':
        # Some restricted Linux runtimes forbid socketpair.send(), which asyncio
        # normally uses to wake the loop after stdio worker-thread reads. A timer
        # keeps that loop responsive without opening a network listener.
        import asyncio
        import contextlib

        async def serve():
            async def tick():
                while True:
                    await asyncio.sleep(0.05)
            heartbeat = asyncio.create_task(tick())
            try:
                await build_server().run_stdio_async(show_banner=False)
            finally:
                heartbeat.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await heartbeat
        asyncio.run(serve())
    else:
        build_server().run(show_banner=False)


if __name__ == '__main__':
    main()
