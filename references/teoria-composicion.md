# Teoría de composición (integrada)

Extracto consolidado de la antigua skill `music-composition-patterns`. Es guía de
criterio, no código: el motor ya implementa el vocabulario (escalas, cifrados,
patrones). Úsalo para **elegir** tonalidad, progresión, estructura y dinámicas.

## La regla fundamental

La música es coordinar sonido en el tiempo mediante **patrones**. Hace falta:
1. grooves que se repiten y varían; 2. estructura narrativa; 3. motivos que se
desarrollan; 4. sinergia entre instrumentos (diálogo, no capas independientes).

## Escalas y progresiones por emoción

| Emoción | Escala | Progresión de referencia |
|---|---|---|
| Tristeza | menor natural (Dm, Am) | `i - VI - III - VII` → Dm - Bb - F - A |
| Romance | mayor (C, F) | `I - V - vi - IV` → C - G - Am - F |
| Fúnebre | menor natural (Dm) | `i - iv - V - i` → Dm - Gm - A - Dm |
| Épico | mayor/dorico (G, D) | `I - V - vi - iii - IV` → C - G - Am - Em - F |
| Heroico | mixolidio (A) | `I - V - vi - IV` con cuerdas y metales |
| Tensión | frigio (D, E) | `i - bII - i` estancado, sin resolución |

En el `SongSpec` basta con `"key"` + `"scale"` y la `"progression"` como cifrados.
El motor resuelve los grados relativos a la raíz de cada acorde.

## Estructura de secciones por emoción

| Emoción | Secciones (proporción / intensidad) |
|---|---|
| Triste | intro .15/.3 · desarrollo .35/.6 · clímax .25/.9 · resolución .25/.4 |
| Romántica | intro .12/.4 · tema A .25/.6 · tema B .25/.7 · clímax .20/.9 · coda .18/.3 |
| Fúnebre | intro .20/.2 · lamento .30/.5 · tributo .25/.8 · final .25/.3 |
| Épica | intro .10/.3 · desarrollo .30/.6 · clímax .30/1.0 · resolución .30/.5 |

Traduce proporciones a `bars` (a 4/4, 1 compás = 4 negras). La intensidad se mapea
a `dynamics` (`pp`…`ff`).

## Grooves (16 pasos = 1 compás a 4/4)

`1` = nota, `0` = silencio. Se aplican por instrumento; el motor los abstrae en
patrones de acompañamiento equivalentes.

```
Triste:    piano [1,0,1,0,1,0,1,0,...]   cello [1,0,0,0,0,0,0,0,...]
Romántico: harp  [1,0,0,1,0,0,1,0,...]   violin[0,0,1,0,0,0,1,0,...]
Fúnebre:   strings[1,0,0,0,...]          timpani[1,0,0,0,...]
Épico:     strings[1,1,0,1,...]          brass [1,0,0,1,...]
Ambient:   pad   [1,0,0,0,...]           arp   [1,0,1,0,...]
```

Equivalencias directas en el motor: `block_chords`, `bass_root`, `bass_pulse`,
`arpeggio_up/down/updown`, `alberti`, `waltz`, `pad`.

## Motivos melódicos

Un motivo son 2–4 notas que: (1) aparecen al inicio, (2) se desarrollan, (3)
retornan transformadas. Reglas prácticas:
- Empezar en tónica (grado 0) o dominante (grado 4/5 según escala).
- Movimiento por grados, no saltos grandes (usa `escala_ascendente`,
  `giro_ornacional`, `descenso_cadencia`).
- Variar cambiando 1–2 notas, invirtiendo la dirección o cambiando el ritmo.
- El motivo de la sección A reaparece en el clímax; el motor no lo encadena solo,
  así que repite el patrón o duplícalo con otra `octave`/`instrument`.

## Sinergia entre instrumentos

1. **Melodía** en un solo instrumento (usar `melody.track`).
2. **Respuesta** con otro instrumento en los huecos (patrón distinto).
3. **Acompañamiento**: bajo + armonía.
4. La melodía necesita silencios; no todos los instrumentos suenan siempre.

## Arreglo: dar espacio (verificado 2026-10-19)

`drum_grid` y los patrones de acompañamiento son cómodos pero producen resultados
**mecánicos** si se usan para toda una canción. Defectos medidos en una pieza real
generada solo con `render_song` + `drum_grid` (120 compases):

| Síntoma audible | Medición | Causa |
|---|---|---|
| «batería que se solapa» | 960 ticks con 2–3 golpes simultáneos | `drum_grid` dispara kick+hat+crash en el mismo paso |
| «intensidad inadecuada» | 27.0 notas/compás **idénticas** en los 120 compases | `sdyn` plano, sin variación por función |
| «no se aprecian las guitarras» | guitarra en `arpeggio_up` | arpegios ≠ power chords; timbre tipo 8-bit |
| «sonido agudo que no cuadra» | lead alcanzaba MIDI 102 | sin tope de registro |
| «suena a 8-bit, no a metal» | todos los instrumentos el 100% del tiempo | sin espacio entre instrumentos |

### Reglas para material denso (metal, orquesta, rock)

1. **Grooves por función de sección**, no una rejilla única: escribe patrones
distintos para intro / verso / pre-estribillo / estribillo / solo / outro.
2. **Separa dinámica por pieza de batería:** bombo en pulsos fuertes ≠ hi-hat en
corcheas. No uses una sola velocidad para todo el kit.
3. **Fills SOLO en bordes de sección**, nunca cada 4 compases por contador.
4. **Guitarras = power chords** (raíz + 5ta + 8va) con palm mute y doble pista
paneada, no arpegios. Octava 3 (48–71) es el cuerpo; octava 2 (36–59) se
embarra con el bajo.
5. **Deja callar instrumentos.** El piano/teclado debe tener secciones de
**silencio** para que respiren las guitarras.
6. **Tope explícito de registro** por pista: filtra `if p <= N` en vez de confiar
en la octava base del acorde. Un `r5+12` se escapa fácil por encima de 90.

Para material así, escribe los eventos **nota a nota** con un script propio
(referencia autónoma dentro de la skill: `scripts/example_dense_arrangement.py`)
en lugar de depender solo de los patrones de `render_song`.

Aplicación ejecutable obligatoria: `scripts/composition_guard.py` abre las
lecturas, valida decisiones, ejecuta el compositor y exige
`scripts/audit_arrangement.py` antes de publicar. El ejemplo interno corrige
además ataques triples y notas de duración cero presentes en la v2 histórica.
Los ataques dobles no demuestran enmascaramiento acústico: bombo+platillo está
permitido. Los topes, silencios y densidades del protocolo son un contrato local
para arreglos densos; calidad de timbre y fidelidad estilística requieren escucha.

**Antes de componer:** leer `docs/`
(COMPARATIVA-BATERIA-METAL, TEORIA-Y-ARQUITECTURA) — ahí están los diagnósticos
ya verificados; no repetirlos.

## Dinámicas y render

Velocidades del motor: `pp`=20, `p`=35, `mp`=50, `mf`=70, `f`=90, `ff`=110.
Con muchas notas simultáneas conviene quedarse en `pp`–`mf` para evitar distorsión
interna de FluidSynth. `render` ya aplica `-g 0.8`; para material denso puedes bajar
la ganancia, la API `render_audio(..., gain=0.55)` lo expone; la CLI conserva 0.8.
El flujo por stems de PROTOCOL.md usa 0.5 y mide antes/después.

Normalización de audio (opcional, fuera del motor):
```bash
ffmpeg -y -i out.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a libvorbis -q:a 5 out.ogg
```
