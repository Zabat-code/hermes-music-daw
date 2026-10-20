#!/usr/bin/env python3
"""Required entry point for new compositions: read -> decide -> write -> verify.

Usage: composition_guard.py plan.json --out final.mid -- compositor.py --out '{draft}'
The composer runs with the same Python interpreter. {draft} is a new temporary MIDI.
Does not publish final.mid if the process, auditor or plan contract fails.
This is not a security sandbox: an agent with arbitrary write access can bypass it.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

if __package__:
    from .audit_arrangement import HARMONIC, RANGES, audit, format_report
else:
    from audit_arrangement import HARMONIC, RANGES, audit, format_report

SKILL = Path(__file__).resolve().parent.parent
DOCS = SKILL / 'docs'
READINGS = [DOCS / name for name in (
    'ERROR-REPETIDO-2026-10-19.md', 'OBSERVACIONES-PARA-AUDITOR-2026-10-19.md',
    'COMPARATIVA-BATERIA-METAL-2026-10-19.md', 'TEORIA-Y-ARQUITECTURA-2026-10-19.md',
    'HALLAZGOS.md')] + [SKILL / 'references/teoria-composicion.md',
                         SKILL / 'references/rendering.md',
                         SKILL / 'scripts/example_dense_arrangement.py']


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_hashes():
    return {str(SKILL / 'scripts' / name): digest(SKILL / 'scripts' / name)
            for name in ('composition_guard.py', 'audit_arrangement.py', 'hermesmusic.py')}


def verify_delivery(midi):
    midi = Path(midi).resolve()
    receipt = json.loads(Path(str(midi) + '.audit.json').read_text())
    if receipt['sha256'] != digest(midi):
        raise ValueError('MIDI modified after the audit: invalid certificate')
    if receipt['code_sha256'] != code_hashes():
        raise ValueError('engine/auditor/protocol changed: repeat the composition workflow')
    if any(digest(p) != h for p, h in receipt['readings_sha256'].items()):
        raise ValueError('readings changed: repeat the composition workflow')
    report = audit(midi, receipt['plan']['profile'])
    if not report['ok']:
        raise ValueError(format_report(report))
    verify_plan(receipt['plan'], report, midi)
    return report


def validate_plan(plan):
    if plan.get('profile') != 'dense':
        raise ValueError('implemented composition entry point: profile=dense; other profiles require explicit design')
    if not isinstance(plan.get('intent'), str) or not plan['intent'].strip():
        raise ValueError('missing intent: genre/variant, goal and sonic criteria')
    sections = plan.get('sections', [])
    if len(sections) < 2 or len({s['name'] for s in sections}) != len(sections):
        raise ValueError('unique sections with contrast are required')
    for s in sections:
        if type(s['bars']) is not int or s['bars'] < 2 or not s.get('groove'):
            raise ValueError('each section requires bars>=2 and a groove decision')
        if not isinstance(s.get('density'), (int, float)) or s['density'] < 0:
            raise ValueError('each section requires target density >=0')
    if max(s['density'] for s in sections) - min(s['density'] for s in sections) < 2:
        raise ValueError('plan lacks density contrast >=2')
    instruments = plan.get('instruments', [])
    if not instruments or len({i['name'] for i in instruments}) != len(instruments):
        raise ValueError('declare instruments with unique names')
    silence = False
    for i in instruments:
        role = i['role']
        if role not in RANGES and role != 'drums':
            raise ValueError(f'role without a contract: {role}')
        if role != 'drums':
            lo, hi = RANGES[role]
            if not lo <= i['min'] <= i['max'] <= hi:
                raise ValueError(f'register of {i["name"]} outside the contract {lo}..{hi}')
        if type(i.get('silent_bars')) is not int or i['silent_bars'] < 0:
            raise ValueError('declare silent_bars per instrument')
        silence |= role in HARMONIC and i['silent_bars'] >= 1
    if not silence:
        raise ValueError('plan lacks harmonic instrument silence: declare silent_bars>=1 '
                         'for piano/guitar/pad/strings/choir and write those bars with no notes or sustain; see PROTOCOL.md')
    borders, total = [], 0
    for s in sections:
        total += s['bars']
        borders.append(total)
    if not isinstance(plan.get('fill_bars'), list) or any(b not in borders for b in plan['fill_bars']):
        raise ValueError(f'fill_bars must contain only section endings (numbered from 1): '
                         f'{borders}; match the actual fills to that list; see PROTOCOL.md')


def verify_plan(plan, report, midi):
    import mido
    if report['bars'] != sum(s['bars'] for s in plan['sections']):
        raise ValueError(f'MIDI does not match the planned bar count: MIDI={report["bars"]}, '
                         f'plan={sum(s["bars"] for s in plan["sections"])}. '
                         'Correct sections and end_of_track; see PROTOCOL.md')
    actual = {s['name']: s for s in report['tracks']}
    if set(actual) != {i['name'] for i in plan['instruments']}:
        raise ValueError('actual instruments differ from those declared in the plan')
    for i in plan['instruments']:
        s = actual[i['name']]
        if s['role'] != i['role'] or s['silent_bars'] < i['silent_bars']:
            raise ValueError(f'role/silence does not match the plan: {i["name"]}')
        if i['role'] != 'drums' and (s['range'][0] < i['min'] or s['range'][1] > i['max']):
            raise ValueError(f'register does not match the plan: {i["name"]}')
    # This entry point supports dense contracts in 4/4. It does not guess sections.
    m = mido.MidiFile(midi)
    markers = []
    for tr in m.tracks:
        tick = 0
        for msg in tr:
            tick += msg.time
            if msg.type == 'time_signature' and (msg.numerator, msg.denominator) != (4, 4):
                raise ValueError('the current dense entry point requires 4/4')
            if msg.type == 'marker':
                markers.append((tick, msg.text))
    expected, bar = [], 0
    for s in plan['sections']:
        expected.append((bar * 4 * m.ticks_per_beat, s['name']))
        bar += s['bars']
    if sorted(markers) != expected:
        raise ValueError('MIDI markers do not match the planned sections')
    if report['fill_bars'] != plan['fill_bars']:
        raise ValueError(f'detected fills do not match the planned fill_bars (heuristic): '
                         f'MIDI={report["fill_bars"]}, plan={plan["fill_bars"]}. '
                         'Correct toms/snares at boundaries and the list in the plan; see PROTOCOL.md')
    actual_density = dict(report['density_sections'])
    for section in plan['sections']:
        if abs(actual_density[section['name']] - section['density']) > 3:
            raise ValueError(f'density differs from the plan by more than 3 hits: {section["name"]}; '
                             f'MIDI={actual_density[section["name"]]}, plan={section["density"]}. '
                             'Compare density_sections from the auditor and correct the groove or intent; see PROTOCOL.md')


def main(argv=None):
    argsv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    try:
        if len(argsv) == 2 and argsv[0] == '--verify':
            report = verify_delivery(argsv[1])
            print(f'VALID CERTIFICATE: {report["file"]}; audit repeated, exit 0')
            return 0
        if argsv and argsv[0] in ('-h', '--help'):
            print(__doc__.strip())
            print('\nUsage: composition_guard.py plan.json --out final.mid -- compositor.py --out {draft}')
            print('Subsequent verification: composition_guard.py --verify final.mid')
            print('\nplan.json must include: profile="dense", intent, sections with groove/'
                  'density, and instruments with role/min/max MIDI/silence.')
            print('Concrete schema: scripts/example_dense_arrangement.py --plan plan.json')
            return 0
        split = argsv.index('--')
        args = parser.parse_args(argsv[:split])
        command = argsv[split + 1:]
        if not command or not any('{draft}' in item for item in command):
            raise ValueError('the command requires compositor.py and --out {draft}')
        print('REQUIRED PROTOCOL: 1 READ -> 2 DECIDE -> 3 WRITE -> 4 VERIFY', flush=True)
        evidence = {}
        for path in READINGS:
            content = path.read_text()
            evidence[str(path)] = digest(path)
            print(f'\nREADING {path}\n{content}', flush=True)
        # Read and validate the plan before executing a single note from the composer.
        plan = json.loads(args.plan.read_text())
        validate_plan(plan)
        plan_hash = digest(args.plan)
        print('\nVALIDATED DECISIONS\n' + json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
        out = args.out.resolve()
        receipt = Path(str(out) + '.audit.json')
        if out.exists() or receipt.exists():
            raise FileExistsError(f'deliveries are not overwritten: {out} / {receipt}')
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.composicion-', dir=out.parent) as tmp:
            draft = Path(tmp) / 'borrador.mid'
            argv_composer = [item.replace('{draft}', str(draft)) for item in command]
            print('WRITE: running composer; no approved delivery yet', flush=True)
            subprocess.run([sys.executable, *argv_composer], check=True)
            if not draft.is_file() or draft.is_symlink():
                raise ValueError('the composer did not produce the expected draft')
            report = audit(draft, plan['profile'])
            print(format_report(report), flush=True)
            if not report['ok']:
                raise ValueError('arrangement gate rejected; MIDI will not be published')
            verify_plan(plan, report, draft)
            if digest(args.plan) != plan_hash or any(digest(p) != h for p, h in evidence.items()):
                raise ValueError('plan/readings changed during composition: repeat the protocol')
            report.update(file=str(out), plan_sha256=plan_hash, readings_sha256=evidence,
                          composer_argv=command, code_sha256=code_hashes(), plan=plan)
            # Create without overwriting; the hash binds the certificate to the exact MIDI.
            tmp_receipt = Path(tmp) / 'audit.json'
            tmp_receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            os.link(tmp_receipt, receipt)
            try:
                os.link(draft, out)
            except Exception:
                receipt.unlink()
                raise
        print(f'PUBLISHED: {out}\nSTRUCTURAL CERTIFICATE: {receipt}\nListening is required before claiming sound quality.')
        return 0
    except Exception as exc:
        print(f'ABORT (exit 1): {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
