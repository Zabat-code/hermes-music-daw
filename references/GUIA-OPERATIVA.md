# GUÍA OPERATIVA CONSOLIDADA — hermes-music

**Propósito:** reemplaza la lectura obligatoria de 5 documentos (31 KB) por esta
guía de ~4 KB. Las fuentes completas quedan como referencia bajo demanda.

**Origen:** consolidación de `ERROR-REPETIDO-2026-10-19.md`,
`OBSERVACIONES-PARA-AUDITOR-2026-10-19.md`, `COMPARATIVA-BATERIA-METAL-2026-10-19.md`,
`TEORIA-Y-ARQUITECTURA-2026-10-19.md` y `HALLAZGOS.md`.

---

## 1. Errores que ya se documentaron (no repetir)

| Error | Causa | Corrección |
|---|---|---|
| Numerales romanos | `parse_chord('I')` → `ValueError` | Usar acordes directos: `E`, `G#m`, `A`, `B` |
| `Maj7`/`maj7` | Calidad no soportada | Simplificar a mayor; fallback a la raíz |
| Batería 3+ piezas | El auditor lo rechaza | Máx. 2 piezas por ataque; redistribuir |
| Acorde repetido | "Ruido mecánico", suena antinatural | Grooves por sección + variación de frases |
| `program` como string | `TypeError` en `build_track` | Convertir a `int` antes del chequeo de rango |
| Pistas sin `pattern` | Se saltan en `render_song` | Generar tonos de acorde desde la progresión |

## 2. Contrato denso (puertas del auditor)

- **Batería:** máx. 2 piezas del kit por ataque. Rechaza duplicados, doble
  platillo/correa simultáneo, caja+tom simultáneo.
- **Dinámica:** >=5 velocidades distintas y rango >=10 en pistas con >=16 notas.
- **Patrones:** >=3 patrones de batería; ninguno >50% de compases activos.
- **Densidad:** >=3 niveles; contraste >=2 entre secciones.
- **Espacio:** >=1 instrumento armónico con >=1 compás sin notas.
- **Registros:** bass 24-60, rhythm_guitar 40-84, lead 48-90, piano 36-84,
  pad/strings 36-90, choir 36-84. **Rol desconocido: abortar.**
- **Fills:** rechaza periodicidad de 4 compases (>=4 candidatos, >=75% intervalos = 4).

**Estas no son leyes musicales.** Son contratos locales de claridad y contraste.
Otro estilo requiere diseñar y probar un perfil; **nunca desactivar puertas.**

## 3. Cómo se compone un arreglo denso (receta)

1. **Estructura primero.** Secciones con energía creciente: intro (baja) →
   verse → prechorus → chorus (alta) → bridge (baja) → solo → chorus final → outro.
2. **Riffs por sección, no un grid repetido.** Cada sección tiene su groove:
   verse = semicorcheas con palm mute; chorus = corcheas con acordes; bridge = medio tiempo.
3. **Variación de frases.** Rotar el motivo cada 4 compases; dejar huecos
   (respiración) en el compás 3 de cada 4 para que ningún patrón domine >50%.
4. **Fills solo en el borde de sección.** Reemplazan caja y platillo del último beat.
   El fill debe TERMINAR dentro del compás (dur < 1.0) o el auditor cuenta un compás extra.
5. **Doble bombo en semicorcheas** es el sello del power metal. Acentuar los tiempos
   fuertes (0, 1, 2, 3) con más velocidad.
6. **Diálogo instrumental.** Que las guitarras no suenen todas a la vez: la rítmica
   calla en el solo, el bajo sostiene en el bridge.
7. **Articulación explícita.** Duraciones cortas (0.1-0.3 beats) = staccato/palm mute;
   largas (>1.0) = sostenido.

## 4. Registros y roles seguros

| Rol | Programa GM sugerido | Registro |
|---|---|---|
| drums | 0 (canal 9) | 35-51 |
| bass | 34 (Electric Finger) | 24-60 |
| rhythm_guitar | 30 (Distortion) | 40-84 |
| lead | 25/26/29 (no 31 Harmonics: metálico y agudo) | 48-90 |
| piano | 0 | 36-84 |
| strings | 48 | 36-90 |

**Nota:** el programa 31 (*Guitar Harmonics*) suena metálico/agudo y fue rechazado
en escucha real. Preferir 25/26/29 para guitarras leader.

## 5. Flujo obligatorio

```bash
PY=python; S=scripts
"$PY" "$S/example_dense_arrangement.py" --plan plan.json
"$PY" "$S/composition_guard.py" plan.json --out piece.mid -- composer.py --out '{draft}'
"$PY" "$S/audit_arrangement.py" piece.mid --json revision.json
"$PY" "$S/composition_guard.py" --verify piece.mid
```

`plan.json` debe incluir: `profile`, `intent` con género/variante, `sections` con
`bars`/`groove`/`density`, `instruments` con rol/min/max MIDI/silencios, y
`fill_bars` solo en finales de sección.

## 6. Verificación final

- `validate_midi` sin problemas (notas cerradas, duración positiva).
- Auditor con exit 0.
- **Audio sin saturación:** pico <= -1 dB. Normalizar con
  `loudnorm=I=-16:TP=-1.5:LRA=11` si el pico llega a 0 dB.
- **Escuchar antes de declarar calidad.** Sin escucha, entregar como
  "maqueta auditada estructuralmente; calidad sonora pendiente".

## 7. Referencias completas (bajo demanda)

Solo leer si esta guía no basta:

| Necesidad | Archivo |
|---|---|
| Esqueleto nota por nota | `scripts/example_dense_arrangement.py` |
| Detalle de batería metal | `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md` |
| Teoría y armonía | `references/teoria-composicion.md` |
| Render y medición | `references/rendering.md` |
| Arquitectura | `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md` |
| Auditoría de géneros | `~/.hermes/documentacion/hermesmusic/AUDITORIA-GENEROS-2026-10-19.md` |
| Índice de decisión | `references/INDICE.md` |
