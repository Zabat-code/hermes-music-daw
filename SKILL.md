---
name: hermes-music
description: Componer, renderizar y analizar MIDI con mido.
version: 1.0.0
author: the hermes-music-daw authors
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [music, midi, composition, audio, fluidsynth, mido]
    category: creative
---

# Hermes Music Skill

Guía vigente del paquete autónomo: [PROTOCOL.md](PROTOCOL.md). Instalación y MCP:
[README.md](README.md). Ejecutar ejemplos desde la raíz con el venv activado.
Las rutas antiguas de documentos históricos no son requisitos de instalación.

## COMPOSICIÓN: PROTOCOLO OBLIGATORIO ANTES DE ESCRIBIR MÚSICA

**Entrada única para composición nueva de arreglos densos: `scripts/composition_guard.py`.**
No entregar un MIDI generado directamente con `mido`, `build_track`, `gen`,
`compose` o `render_song` como pieza terminada. El motor audita `render_song`
antes de guardar; la entrada obligatoria añade lectura, decisiones verificables
y publicación con certificado. Un fallo devuelve **exit 1 y ABORTA** la entrega.

1. **LEER**, antes de escribir eventos: [comparativa de batería](docs/COMPARATIVA-BATERIA-METAL-2026-10-19.md),
   [arquitectura](docs/TEORIA-Y-ARQUITECTURA-2026-10-19.md),
   [teoría](references/teoria-composicion.md), [render](references/rendering.md)
   y [ejemplo autónomo](scripts/example_dense_arrangement.py).
   La entrada ejecutable los abre, muestra y registra sus hashes ANTES del compositor.
2. **DECIDIR** y escribir `plan.json`: `profile: "dense"`, intención/género/variante,
   secciones con nombre, compases, groove y densidad objetivo; instrumentos con
   nombre, rol, mínimo/máximo MIDI y compases completos de silencio; `fill_bars`
   solo en finales de sección. La entrada rechaza planes sin contraste o espacio.
   Usar `example_dense_arrangement.py --plan plan.json` como esquema concreto;
   adaptar sus decisiones a la pieza solicitada antes de generar notas.
3. **ESCRIBIR** un compositor que acepte `--out` y cree marcadores por sección.
   Para metal/rock denso, autoría nota a nota siguiendo el ejemplo: riffs de
   quintas, diálogo instrumental, batería por frase y articulaciones explícitas.
   Una rejilla única repetida toda la canción no es un arreglo terminado.
   Ejecutarlo únicamente mediante la entrada de abajo; `{draft}` es temporal.
4. **VERIFICAR antes de declarar terminado**: la entrada ejecuta
   `audit_arrangement.py` sobre los bytes generados, comprueba instrumentos,
   registros, silencios y forma contra el plan. Solo con exit 0 publica el MIDI
   y `MIDI.audit.json`, con hash del archivo exacto. Cualquier edición posterior
   invalida ese certificado: volver a auditar y publicar. Ejecutar también el
   auditor explícitamente al revisar material existente y conservar su salida.
   Antes de entregar, `composition_guard.py --verify pieza.mid` comprueba hashes
   del MIDI, lecturas y código, repite el auditor y verifica el plan guardado.
5. **RENDERIZAR y ESCUCHAR** después de pasar los gates. Aplicar
   `references/rendering.md`, verificar duración/picos y comparar audio.
   Si no hay escucha, entregar como «maqueta estructuralmente auditada;
   calidad sonora pendiente». El análisis MIDI no demuestra timbre ni gusto.

```bash
PY=python
S=scripts
"$PY" "$S/example_dense_arrangement.py" --plan plan.json
# Revisar/adaptar plan.json y el compositor antes de ejecutar:
"$PY" "$S/composition_guard.py" plan.json --out pieza.mid -- compositor.py --out '{draft}'
# Obligatorio en revisión; exit 1 impide entrega:
"$PY" "$S/audit_arrangement.py" pieza.mid --json revision.json
"$PY" "$S/composition_guard.py" --verify pieza.mid
```

**Gates del contrato denso:** máximo 2 piezas del kit por ataque; rechazar
duplicados, dos platillos/hat y caja+tom simultáneos. También agrupar ataques
separados por <=1/48 de negra para detectar colisiones ocultas por jitter.
Pistas de >=16 notas: >=5 velocidades distintas y amplitud >=10; >=3 patrones
de batería sin que uno supere el 50% de compases activos; >=3 densidades y
contraste >=2 golpes entre secciones; >=1 instrumento armónico con >=1 compás
sin notas ni sustain. Registros: bajo 24–60, guitarra rítmica 40–84, lead 48–90,
piano 36–84, pad/cuerdas 36–90, coro 36–84. Rol no reconocido: abortar y diseñar
un perfil explícito. Fills inferidos por toms/caja: rechazar periodicidad de 4
compases (>=4 candidatos y >=75% de intervalos iguales a 4) y candidatos fuera
de bordes marcados. Esta heurística NO identifica todos los fills posibles.

Estos son contratos locales de claridad y contraste, **no leyes musicales**:
un ataque triple puede ser musicalmente válido fuera de este contrato. El perfil
denso es el implementado por la entrada (4/4); otro estilo requiere implementar
y probar un perfil adecuado, sin desactivar gates para forzar un aprobado.
El motor conserva su API; piezas antes aceptadas pueden ahora abortar. Sin
batería aplica controles básicos de estructura, dinámica y registro; eso no
constituye aprobación del arreglo denso.

**ANTI-PATRÓN PROHIBIDO: «declarar éxito porque `validate_midi` pasó».**
Tampoco bastan una etiqueta del clasificador, duración correcta ni `ffprobe`.
La v2 histórica NO es un caso dorado: contiene ataques triples y notas de
duración cero. El ejemplo interno corrige esos defectos y se prueba por separado.

**Límite de obligatoriedad:** la entrada y `render_song` abortan en código.
Una skill no puede impedir que un agente con acceso arbitrario escriba otro
programa o publique por fuera del motor. Para impedir esa evasión en TODO Hermes
se requiere un hook de entrega/permisos del runtime que exija el certificado;
no confundir una instrucción en Markdown con esa garantía de seguridad.

Motor único en Python sobre `mido` para **componer canciones MIDI** desde un
`SongSpec` JSON o una receta, **validarlas** y **exportarlas a audio**. Toda la
lógica vive en `scripts/hermesmusic.py`; la skill no reescribe parsers ni
lógica de timing en cada llamada. Sustituye al antiguo sistema de parches de las
skills `midi-*` y `deprecated_*`.

## When to Use

- Crear o iterar una pieza MIDI (tema de amor, batalla, ambiente, fanfarria).
- Convertir una idea musical (tonalidad + progresión + melodía) en `.mid` y `.mp3`.
- Auditar un MIDI: notas sin cerrar, re-disparos, pistas vacías, duración.
- Reutilizar vocabulario ya resuelto: escalas, cifrados de acorde y patrones.

No lo uses para transcribir audio a MIDI (eso es otra tarea) ni para editar de
forma no destructiva un MIDI ajeno: el motor **genera** canciones desde cero.

- Python 3.12+; instalar en un venv con `python -m pip install -e '.[dev]'`.
  Ejecutar `python scripts/check_install.py` para dependencias y render. No hace
  falta instalar Hermes para usar este paquete.

## How to Run

Ruta de la skill (relativa a `~/.hermes/skills/`): `hermes-music/`.

```bash
M=scripts/hermesmusic.py

python3 "$M" recipes                       # recetas disponibles
python3 "$M" gen --recipe love_theme --key F --title Reencuentro -o tema.mid
python3 "$M" compose mi.spec.json -o mi.mid --audio mi.mp3
python3 "$M" validate mi.mid
python3 "$M" render mi.mid mi.mp3
```

Ejecuta los comandos con `terminal`. Escribe specs con `write` y léelos con
`read_file`. Localiza ficheros existentes con `search_files`.

## Quick Reference

| Comando | Efecto |
|---|---|
| `recipes` | Lista las recetas internas. |
| `gen --recipe R --key T` | Genera un `.mid` desde una receta. |
| `compose SPEC.json` | Genera desde un `SongSpec` propio. |
| `validate MIDI [--expect 80]` | Reporta problemas y duración. |
| `render MIDI AUDIO` | Exporta `.mp3`/`.ogg`/`.wav` con SoundFont. |

Recetas: `love_theme`, `battle`, `fanfarria`, `taverna`, `mazmorra`, `misterio`,
`pueblo`, `epica`, `funebre`. Para criterio musical (estructuras, grooves,
motivos, velocidades) lee `references/teoria-composicion.md` con `read_file`;
para game-specific adjustments, `references/game-project.md`.

| Concepto | Valores |
|---|---|
| Escalas (`scale`) | `mayor`, `menor_natural`, `menor_armonica`, `menor_melodica`, `dorico`, `frigio`, `frigio_dominante`, `lidico`, `mixolidio`, `locrio`, `alterada`, `pentatonica_menor`, `pentatonica_mayor`, `blues` |
| Acordes (`progression`) | cifrado anglo: `F`, `Am7`, `Fmaj7`, `C/E`, `G7sus4`, `Bb`, `Dm7`, `Bbmaj7`. Usa siempre `maj7` (no `Maj7`); el parser `_QUAL` distingue mayúsculas. Un acorde desnudo como `E` se interpreta como mayor. |
| Patrones de acompañamiento | `arpeggio_up`, `arpeggio_down`, `arpeggio_updown`, `block_chords`, `bass_root`, `bass_pulse`, `alberti`, `waltz`, `pad`, `choir_pad`, `drum_metal` | 
| Patrones melódicos | `salto_climax`, `arpegio_confiado`, `escala_ascendente`, `giro_ornacional`, `nota_repetida`, `descenso_cadencia`, `swagger`, `balada` |
| Dinámicas | `pp`, `p`, `mp`, `mf`, `f`, `ff` |
| Registro | `low`, `mid`, `high` (o `octave` explícito) |
| Batería (`drum_grid`) | `grid = {kick, snare, hihat, cymbal, tom, ride}: [16]` con cada celda como `(intensity, offset_beats)` o un único `intensity`. `grid_threshold` (0..1) filtra por intensidad; `offset_beats` desplaza el tiempo. Si la clave es `ride` (pitch 51), el motor la genera en el canal 9 — `midi-rhythm-genre` agrupa pitch 51 dentro de la clase `cymbal`, así que la plantilla jazz `ride` se compara contra `grid["cymbal"]`; usa siempre la clave `ride` para patrones de jazz/blues. | 
| Swing (`drum_grid`) | El motor `rhythm_genre.classify_genre` calcula swing sobre **todos** los onsets de la batería (kick+snare+ride+hihat+tom), no solo el ride. Fórmula exacta: `m = mean(offbeats); swing = round(clamp((m - 0.5) / 0.17, 0, 1))` donde `offbeats` = onsets cuyo `beat % 1.0` cae entre 0.15 y 0.85, y 0.5 = recto (mean de onsets en posición semicorazón). Como el kick/snare suelen estar en onbeats rectos (0.0/0.5), su presencia baja el promedio del swing **combinado** aunque el ride tenga el offset correcto. Swing target: 0.55–0.65 = jazz/blues (ride `x.xx.xx.x.xx.xx.` con offbeats retrasados ~0.2–0.3b), 0.05–0.20 = rock/pop/vals, ~0.0 = march/electronica four-on-floor. Para verificar swing real del ride, filtra pitch 51 (ride) antes de medir: el ride solo domina el promedio solo cuando es notoriamente más denso que el resto. Si el swing combinado es bajo pero el ride suena swing, reduce kicks rectos o añade más notas swing al piano_comp. |

## Procedure

Aplicar primero el protocolo obligatorio del inicio. Esta sección solo describe
la API de bajo nivel; no sustituye lectura, plan ni gates.

1. **Elige la vía.** Para control fino, escribe
   un `SongSpec` JSON (modelo en `references/reencuentro.spec.json`) o eventos
   explícitos como `scripts/example_dense_arrangement.py`.
2. **Define la pieza.** Claves de nivel raíz: `title`, `key`, `scale`, `tempo`,
   `meter` y `humanize` (`seed`, `velocity`, `ticks`).
3. **Escribe las secciones.** Cada sección es `name`, `bars`, `progression`
   (lista de cifrados que se repiten por compás) y, si lleva melodía,
   `melody` con notas explícitas (`{bar, beat, dur, note}`) o un `pattern`.
4. **Añade acompañamiento.** En `tracks`, cada pista lleva `role`, `instrument`
   (GM), `pattern`, `register` u `octave`, `dynamics` y, para percusión,
   `is_drum: true` y `channel: 9`.
5. **Genera mediante `composition_guard.py` y exige auditoría exit 0.** `validate_midi` es una comprobación estructural complementaria. Inspecciona roles indispensables (bajo, riffs, lead, percusión según estilo); no aceptes pistas vacías como «solos».
6. **Exporta y escucha.** Añade `--audio salida.mp3` (o llama a `render`); compara el audio con referencias del género antes de declarar calidad/fidelidad.

### Modelo de `SongSpec`

```json
{
  "title": "Pieza", "key": "F", "scale": "mayor", "tempo": 72, "meter": [4, 4],
  "humanize": {"seed": 42, "velocity": 0.08, "ticks": 4},
  "sections": [
    {"name": "A", "bars": 8, "progression": ["F", "C/E", "Dm7", "Bb"],
     "dynamics": "mp",
     "melody": {"instrument": 40, "track": "lead", "dynamics": "mp",
                "notes": [{"bar": 0, "beat": 0, "dur": 1, "note": "C5"}]}}
  ],
  "tracks": [
    {"role": "harp", "instrument": 46, "pattern": "arpeggio_up",
     "register": "high", "dynamics": "p"}
  ]
}
```

## Pitfalls

- **`validate_midi` agrupa notas abiertas por `(canal, pitch)`, no solo pitch.**
  Dos notas del mismo pitch en canales distintos pueden solaparse legalmente;
  con clave solo por pitch daba falsos positivos "re-disparo sin note_off".
  Al tocar ese código, recuerda que `MetaMessage` no tiene `.channel`/`.note`
  (guardar con `hasattr`/`is_meta` antes de construir la clave).
- **No reimplementes el timing.** Usa `build_track` (absoluto → orden → delta).
  Nunca escribas `max(0, delta)`: oculta el bug en vez de arreglarlo; el motor
  levanta `ValueError` ante un delta negativo.
- **`note` usa octava científica:** `C4` = Do central (MIDI 60). `Bb3` = 58.
- **Percusión siempre en el canal 9** (`is_drum: true` fuerza el canal 9). Un
  `program_change` en el canal 9 no aplica.
- **`drum_grid` con tuples `(intensity, offset)`.** El motor (hermesmusic.py:501)
  verifica `isinstance(val, (list, tuple))` ANTES de leer la intensidad. Si la
  celda es un número plano, se interpreta como `(número, 0.0)` — no `(0.0, número)`.
  Un error común: pasar `[0.9]` esperando offset; usa siempre `(0.9, offset)` para
  desplazamientos. La clave `ride` (pitch 51) se mapea al `dmap` del motor y, a través
  de `DRUM_CLASS` en rhythm_genre, se agrupa en la clase `cymbal` — usa la clave `ride`
  en el grid para patrones jazz (la plantilla `jazz.ride = "x.xx.xx.x.xx.xx."` se
  compara contra `grid["cymbal"]`).
- **La melodía procedural es relativa al acorde.** Los grados del patrón se
  suman al grado de la raíz del acorde dentro de la escala; no son grados
  absolutos de la tonalidad.
- **El `off` nunca va después del siguiente `on`.** `build_track` cierra solo el
  pitch previo para que no queden notas solapadas ni sin cerrar.
- **Un SoundFont con `-F` en `fluidsynth` no renderiza si el `.mid` está vacío:**
  valida antes de exportar.
- **`humanize.ticks` no debe superar ~10** (a 480 tpb) o desdibuja el pulso.
- **Render: el tail de release añade 4–8 s.** La duración del `.mp3` es
  `duration + tail`. Para una longitud fija, resta los segundos de tail a
  `bars` de la sección final (o corta el `.mp3` con `ffmpeg -t N`).
- **Registra los errores de duplicación de pistas:** `tracks_global` en todas
  las secciones + `tracks` en cada una. Aplica una sola vez.
- **`tracks_global` aplica a todas las secciones.** La batería o cualquier pista
  declarada allí aparece en cada `bars`. Si una pista ya lleva un `pattern`
  específico de una sección, no la repitas en `tracks_global` (duplica defectos).
- **Voces reales no existen.** `voice_*` no está en el diccionario. Para la
  armonía de 3 voces usa `choir_pad` (instrument 53, 3 capas) o
  `choir` en los `tracks`; el resultado es un pad coral, no vocal real.
- **Para guitarra eléctrica (30) y fiddle (40):** `block_chords` suena igual
  que cuerdas; `arpeggio_up` es un pulso. No apliques `drum_metal` fuera del
  canal 9.

## Planificador armónico experimental (NO acredita fidelidad al género)

`references/genre_profiles.json` cubre 100 etiquetas y 104 variantes (22 con fuente específica, 5 con fuente familiar y 73 provisionales). Los géneros paraguas exigen variante. Cada ficha detalla identidad, roles candidatos, métrica, estrategia armónica, diferencias y fuentes; no genera la instrumentación automáticamente. `scripts/genre_engine.py` organiza motivo A, contraste B, retornos A' y A'', puente y coda mediante permutaciones acotadas, semilla y puntuación explicable; exporta **solo una guía de acordes de piano**. Es heurístico: ni «gusto humano» ni ritmo/timbre de los 100 géneros están validados. El renderer actual sigue limitado para compases y grooves ajenos a 4/4.

```bash
PY=python
ENGINE=scripts/genre_engine.py
"$PY" "$ENGINE" profile --genre power_metal --variant symphonic
"$PY" "$ENGINE" plan --genre power_metal --key A --seed 17 --out output/power_metal_harmonic_plan.json
"$PY" "$ENGINE" guide --genre waltz --key F --out output/waltz_harmonic_guide.mid
"$PY" -m unittest discover -s tests -q
```

Fuentes y arquitectura: `docs/TEORIA-Y-ARQUITECTURA-2026-10-19.md`.

## Patrón genre_grid

El patrón `genre_grid` carga una **plantilla parcial de batería** desde `references/genre_configs.json` (100 etiquetas; solo 15 grids distintos). NO crea instrumentos, bajo, guitarra, melodía, solo ni forma: la lista `instruments` se guarda en `_genre_instruments`, pero el motor no la consume para generar pistas. Tener una etiqueta no acredita fidelidad al género. Investigación y matriz preliminar de las 100 etiquetas: `docs/AUDITORIA-GENEROS-2026-10-19.md`.

Uso en spec:
```json
{"tracks_global": [{"role": "drums", "pattern": "genre_grid", "genre": "jazz"}]}
```

El patrón transfiere kick/snare/hihat/ride/cymbal de una rejilla de 16 pasos y el rango de dinámica a esa pista; no valida ni impone el tempo/compás/densidad propios del género. Varias etiquetas comparten exactamente el grid, incluyendo tradiciones que requieren ciclos de varios compases o no admiten batería pop por defecto. Antes de llamar «composición de género X» a un resultado, escribir roles, células rítmicas, armonía, forma y variaciones del género en el `SongSpec`; inspeccionar pistas realmente pobladas, compás, duración y render final. Ver `scripts/hermesmusic.py` sección `genre_grid` y la auditoría indicada arriba.

Géneros disponibles: rock, pop, blues, jazz, swing, bossa_nova, samba, funk, soul, rnb, disco, house, techno, trance, dubstep, drum_and_bass, hiphop, trap, reggae, ska, punk, metal, hardcore, grunge, indie, classical, baroque, romantic, electronic, ambient, lo_fi, synthwave, vaporwave, chillwave, folk, country, bluegrass, mariachi, flamenco, tango, salsa, rumba, mambo, cha_cha, bolero, reggaeton, bachata, cumbia, vallenato, afrobeat, highlife, gospel, doo_wop, calypso, soca, zydeco, polka, waltz, mazurka, tarantella, march, minuet, reel, jig, breakbeat, breaks, gabber, psybient, downtempo, idm, footwork, juke, trap_rock, nu_disco, chillout, new_age, meditation, mantra, industrial, darkwave, goth, post_rock, math_rock, prog_rock, post_metal, doom_metal, black_metal, death_metal, power_metal, thrash_metal, speed_metal, sludge_metal, stoner_metal, drone, spoken_word, comedy_music, alternative, trip_hop, drill, experimental.

**Verificado con `rhythm_genre.classify_genre` (3 géneros):** jazz→jazz (ranking 1.º, swing 0.6), rock→rock (ranking 1.º, swing 0.05), bossa_nova→bossa (ranking 1.º, swing 0.2). La validación MIDI reporta `sin problemas` en los 3 casos. El `genre_grid` lee la config una vez por generación (cache implícito de Python por import); para 100 géneros el JSON ocupa ~12 KB.

## Chaining

Esta es la skill **única** para generar y renderizar MIDI. Otras skills la llaman en
vez de duplicar el motor:

- **`audio-gen`** — SFX, tonos y pads con `ffmpeg`; para MIDI→audio usa el `render`
  de `hermes-music`.
- **`midi-pipeline`** — análisis, deduplicación y recomendación por
  escena; para generar, llama a `hermes-music` (`gen`/`compose`).
- **`musicxml-omr-parsing`** — partitura/imagen → MIDI; luego valida y renderiza con
  `hermes-music`.
- **`songwriting-and-ai-music`** — letras y prompts de Suno; dominio distinto.
- **`ai-music-tech-finder`** — comparativa de herramientas de música con IA.

Patrón de encadenado: carga la otra skill con `skill_view`, y para la parte musical
invoca este motor por ruta (`scripts/hermesmusic.py`).

## Verification

Antes de dar por terminada la composición, la entrada obligatoria debe haber
publicado el MIDI y su certificado. En una revisión independiente ejecutar:

```bash
PY=python
"$PY" scripts/audit_arrangement.py mi.mid
python3 "$M" validate mi.mid --expect 80.0
```

Si cualquiera devuelve código distinto de 0, abortar y corregir. Notas
balanceadas y duración correcta por sí solas no aprueban un arreglo.
