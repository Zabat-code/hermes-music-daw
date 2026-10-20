# ERROR REPETIDO: composición densa sin consultar la documentación auditada

**Fecha:** 2026-10-19
**Herramienta:** skill `hermes-music` (motor `hermesmusic.py`)
**Severidad:** alta — el error ocurrió **dos veces** y la corrección estaba documentada pero no aplicada.

---

## Qué pasó (hechos, no interpretación)

El usuario pidió una canción power metal para gym (3:00, 2 guitarras, bajo, batería, piano sintético).
Generé una v1 con `render_song()` + `drum_grid`. El usuario la rechazó por escucha con cinco quejas.
Todas eran correctas y **todas ya estaban diagnosticadas** en `~/.hermes/documentacion/hermesmusic/`
desde ese mismo día (trabajo previo sobre la pieza "Ash to Dawn").

### Ocurrencia 1 — "Ash to Dawn" (misma fecha, antes)
- Pieza generada con el mismo enfoque (`render_song` + rejilla de batería).
- Diagnóstico documentado en `COMPARATIVA-BATERIA-METAL-2026-10-19.md`:
  - 68 compases densos con **exactamente 8 bombos y 8 rides por compás**, ambos disparados juntos.
  - Patrón más repetido: 45 de 78 compases. Sin huecos ni síncopas.
  - Fills idénticos cada 4 compases, sin reaccionar a cadencias.
- Corrección propuesta en el mismo documento (4 puntos) — **NO aplicada al motor**.
- Se hizo una v2 de esa pieza (`ash_to_dawn_drums_v2.py`) con grooves escritos a mano,
  pero **como archivo suelto del proyecto, no como regla del motor ni de la skill**.

### Ocurrencia 2 — "Iron Determination" (esta sesión)
- Generé v1 con el mismo `render_song` + `drum_grid` → **repitió los mismos defectos**.
- El usuario lo detectó de nuevo por escucha.

## Por qué se repitió (causa raíz)

1. **La corrección vive en un `.md` que nadie lee.** `COMPARATIVA-BATERIA-METAL-2026-10-19.md`
   y `documentacion/hermesmusic/HALLAZGOS.md` contienen el diagnóstico, pero **nada en el flujo
   de trabajo obliga a abrirlos** antes de componer.
2. **La skill `hermes-music` no menciona esos documentos.** Su `SKILL.md` y sus `references/`
   no enlazan `documentacion/hermesmusic/`, así que un agente que carga la skill no se entera.
3. **El motor no cambió.** `drum_grid` sigue produciendo rejilla mecánica; `render_song` sigue
   sin reglas de registro, de espacio entre instrumentos ni de variación dinámica.
4. **El "éxito" se declaró por métricas que no detectan el problema.** `validate_midi` no tiene
   notas huérfanas ni duración mal → "sin problemas". El clasificador dijo "metal". Nada de eso
   mide si la batería se solapa, si hay espacio o si el timbre suena a 8-bit.
5. **La v2 de la ocurrencia 1 no se generalizó.** Fue un parche para una pieza, no una regla
   reutilizable; la siguiente pieza partió de cero con el patrón defectuoso.

## Defectos medidos (v1 de Iron Determination, 120 compases)

| Síntoma audible (usuario) | Medición objetiva | Causa en el código |
|---|---|---|
| «las baterías se solapan» | 960 ticks con 2–3 golpes simultáneos | `drum_grid` emite kick+hihat+crash en el mismo paso |
| «la intensidad no es adecuada» | 27.0 notas/compás **idénticas** en los 120 compases; solo 2 velocidades (90/110) | `sdyn` plano por sección, sin variación por función |
| «no se aprecian las guitarras» | guitarra rítmica con `arpeggio_up` | arpegios en vez de power chords |
| «un sonido agudo que no cuadra» | `lead_guitar` alcanzaba MIDI 102 | sin tope de registro |
| «es más música de 8-bit que metal» | 5 instrumentos sonando el 100% del tiempo | sin reglas de espacio / silencios |

## Qué NO detectó el pipeline de validación

- `validate_midi` → "sin problemas" (solo mira notas huérfanas y duración).
- `classify_genre` → "metal" (mira onsets y tempo, no solapamiento ni espacio).
- `ffprobe`/`astats` → duración y pico correctos.
- **Ninguna de estas pruebas mide los cinco defectos reales.** El pipeline decía "listo" en todo.

## Corrección aplicada en esta sesión

- v2 con **autoría nota a nota** (`compose_gym_power_metal_v2.py`), grooves por función de sección,
  velocidades separadas por pieza del kit, fills solo en bordes, power chords dobles paneados,
  piano que calla en versos/solo, lead limitado a 76–88.
- Se añadieron reglas a `references/teoria-composicion.md` (sección "Arreglo: dar espacio").
- **Pendiente:** que esas reglas sean un **guardarraíl obligatorio** dentro de la skill,
  no un párrafo más que un agente puede no leer.
