#!/usr/bin/env python3
"""Offline smoke test for the complete MIDI + audio + MCP workflow (exit 0/1)."""
from __future__ import annotations

from importlib import import_module, metadata
import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main() -> int:
    failures = []

    def report(name, ok, detail):
        print(f'{"OK" if ok else "MISSING/ERROR"} {name}: {detail}')
        if not ok:
            failures.append(name)

    report('Python', sys.version_info >= (3, 12), sys.version.split()[0])
    deps_ok = True
    for name in ('mido', 'numpy', 'pedalboard', 'fastmcp'):
        try:
            import_module(name)
            report(name, True, metadata.version(name))
        except Exception as exc:
            report(name, False, f'{exc}; run: python -m pip install -e .')
            deps_ok = False
    if deps_ok:
        if __package__:
            from .audio_utils import executable, find_soundfont
        else:
            from audio_utils import executable, find_soundfont
        for name, flag in (('fluidsynth', '--version'), ('ffmpeg', '-version'), ('ffprobe', '-version')):
            try:
                path = executable(name)
                env = os.environ.copy()
                if name == 'fluidsynth':
                    env.setdefault('SDL_AUDIODRIVER', 'dummy')
                result = subprocess.run([path, flag], capture_output=True, text=True, timeout=15, env=env)
                if result.returncode:
                    raise RuntimeError(f'exit {result.returncode}: {result.stderr[:200]}')
                report(name, True, f'{path} | {(result.stdout or result.stderr).splitlines()[0]}')
            except Exception as exc:
                report(name, False, f'{exc}; on Mint/Ubuntu: sudo apt install fluidsynth ffmpeg')
        try:
            sf = find_soundfont()
            if not sf:
                raise RuntimeError('install fluid-soundfont-gm or set MIDI_SOUNDFONT=/path/to/font.sf2')
            with open(sf, 'rb') as f:
                header = f.read(12)
            if header[:4] != b'RIFF' or header[8:12] != b'sfbk':
                raise ValueError(f'Not a RIFF SoundFont: {sf}')
            report('SoundFont', True, sf)
        except Exception as exc:
            report('SoundFont', False, str(exc))
    root = Path(__file__).resolve().parents[1]
    needed = ['references/genre_configs.json', 'references/genre_profiles.json',
              'references/rendering.md', 'references/teoria-composicion.md',
              'scripts/example_dense_arrangement.py', 'PROTOCOL.md']
    needed += [f'docs/{name}' for name in (
        'ERROR-REPETIDO-2026-10-19.md', 'OBSERVACIONES-PARA-AUDITOR-2026-10-19.md',
        'COMPARATIVA-BATERIA-METAL-2026-10-19.md', 'TEORIA-Y-ARQUITECTURA-2026-10-19.md', 'HALLAZGOS.md')]
    missing = [name for name in needed if not (root / name).is_file()]
    report('package resources', not missing, ', '.join(missing) if missing else 'all guard readings and genre data present')
    try:
        with tempfile.TemporaryDirectory(prefix='.install-check-', dir=Path.cwd()) as work:
            (Path(work) / 'probe').write_text('ok')
        report('output directory', True, f'{Path.cwd()} (writable)')
    except OSError as exc:
        report('output directory', False, str(exc))
    print(f'RESULT: {"FAIL" if failures else "PASS"} ({len(failures)} missing/error checks)')
    return int(bool(failures))


if __name__ == '__main__':
    sys.exit(main())
