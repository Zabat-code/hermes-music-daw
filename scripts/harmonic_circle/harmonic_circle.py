#!/usr/bin/env python3
"""
Harmonic Circle Progressions MIDI Generator
===========================================

Genera progresiones de acordes MIDI basadas en el Círculo de Quintas,
basado en el video "Un TRUCO INCREÍBLE PARA ENTENDER ACORDES Y ESCALAS:
El Círculo de Quintas" de Jaime Altozano (con millones de vistas).

Funciona con:
  - El Círculo de Quintas (I, IV, V, vi, III, II, vii°)
  - Extended chords (7, 9, 11, 13)
  - Substitutions (ii° → V, vi → III, etc.)
  - Function harmony (Tonic, Subdominant, Dominant)

MIDI output:
  - Pista 0: Voz (harmonías en octavas)
  - Pista 1: Bajo (root note)
  - Pista 2: Arpegio de la melodía

Uso:
    python3 harmonic_circle.py --genre pop --progression "I-vi-IV-V" --out pop.mid

    # Listar progresiones
    python3 harmonic_circle.py list
"""

import argparse
import json
import sys
import os
from pathlib import Path
import mido


# ---------- Semitones por dimensión ----------

# Dimensión de cada nota de la escala (MIDI 0-127)
# C mayor = 0
SCALE_DEGREES = {
    # Notas fuertes
    'I': 0,    # Tónica
    'II': 2,   # Supertónica
    'III': 4,  # Tercera
    'IV': 5,   # Subdominante
    'V': 7,    # Dominante
    'VI': 9,   # Submediante
    'VII': 11, # Líder
    # Notas menores (mismo patrón relativo)
    'ii': 2,   # Super tónica menor
    'iii': 4,  # Tercera menor
    'vi': 9,   # Submediante menor
    'vii': 11, # Líder menor
}

# Segundos de cada nota de calidad
QUALITIES = {
    'maj': [0, 4, 7],          # Mayoria
    'min': [0, 3, 7],          # Menor
    'dom7': [0, 4, 7, 10],     # Dominante 7ª
    'maj7': [0, 4, 7, 11],     # Mayor 7ª
    'min7': [0, 3, 7, 10],     # Menor 7ª
    'dim7': [0, 3, 6, 9],      # Disminuida 7ª
    'aug': [0, 4, 8],          # Aumentada
    '5': [0, 7],               # Ocasión 5ª
}

# Código de gramática para progresiones
# Ej: "I-vi-IV-V" = Tónica, Submediante, Subdominante, Dominante
#     "I-V-vi-IV" = Pop progression clásica
#     "ii-V-I" = Función clásica
#     "I-V-vi-III-IV-I-V" = Song structure

# Progresiones predefinidas (notas de la escala + cualidad)
POP_PROGRESSIONS = [
    {
        'name': 'I-V-vi-IV',
        'progression': ['I', 'V', 'vi', 'IV'],
        'quality': 'maj',
        'description': 'Progresión clásica pop',
        'chord_types': ['maj', 'maj', 'min', 'maj'],
    },
    {
        'name': 'I-vi-IV-V',
        'progression': ['I', 'vi', 'IV', 'V'],
        'quality': 'maj',
        'description': 'Progresión de la canción "Let It Be"',
        'chord_types': ['maj', 'min', 'maj', 'maj'],
    },
    {
        'name': 'I-V-vi-III-IV-I-V',
        'progression': ['I', 'V', 'vi', 'III', 'IV', 'I', 'V'],
        'quality': 'maj',
        'description': 'Progresión punta de lanza (The Sing-Along)',
        'chord_types': ['maj', 'maj', 'min', 'min', 'maj', 'maj', 'maj'],
    },
    {
        'name': 'I-V-IV-vi',
        'progression': ['I', 'V', 'IV', 'vi'],
        'quality': 'maj',
        'description': 'Progresión de la era 80s',
        'chord_types': ['maj', 'maj', 'maj', 'min'],
    },
]

REGGAE_PROGRESSIONS = [
    {
        'name': 'I-vi-IV-V',
        'progression': ['I', 'vi', 'IV', 'V'],
        'quality': 'maj',
        'description': 'Progresión de la bachata/reggae',
        'chord_types': ['maj', 'min', 'maj', 'maj'],
    },
    {
        'name': 'I-VII-I-VI',
        'progression': ['I', 'VII', 'I', 'VI'],
        'quality': 'maj',
        'description': 'Progresión del club Latino',
        'chord_types': ['maj', 'min', 'maj', 'min'],
    },
]

CLASSICAL_PROGRESSIONS = [
    {
        'name': 'ii-V-I',
        'progression': ['ii', 'V', 'I'],
        'quality': 'dom7',
        'description': 'Tonica de la función musical',
        'chord_types': ['min7', 'dom7', 'maj'],
    },
    {
        'name': 'I-IV-V-I',
        'progression': ['I', 'IV', 'V', 'I'],
        'quality': 'maj',
        'description': 'Tonica clásica de la canción',
        'chord_types': ['maj', 'maj', 'maj', 'maj'],
    },
    {
        'name': 'I-vi-IV-V',
        'progression': ['I', 'vi', 'IV', 'V'],
        'quality': 'maj',
        'description': 'Progresión del círculo de la mecánica',
        'chord_types': ['maj', 'min', 'maj', 'maj'],
    },
]


# ---------- Cálculo de acordes ----------

def get_scale_notes(root, quality='maj'):
    """Obtiene las notas de un acorde a partir de la raíz y calidad."""
    root_idx = SCALE_DEGREES[root]
    intervals = QUALITIES[quality]

    # Ajustar a pitch 0-127 (MIDI)
    notes = []
    for interval in intervals:
        note_idx = (root_idx + interval) % 12
        # Convertir a pitch 0-127 (asumiendo C3 = 48, A2 = 45)
        pitch = 48 + (note_idx * 2)  # ~2 semitones por grado promedio
        notes.append(pitch)

    return notes


def get_chord(root, quality='maj'):
    """Devuelve las notas del acorde."""
    return get_scale_notes(root, quality)


# ---------- Generación de MIDI ----------

def create_harmony_track(title, notes, channel=0):
    """Crea una pista MIDI con una armonía."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=title, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))

    if not notes:
        return track

    # Cada acorde dura 2 segundos (aprox 8 cuartos a 120 BPM)
    seconds_per_chord = 2.0
    ticks_per_beat = 480
    beats_per_second = 60.0 / 120.0  # 0.5 segundos por cuarto
    ticks_per_second = ticks_per_beat * beats_per_second

    for i, note in enumerate(notes):
        chord_time = i * ticks_per_second * 4  # 4 notas por acorde
        track.append(mido.Message('note_on', channel=channel, note=note, velocity=80, time=int(chord_time)))
        track.append(mido.Message('note_off', channel=channel, note=note, velocity=60, time=10))

    return track


def create_bass_track(title, progressions):
    """Crea una pista de bajo con la tríada de cada acorde."""
    track = mido.MidiTrack()
    track.append(mido.MetaMessage('track_name', name=title, time=0))
    track.append(mido.MetaMessage('set_tempo', tempo=500000, time=0))
    track.append(mido.MetaMessage('time_signature', numerator=4, denominator=4, time=0))

    bass_notes = []
    for prog in progressions:
        for chord in prog['progression']:
            root_name = chord if isinstance(chord, str) else chord.get('root', 'I')
            root_idx = SCALE_DEGREES.get(root_name, 0)
            bass_note = 36 + (root_idx * 2)  # C1, D1, E1, etc.
            bass_notes.append((bass_note, root_name))

    for i, (note, root) in enumerate(bass_notes):
        chord_time = i * 960  # 2 segundos a 120 BPM
        track.append(mido.Message('note_on', channel=1, note=note, velocity=70, time=int(chord_time)))
        track.append(mido.Message('note_off', channel=1, note=note, velocity=50, time=10))

    return track


def create_harmony_midi(progressions, output_file):
    """Crea un archivo MIDI con progresiones armónicas."""
    if not progressions:
        print('ERROR: No se proporcionaron progresiones', file=sys.stderr)
        return 1

    print(f'🎵 Generando progresiones armónicas MIDI')
    print(f'   Progresiones: {len(progressions)}')

    for i, prog in enumerate(progressions):
        print(f'   Progresión {i+1}: {prog["name"]}')

    # Crear pistas
    tracks = []

    # Pista 0: Voz armónica
    voice_notes = []
    for prog in progressions:
        for chord in prog['progression']:
            notes = get_chord(chord, prog.get('quality', 'maj'))
            voice_notes.extend(notes)

    tracks.append(create_harmony_track('Voice', voice_notes))

    # Pista 1: Bajo
    tracks.append(create_bass_track('Bass', progressions))

    # Pista 2: Arpegio
    arpeggio_notes = []
    for prog in progressions:
        for chord in prog['progression']:
            notes = get_chord(chord, prog.get('quality', 'maj'))
            # Arpegio ascendente - reverso
            arpeggio = notes + notes[::-1]
            arpeggio_notes.extend(arpeggio[::2])  # Saltos de 2

    tracks.append(create_harmony_track('Arpeggio', arpeggio_notes))

    # Crear archivo
    mid = mido.MidiFile()
    mid.ticks_per_beat = 480
    mid.tracks = tracks

    mid.save(output_file)

    print(f'   ✅ Guardado: {output_file}')
    return 0


def list_progressions():
    """Lista las progresiones disponibles."""
    print('🔥 Progresiones armónicas disponibles:')
    all_progs = POP_PROGRESSIONS + REGGAE_PROGRESSIONS + CLASSICAL_PROGRESSIONS
    for i, prog in enumerate(all_progs):
        print(f'  {i+1:2d}. {prog["name"]:30s} | {prog["description"]}')


def main():
    parser = argparse.ArgumentParser(
        description='Harmonic Circle Progressions MIDI Generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Ejemplos:
    python3 harmonic_circle.py --genre pop --out pop.mid
    python3 harmonic_circle.py --names "I-V-vi-IV" --out my_progression.mid
    python3 harmonic_circle.py list
        '''
    )
    parser.add_argument('--genre', '-g', help='Género (pop, reggae, classical)')
    parser.add_argument('--names', '-n', nargs='+', help='Progresiones específicas (ej: I-V-vi-IV, I-V-VI-IV)')
    parser.add_argument('--out', '-o', help='Archivo de salida')
    parser.add_argument('--list', '-l', action='store_true', help='Lista las progresiones disponibles')

    args = parser.parse_args()

    if args.list or args.genre == 'list':
        list_progressions()
        return

    if not args.genre and not args.names:
        print('ERROR: -n o -g son requeridos', file=sys.stderr)
        print('   Alelos: --list para ver progresiones disponibles', file=sys.stderr)
        sys.exit(1)

    if args.out is None:
        args.out = f'harmonic_{args.genre}.mid'

    # Seleccionar progresiones
    all_progs = POP_PROGRESSIONS + REGGAE_PROGRESSIONS + CLASSICAL_PROGRESSIONS

    if args.names:
        # Progresiones específicas
        progressions = []
        for name in args.names:
            for prog in all_progs:
                if prog['name'] == name:
                    progressions.append(prog)
                    break
            else:
                print(f'   ⚠️  Progresión no encontrada: {name}', file=sys.stderr)

    elif args.genre:
        genre_map = {
            'pop': POP_PROGRESSIONS,
            'reggae': REGGAE_PROGRESSIONS,
            'classical': CLASSICAL_PROGRESSIONS,
        }
        progressions = genre_map.get(args.genre.lower(), POP_PROGRESSIONS)

    # Crear MIDI
    sys.exit(create_harmony_midi(progressions, args.out))


if __name__ == '__main__':
    main()
