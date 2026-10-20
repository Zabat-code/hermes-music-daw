# Investigación: características reales del power metal (2026-10-19)

Recopilada para la v3 de "Iron Determination". Objetivo: dejar de adivinar el género
y partir de rasgos documentados. Fuentes citadas al pie de cada bloque.

## Tempo y métrica

- Rango habitual **160–200 BPM**; el extremo (DragonForce, "Through the Fire and Flames")
  llega a **~200 BPM** con corcheas a 400. El power metal europeo típico vive en 160–190.
- Compás 4/4 casi siempre; algunos pasajes en 6/8 o 12/8 para el aire "galopante".
- **Aplicado en v3:** 185 BPM, 4/4, 140 compases → 181.6 s.

## Batería — el sello del género

- **Doble bombo continuo en semicorcheas (16avos)** como colchón rítmico. Es *la*
  característica más identificable del power metal.
- Caja en **2 y 4** (backbeat) sobre el doble bombo.
- Crash en los arranques de sección; ride o hi-hat en corcheas.
- Los fills existen pero son **transiciones**, no un ciclo fijo: marcan cambios de sección.
- **Error a evitar (medido en la v1):** disparar bombo + hi-hat + crash en el mismo
  instante. El oído no separa los tres y suena a barullo; el auditor lo marca como
  "3+ piezas" (enmascaramiento).
- **Aplicado en v3:** doble bombo 16avos con acentos por negra, variación por frase
  (hueco en el compás 3 del verso, síncopa en el 4 del coro) para que ningún patrón
  domine; máximo 2 piezas del kit por instante.

## Guitarras — el riff

- **Riff de galope:** una corchea seguida de dos semicorcheas (patrón "ta-ka-ka").
  **NO son tresillos**: un tresillo da sensación de shuffle y arruina el género.
- **Palm mute** (apagado con la palma) en las notas graves; produce el "chug" percusivo.
- **Nota pedal**: la guitarra mantiene una nota grave mientras la armonía cambia encima.
- **Power chords** (raíz + 5ª, a veces + 8ª) como base; el metal no usa tríadas completas
  en la rítmica (la 3ª la lleva el lead).
- **Twin guitars** (dos guitarras): la armonización canónica es en **terceras diatónicas**,
  no terceras paralelas ciegas (eso produce errores fuera de la escala).
- **Aplicado en v3:** 2 guitarras rítmicas L/R (quintas + pedal + galope, paneadas 22/105)
  y 2 leads armonizados en terceras diatónicas (paneadas 40/88).

## Armonía y tonalidad

- Menor natural con **7ª elevada puntual** (menor armónica) = el color "neoclásico"
  (influencia de Malmsteen/Yngwie). Se usa como **evento** en el solo, no en todo.
- Progresión emblemática: **♭VI–♭VII–i** (en La menor: F–G–Am). Es la cadencia que
  "sube" y es el gesto más usado del género.
- **Armonía lenta en el coro:** un acorde sostenido por 2 compases. La energía viene del
  ritmo y las voces, no del cambio armónico. Un coro que cambia de acorde cada negra
  suena a pop, no a power metal.
- El **coro final sube** un tono o semitono (modulación) = coronación.
- **Aplicado en v3:** Am con F–G–Am; coro con 1 acorde por 2 compases; coro final
  modulado Am→Bm; solo en menor armónica.

## Estructura (single de power metal)

intro → verso → pre-coro → **coro** → verso2 → pre-coro2 → **coro2** → puente →
**solo** → **coro final (modulado)** → outro.

- El solo va **después del puente**, no antes.
- El coro se repite **3 veces** con el último subido.
- **Aplicado en v3:** 11 secciones, 140 compases, coro x3 con el tercero en Bm.

## Bajo

- En **corcheas**, ligado al bombo; en el coro sube una octava para "abrir".
- Fills de subida (raíz–2ª–3ª–5ª) en las transiciones de sección.
- **Aplicado en v3:** corcheas, octava arriba en el coro, fill de 4 notas en los bordes.

## Referencias de escucha citadas

- **DragonForce** — extremo del tempo (~200 BPM), solos neoclásicos con armonías de
  terceras, doble bombo continuo.
- **Metallica** — el riff palm-muteado y la nota pedal (aunque es thrash/heavy, es la
  referencia que el usuario pidió; su influencia en el riff de galope es directa).

## Lo que NO se puede garantizar con GM

- El SoundFont General MIDI **no** reproduce palm mute, distorsión real ni el timbre de
  una guitarra de metal. Suena a "maqueta", no a producción.
- La calidad sonora requiere escucha humana; el auditor solo certifica **estructura**.
- El auditor declara esto explícitamente: "no prueba timbre, enmascaramiento acústico,
  palm mute, armonía correcta ni calidad musical".

## Fuentes

- Búsquedas web sobre características del género, tempo, doble bombo y estructura
  (resultados consolidados en esta sesión; se citan los rasgos, no URLs inventadas).
- `~/.hermes/skills/hermes-music/references/genre_configs.json` (perfil `power_metal`:
  tempo 120–160, 4/4, density 12).
- `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md`
  (diagnóstico de batería mecánica, referencia CC0 de nene).
- `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md`
  (Boddington/Jordan/Herbst sobre armonía del metal; Garza sobre tipos de riff).
