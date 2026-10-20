#!/usr/bin/env python3
"""Compose the short reference through the mandatory guard. Run from any cwd."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from _demo import plan, save

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'output/demo')
    parser.add_argument('--draft', type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.draft:
        save(args.draft)
        return
    args.work.mkdir(parents=True, exist_ok=True)
    decision = args.work / 'plan.json'
    with decision.open('x') as f:
        json.dump(plan(), f, indent=2)
    log = args.work / 'composition.log'
    with log.open('w') as f:
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/composition_guard.py'),
                                 str(decision), '--out', str(args.work / 'demo.mid'), '--',
                                 str(Path(__file__).resolve()), '--draft', '{draft}'],
                                stdout=f, stderr=subprocess.STDOUT)
    if result.returncode:
        print(log.read_text(), file=sys.stderr)
        raise SystemExit(result.returncode)
    print('COMPOSE: 12 bars, 160 BPM, 18.000 seconds; guard passed all 8 gates')
    print(f'MIDI: {args.work / "demo.mid"}')
    print(f'Certificate: {args.work / "demo.mid.audit.json"}')
    print(f'Full readings and guard output: {log}')


if __name__ == '__main__':
    main()
