# Hermes Music + DAW (español)

Composición MIDI en Python con verificación ejecutable de arreglos, más un servidor
MCP headless para mezcla y masterización offline. Solo CPU; no requiere ventana de
DAW, tarjeta de audio, GPU, descarga de modelos ni cuenta en la nube.

**Empieza aquí:** [protocolo de agentes](PROTOCOL.md) · [arquitectura](docs/ARCHITECTURE.md) ·
[índice de documentación](docs/README.md) · [contribuir](CONTRIBUTING.md).

English: [README.md](README.md)

---

## Por qué existe el guardarraíl

El mismo arreglo defectuoso ocurrió **dos veces**: batería mecánica, golpes
solapados, dinámica plana, instrumentos amontonados y guitarras GM que sonaban
como una maqueta de 8 bits. La corrección ya estaba escrita en Markdown.
**No cambió la siguiente composición.**

La respuesta fue ejecutable: **leer → decidir → componer → auditar → publicar**.
Ocho gates de arreglo abortan una entrega defectuosa con código de salida 1. Una
auditoría externa encontró después fallos en la propia v2 del autor; también se
corrigieron. La lección es la razón de este repositorio: la documentación necesita
aplicarse en el punto donde se entrega un artefacto.

El guardarraíl registra el SHA-256 exacto del MIDI, el plan, las lecturas exigidas
y el código del guard. Editar el MIDI invalida su recibo. Es un registro de
integridad, **no una firma digital, certificado estético ni sandbox de seguridad**.
Código arbitrario puede evadirlo; un agente debe usar el punto de entrada prescrito.

## Instalación

Probado con Python 3.12.3 en Linux. Las versiones principales están fijadas en
[requirements.txt](requirements.txt): Mido 1.3.3, NumPy 2.5.3, Pedalboard 0.9.26,
FastMCP 4.1.1.

Desde una copia descargada o clonada:

```bash
cd hermes-music-daw
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
# Linux Mint / Ubuntu: dependencias externas para audio, no para análisis MIDI
sudo apt install fluidsynth fluid-soundfont-gm ffmpeg
python scripts/check_install.py
```

## Uso rápido

### 1. Componer y auditar

```bash
python examples/01_compose.py --work output/mi-primera-vez
python examples/02_audit.py --work output/mi-primera-vez
```

El primer comando crea el plan, ejecuta el compositor a través del guardarraíl y
publica el MIDI solo después de pasar los 8 gates. El segundo verifica el
certificado.

### 2. Mezclar y masterizar

```bash
python examples/03_mix_and_master.py --work output/mi-primera-vez
```

Renderiza stems, aplica la cadena de mezcla del perfil, masteriza y verifica.

### 3. Usar el MCP

El servidor expone 10 herramientas por stdio (FastMCP):

| Herramienta | Qué hace |
|---|---|
| `list_profiles` | Perfiles de mezcla disponibles |
| `render_stems` | Separa un MIDI en un WAV por instrumento |
| `analyze_audio` | Pico, RMS, correlación estéreo, 10 bandas de octava |
| `analyze_masking` | Qué pares de stems compiten por banda |
| `auto_mix` | Aplica la cadena del perfil y devuelve métricas |
| `apply_eq` | EQ puntual sobre un archivo |
| `apply_comp` | Compresión puntual sobre un archivo |
| `master` | Cadena de master con objetivo de loudness |
| `compare_to_reference` | Compara dos archivos (loudness, balance, estéreo) |
| `release_check` | Veredicto listo / necesita trabajo |

## Arquitectura

```
hermes-music-daw/
├── scripts/            motor de composición, guardarraíl, auditor, MCP y mezcla
├── tests/              74 tests + 100 subtests
├── examples/           3 scripts ejecutables + muestra
├── references/         100 géneros, teoría, render, efectos
├── docs/               arquitectura, protocolo, investigación
├── PROTOCOL.md         el recorrido obligatorio para agentes
└── pyproject.toml      empaquetado instalable
```

## Los 8 gates de arreglo

| Gate | Qué verifica |
|---|---|
| `structure` | Notas cerradas y duración positiva |
| `dynamics` | Mínimo 5 velocidades y amplitud 10 |
| `register` | Rangos MIDI por rol dentro del contrato |
| `space` | Al menos un instrumento armónico calla un compás completo |
| `overlap` | Máximo 2 piezas del kit por ataque |
| `patterns` | Mínimo 3 patrones, ninguno domina más del 50 % |
| `density` | Mínimo 3 niveles y contraste entre secciones |
| `fills` | Fills solo en bordes de sección, no periódicos |

## Límites honestos

1. **El SoundFont General MIDI no reproduce timbre real** (palm mute, distorsión,
   timbre de guitarra de metal). Suena a maqueta, no a producción.
2. **El auditor certifica estructura, no gusto musical.** Un `ready` no significa
   que suene bien.
3. **Los perfiles de mezcla son valores de partida**, no verdad absoluta.
4. **73 de los perfiles de género son `provisional`** (no auditados por escucha).
5. **El análisis de masking es heurístico**: señala dónde investigar, no prueba
   inaudibilidad.

## Contribuir

Ver [CONTRIBUTING.md](CONTRIBUTING.md). Ejecuta `python scripts/check_install.py`
antes de empezar y `python -m pytest tests/ -q` antes de enviar cambios.
