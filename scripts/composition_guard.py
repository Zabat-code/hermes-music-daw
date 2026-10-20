#!/usr/bin/env python3
"""Entrada obligatoria para composición nueva: leer → decidir → escribir → verificar.

Uso: composition_guard.py plan.json --out final.mid -- compositor.py --out '{draft}'
El compositor se ejecuta con el mismo Python. {draft} es un MIDI temporal nuevo.
No publica final.mid si el proceso, el auditor o el contrato del plan fallan.
No es un sandbox de seguridad: un agente con escritura arbitraria puede evadirlo.
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
        raise ValueError('MIDI modificado después de la auditoría: certificado inválido')
    if receipt['code_sha256'] != code_hashes():
        raise ValueError('motor/auditor/protocolo cambiaron: repetir flujo de composición')
    if any(digest(p) != h for p, h in receipt['readings_sha256'].items()):
        raise ValueError('lecturas cambiaron: repetir flujo de composición')
    report = audit(midi, receipt['plan']['profile'])
    if not report['ok']:
        raise ValueError(format_report(report))
    verify_plan(receipt['plan'], report, midi)
    return report


def validate_plan(plan):
    if plan.get('profile') != 'dense':
        raise ValueError('entrada de composición implementada: profile=dense; otros perfiles requieren diseño explícito')
    if not isinstance(plan.get('intent'), str) or not plan['intent'].strip():
        raise ValueError('falta intent: género/variante, objetivo y criterio sonoro')
    sections = plan.get('sections', [])
    if len(sections) < 2 or len({s['name'] for s in sections}) != len(sections):
        raise ValueError('se requieren secciones únicas con contraste')
    for s in sections:
        if type(s['bars']) is not int or s['bars'] < 2 or not s.get('groove'):
            raise ValueError('cada sección necesita bars>=2 y decisión groove')
        if not isinstance(s.get('density'), (int, float)) or s['density'] < 0:
            raise ValueError('cada sección necesita densidad objetivo >=0')
    if max(s['density'] for s in sections) - min(s['density'] for s in sections) < 2:
        raise ValueError('plan sin contraste de densidad >=2')
    instruments = plan.get('instruments', [])
    if not instruments or len({i['name'] for i in instruments}) != len(instruments):
        raise ValueError('declarar instrumentos con nombres únicos')
    silence = False
    for i in instruments:
        role = i['role']
        if role not in RANGES and role != 'drums':
            raise ValueError(f'rol sin contrato: {role}')
        if role != 'drums':
            lo, hi = RANGES[role]
            if not lo <= i['min'] <= i['max'] <= hi:
                raise ValueError(f'registro de {i["name"]} fuera del contrato {lo}..{hi}')
        if type(i.get('silent_bars')) is not int or i['silent_bars'] < 0:
            raise ValueError('declarar silent_bars por instrumento')
        silence |= role in HARMONIC and i['silent_bars'] >= 1
    if not silence:
        raise ValueError('plan sin silencio de instrumento armónico: declarar silent_bars>=1 '
                         'en piano/guitarra/pad/cuerdas/coro y escribir esos compases sin notas ni sustain; ver PROTOCOL.md')
    borders, total = [], 0
    for s in sections:
        total += s['bars']
        borders.append(total)
    if not isinstance(plan.get('fill_bars'), list) or any(b not in borders for b in plan['fill_bars']):
        raise ValueError(f'fill_bars debe contener solo finales de sección (numerados desde 1): '
                         f'{borders}; hacer coincidir los fills reales con esa lista; ver PROTOCOL.md')


def verify_plan(plan, report, midi):
    import mido
    if report['bars'] != sum(s['bars'] for s in plan['sections']):
        raise ValueError(f'el MIDI no cumple los compases del plan: MIDI={report["bars"]}, '
                         f'plan={sum(s["bars"] for s in plan["sections"])}. '
                         'Corregir secciones y end_of_track; ver PROTOCOL.md')
    actual = {s['name']: s for s in report['tracks']}
    if set(actual) != {i['name'] for i in plan['instruments']}:
        raise ValueError('instrumentos reales distintos de los declarados en el plan')
    for i in plan['instruments']:
        s = actual[i['name']]
        if s['role'] != i['role'] or s['silent_bars'] < i['silent_bars']:
            raise ValueError(f'rol/silencios no cumplen plan: {i["name"]}')
        if i['role'] != 'drums' and (s['range'][0] < i['min'] or s['range'][1] > i['max']):
            raise ValueError(f'registro no cumple plan: {i["name"]}')
    # Esta entrada soporta contratos densos en 4/4. No adivina secciones.
    m = mido.MidiFile(midi)
    markers = []
    for tr in m.tracks:
        tick = 0
        for msg in tr:
            tick += msg.time
            if msg.type == 'time_signature' and (msg.numerator, msg.denominator) != (4, 4):
                raise ValueError('entrada densa actual requiere 4/4')
            if msg.type == 'marker':
                markers.append((tick, msg.text))
    expected, bar = [], 0
    for s in plan['sections']:
        expected.append((bar * 4 * m.ticks_per_beat, s['name']))
        bar += s['bars']
    if sorted(markers) != expected:
        raise ValueError('marcadores MIDI no cumplen las secciones del plan')
    if report['fill_bars'] != plan['fill_bars']:
        raise ValueError(f'los fills detectados no cumplen fill_bars del plan (heurística): '
                         f'MIDI={report["fill_bars"]}, plan={plan["fill_bars"]}. '
                         'Corregir toms/cajas en bordes y la lista del plan; ver PROTOCOL.md')
    actual_density = dict(report['density_sections'])
    for section in plan['sections']:
        if abs(actual_density[section['name']] - section['density']) > 3:
            raise ValueError(f'densidad difiere más de 3 golpes del plan: {section["name"]}; '
                             f'MIDI={actual_density[section["name"]]}, plan={section["density"]}. '
                             'Comparar density_sections del auditor y corregir groove o intención; ver PROTOCOL.md')


def main(argv=None):
    argsv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    try:
        if len(argsv) == 2 and argsv[0] == '--verify':
            report = verify_delivery(argsv[1])
            print(f'CERTIFICADO VIGENTE: {report["file"]}; auditoría repetida, exit 0')
            return 0
        if argsv and argsv[0] in ('-h', '--help'):
            print(__doc__.strip())
            print('\nUso: composition_guard.py plan.json --out final.mid -- compositor.py --out {draft}')
            print('Verificación posterior: composition_guard.py --verify final.mid')
            print('\nEl plan.json debe incluir: profile="dense", intent, sections con groove/'
                  'densidad, e instrumentos con rol/min/max MIDI/silencios.')
            print('Esquema concreto: scripts/example_dense_arrangement.py --plan plan.json')
            return 0
        split = argsv.index('--')
        args = parser.parse_args(argsv[:split])
        command = argsv[split + 1:]
        if not command or not any('{draft}' in item for item in command):
            raise ValueError('el comando necesita compositor.py y --out {draft}')
        print('PROTOCOLO OBLIGATORIO: 1 LEER → 2 DECIDIR → 3 ESCRIBIR → 4 VERIFICAR', flush=True)
        evidence = {}
        for path in READINGS:
            content = path.read_text()
            evidence[str(path)] = digest(path)
            print(f'\nLECTURA {path}\n{content}', flush=True)
        # Se lee y valida el plan antes de ejecutar una sola nota del compositor.
        plan = json.loads(args.plan.read_text())
        validate_plan(plan)
        plan_hash = digest(args.plan)
        print('\nDECISIONES VALIDADAS\n' + json.dumps(plan, ensure_ascii=False, indent=2), flush=True)
        out = args.out.resolve()
        receipt = Path(str(out) + '.audit.json')
        if out.exists() or receipt.exists():
            raise FileExistsError(f'no se sobrescriben entregas: {out} / {receipt}')
        out.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='.composicion-', dir=out.parent) as tmp:
            draft = Path(tmp) / 'borrador.mid'
            argv_composer = [item.replace('{draft}', str(draft)) for item in command]
            print('ESCRIBIR: ejecutando compositor; todavía no hay entrega aprobada', flush=True)
            subprocess.run([sys.executable, *argv_composer], check=True)
            if not draft.is_file() or draft.is_symlink():
                raise ValueError('el compositor no produjo el borrador esperado')
            report = audit(draft, plan['profile'])
            print(format_report(report), flush=True)
            if not report['ok']:
                raise ValueError('gate de arreglo rechazado; no se publica el MIDI')
            verify_plan(plan, report, draft)
            if digest(args.plan) != plan_hash or any(digest(p) != h for p, h in evidence.items()):
                raise ValueError('plan/lecturas cambiaron durante la composición: repetir protocolo')
            report.update(file=str(out), plan_sha256=plan_hash, readings_sha256=evidence,
                          composer_argv=command, code_sha256=code_hashes(), plan=plan)
            # Crear sin sobrescribir; el hash vincula certificado y MIDI exactos.
            tmp_receipt = Path(tmp) / 'audit.json'
            tmp_receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
            os.link(tmp_receipt, receipt)
            try:
                os.link(draft, out)
            except Exception:
                receipt.unlink()
                raise
        print(f'PUBLICADO: {out}\nCERTIFICADO ESTRUCTURAL: {receipt}\nFalta escucha para afirmar calidad sonora.')
        return 0
    except Exception as exc:
        print(f'ABORTAR (exit 1): {type(exc).__name__}: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
