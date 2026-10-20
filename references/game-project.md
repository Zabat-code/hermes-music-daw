# Game project — project adjustments

Specific notes for the placeholder game project (a Ren'Py RPG). Everything else (engine, patterns,
verification, render) comes from the `hermes-music` skill; do not duplicate the engine.

## Battle Theme

- **Base recipe:** `battle` (`gen --recipe battle --key A`, 160 BPM).
- **Target duration:** exactly **72 s** (48 bars at 160 BPM, 4/4).
  Verify with `validate` before exporting; the historical bug produced 117 s.
- **Instruments:** horn/brass (61), pitched timpani (program 47 on a melodic channel), strings (48),
  bass (32/33), flute (73) — adjust in `SongSpec` with `instrument`.
- To force duration, adjust `bars` of the sections until `validate`
  reports ~72 s. The engine does not cut: duration is a consequence of `bars` and BPM.

The legacy `battle` recipe is not a passing dense arrangement. Its channel-9
part does not select a pitched timpani program; percussion uses the GM drum map.
Adapt the score and plan through the guard instead of treating this recipe as
a verified finished piece.

## Render and Export

Use `hermes-music`'s `render` (FluidR3_GM.sf2, `-g 0.8`). Do not use
`default-GM.sf3` for this historical workflow; the reported timeout was specific
to that environment, not a general SoundFont property.

The `.ogg` files go in `game/audio/` of the project and play with:

```renpy
$ renpy.music.play("audio/battle.ogg", channel="music", loop=True)
```

**MIDI→OGG adds a variable release tail.** The following historical stream-copy
command makes a packet-boundary cut; it does not guarantee sample-exact timing.
For exact delivery, cut/fade decoded audio, re-encode and measure the final file:
```bash
ffmpeg -y -i out.ogg -t 72 -c copy out_cortado.ogg
```

## User Preference

Do not generate music unless explicitly requested.
