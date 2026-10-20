# Hermes Music + DAW

Herramientas Python para componer MIDI con controles de arreglo y procesar audio
offline. El proyecto tiene dos componentes:

| Componente | Función |
| --- | --- |
| `hermes-music` | Composición MIDI, ocho gates de arreglo y recibos de integridad SHA-256 |
| `hermes-daw` | Servidor MCP por stdio con diez herramientas de renderizado, análisis, mezcla y masterización |

Funciona con CPU, sin ventana de DAW ni interfaz de audio. General MIDI produce
maquetas; los controles estructurales y las mediciones no certifican calidad sonora.

**English:** [README.md](../README.md) · **Español:** [README.es.md](../README.es.md)

## Por qué existe el guardarraíl

Un arreglo repitió defectos ya documentados: batería mecánica, ataques solapados,
dinámica plana e instrumentos sin espacio. La corrección escrita no evitó la
siguiente entrega defectuosa. Por eso el flujo exige **leer → decidir → componer
→ auditar → entregar**.

`composition_guard.py` lee las referencias, valida el plan, ejecuta el compositor
sobre un MIDI temporal y contrasta el resultado con el plan y los ocho gates.
Si falla, aborta con código 1. Si pasa, publica el MIDI y su recibo sin sobrescribir
entregas anteriores. Aquí «publicar» significa crear archivos locales.

El recibo vincula el MIDI exacto, el plan guardado, las lecturas y tres archivos
del motor/auditor/guard. Una edición del MIDI invalida la verificación. Es evidencia
de integridad: no es una firma digital ni un sandbox. El flujo depende de que el
agente use el punto de entrada indicado; código arbitrario puede evitarlo.

## Instalar y probar

Desde una copia del repositorio, con Python 3.12 en Linux Mint/Ubuntu:

```bash
cd hermes-music-daw
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
sudo apt install fluidsynth fluid-soundfont-gm ffmpeg
python scripts/check_install.py
python -m pytest tests/ -q
```

FluidSynth, FFmpeg y un SoundFont son necesarios para audio y las pruebas de
integración. `MIDI_SOUNDFONT` permite seleccionar otro SoundFont. Los gates MIDI
no necesitan dispositivo de audio. La configuración de clientes MCP está en el
[README principal](../README.md#mcp-tools-and-clients).

## Ejecutar el ejemplo

Usa un directorio de salida nuevo en cada ejecución:

```bash
python examples/01_compose.py --work output/demo
python examples/02_audit.py --work output/demo
python examples/03_mix_and_master.py --work output/demo
```

El primer paso crea y certifica un MIDI de 12 compases y 18 segundos. El segundo
repite la auditoría y verifica el recibo. El tercero renderiza seis stems WAV,
mezcla, masteriza, exporta OGG y comprueba ese OGG. Conserva la cola del sintetizador
y guarda métricas JSON; un objetivo de master incumplido o un resultado
`needs_work` devuelve código 1. La escucha humana sigue pendiente.

## Qué comprueban los ocho gates

El contrato de composición `dense` está limitado a 4/4:

| Gate | Condición |
| --- | --- |
| `structure` | Notas cerradas, duración positiva y secuencia no vacía |
| `dynamics` | Cinco velocidades distintas y rango mínimo de 10 en partes con al menos 16 notas |
| `register` | Registro dentro del rango permitido para cada rol reconocido |
| `space` | Un instrumento armónico calla al menos un compás completo, sin notas ni sustain |
| `overlap` | Máximo dos golpes por ataque; también rechaza duplicados, dos platillos y caja con tom, incluidos grupos cercanos |
| `patterns` | Tres patrones de batería como mínimo; ninguno supera el 50 % de compases activos |
| `density` | Tres niveles de golpes por compás y contraste mínimo de dos entre secciones |
| `fills` | Candidatos detectados por toms/caja en bordes de sección; rechaza periodicidad de cuatro compases según el umbral del auditor |

Los fills se infieren mediante una heurística que no detecta todos los casos.
Son reglas de un contrato local; otros estilos necesitan contratos propios.

## Audio y límites

El MCP expone `list_profiles`, `render_stems`, `analyze_audio`, `analyze_masking`,
`auto_mix`, `apply_eq`, `apply_comp`, `master`, `compare_to_reference` y
`release_check`. La composición y la verificación del recibo se ejecutan por CLI.
El renderizador MCP no exige un recibo: verifica el MIDI antes de usarlo.

Los perfiles `balanced` y `power_metal` son puntos de partida con DSP por rol,
balance estéreo lineal y cadena de bus. El master añade normalización FFmpeg en
dos pasadas; devuelve mediciones y `target_met`. `release_check` mide LUFS,
true peak y LRA, y aplica controles técnicos limitados. `ready` no significa
que una pieza suene bien ni que cumpla un objetivo de loudness elegido.

El catálogo contiene 100 etiquetas de género; 73 perfiles son provisionales.
El planificador experimental genera guías armónicas de piano, no canciones
completas de cada género. General MIDI no garantiza palm mute ni guitarras
realistas, y el análisis de masking solo señala posibles solapamientos espectrales.
Las utilidades antiguas no forman parte del flujo probado.

Para desarrollar o revisar cambios: [protocolo](../PROTOCOL.md),
[arquitectura](ARCHITECTURE.md), [documentación](README.md) y
[contribución](../CONTRIBUTING.md). Licencia del código original:
[MIT](../LICENSE); dependencias y muestras conservan sus
[avisos de terceros](../THIRD_PARTY_NOTICES.md).
