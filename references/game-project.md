# a game project — ajustes de proyecto

Notas específicas del RPG **a game project** (Ren'Py). Todo lo demás (motor, patrones,
validación, render) viene de la skill `hermes-music`; no dupliques el engine.

## Tema de batalla

- **Receta base:** `battle` (`gen --recipe battle --key A`, 160 BPM).
- **Duración objetivo:** exactamente **72 s** (≈73 compases a 160 BPM, 4/4).
  Verifica con `validate` antes de exportar; el bug histórico producía 117 s.
- **Instrumentos:** trompa/brass (61), timpani (47, canal 9), cuerdas (48),
  bajo (32/33), flauta (73) — ajusta en el `SongSpec` con `instrument`.
- Para forzar la duración, ajusta `bars` de las secciones hasta que `validate`
  reporte ~72 s. El motor no recorta: la duración es consecuencia de `bars` y BPM.

## Render y export

Usa el `render` de `hermes-music` (FluidR3_GM.sf2, `-g 0.8`). NO uses
`default-GM.sf3` (141 MB, hace timeout).

Los `.ogg` van en `game/audio/` del proyecto y se reproducen con:

```renpy
$ renpy.music.play("audio/battle.ogg", channel="music", loop=True)
```

**MIDI→OGG añade 4–8 s de release tail.** Si necesitas un corte exacto:
```bash
ffmpeg -y -i out.ogg -t 72 -c copy out_cortado.ogg
```

## Preferencia del usuario

No generar música salvo que se pida explícitamente.
