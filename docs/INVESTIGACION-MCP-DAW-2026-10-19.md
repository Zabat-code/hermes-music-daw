# MCP DAW: investigación de implementación (2026-10-19)

Investigación para construir un DAW que the agent (agente) y the human operator puedan
usar para **ajustar la calidad** de las piezas generadas. El MIDI no captura
palm mute, distorsión, timbre ni mezcla: eso se hace en el dominio del audio.

## 1. El problema real

El motor `hermesmusic.py` produce MIDI. FluidSynth lo convierte a audio con un
SoundFont General MIDI. Eso suena a **maqueta**, no a producción: GM no tiene
guitarra distorsionada real, no hay paneo por stem, no hay EQ, ni compresión, ni
mastering. Las piezas "suenan mejor" pero nunca sonarán a disco sin una etapa de
**mezcla y masterización** sobre stems separados.

La etapa que falta: **renderizar cada instrumento por separado (stems) → mezclar**.

## 2. Opciones evaluadas (con datos verificados)

| Opción | Qué es | Peso | Headless | Licencia | Veredicto |
|---|---|---|---|---|---|
| **Pedalboard** (Spotify) | Efectos de audio + VST3 en Python | **5 MB** | ✅ sí | GPL-3 (uso libre) | ✅ **instalado y funcionando** |
| **dawdreamer** | DAW completo en Python (JUCE): render VST, timeline | 40 MB | ✅ sí | GPL-3 | ⚪ viable, pesado |
| **REAPER** | DAW real; MCPs maduros (176/181/600+ tools) | 13.7 MB instalador | ⚠️ requiere GUI/X11 | Comercial ($60) | ⚪ portable install posible |
| **Ardour 8** | DAW libre en apt | 57 MB + deps | ⚠️ GUI | GPL-2 | ⚪ apt disponible |
| **LMMS** | Ya instalado | — | ✅ `lmms render` | GPL-2 | ⚠️ limitado |
| **ffmpeg** | 160 filtros de audio | ya instalado | ✅ sí | LGPL | ✅ complemento |

**Decisión:** empezar con **Pedalboard + ffmpeg** (0 instalaciones pesadas, 100%
headless, funciona ya). REAPER queda como fase 2 si se quiere edición interactiva.

## 3. Repos relacionados encontrados (reales, verificados por búsqueda)

MCPs de DAW que existen y sirven de referencia de diseño:

| Repo | Stars | Qué hace | Nota |
|---|---|---|---|
| `TwelveTake-Studios/reaper-mcp` | 83 | 176 tools: mixing, mastering, MIDI, medición EBU | Bridge Lua + JSFX; REAPER stock |
| `xDarkzx/reaper-mcp` | 100 | 181 tools: composición, mezcla, mastering, QC | Apache-2.0 |
| `fadelabs/phantom` | 39 | **MCP + skills de ingeniería de audio, headless con Pedalboard** | ⭐ **el más cercano a lo que queremos** |
| `HighVoltSound/ableton-auto-mix-mcp` | 1 | Auto-mezcla/master por género, 11 perfiles | Perfiles de estilo JSON |
| `rosasynthesiz/flstudio-mcp` | 94 | 67 tools, "Mix Doctor", FL Studio | Solo Win/macOS |
| `guvense/hellyee` | 6 | Ableton por OSC, mide y ajusta en bucle | Cierra el lazo medición→ajuste |
| `Cybolic/LinReaper` | — | Instalador de REAPER para Linux (Wine) | Alternativa vieja |

**Patrón común de los buenos:** miden → deciden → aplican → **vuelven a medir**.
No adivinan. `phantom` y `hellyee` lo declaran explícitamente.

## 4. Lo que YA está implementado y verificado (2026-10-19)

### `~/.hermes/skills/hermes-music/scripts/mix_engine.py`
Motor de mezcla headless con Pedalboard. Funciona de verdad:

- Carga stems WAV por rol (drums, bass, rhythm_guitar_L/R, lead_guitar_L/R)
- **Cadena por rol:** HPF (evita enmascaramiento), EQ de presencia, compresión
- **Paneo real** mid/side (no solo un número en el MIDI)
- **Bus master:** HPF + corte de barro (300 Hz) + aire (8 kHz) + compresión de bus
  + trim + limitador a -1 dBTP
- **Perfiles por género** (`power_metal`, `balanced`) con valores de partida
- Devuelve métricas: pico, RMS, stems usados/ignorados

### Verificado con la pieza real "Iron Determination v3"
```
6 stems WAV renderizados (uno por instrumento) desde el MIDI
mix_engine.py --profile power_metal
  → peak_db: -1.97 (sin clipping)
  → rms_db:  -19.3
  → 180.5 s
OGG final: ~/Desktop/iron_determination_v3_MEZCLADO.ogg
  → pico -0.61 dB, RMS -15.2 dB, 180.000 s, 44.1 kHz
```

### Hallazgo técnico
La suma de 6 stems satura a **0 dB (clipping)** si no se recorta antes del
limitador. Se añadió un `Gain(trim=-3 dB)` en el bus master. Sin ese recorte, el
limitador no puede evitar el clipping porque ya entra saturado.

## 5. Arquitectura propuesta del MCP DAW

### Fase 1 — Mezcla headless (implementable ya)
```
hermes-daw-mcp (FastMCP, stdio)
├── list_profiles()              → perfiles de mezcla disponibles
├── render_stems(midi, outdir)   → separa el MIDI en WAV por instrumento
├── analyze_stem(wav)            → pico, RMS, espectro, correlación estéreo
├── analyze_masking(dir)         → qué pares de stems se tapan (solapamiento de bandas)
├── auto_mix(dir, profile)       → aplica la cadena del perfil, devuelve métricas
├── apply_eq(wav, band, gain)    → EQ puntual sobre un stem
├── apply_comp(wav, ...)         → compresión puntual
├── master(wav, target_lufs)     → cadena de master con objetivo de loudness
├── compare_to_reference(a, b)   → compara contra una referencia
└── release_check(wav, profile)  → veredicto listo/necesita trabajo (LUFS/TP/LRA)
```
Cada tool: **mide antes → aplica → mide después → reporta la diferencia**.
Nunca "suena mejor" sin evidencia numérica.

### Fase 2 — Edición interactiva (si se quiere)
REAPER **portable install** (13.7 MB, corre sin instalar): permite edición manual
of the operator on el mismo proyecto que el agente mezcla. Requiere X11 (ya hay
`DISPLAY=:0`). Se conectaría con un bridge tipo `reaper-mcp`.

### Fase 3 — Medición perceptual
`librosa` para features (MFCC, centroide espectral, tempo, tonalidad) y comparación
contra referencias de power metal. Cierra el lazo sin oídos humanos.

## 6. Restricciones reales de este equipo

- **Disco al 93%** (8.2 GB libres en `/dev/sda6`). Un DAW con samples pesa mucho;
  los stems WAV de 3 min ya ocupan 30 MB cada uno. Hay un disco externo de 298 GB
  y an external disk para material pesado.
- **CPU i3-6006U, sin GPU, 16 GB RAM.** El render es secuencial; funciona pero lento
  (el render de stems tomó ~2 min).
- **Sin JACK/ALSA de estudio.** La mezcla es offline (archivos), no en tiempo real.
  Eso es una ventaja: no necesita tarjeta de sonido.

## 7. Lo que NO puede hacer el MCP (honestidad)

- **No puede juzgar si suena bien.** Mide (LUFS, pico, espectro, correlación) y
  aplica cadenas conocidas. La decisión estética es humana.
- **No inventa timbres.** Con GM, una guitarra suena a guitarra GM. Para sonar a
  metal real hacen falta samples/VST de calidad (fase 2+).
- **No reemplaza a un ingeniero.** Es un asistente que deja la mezcla en un punto
  de partida medible y consistente.

## 8. Próximos pasos concretos

1. Construir el MCP FastMCP con las 10 tools de la fase 1.
2. Añadir análisis espectral real (numpy FFT o librosa) para el detector de masking.
3. Probar el lazo completo: MIDI → stems → auto_mix → master → release_check.
4. Evaluar REAPER portable if the operator wants edición manual.
5. Documentar el flujo en la skill `hermes-music` con el guardarraíl correspondiente.

## Fuentes

- Búsquedas web sobre MCPs de DAW y librerías de audio Python (resultados citados arriba).
- `pip download`/`pip install` verificados: pedalboard 0.9.26 (5 MB), dawdreamer 0.9.0 (40 MB).
- Prueba real: `mix_engine.py` sobre 6 stems de "Iron Determination v3".
- `~/.hermes/documentacion/hermesmusic/INVESTIGACION-POWER-METAL-2026-10-19.md`
- `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md`
