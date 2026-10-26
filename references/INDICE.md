# ÍNDICE DE DECISIÓN — hermes-music

**Regla de oro:** este archivo es lo ÚNICO que se lee al empezar. Las referencias
completas se cargan **solo** cuando la tarea las necesita. No leer todo.

## 1. Elige la tarea

| Tarea | Qué necesitas | Referencia | Tamaño |
|---|---|---|---|
| **Componer arreglo denso** (metal/rock) | Esqueleto nota por nota, grooves, fills | `scripts/example_dense_arrangement.py` | 19.7 KB |
| **Diseñar batería metal** | Comparativa de grooves y patrones | `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md` | 4.7 KB |
| **Armonía y teoría** | Progresiones, motivos, forma | `references/teoria-composicion.md` | 6.4 KB |
| **Renderizar y medir audio** | FluidSynth, picos, duración | `references/rendering.md` | 4.7 KB |
| **Entender la arquitectura** | Cómo encajan los módulos | `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md` | 5.8 KB |
| **Auditar una pieza existente** | Puertas del contrato | `scripts/audit_arrangement.py` | 16.4 KB |
| **Género concreto** | Perfil y estrategia armónica | `references/genre_profiles.json` (100 perfiles) | 134 KB |
| **Investigar un fallo** | Errores ya documentados | `~/.hermes/documentacion/hermesmusic/ERROR-REPETIDO-2026-10-19.md` | 4.5 KB |

## 2. Ruta según el género / complejidad

| Género | Perfil | Variante obligatoria |
|---|---|---|
| metal, rock, alternative | requiere `--variant` | sí (hard_rock, soft_rock…) |
| blues, ambient, baroque, death_metal, black_metal, doom_metal | directo | no |
| jazz | requiere `--variant` | sí (bebop, modal, swing_small_combo) |
| classical | requiere `--variant` | sí (classical_period, concert_music) |
| folk, country, bluegrass | requiere `--variant` | sí |

**Complejidad no es género.** Piano solo puede ser virtuoso; un conjunto puede ser
sencillo. El eje de arreglo es independiente: instrumento solo / conjunto pequeño /
arreglo denso.

## 3. Controles obligatorios (no negociables)

**Comunes:**
- Notas cerradas y duración positiva
- Duración exacta pedida
- MIDI válido (`validate_midi` sin problemas)
- Audio sin saturación (pico <= -1 dB)

**Específicos:**
- **Piano:** pedal, articulación, registro
- **Arreglo denso:** colisiones de percusión, registro, espacio entre capas
  (máx. 2 piezas de kit por ataque)

**La escucha no se sustituye por métricas.** Entregar como "maqueta auditada
estructuralmente; calidad sonora pendiente" si no se escuchó.

## 4. Punto de entrada obligatorio

```bash
PY=python
S=scripts
"$PY" "$S/example_dense_arrangement.py" --plan plan.json
"$PY" "$S/composition_guard.py" plan.json --out piece.mid -- composer.py --out '{draft}'
"$PY" "$S/audit_arrangement.py" piece.mid --json revision.json
"$PY" "$S/composition_guard.py" --verify piece.mid
```

**No entregar un MIDI generado con `mido`, `build_track`, `render_song` o `compose`
como pieza terminada.** El guard audita y publica con certificado; falla con exit 1.

## 5. Puertas del contrato denso (resumen)

- Máx. **2 piezas de batería** por ataque
- >=5 velocidades distintas y rango >=10 en pistas con >=16 notas
- >=3 patrones de batería, ninguno >50% de compases activos
- >=3 niveles de densidad; contraste >=2 entre secciones
- >=1 instrumento armónico con >=1 compás sin notas
- Registros: bass 24-60, rhythm_guitar 40-84, lead 48-90, piano 36-84,
  pad/strings 36-90, choir 36-84. **Rol desconocido: abortar.**
- Fills: rechazar periodicidad de 4 compases

**Estas no son leyes musicales** — son contratos locales de claridad y contraste.
Otro estilo requiere diseñar y probar un perfil, **nunca desactivar puertas**.

## 6. Verificación de estilo con CLAP (brújula, no veredicto)

Antes o después de renderizar, se puede comprobar si el audio va por el estilo
pedido usando **CLAP** (`laion/larger_clap_music_and_speech`, 194M, ya instalado
en `~/Modelo/clap`). Carga en ~1 s y corre en CPU.

```bash
PY=~/.hermes/venvs/hermes-3.12/bin/python
"$PY" scripts/clap_check.py pieza.ogg --compare \
  "power metal with double bass drum" \
  "classical orchestral with strings" \
  "electronic dance with synths"
```

Salida: similitud (0-100) por descripción y cuál gana.

**Límites honestos:**
- CLAP evalúa **parecido de estilo**, no calidad, ni gusto, ni mezcla.
- No sustituye la escucha humana: ese es el veredicto final.
- Sirve para detectar a tiempo que la pieza no es lo pedido y evitar renders a ciegas.
- El script decodifica solo a **48 kHz mono** (requisito de CLAP).
- Usa `pooler_output` (no el tensor crudo) — detalle técnico ya resuelto.

## 7. Lectura de partitura (sin audio) — detecta escritura rara

El MIDI **ya es** la partitura en digital: leerlo da lo mismo que leer la imagen
de MuseScore, sin OCR. `score_check.py` reproduce la lectura visual:

```bash
python3 scripts/score_check.py pieza.mid
python3 scripts/score_check.py pieza.mid --threshold 76   # E5 por defecto
```

Cinco mediciones: densidad vertical (notas a la vez), registro agudo (notas por
encima del umbral), ligaduras/retrigger, distribución por octava y haces.

**Úsalo ANTES de renderizar:** si una pista aparece al >40% en registro agudo,
se corrige antes de gastar CPU en audio. Umbral de agudez ajustable (`--threshold`).

**Límites:** detecta problemas de *escritura*, no de gusto ni mezcla. No detecta
timbre directamente (el programa GM sí se reporta). No sustituye la escucha.

## 8. Errores ya documentados (no repetir)

- **Numerales romanos en `parse_chord`:** `I`, `ii`, `V` lanzan `ValueError`.
  Usar acordes directos: `E`, `G#m`, `A`, `B`.
- **Batería con 3+ piezas simultáneas:** el auditor lo rechaza. Redistribuir.
- **Acordes `Maj7`/`maj7`:** no soportados. Simplificar a mayor con fallback a la raíz.
- **Rellenar con el mismo acorde repetido:** produce "ruido mecánico". Usar grooves
  por sección y variación de frases.
