# Production Effects MIDI Mapper — Technical Reference

This reference documents the **Production Effects MIDI Mapper**, a skill that
applies production effects to MIDI files, based on the analysis of the video
**MOTOMAMI: an in-depth musical analysis ft. Rosalía** by Jaime Altozano.

## Architecture

```
input.mid → effects_apply.py --effect E --params P → output.mid
```

The mechanism is **editing MIDI events** in the file without converting to another format:
- `pitch bend` → autotune, pitch shift
- `control_change` → filter, distortion, reverb, chorus, flanger, vocoder
- `note_on` → velocity, sidechain (note_off)

## Effects Mapping to MIDI Events

| Effect | MIDI event | Parameter | MIDI range |
|--------|-------------|-----------|--------------|
| `autotune` | `pitch_bend` + `CC1 (modulation)` | 12–50 semitones | 0–16383 |
| `pitch_shift` | `pitch_bend` (constant) | `semitones` | -127–127 |
| `filter` | `CC74 (cutoff)` + `CC71 (resonance)` | 80–200 Hz | 0–127 |
| `distortion` | `CC11 (expression)` + `velocity` | 0–0.4 intensity | 0–127 |
| `reverb` | `CC91 (wet)` + `CC94 (damping)` | 0.3–0.7 wet | 0–127 |
| `sidechain` | `CC11` + `note_off` (backmask) | -12 dB | 0–127 |
| `vocoder` | `CC73 (carrier)` + `CC10 (expression)` | 73 carrier | 0–127 |
| `chorus` | `CC66 (depth)` + `CC58 (rate)` | 0.5 depth | 0–127 |
| `flanger` | `CC11` + `CC106 (speed)` | 0.5 depth / 0.2 rate | 0–127 |

## Production Recipes (from MOTOMAMI)

The **MOTOMAMI** video transcription identified these techniques:

| Recipe | Effects | Context |
|--------|---------|----------|
| `motomami_voice` | autotune + filter + no reverb | Voice without reverb, no backing vocals; filter removes highs |
| `motomami_drums` | filter + distortion | Aggressive drums, cold filter on highs |
| `minimalist` | reverb + low cutoff | Minimal production, few instruments |
| `atlas` | chorus + sidechain | Extreme collage with complex mixes |

### Recipe Usage Example

```python
from effects_apply import apply_effects

# Apply motomami recipe to voice (channel 1)
apply_effects('input.mid', 'output.mid', 'autotune',
    params={'min_semitone': 12, 'max_semitone': 50, 'velocity': 0.8}
)
```

## Applied Musical Principles

### 1. Dry Voice (Without Reverb)
According to MOTOMAMI: "they usually put their voice dry, without reverb or backing vocals."
- CC91 (reverb depth) = 0 for voice channel
- CC94 (damping) = 0

### 2. Filter for Highs
"The filter is to remove the high frequencies". It is the best friend of the voice.
- CC74 (cutoff) in 80–200 Hz range for low frequencies
- CC71 (resonance) at a moderate value

### 3. Aggressive Autotune
For effect (not neutral correction):
- pitch bend 12–50 semitones
- CC1 value of 12–50 to limit correction

### 4. Minimalist vs. Maximalist Production
- Minimalist: few instruments, clean channels
- Maximalist (collage): multiple layers, complex mixes

### 5. Distortion
For an aggressive effect:
- CC11 (expression) at 0.4–0.6
- velocity spikes on important notes

## Verification

After applying an effect, validate the MIDI:

```bash
python3 effects_apply.py input.mid output.mid --effect autotune
python3 -c "import mido; m = mido.MidiFile('output.mid'); print(f'pistas: {len(m.tracks)}, tiempo: {m.length:.2f}s')"
```

Verify that the tracks have balanced `note_on`/`note_off` and that the total
duration is consistent with the original.
