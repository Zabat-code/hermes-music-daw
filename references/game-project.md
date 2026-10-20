# Game project — project adjustments

Specific notes for the placeholder game project (a Ren'Py RPG). Everything else (engine, patterns,
verification, render) comes from the `hermes-music` skill; do not duplicate the engine.

## Battle Theme

- **Base recipe:** `battle` (`gen --recipe battle --key A`, 160 BPM).
- **Target duration:** exactly **72 s** (≈73 bars at 160 BPM, 4/4).
  Verify with `validate` before exporting; the historical bug produced 117 s.
- **Instruments:** horn/brass (61), timpani (47, channel 9), strings (48),
  bass (32/33), flute (73) — adjust in `SongSpec` with `instrument`.
- To force duration, adjust `bars` of the sections until `validate`
  reports ~72 s. The engine does not cut: duration is a consequence of `bars` and BPM.

## Render and Export

Use `hermes-music`'s `render` (FluidR3_GM.sf2, `-g 0.8`). Do not use
`default-GM.sf3` (141 MB, times out).

The `.ogg` files go in `game/audio/` of the project and play with:

```renpy
$ renpy.music.play("audio/battle.ogg", channel="music", loop=True)
```

**MIDI→OGG adds 4–8 s of release tail.** If you need an exact cut:
```bash
ffmpeg -y -i out.ogg -t 72 -c copy out_cortado.ogg
```

## User Preference

Do not generate music unless explicitly requested.
