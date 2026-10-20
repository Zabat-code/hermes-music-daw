#!/usr/bin/env python3
"""Render audited MIDI, mix all six stems, master, encode OGG and verify that export."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from composition_guard import verify_delivery
from daw_mcp import render_stems, auto_mix, master, release_check
from audio_utils import executable, run_process


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'output/demo')
    args = parser.parse_args()
    work = args.work
    verify_delivery(work / 'demo.mid')
    rendered = render_stems(str(work / 'demo.mid'), str(work / 'stems'))
    print(f'RENDER: {rendered["count"]} stems')
    # Preserve the synthesizer release tail by inferring the longest stem duration.
    mixed = auto_mix(str(work / 'stems'), str(work / 'mix.wav'), 'balanced')
    print(f'MIX: {mixed["seconds"]} s, peak {mixed["peak_db"]} dBFS, RMS {mixed["rms_db"]} dBFS')
    mastered = master(str(work / 'mix.wav'), str(work / 'master.wav'), -16.0, 'balanced')
    print(f'MASTER: {json.dumps(mastered["loudness"], sort_keys=True)}; target_met={mastered["target_met"]}')
    run_process([executable('ffmpeg'), '-nostdin', '-y', '-i', str(work / 'master.wav'),
                 '-ar', '44100', '-ac', '2', '-c:a', 'libvorbis', '-q:a', '5', str(work / 'demo.ogg')])
    check = release_check(str(work / 'demo.ogg'), 'balanced')
    results = {'render': rendered, 'mix': mixed, 'master': mastered, 'release': check}
    (work / 'results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False) + '\n')
    print(f'RELEASE (OGG): {check["verdict"]}; issues={check["issues"]}')
    print(f'OGG: {work / "demo.ogg"}')
    print('Structurally audited GM demo; listening quality pending human review.')
    if not mastered['target_met'] or check['verdict'] != 'ready':
        raise SystemExit(1)


if __name__ == '__main__':
    main()
