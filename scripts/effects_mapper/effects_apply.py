#!/usr/bin/env python3
"""
Production Effects MIDI Mapper
===============================

Experimental MIDI event edits inspired by the production techniques in
Jaime Altozano's video "MOTOMAMI: an in-depth musical analysis ft. Rosalia".

Effect names describe intentions, not functioning audio DSP. Known defects:
autotune/pitch_shift use invalid Mido note attributes; filter/sidechain can
produce invalid controller values; sidechain's note-off branch is unreachable.
Per-track exceptions are warnings and do not necessarily make the CLI fail.
See references/effects_mapper.md for the actual behavior of all nine names.

Usage:
    python3 effects_apply.py input.mid output.mid --effect autotune --params "..."

Parameters must be valid JSON. The CLI does not dispatch a list subcommand;
call list_effects() from Python to inspect the historical effect metadata.
"""

import sys
import json
import argparse
from pathlib import Path
import mido


# ---------- Effect recipes ----------

EFFECTS = {
    'autotune': {
        'params': {
            'min_semitone': 12,
            'max_semitone': 50,
            'velocity': 0.8,
        },
        'description': 'Autotune: aggressive pitch correction for vocals',
        'notes': [
            'Apply pitch bend to notes (channel 1 vocals)',
            'Use CC1 (modulation) with a 12-50-cent envelope',
            'Reduce reverb and chorus for "dry" vocals',
        ],
    },
    'pitch_shift': {
        'params': {
            'semitones': 0,
            'velocity': 0.9,
        },
        'description': 'Pitch shifting: transpose the key up/down',
        'notes': [
            'Apply constant pitch bend (fixed semitones)',
            'Use velocity to control intensity',
        ],
    },
    'filter': {
        'params': {
            'cutoff_low': 80,
            'cutoff_high': 200,
            'resonance': 20,
            'velocity': 0.8,
        },
        'description': 'Low-pass/high-pass filter for texture',
        'notes': [
            'Apply CC74 (filter cutoff) from cutoff_low to cutoff_high',
            'CC71 (filter resonance) with the resonance value',
            'Remove high frequencies (per the MOTOMAMI analysis)',
        ],
    },
    'distortion': {
        'params': {
            'intensity': 0.4,
            'velocity': 0.9,
        },
        'description': 'Saturation distortion',
        'notes': [
            'Apply CC11 (expression) with distortion intensity',
            'Add velocity spikes for aggression',
            'Per the analysis: "Heavily distorted"',
        ],
    },
    'reverb': {
        'params': {
            'wet': 0.3,
            'dry': 0.7,
            'room': 30,
            'velocity': 0.8,
        },
        'description': 'Spatial reverberation',
        'notes': [
            'Apply CC91 (reverb depth) at the wet level',
            'CC94 (Effects 4 Depth) based on room; not standard reverb damping',
            'Vocals without reverb (dry), per the MOTOMAMI analysis',
        ],
    },
    'sidechain': {
        'params': {
            'duck_amount': -12,
            'attack': 5,
            'release': 20,
            'velocity': 0.8,
        },
        'description': 'Accompaniment ducking',
        'notes': [
            'Apply backmask (note_off) to accompaniment when vocals enter',
            'CC11 (expression) with duck_amount attenuation',
            'Fast attack, longer release',
        ],
    },
    'vocoder': {
        'params': {
            'carrier': 73,
            'modulation': 10,
            'velocity': 0.8,
        },
        'description': 'Vocoder: voice as modulator',
        'notes': [
            'Rewrite CC73 (attack time); no carrier is generated',
            'Rewrite CC10 (pan), not expression',
            'No formant or vocoder DSP is implemented',
        ],
    },
    'chorus': {
        'params': {
            'depth': 0.5,
            'rate': 0.3,
            'velocity': 0.8,
        },
        'description': 'Chorus/echo for spatial width',
        'notes': [
            'Rewrite CC66 (sostenuto) with depth; not standard chorus depth',
            'Rewrite CC58 based on rate; not a standard chorus-rate control',
            '"Wild mixes" effect',
        ],
    },
    'flanger': {
        'params': {
            'depth': 0.5,
            'speed': 0.2,
            'velocity': 0.8,
        },
        'description': 'Flanger: sweeping effect',
        'notes': [
            'Apply CC11 (expression) with depth',
            'Rewrite CC106 based on speed; not a standard flanger-speed control',
            'For a melodic "swirl" effect',
        ],
    },
}


# ---------- Effect modules ----------

def apply_autotune(track, params):
    """Attempt pitchbend assignment on channel-0 notes; invalid for Mido notes."""
    min_semitone = params.get('min_semitone', 12)
    max_semitone = params.get('max_semitone', 50)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'note_on' and msg.channel == 0:
            # Legacy attempt: note_on does not support a pitchbend attribute.
            bend = int(min_semitone + (max_semitone - min_semitone) * msg.velocity * 0.5)
            msg.pitchbend = bend
            msg.velocity = int(msg.velocity * velocity)
        elif msg.type == 'control_change':
            # CC1 = modulation
            if msg.control == 1:
                msg.value = int(12 + (50 - 12) * msg.value * 0.5)


def apply_pitch_shift(track, params):
    """Attempt transposition; msg.pitch is not a valid note_on attribute."""
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
    """Apply filter: CC74 (cutoff) and CC71 (resonance)."""
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
    """Apply distortion: CC11 + velocity spikes."""
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
    """Rewrite existing CC91/CC94 and velocity; synthesizer-dependent result."""
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
    """Legacy ducking attempt: default CC11 is invalid; note-off branch is unreachable."""
    duck_amount = params.get('duck_amount', -12)
    attack = params.get('attack', 5)
    release = params.get('release', 20)
    velocity = params.get('velocity', 0.8)

    for msg in track:
        if msg.type == 'control_change':
            if msg.control == 11:
                msg.value = int(duck_amount * 127)
        elif msg.type == 'note_on' and msg.channel == 1:
            # Vocals on channel 1; backmask (note_off) the accompaniment on channels 0-8
            if msg.channel != 1:
                msg.note_off()


def apply_vocoder(track, params):
    """Rewrite CC73 (attack time), CC10 (pan) and velocity; no vocoder DSP."""
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
    """Apply chorus: CC66 and CC58."""
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
    """Apply flanger: CC11 and CC106."""
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


# ---------- Main logic ----------

def apply_effects(midi_file, output_file, effect_name, params=None):
    """
    Apply an effect to a MIDI file.

    Args:
        midi_file: Path to the input MIDI file
        output_file: Path to the output MIDI file
        effect_name: Effect name
        params: Optional parameter dictionary

    Returns:
        int: Status code (0 = OK, 1 = error)
    """
    if not Path(midi_file).exists():
        print(f'ERROR: File not found: {midi_file}', file=sys.stderr)
        return 1

    if effect_name not in EFFECT_FUNCTORS:
        print(f'ERROR: Unknown effect "{effect_name}"', file=sys.stderr)
        print(f'   Available effects: {", ".join(EFFECT_FUNCTORS.keys())}', file=sys.stderr)
        return 1

    effect = EFFECT_FUNCTORS[effect_name]
    if params is None:
        params = EFFECTS[effect_name]['params']

    # Read MIDI
    try:
        mid = mido.MidiFile(midi_file)
    except Exception as e:
        print(f'ERROR: Could not read {midi_file}: {e}', file=sys.stderr)
        return 1

    print(f'Reading: {midi_file}')
    print(f'   Duration: {mid.length:.2f}s | {len(mid.tracks)} tracks | tpb: {mid.ticks_per_beat}')

    # Apply the effect to each track
    applied = []
    for i, track in enumerate(mid.tracks):
        # Only apply to tracks with notes
        has_notes = any(msg.type in ('note_on', 'note_off') for msg in track)
        if not has_notes:
            continue

        try:
            effect(track, params)
            applied.append(i)
        except Exception as e:
            print(f'   WARNING: Error on track {i}: {e}', file=sys.stderr)

    print(f'   Effect "{effect_name}" applied to {len(applied)}/{len(mid.tracks)} tracks')

    # Save
    try:
        mid.save(output_file)
        print(f'Saved: {output_file}')
        return 0
    except Exception as e:
        print(f'ERROR: Could not save {output_file}: {e}', file=sys.stderr)
        return 1


def list_effects():
    """Print historical effect intentions/parameters, not verified capabilities."""
    print('Available effects:')
    for name, data in EFFECTS.items():
        print(f'  {name:15s} | {data["description"]}')
        print(f'    Parameters: {json.dumps(data["params"], indent=4).replace(chr(10), chr(10)+"    ")}')
        print(f'    Notes: {data["notes"]}')


def main():
    parser = argparse.ArgumentParser(
        description='Production Effects MIDI Mapper',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Examples (legacy; inspect warnings):\n    python3 effects_apply.py input.mid output.mid --effect distortion\n    python3 effects_apply.py input.mid output.mid --effect distortion --params \'{"intensity": 0.4, "velocity": 0.9}\'\n    Metadata: call list_effects() from Python; no CLI list subcommand.'
    )
    parser.add_argument('input', help='Input MIDI file')
    parser.add_argument('output', help='Output MIDI file')
    parser.add_argument('--effect', '-e', required=True, help='Effect name')
    parser.add_argument('--params', '-p', help='JSON parameters (e.g.: {"cutoff_low": 60, "cutoff_high": 150})')

    args = parser.parse_args()

    params = None
    if args.params:
        try:
            params = json.loads(args.params)
        except json.JSONDecodeError as e:
            print(f'ERROR: Invalid JSON in --params: {e}', file=sys.stderr)
            sys.exit(1)

    sys.exit(apply_effects(args.input, args.output, args.effect, params))


if __name__ == '__main__':
    main()
