---
name: effects_mapper
description: Maps production effects (autotune, filter, distortion, reverb, sidechain, vocoder, pitch shift) to MIDI events. Based on Jaime Altozano's channel analysis.
version: 1.0.0
platform: linux
inputs:
  - midi_file: path | .mid/.midi
  - effect_name: string | autotune | pitch_shift | filter | distortion | reverb | sidechain | vocoder | chorus | flanger
  - output_file: string | path .mid
  - params: dict | optional
dependencies: [mido, music21]
triggers:
  - apply effects to MIDI
  - production mapping
  - vocal effects
---

# Production Effects MIDI Mapper

Production effects engine for MIDI, based on the analysis of the video
**MOTOMAMI: an in-depth musical analysis ft. Rosalía** (Jaime Altozano).
Extracts from the transcription 10 production techniques that can be mapped to
MIDI events.

## Implemented Effects

| Effect | Technology | Generated MIDI events |
|--------|------------|------------------------|
| `autotune` | Auto-Tune (pitch correction) | pitch bend, CC1 |
| `pitch_shift` | Pitch shifting | pitch bend, velocity |
| `filter` | Low-pass filter | CC74, CC71 |
| `distortion` | Distortion | CC11, velocity spikes |
| `reverb` | Reverberation | CC91, CC94 |
| `sidechain` | Ducking of accompaniment | CC11, backmask |
| `vocoder` | Vocoder | CC10 (expression), CC73 |
| `chorus` | Chorus/echo | CC66, CC58 |
| `flanger` | Flanger | CC11, CC106 |

## Usage

```bash
python3 the skill's scripts/effects_mapper/effects_apply.py input.mid output.mid --effect autotune --params "{velocity: 0.8}"

# List available recipes
python3 the skill's scripts/effects_mapper/effects_apply.py list
```

## Recipes

```python
RECIPES = {
    'motomami': {
        'effect': 'autotune',
        'params': {'min_semitone': 12, 'max_semitone': 50, 'velocity': 0.8},
        'description': 'Voice with aggressive autotune, dry voice, filter on highs'
    },
    'drum_loop': {
        'effect': 'filter',
        'params': {'cutoff_low': 80, 'cutoff_high': 200},
        'description': 'Drums with filter that cools the highs'
    }
}
```

## Musical Effects from the Video

- **Voice:** no reverb, no backing vocals, dry voice (channel 1)
- **Filter:** remove high frequencies for texture
- **Distortion:** aggressive, saturates the voice
- **Minimalist production:** use few instruments, channel 1 voice
- **Autotune:** aggressive pitch correction for effect
