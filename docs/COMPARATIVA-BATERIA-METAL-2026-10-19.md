# Comparación de batería MIDI: Ash to Dawn vs. referencia metal (2026-10-19)

## Procedencia y licencia

- Referencia: «Boss Battle #9 [Metal]», **nene**, OpenGameArt, publicado 2023-04-27. Página inspeccionada en Brave: `https://opengameart.org/content/boss-battle-9-metal`; anuncia MIDI incluido y licencia **CC0/Public Domain**. Archivo publicado en `https://opengameart.org/sites/default/files/boss_battle_9.mid`.
- Descarga local: `~/.hermes/music/FinalBattlePowerMetal_AshToDawn/reference_nene_boss_battle_9.mid` (17,524 bytes, SHA-256 `d9848be9fb7d4e9d1a1f6c7e2882f806dac4ca90b3db462e97b2f5fff3bdee38`). Respuesta HTTP 200, `audio/midi`, encabezado `MThd`; se verificó que los bytes guardados coinciden con la respuesta. Página vista en el Brave real y descarga directa de su enlace de archivo confirmado.
- Comparada con `~/.hermes/music/FinalBattlePowerMetal_AshToDawn/Ash_to_Dawn_demo.mid`, que es el MIDI fuente del OGG entregado antes. **No se alteró la canción original, el OGG del Escritorio ni el motor.**

## Lo observado en el MIDI (no es evaluación auditiva)

| Variable | Referencia de nene | Ash to Dawn |
|---|---:|---:|
| Duración musical | 59.47 s | 120.00 s |
| Tempo inicial | ~113 BPM (530,973 μs/negras) | 156 BPM |
| Compás | 4/4 | 4/4 |
| Compases | 28 | 78 |
| Golpes de batería | 540 | 1435 |
| Patrones de ataques de percusión distintos por compás* | 22/28 | 8/78 |
| Patrón más repetido* | 4 compases | 45 compases |
| Bombo GM36 | 247 | 584 |
| Caja GM38 | 119 | 156 |
| Platillo recurrente | GM55 splash: 91 | GM51 ride: 544; GM42 hi-hat: 48 |
| Toms y otros platillos | Presentes y repartidos | Fills de cuatro toms al cierre de cada bloque de cuatro compases |
| Bajo / guitarras | 240 notas de bajo; dos guitarras de 383 cada una y lead 404 | 584 notas de bajo; dos guitarras de 1284 cada una, lead 262 |

\*Firma de patrón = conjunto de golpes por instrumento GM y fase dentro de compás, sin dinámicas ni duración. El número no determina calidad musical ni cuenta instrumentos tonales.

### Grooves observados

- En la referencia, los compases 5–7 ponen bombo en contratiempos de corchea (0.25, 0.75, 1.25 ...), caja en 0, 0.5, 1 ...; el compás 9 cambia a caja en pulsos 1 y 3 (contados desde cero) y bombo con semicorcheas y silencios. Otras secciones alternan variaciones, redobles de bombo y toms. El comienzo es un fill de entrada, no la rejilla principal. Atención: esta referencia NO es modelo universal: la caja aparece en todas las corcheas de algunos compases, GM55 (splash) aparece frecuentemente como pulso regular, y la batería exportada emplea velocidad 95 prácticamente constante, por lo que también puede sonar artificial con un banco GM.
- En **Ash to Dawn**, todos los 68 compases de secciones densas contienen **exactamente ocho bombos y ocho rides por compás**, ambos disparados juntos en 0, 0.5, 1, 1.5, 2, 2.5, 3 y 3.5 pulsos. La caja repite dos golpes por compás (1 y 3). La sustitución tras la intro se resuelve casi solo cambiando hi-hat GM42 por ride GM51; no hay huecos, síncopas de bombo ni fraseo condicionado por guitarra o bajo. En el corpus de 78 compases, el patrón más repetido aparece 45 veces, y los dos más comunes suman 62. Fills periódicos reaparecen con las mismas alturas GM47-45-43-41 y el crash anticipado en 3.75, sin reaccionar a cadencias o respiración de riffs.

## Diagnóstico probable (inferencia, no certeza auditiva)

La batería que se siente «rara» es coherente con **rejilla mecánica uniforme + ride perpetuo + redoble idéntico cada cuatro compases**. Al renderizar con FluidR3 GM, el platillo GM51 repetido sobre cada bombo puede subrayar aún más el efecto sintetizado. La referencia CC0 presenta cambios de groove y de microfiguras dentro de las frases, aunque tampoco demuestra por sí sola una interpretación humana. No se compararon grabaciones de batería aislada ni se hizo escucha A/B humana: no atribuir cada sensación del usuario a una causa acústica definitiva.

## Corrección sugerida antes de rehacer la pieza (NO aplicada)

1. Escribir 3–4 grooves intencionales por función (amenaza, riff, preparación, clímax) con variaciones locales y silencios. Evitar bombo/platillo en todos los contratiempos durante toda la canción.
2. Alinear bombo con acentos reales del riff y del bajo; reservar semicorcheas/doble bombo para empujes, intercalar patrones más abiertos para que se note el contraste.
3. Separar dinámica de caja, hi-hat y ride; no usar ride GM51 continuamente en secciones enteras. Introducir crash en comienzos de frase y fills solo en transiciones relevantes, no en cada cuarto compás por contador.
4. Probar en el mismo SoundFont la pieza nueva y la referencia y someter el resultado a escucha comparativa humana antes de declarar «metal».

Este estudio justifica ajustar el algoritmo; **no se copiaron riffs ni patrones íntegros de la referencia** ni se cambió ningún archivo del juego.
