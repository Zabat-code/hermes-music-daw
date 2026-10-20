# Observaciones: por qué OTRO modelo repetiría este error

Escrito para que un auditor externo entienda el patrón de fallo, no solo el caso concreto.

## Trampas que empujan a cualquier agente al mismo error

1. **La ruta fácil "funciona".** `render_song(spec, out)` + un `drum_grid` produce un MIDI
   válido, con la duración exacta pedida y clasificado como "metal". Un agente optimiza a
   "entregar algo que pasa las pruebas" y para ahí. **El éxito aparente es la trampa.**

2. **La validación disponible es ciega a lo musical.** `validate_midi` (notas huérfanas,
   duración) y `classify_genre` (onsets, tempo) devuelven OK. Un agente que confía en el
   pipeline existente **no tiene señal de que algo está mal**. No hay test que falle.

3. **La documentación correctiva está fuera de la skill.** Los diagnósticos viven en
   `~/.hermes/documentacion/hermesmusic/`, pero la skill `hermes-music` **no los enlaza**.
   Un agente que carga la skill (el gesto correcto) sigue sin verlos. Cargar la skill
   *parece* cumplir el protocolo.

4. **Las reglas están escritas como prosa, no como gate.** "La melodía necesita silencios",
   "no todos los instrumentos suenan siempre" — son consejos en un `.md`, no comprobaciones.
   Un agente puede leerlos y no aplicarlos sin que nada lo detenga.

5. **El patrón cómodo está primero.** `drum_grid` y los patrones de `render_song` son las
   primeras herramientas que aparecen; la autoría nota a nota (que es lo que produce buen
   resultado) exige escribir un script propio, más trabajo. El camino de menor resistencia
   es el defectuoso.

6. **El ejemplo de referencia está enterrado.** Existe `ash_to_dawn_drums_v2.py` que hace
   *exactamente* lo correcto (grooves por frase, velocidades variadas, fills solo en bordes),
   pero vive en `~/.hermes/music/FinalBattlePowerMetal_AshToDawn/`, fuera de la skill.
   Un agente nuevo no lo encuentra.

7. **La corrección se guardó como parche de un caso, no como regla.** La v2 de la primera
   pieza resolvió *esa* pieza; nada se generalizó al motor ni a la skill. La siguiente
   composición partió del patrón defectuoso otra vez.

8. **"Documentar el error" se confunde con "arreglar el error".** Se documentó dos veces
   (`HALLAZGOS.md`, `COMPARATIVA-BATERIA-METAL.md`) y el error volvió igual. Documentar sin
   instrumentar el gate **no cambia el comportamiento del próximo agente**.

## Requisitos que debe cumplir el guardarraíl (para el auditor)

El arreglo NO debe ser otro `.md` más. Debe ser un **protocolo obligatorio y verificable**
que un agente no pueda saltarse. Criterios:

1. **Punto de entrada único.** Al cargar la skill `hermes-music` para *componer* (no para
   consultar), el agente debe topar con el protocolo antes de escribir música.
2. **Secuencia explícita de pasos**, no una lista de consejos: qué leer, qué decidir, qué
   escribir, en qué orden, y qué NO hacer.
3. **Gates automáticos que fallen ruidosamente.** Pruebas que midan los defectos reales
   (solapamiento de batería, variación dinámica, espacio/silencios, topes de registro) y
   que **aborten** si no se cumplen — no que informen.
4. **Aplicación al momento, no diferida.** La auditoría debe correr sobre la pieza generada
   y decir si es aceptable, antes de declarar nada terminado.
5. **Que el propio motor ayude.** Donde sea posible, que el código rechace configuraciones
   defectuosas (p. ej. `drum_grid` que dispara 3 piezas en el mismo paso, o un patrón de
   acompañamiento en toda la canción sin variación) en vez de confiar en la disciplina.
6. **Ejemplo de referencia dentro de la skill**, no en una carpeta de proyecto aparte.
7. **Anti-patrón documentado y prohibido**: "declarar éxito porque validate_midi pasó".

## Material que el auditor debe revisar

- `~/.hermes/skills/hermes-music/SKILL.md`
- `~/.hermes/skills/hermes-music/references/teoria-composicion.md` (sección "Arreglo: dar espacio")
- `~/.hermes/skills/hermes-music/references/rendering.md`
- `~/.hermes/skills/hermes-music/scripts/hermesmusic.py` (funciones `render_song`, `drum_grid`)
- `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md`
- `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md`
- `~/.hermes/documentacion/hermesmusic/HALLAZGOS.md`
- `~/.hermes/documentacion/hermesmusic/ERROR-REPETIDO-2026-10-19.md`
- `~/.hermes/music/FinalBattlePowerMetal_AshToDawn/ash_to_dawn_drums_v2.py` (ejemplo bueno)
- `~/.hermes/cache/scratch/compose_gym_power_metal.py` (v1 defectuosa)
- `~/.hermes/cache/scratch/compose_gym_power_metal_v2.py` (v2 corregida)
