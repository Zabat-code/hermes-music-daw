#!/usr/bin/env python3
"""
Production Effects MIDI Mapper
===============================

Aplica efectos de producción a archivos MIDI, basados en el análisis del
video "MOTOMAMI: an in-depth musical analysis ft. Rosalía" de Jaime Altozano.

Efectos:
- autotune: pitch correction agresiva (pitch bend + CC1)
- pitch_shift: desplazamiento de tonalidad
- filter: filtro pasa-baja/pasa-alta (CC74, CC71)
- distortion: distorsión de saturación (CC11, velocity)
- reverb: reverberación (CC91, CC94)
- sidechain: ducking de acompañamiento (CC11)
- vocoder: modulación de voz (CC10, CC73)
- chorus: coros/eco espacial (CC66, CC58)
- flanger: flanger (CC11, CC106)

Uso:
    python3 effects_apply.py input.mid output.mid --effect autotune --params "..."
    python3 effects_apply.py list
"""

import sys
import json
import argparse
from pathlib import Path
import mido


# ---------- Recetas de efectos ----------

EFFECTS = {
    'autotune': {
        'params': {
            'min_semitone': 12,
            'max_semitone': 50,
            'velocity': 0.8,
        },
        'description': 'Autotune: pitch correction agresiva para voz',
        'notes': [
            'Aplica pitch bend a las notas (canal 1 voz)',
            'Usa CC1 (modulation) con envolutura de 12-50 semicientos',
            'Reduce reverb y coros para voz "seca"',
        ],
    },
    'pitch_shift': {
        'params': {
            'semitones': 0,
            'velocity': 0.9,
        },
        'description': 'Pitch shifting: subir/bajar tonalidad',
        'notes': [
            'Aplica pitch bend constante (semitones fijo)',
            'Usa velocity para control de intensidad',
        ],
    },
    'filter': {
        'params': {
            'cutoff_low': 80,
            'cutoff_high': 200,
            'resonance': 20,
            'velocity': 0.8,
        },
        'description': 'Filtro pasa-baja/pasa-alta para textura',
        'notes': [
            'Aplica CC74 (filter cutoff) desde cutoff_low hasta cutoff_high',
            'CC71 (filter resonance) con valor de resonance',
            'Quita frecuencias agudas (según análisis MOTOMAMI)',
        ],
    },
    'distortion': {
        'params': {
            'intensity': 0.4,
            'velocity': 0.9,
        },
        'description': 'Distorsión de saturación',
        'notes': [
            'Aplica CC11 (expression) con intensidad de distancia',
            'Añade velocity spikes para agresividad',
            'Según análisis: "Ultra distorsionadas"',
        ],
    },
    'reverb': {
        'params': {
            'wet': 0.3,
            'dry': 0.7,
            'room': 30,
            'velocity': 0.8,
        },
        'description': 'Reverberación espacial',
        'notes': [
            'Aplica CC91 (reverb depth) con nivel wet',
            'CC94 (reverb damping) según room',
            'Voz sin reverb (dry) según análisis MOTOMAMI',
        ],
    },
    'sidechain': {
        'params': {
            'duck_amount': -12,
            'attack': 5,
            'release': 20,
            'velocity': 0.8,
        },
        'description': 'Ducking de acompañamiento',
        'notes': [
            'Aplica backmask (note_off) a acompañamiento cuando entra voz',
            'CC11 (expression) con duck_amount de atenuación',
            'Ataque rápido, release más largo',
        ],
    },
    'vocoder': {
        'params': {
            'carrier': 73,
            'modulation': 10,
            'velocity': 0.8,
        },
        'description': 'Vocoder: voz como moduladora',
        'notes': [
            'Aplica CC73 (initial tempo) como carrier',
            'CC10 (expression) como mod',
            'Mapeo de formantes según análisis MOTOMAMI',
        ],
    },
    'chorus': {
        'params': {
            'depth': 0.5,
            'rate': 0.3,
            'velocity': 0.8,
        },
        'description': 'Coros/eco para espaciamiento',
        'notes': [
            'Aplica CC66 (chorus depth) con profundidad',
            'CC58 (chorus rate) según tasa',
            'Efecto de "mezclas loquísimas"',
        ],
    },
    'flanger': {
        'params': {
            'depth': 0.5,
            'speed': 0.2,
            'velocity': 0.8,
        },
        'description': 'Flanger: efecto de playateado',
        'notes': [
            'Aplica CC11 (expression) con depth',
            'CC106 (flanger speed) según velocidad',
            'Para efecto de "giro" melódico',
        ],
    },
}


# ---------- Módulos de efecto ----------

def apply_autotune(track, params):
    """Aplica autotune: pitch bend + CC1 para voz en canal 1."""
    min_semitone = params.get('min_semitone', 12)
    max_semitone = params.get('max_semitone', 50)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'note_on' and msg.channel == 0:
            # Pitch bend: pitch bend +12 to +50 semitones (voz agresiva)
            bend = int(min_semitone + (max_semitone - min_semitone) * msg.velocity * 0.5)
            msg.pitchbend = bend
            msg.velocity = int(msg.velocity * velocity)
        elif msg.type == 'control_change':
            # CC1 = modulation
            if msg.control == 1:
                msg.value = int(12 + (50 - 12) * msg.value * 0.5)


def apply_pitch_shift(track, params):
    """Aplica pitch shift: desplazamiento constante."""
    semitones = params.get('semitones', 0)
    velocity = params.get('velocity', 0.9)

    for msg in track:
        if msg.type == 'note_on':
            # Shift pitch by semitones
            new_pitch = msg.pitch + semitones
            if 0 <= new_pitch <= 127:
                new_note = mido.mid2freq(new_pitch / 12 * 440)  # not used directly
                msg.pitch = new_pitch
            msg.velocity = int(msg.velocity * velocity)


def apply_filter(track, params):
    """Aplica filtro: CC74 (cutoff) y CC71 (resonance)."""
    cutoff_low = params.get('cutoff_low', 80)
    cutoff_high = params.get('cutoff_high', 200)
    resonance = params.get('resonance', 20)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            # CC74 = filter cutoff
            if msg.control == 74:
                msg.value = int(cutoff_low + (cutoff_high - cutoff_low) * msg.value * 0.5)
            # CC71 = filter resonance
            elif msg.control == 71:
                msg.value = resonance


def apply_distortion(track, params):
    """Aplica distorsión: CC11 + velocity spikes."""
    intensity = params.get('intensity', 0.4)
    velocity = params.get('velocity', 0.9)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 11:
                msg.value = int(intensity * 127)
        elif msg.type == 'note_on':
            # Add velocity spikes for aggression
            msg.velocity = int(msg.velocity * velocity)


def apply_reverb(track, params):
    """Aplica reverb: CC91 (wet) y CC94 (damping)."""
    wet = params.get('wet', 0.3)
    dry = params.get('dry', 0.7)
    room = params.get('room', 30)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 91:
                msg.value = int(wet * 127)
            elif msg.control == 94:
                msg.value = room
        elif msg.type == 'note_on':
            msg.velocity = int(msg.velocity * velocity)


def apply_sidechain(track, params):
    """Aplica sidechain: backmask + CC11 ducking."""
    duck_amount = params.get('duck_amount', -12)
    attack = params.get('attack', 5)
    release = params.get('release', 20)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 11:
                msg.value = int(duck_amount * 127)
        elif msg.type == 'note_on' and msg.channel == 1:
            # Voz en canal 1; backmask (note_off) al acompañamiento en canales 0-8
            if msg.channel != 1:
                msg.note_off()


def apply_vocoder(track, params):
    """Aplica vocoder: CC73 (carrier) y CC10 (expression)."""
    carrier = params.get('carrier', 73)
    modulation = params.get('modulation', 10)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 73:
                msg.value = carrier
            elif msg.control == 10:
                msg.value = modulation
        elif msg.type == 'note_on':
            msg.velocity = int(msg.velocity * velocity)


def apply_chorus(track, params):
    """Aplica chorus: CC66 y CC58."""
    depth = params.get('depth', 0.5)
    rate = params.get('rate', 0.3)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 66:
                msg.value = int(depth * 127)
            elif msg.control == 58:
                msg.value = int(rate * 127)
        elif msg.type == 'note_on':
            msg.velocity = int(msg.velocity * velocity)


def apply_flanger(track, params):
    """Aplica flanger: CC11 y CC106."""
    depth = params.get('depth', 0.5)
    speed = params.get('speed', 0.2)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 11:
                msg.value = int(depth * 127)
            elif msg.control == 106:
                msg.value = int(speed * 127)
        elif msg.type == 'note_on':
            msg.velocity = int(msg.velocity * velocity)


EFFECT_FUNCTORS = {
    'autotune': apply_autotune,
    'pitch_shift': apply_pitch_shift,
    'filter': apply_filter,
    'distortion': apply_distortion,
    'reverb': apply_reverb,
    'sidechain': apply_sidechain,
    'vocoder': apply_vocoder,
    'chorus': apply_chorus,
    'flanger': apply_flanger,
}


# ---------- Lógica principal ----------

def apply_effects(midi_file, output_file, effect_name, params=None):
    """
    Aplica un efecto a un archivo MIDI.

    Args:
        midi_file: Path al archivo MIDI de entrada
        output_file: Path al archivo MIDI de salida
        effect_name: Nombre del efecto
        params: Dict de parámetros opcionales

    Returns:
        int: Código de estado (0 = OK, 1 = error)
    """
    if not Path(midi_file).exists():
        print(f'ERROR: No se encontró {midi_file}', file=sys.stderr)
        return 1

    if effect_name not in EFFECT_FUNCTORS:
        print(f'ERROR: Efecto desconocido "{effect_name}"', file=sys.stderr)
        print(f'   Efectos disponibles: {", ".join(EFFECT_FUNCTORS.keys())}', file=sys.stderr)
        return 1

    effect = EFFECT_FUNCTORS[effect_name]
    if params is None:
        params = EFFECTS[effect_name]['params']

    # Leer MIDI
    try:
        mid = mido.MidiFile(midi_file)
    except Exception as e:
        print(f'ERROR: No se pudo leer {midi_file}: {e}', file=sys.stderr)
        return 1

    print(f'📀 Leyendo: {midi_file}')
    print(f'   Tiempo: {mid.length:.2f}s | {len(mid.tracks)} pistas | tpb: {mid.ticks_per_beat}')

    # Aplicar efecto a cada pista
    applied = []
    for i, track in enumerate(mid.tracks):
        # Solo aplicar a pistas con notas
        has_notes = any(msg.type in ('note_on', 'note_off') for msg in track)
        if not has_notes:
            continue

        try:
            effect(track, params)
            applied.append(i)
        except Exception as e:
            print(f'   ⚠️  Error en pista {i}: {e}', file=sys.stderr)

    print(f'   ✅ Efecto "{effect_name}" aplicado a {len(applied)}/{len(mid.tracks)} pistas')

    # Guardar
    try:
        mid.save(output_file)
        print(f'💾 Guardado: {output_file}')
        return 0
    except Exception as e:
        print(f'ERROR: No se pudo guardar {output_file}: {e}', file=sys.stderr)
        return 1


def list_effects():
    """Lista los efectos disponibles."""
    print('🔧 Efectos disponibles:')
    for name, data in EFFECTS.items():
        print(f'  {name:15s} | {data["description"]}')
        print(f'    Parámetros: {json.dumps(data["params"], indent=4).replace(chr(10), chr(10)+"    ")}')
        print(f'    Notas: {data["notes"]}')


def main():
    parser = argparse.ArgumentParser(
        description='Production Effects MIDI Mapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Ejemplos:\n    python3 effects_apply.py input.mid output.mid --effect autotune\n    python3 effects_apply.py input.mid output.mid --effect filter --params \'{"cutoff_low": 60, "cutoff_high": 150}\'\n    python3 effects_apply.py list'
    )
    parser.add_argument('input', help='Archivo MIDI de entrada')
    parser.add_argument('output', help='Archivo MIDI de salida')
    parser.add_argument('--effect', '-e', required=True, help='Nombre del efecto')
    parser.add_argument('--params', '-p', help='Parámetros JSON (ej: {"cutoff_low": 60, "cutoff_high": 150})')

    args = parser.parse_args()

    params = None
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(f'ERROR: JSON inválido en --params: {e}', file=sys.stderr)
            sys.exit(1)

    sys.exit(apply_effects(args.input, args.output, args.effect, params))


if __name__ == '__main__':
    main()
