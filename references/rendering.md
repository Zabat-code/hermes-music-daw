# Render y exportación: guía vigente

Aplicar primero [PROTOCOL.md](../PROTOCOL.md): componer con guard → auditoría y
certificado → stems → mezcla → master → verificar el formato final → escucha.
Un archivo MIDI válido no acredita un arreglo, un timbre ni calidad musical.

## Dependencias y rutas

Python 3.12 con dependencias del paquete. Para audio se necesitan FluidSynth,
FFmpeg (con loudnorm y libvorbis) y un SoundFont General MIDI. En Mint/Ubuntu:

```bash
sudo apt install fluidsynth ffmpeg fluid-soundfont-gm
python scripts/check_install.py
```

El SoundFont se busca en tiempo de llamada: `MIDI_SOUNDFONT` tiene prioridad,
luego FluidR3_GM, TimGM6mb y ubicaciones comunes de `.sf2`. Un override inválido
aborta. No se incluye el SoundFont en el paquete. Los ejecutables se buscan en
PATH o con `FLUIDSYNTH`, `FFMPEG`, `FFPROBE`. Para ubicaciones exactas y errores,
usar el smoke test. La librería no requiere el directorio personal del autor.

FluidSynth enumera dispositivos SDL incluso en modo archivo. Los subprocesses
offline usan por defecto `SDL_AUDIODRIVER=dummy`, lo que evita un bloqueo de
PulseAudio observado en el sandbox. No se necesita tarjeta de sonido.

## Maqueta rápida frente a stems

Render único (tras auditar):

```bash
python scripts/hermesmusic.py render piece.mid piece.ogg
```

La CLI conserva ganancia 0.8. En arreglos densos, usar
`render_audio(..., gain=0.55)` desde Python o `render_stems` (default 0.5). Medir
picos después: un default no garantiza ausencia de clipping. General MIDI no
reproduce palm mute, distorsión de amplificador ni articulaciones realistas.
La duración corta de una nota solo aproxima una articulación MIDI.

Para mezcla por instrumento, usar el ejemplo ejecutable:

```bash
python examples/01_compose.py --work output/render-demo
python examples/02_audit.py --work output/render-demo
python examples/03_mix_and_master.py --work output/render-demo
```

`render_stems` exige nombres seguros y únicos, un canal por pista con notas y
una carpeta nueva/vacía. Conserva metadatos globales en sus ticks originales.
Un track tipo 0 multicanal se debe dividir primero; controladores y programas
compartidos entre pistas no se reconstruyen automáticamente.

## Duración y colas

FluidSynth añade release tail (en el ejemplo medido, 4.526 s). La mezcla sin
duración explícita conserva el stem más largo. `--duration N` recorta o rellena;
no debe usarse para ocultar un fin de arreglo mal escrito. Para tiempo exacto
con fade-out, aplicar el recorte/fade antes de la medición final y documentarlo.

## Procesamiento y mediciones

Los perfiles de [mezcla](../docs/MIX_PROFILES.md) son puntos de partida. Las
cadenas por rol aplican HPF, EQ y compresión, seguidas de balance estéreo lineal
y nivel. No es paneo mid/side ni de potencia constante. Mono se duplica y las
tasas distintas se remuestrean a 44100 Hz. Los nombres desconocidos abortan.

El bus trabaja en float, aplica EQ/compresión, trim -3 dB y limitador de muestras.
Una suma float >0 dBFS no es por sí sola clipping de PCM; al escribir a un formato
limitado sí se puede recortar. El trim y limitador tampoco garantizan true peak.
Medir el archivo final, no inferir garantías del nombre de un efecto.

`analyze_audio` devuelve pico de muestras, RMS dBFS, correlación estéreo y energía
normalizada por octava. No devuelve LUFS. `analyze_masking` calcula similitud
heurística por bandas: no prueba inaudibilidad. Comparar duración/material
semejantes para una comparación tonal útil.

`master` mantiene la cadena Pedalboard y añade normalización FFmpeg loudnorm en
dos pasadas: LUFS objetivo y -1 dBTP. Devuelve las medidas posteriores y
`target_met`; algunas señales limitan el objetivo alcanzable. No anunciar
cumplimiento si es falso. La salida conserva la tasa original; `loudnorm` puede
trabajar internamente a 192 kHz.

## Exportar y volver a verificar

```bash
ffmpeg -nostdin -y -i master.wav -ar 44100 -ac 2 -c:a libvorbis -q:a 5 final.ogg
python - <<'PYCODE'
from hermes_music.scripts.daw_mcp import release_check
print(release_check('final.ogg', profile='balanced'))
PYCODE
```

`release_check` mide LUFS integrado, true peak y LRA mediante FFmpeg; reporta
clipping, margen, RMS muy alto y correlación estéreo sospechosa. `ready` es un
filtro técnico limitado. El encode con pérdida puede aumentar picos: medir
el OGG, no solo el WAV. Una señal mono intencional puede recibir `needs_work`;
registrar la excepción con honestidad.

Escuchar estéreo/mono y comparar referencias antes de afirmar calidad sonora.
Sin escucha, entregar como «maqueta estructuralmente auditada; calidad sonora
pendiente de escucha humana». Véase el historial técnico, incluyendo errores
corregidos, en [la investigación inicial](../docs/INVESTIGACION-MCP-DAW-2026-10-19.md).
