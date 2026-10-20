# Protocolo operativo para agentes

Entrada de lectura: este archivo → [SKILL.md](SKILL.md) → lecturas del guard.
El README contiene instalación; [docs/README.md](docs/README.md) distingue guías
vigentes de evidencia histórica. Ejecutar desde la raíz con el Python del venv
activado. No usar rutas personales del autor.

## 0. Verificar instalación y preparar destino

```bash
python scripts/check_install.py
python -m pytest tests/ -q
```

Ambos deben salir con 0 para validar el entorno completo. Si falta audio, instalar
`fluidsynth`, `ffmpeg`, `fluid-soundfont-gm`, o definir `MIDI_SOUNDFONT`.
`FLUIDSYNTH`, `FFMPEG`, `FFPROBE` permiten seleccionar ejecutables fuera de PATH.
Un override inválido aborta. El smoke test verifica recursos del paquete y permisos
del directorio actual; no sustituye la ejecución del ejemplo.

Si el runtime bloquea `socketpair.send()` y el MCP inicia pero no responde,
configurar `HERMES_DAW_STDIO_POLL=1` en su `env`. Mantiene el event loop activo
con un timer de 50 ms; no abre puertos. El cliente también debe funcionar en ese
runtime. La prueba local mantiene activos ambos loops y usa MCP stdio real.

Elegir un directorio nuevo para cada entrega. El guard nunca sobrescribe MIDI
ni certificado. Mantener plan, compositor, lecturas, log, MIDI, certificado,
informe de auditoría y métricas de audio juntos o localizables.

## 1. Leer → decidir → componer

El guard lee, muestra y calcula hashes de cinco diagnósticos en `docs/`, teoría,
render y ejemplo interno ANTES de ejecutar el compositor. La lectura registrada
no demuestra comprensión: el plan y el MIDI deben cumplir lo declarado.

Para comprobar el flujo corto ya diseñado, ejecutar exactamente:

```bash
python examples/01_compose.py --work output/my-first-run
```

Este comando crea `plan.json`, ejecuta el compositor a través del guard, y publica
`demo.mid` más `demo.mid.audit.json` solo tras pasar auditoría y contrato. Guarda
las lecturas completas en `composition.log`. No trata un fallo como advertencia.

Para una pieza nueva, crear primero decisiones y adaptar TAMBIÉN el compositor:

```bash
mkdir -p output/my-piece
python scripts/example_dense_arrangement.py --plan output/my-piece/plan.json
# Revisar/editar plan.json y el compositor ANTES de generar eventos.
python scripts/composition_guard.py output/my-piece/plan.json \
  --out output/my-piece/piece.mid -- \
  scripts/example_dense_arrangement.py --out '{draft}' \
  > output/my-piece/composition.log 2>&1
```

La última llamada usa la referencia íntegra de 120 compases / 180 s. Para otra
pieza, sustituir el script por un compositor propio que acepte `--out` y
marcadores de sección. El guard lo ejecuta con el MISMO Python. `{draft}` es una
ruta temporal; nunca debe ser una entrega pública. Comprobar el exit code del
guard antes de continuar. Tras un fallo, leer el final de `composition.log`.

Contrato del plan implementado:

- `profile: "dense"`, `intent` explícito con género/variante y límite de timbre.
- `sections`: nombres únicos, `bars` entero >=2, `groove` y `density` objetivo.
  La densidad es **golpes de batería por compás**, promediados por sección.
- `instruments`: nombres idénticos a pistas MIDI, `role`, `min`/`max` MIDI
  (excepto batería), `silent_bars` enteros >=0. Algún instrumento armónico debe
  callar un compás completo sin notas ni sustain.
- `fill_bars`: lista de compases con fill, **numerados desde 1**, solo finales de
  sección. El MIDI debe tener los fills detectados por la heurística en esa lista.
- 4/4, marcadores al inicio exacto de cada sección y fin MIDI en el compás previsto.

Los ocho gates existentes comprueban estructura, dinámica, registro, espacio,
solapamiento del kit, patrones, densidad y fills. No quitar batería para eludir
el contrato ni cambiar umbrales para conseguir un aprobado. Otros estilos
necesitan un contrato diseñado y probado por separado.

## 2. Auditar y verificar el certificado

Para el ejemplo corto:

```bash
python examples/02_audit.py --work output/my-first-run
```

Para la referencia íntegra o una pieza propia:

```bash
python scripts/audit_arrangement.py output/my-piece/piece.mid \
  --json output/my-piece/review.json
python scripts/composition_guard.py --verify output/my-piece/piece.mid
```

Ambos deben salir con 0. `validate_midi`, una etiqueta de clasificador y duración
correcta por sí solos NO aprueban un arreglo. No sobrescribir `*.audit.json`
con el informe independiente de `audit_arrangement`: el certificado contiene
también plan, hashes de lecturas y código.

Una modificación posterior del MIDI exige volver al guard y publicar con otro
nombre. Los certificados actuales incluyen rutas absolutas: tras mover el
checkout o actualizar código/lecturas, volver a ejecutar el flujo. SHA-256 no
es una firma digital ni impide que alguien con escritura falsifique un recibo.

## 3. Renderizar y mezclar

Recorrido completo del ejemplo corto, después de pasos 1 y 2:

```bash
python examples/03_mix_and_master.py --work output/my-first-run
```

El script realiza en orden `verify_delivery` → `render_stems` → `auto_mix` →
`master` → encode OGG → `release_check` sobre el OGG, y conserva `results.json`.
Un target incumplido o un veredicto `needs_work` produce exit 1.

Para una pieza propia, estos son los comandos de audio exactos (requieren la
instalación editable); usar rutas del mismo directorio de trabajo:

```bash
python - <<'PY'
from hermes_music.scripts.composition_guard import verify_delivery
from hermes_music.scripts.daw_mcp import render_stems, list_profiles
verify_delivery('output/my-piece/piece.mid')
print(list_profiles())
print(render_stems('output/my-piece/piece.mid', 'output/my-piece/stems'))
PY
python scripts/mix_engine.py --stems output/my-piece/stems \
  --out output/my-piece/mix.wav --profile balanced
```

`stems/` debe ser nuevo o vacío. Se produce un WAV por pista con notas; nombres
seguros y únicos, un canal por pista. Para tipo 0 multicanal, separar instrumentos
primero. Mantener programas/controladores en la propia pista de cada instrumento.
Se preserva el mapa global de tempo y los tiempos delta. Un fallo de FluidSynth
aborta; nunca inferir éxito por la existencia de un WAV antiguo.

Consultar `list_profiles()` antes de mezclar. Nombres soportados:
`drums`, `electric_bass`, `rhythm_guitar_L`, `rhythm_guitar_R`, `lead_guitar`,
`lead_guitar_L`, `lead_guitar_R`, `synth_piano`. Se admite un subconjunto; cualquier
nombre ajeno aborta incluso si otros sí coinciden. Renombrar con intención o
añadir y probar un perfil; no descartar instrumentos en silencio.

Mono se duplica a estéreo, tasas distintas se remuestrean a 44100 Hz. Sin
`--duration` se usa el stem más largo para conservar colas. `--duration N`
recorta o rellena con ceros: declarar cualquier recorte musical en la entrega.
Archivos sin frames, sin señal, corruptos o con valores no finitos abortan.

## 4. Masterizar y codificar

```bash
python - <<'PY'
from hermes_music.scripts.daw_mcp import master
result = master('output/my-piece/mix.wav', 'output/my-piece/master.wav',
                target_lufs=-16.0, profile='balanced')
print(result)
if not result['target_met']:
    raise SystemExit('Master target not met: inspect dynamics and measured loudness')
PY
ffmpeg -nostdin -y -i output/my-piece/master.wav -ar 44100 -ac 2 \
  -c:a libvorbis -q:a 5 output/my-piece/piece.ogg
```

Si se configuró `FFMPEG` fuera del PATH, sustituir `ffmpeg` por esa ruta. El
master aplica cadena de bus y `loudnorm` de dos pasadas; devuelve LUFS integrado,
true peak medido por FFmpeg y LRA. `target_met` exige ±1 LU del objetivo y
TP <= -0.9 dBTP (tolerancia de 0.1 respecto al objetivo -1). No garantiza que
toda señal pueda llegar al objetivo sin alterar dinámica. El mix ya tiene bus;
el master añade otra cadena deliberada. Comparar antes/después por si se prefiere
omitir procesamiento tonal adicional en una futura política.

No llamar «true peak» al pico de muestras de Pedalboard. No llamar LUFS al RMS.
Forzar sample rate y canales al exportar; `loudnorm` puede trabajar a 192 kHz.
La compresión con pérdida puede elevar picos, por eso se verifica EL OGG FINAL.

## 5. Verificar → escuchar → publicar

```bash
python - <<'PY'
from hermes_music.scripts.composition_guard import verify_delivery
from hermes_music.scripts.daw_mcp import release_check
verify_delivery('output/my-piece/piece.mid')
result = release_check('output/my-piece/piece.ogg', profile='balanced')
print(result)
if result['verdict'] != 'ready':
    raise SystemExit('Delivery needs work: inspect issues')
PY
ffprobe -v error -show_entries format=duration:stream=sample_rate,channels \
  -of json output/my-piece/piece.ogg
```

`release_check` mide y señala clipping, margen de pico/true peak, RMS muy alto
y correlación estéreo sospechosa. Sus umbrales son generales; el parámetro
`profile` se valida y se informa, pero no representa objetivos distintos por
género. LUFS/LRA se reportan; el veredicto no certifica un objetivo de loudness.

Escuchar en estéreo y mono, comprobar balance y timbre. Si el agente no puede
escuchar, entregar como **«maqueta estructuralmente auditada; calidad sonora
pendiente de escucha humana»**. Un `ready` no autoriza afirmar «suena bien».

Antes de compartir: conservar salida real de gates, métricas, licencia y
limitaciones. Publicar MIDI/OGG seleccionados y sus notas de procedencia;
excluir stems/WAV/cache/backups. Subir a GitHub o Reddit es una acción del dueño
tras revisar; este protocolo no ejecuta publicaciones remotas.

## Errores frecuentes y reparación concreta

| Error | Diagnóstico y reparación |
| --- | --- |
| `plan sin silencio de instrumento armónico` | Declarar `silent_bars >= 1` en piano/guitarra/pad/cuerdas/coro Y escribir al menos ese número de compases completos sin notas/sustain. Silenciar solo el lead o el bajo no cuenta. |
| `fill_bars` fuera de finales | Calcular suma acumulada de `bars`: para 4+4+4 los únicos bordes son `[4,8,12]`, no `[3,7,11]`. Incluir solo bordes con fill real detectado. Mover los fills del MIDI; no falsear la lista. |
| Fills detectados ≠ lista del plan | Revisar `fill_bars` del informe. La heurística detecta >=3 toms o >=4 cajas en el último pulso. Corregir ataques y ubicación; no inventar fills en el plan ni aplicar fills periódicos cada 4 compases. |
| `densidad difiere más de 3 golpes` | Comparar `density_sections` con la intención. Es promedio de golpes de batería por compás, no total de notas ni densidad de guitarras. Arreglar el groove o corregir un objetivo mal expresado antes de regenerar; diferencia permitida <=3. |
| Compases del plan ≠ MIDI | Sumar secciones, comprobar marcadores a `bar * 4 * ticks_per_beat`, último `note_off` y `end_of_track`. Un sustain que excede el fin puede añadir un compás. Alinear composición y plan; no truncar notas con un delta negativo oculto. |
| Gate de densidad falla aunque el rango es amplio | Debe haber >=3 niveles de densidad Y contraste entre secciones >=2. Dos secciones distintas pueden tener igual número de golpes. Cambiar la orquestación del kit de forma musical, no añadir jitter. |
| Solapamiento de batería | Máximo dos piezas por ataque; quitar duplicados, doble platillo/hat y caja+tom. Agrupa también ataques muy próximos: el jitter no oculta una colisión. |
| `Unknown profile` / stems no coinciden | Consultar `list_profiles`, usar nombres exactos o diseñar un perfil explícito con tests. No ignorar stems. |
| `no se sobrescriben entregas` | Elegir otro nombre/directorio. El guard protege la evidencia de entregas previas. |
| Certificado inválido / lecturas o código cambiaron | Regenerar por el guard con un destino nuevo. Conservar el recibo anterior como evidencia histórica; no editar hashes. |
| `Silent audio` / `Empty audio` | Verificar notas MIDI, programa, SoundFont y subprocess. No normalizar silencio ni continuar con un stem faltante. |
| `needs_work` tras encode OGG | Revisar `issues` y TP del codec final; bajar objetivo/ganancia y volver a masterizar/codificar. Para mono intencional, documentar la excepción al chequeo estéreo en vez de afirmar que pasó. |
