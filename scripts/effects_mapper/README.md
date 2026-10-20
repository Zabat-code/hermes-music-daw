---
name: effects_mapper
description: Mapea efectos de producción (autotune, filtro, distorsión, reverb, sidechain, vocoder, pitch shift) a eventos MIDI. Basado en análisis del canal de Jaime Altozano.
version: 1.0.0
platform: linux
inputs:
  - midi_file: path | .mid/.midi
  - effect_name: string | autotune | pitch_shift | filter | distortion | reverb | sidechain | vocoder | chorus | flanger
  - output_file: string | path .mid
  - params: dict | opcional
dependencies: [mido, music21]
triggers:
  - aplicar efectos a MIDI
  - mapeo de producción
  - efectos de voz
---

# Production Effects MIDI Mapper

Motor de efectos de producción para MIDI, basado en el análisis del video
**MOTOMAMI: an in-depth musical analysis ft. Rosalía** (Jaime Altozano).
Extrae de la transcripción 10 técnicas de producción que se pueden mapear a
eventos MIDI.

## Efectos Implementados

| Efecto | Tecnología | Eventos MIDI generados |
|--------|------------|------------------------|
| `autotune` | Auto-Tune (pitch correction) | pitch bend, CC1 |
| `pitch_shift` | Pitch shifting | pitch bend, velocity |
| `filter` | Filtro pasa-baja/aguda | CC74, CC71 |
| `distortion` | Distorsión | CC11, velocity spikes |
| `reverb` | Reverberación | CC91, CC94 |
| `sidechain` | Ducking de acompañamiento | CC11, backmask |
| `vocoder` | Vocoder | CC10 (expression), CC73 |
| `chorus` | Coros/eco | CC66, CC58 |
| `flanger` | Flanger | CC11, CC106 |

## Uso

```bash
python3 ~/.hermes/skills/hermes-music/scripts/effects_mapper/effects_apply.py input.mid output.mid --effect autotune --params "{velocity: 0.8}"

# Lista recetas disponibles
python3 ~/.hermes/skills/hermes-music/scripts/effects_mapper/effects_apply.py list
```

## Recetas

```python
RECIPES = {
    'motomami': {
        'effect': 'autotune',
        'params': {'min_semitone': 12, 'max_semitone': 50, 'velocity': 0.8},
        'description': 'Voz con autotune agresivo, voz seca, filtro en agudos'
    },
    'drum_loop': {
        'effect': 'filter',
        'params': {'cutoff_low': 80, 'cutoff_high': 200},
        'description': 'Batería con filtro que enfría los agudos'
    }
}
```

## Efectos Músicales desde el Video

- **Voz:** sin reverb, sin coros, voz desnuda (channel 1)
- **Filtro:** quitar frecuencias agudas para textura
- **Distorsión:** agresiva, sature la voz
- **Producción minimalista:** usar pocos instrumentos, canal 1 voz
- **Autotune:** pitch correction agresivo para efecto
