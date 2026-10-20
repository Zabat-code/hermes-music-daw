# Production Effects MIDI Mapper — Referencia Técnica

Esta referencia documenta el **Production Effects MIDI Mapper**, una habilidad que
aplica efectos de producción a archivos MIDI, basado en el análisis del video
**MOTOMAMI: an in-depth musical analysis ft. Rosalía** de Jaime Altozano.

## Arquitectura

```
input.mid → effects_apply.py --effect E --params P → output.mid
```

El mecanismo es **editar eventos MIDI** del archivo sin convertir a otro formato:
- `pitch bend` → autotune, pitch shift
- `control_change` → filtro, distorsión, reverb, chorus, flanger, vocoder
- `note_on` → velocity, sidechain (note_off)

## Mapeo de Efectos → Eventos MIDI

| Efecto | Evento MIDI | Parámetro | Rango (MIDI) |
|--------|-------------|-----------|--------------|
| `autotune` | `pitch_bend` + `CC1 (modulation)` | 12–50 semitones | 0–16383 |
| `pitch_shift` | `pitch_bend` (constante) | `semitones` | -127–127 |
| `filter` | `CC74 (cutoff)` + `CC71 (resonance)` | 80–200 Hz | 0–127 |
| `distortion` | `CC11 (expression)` + `velocity` | 0–0.4 intensidad | 0–127 |
| `reverb` | `CC91 (wet)` + `CC94 (damping)` | 0.3–0.7 wet | 0–127 |
| `sidechain` | `CC11` + `note_off` (backmask) | -12 dB | 0–127 |
| `vocoder` | `CC73 (carrier)` + `CC10 (expression)` | 73 carrier | 0–127 |
| `chorus` | `CC66 (depth)` + `CC58 (rate)` | 0.5 profundidad | 0–127 |
| `flanger` | `CC11` + `CC106 (speed)` | 0.5 profundidad / 0.2 tasa | 0–127 |

## Recetas de Producción (desde MOTOMAMI)

La transcripción del video **MOTOMAMI** identificó estas técnicas:

| Receta | Efectos | Contexto |
|--------|---------|----------|
| `motomami_voice` | autotune + filter + no reverb | Voz sin reverb, sin coros; filtro quita agudos |
| `motomami_drums` | filter + distortion | Batería "agresiva", filtro frío en agudos |
| `minimalist` | reverb + cutoff bajo | Poca producción, instrumentos pocos |
| `atlas` | chorus + sidechain | Collage extremo con mezclas complejas |

### Ejemplo de uso de recetas

```python
from effects_apply import apply_effects

# Aplicar receta motomami a voz (canal 1)
apply_effects('input.mid', 'output.mid', 'autotune',
    params={'min_semitone': 12, 'max_semitone': 50, 'velocity': 0.8}
)
```

## Principios Musicales Aplicados

### 1. Voz "seca" (sin reverb)
Según MOTOMAMI: "por delante suele poner su voz sin reverb y sin coros".
- CC91 (reverb depth) = 0 para canal de voz
- CC94 (damping) = 0

### 2. Filtro para agudos
"El filtro es quitar las frecuencias agudas". Es el mejor amigo de la voz.
- CC74 (cutoff) en rango 80–200 Hz para baja frecuencia
- CC71 (resonance) a un valor moderado

### 3. Autotune agresivo
Para efecto (no para corrección neutral):
- pitch bend 12–50 semitones
- CC1 valor de 12–50 para limitar la corrección

### 4. Producción minimalista vs. maximalista
- Minimalista: pocos instrumentos, canales limpios
- Maximalista (collage): capas multiples, mezclas complejas

### 5. Distorsión
Para efecto de agresividad:
- CC11 (expression) a 0.4–0.6
- velocity spikes en notas importantes

## Verificación

Después de aplicar un efecto, valida el MIDI:

```bash
python3 effects_apply.py input.mid output.mid --effect autotune
python3 -c "import mido; m = mido.MidiFile('output.mid'); print(f'pistas: {len(m.tracks)}, tiempo: {m.length:.2f}s')"
```

Verifica que las pistas tengan `note_on`/`note_off` balanceados y que el tiempo
total sea coherente con la duración original.
