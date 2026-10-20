#!/usr/bin/env python3
"""Audit the exact MIDI bytes and verify the guard certificate before rendering."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from audit_arrangement import audit, format_report
from composition_guard import verify_delivery


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work', type=Path, default=ROOT / 'output/demo')
    args = parser.parse_args()
    report = audit(args.work / 'demo.mid')
    print(format_report(report))
    if not report['ok']:
        raise SystemExit(1)
    (args.work / 'audit.json').write_text(json.dumps(report, indent=2) + '\n')
    verify_delivery(args.work / 'demo.mid')
    print('CERTIFICATE: valid; MIDI, readings and guard code hashes match')


if __name__ == '__main__':
    main()
