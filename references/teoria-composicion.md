# Composition Theory (Integrated)

Consolidated excerpt from the former `music-composition-patterns` skill. It provides musical
guidance, not code: the engine already implements the vocabulary (scales, chord shapes,
patterns). Use it to **choose** key, progression, structure, and dynamics.

## The Fundamental Rule

Music coordinates sound in time through **patterns**. It requires:
1. repeating and varying grooves; 2. narrative structure; 3. motifs that develop;
   4. synergy between instruments (dialogue, not independent layers).

## Scales and Progressions by Emotion

| Emotion | Scale | Reference Progression |
|---|---|---|
| Sad | natural minor (Dm, Am) | `i - VI - III - VII` → Dm - Bb - F - A |
| Romantic | major (C, F) | `I - V - vi - IV` → C - G - Am - F |
| Funeral | natural minor (Dm) | `i - iv - V - i` → Dm - Gm - A - Dm |
| Epic | major/Dorian (G, D) | `I - V - vi - iii - IV` → C - G - Am - Em - F |
| Heroic | Mixolydian (A) | `I - V - vi - IV` with strings and brass |
| Tension | Phrygian (D, E) | `i - bII - i` stalled, no resolution |

In `SongSpec`, "key" + "scale" and "progression" as chord symbols are sufficient.
The engine resolves degrees relative to each chord's root.

## Section Structure by Emotion

| Emotion | Sections (proportion / intensity) |
|---|---|
| Sad | intro .15/.3 · development .35/.6 · climax .25/.9 · resolution .25/.4 |
| Romantic | intro .12/.4 · theme A .25/.6 · theme B .25/.7 · climax .20/.9 · coda .18/.3 |
| Funeral | intro .20/.2 · lament .30/.5 · tribute .25/.8 · finale .25/.3 |
| Epic | intro .10/.3 · development .30/.6 · climax .30/1.0 · resolution .30/.5 |

Translate proportions into `bars` (in 4/4, 1 bar = 4 eighth notes). Intensity maps to
`dynamics` (`pp`…`ff`).

## Grooves (16 steps = 1 bar in 4/4)

`1` = note, `0` = silence. Applied per instrument; the engine abstracts them into
equivalent accompaniment patterns.

```
Sad:       piano [1,0,1,0,1,0,1,0,...]   cello [1,0,0,0,0,0,0,0,...]
Romantic:  harp  [1,0,0,1,0,0,1,0,...]   violin[0,0,1,0,0,0,1,0,...]
Funeral:   strings[1,0,0,0,...]          timpani[1,0,0,0,...]
Epic:      strings[1,1,0,1,...]          brass [1,0,0,1,...]
Ambient:   pad   [1,0,0,0,...]           arp   [1,0,1,0,...]
```

Direct equivalents in the engine: `block_chords`, `bass_root`, `bass_pulse`,
`arpeggio_up/down/updown`, `alberti`, `waltz`, `pad`.

## Melodic Motifs

A motif is 2-4 notes that: (1) appear at the start, (2) develop, (3) return transformed.
Rules of thumb:
- Start on the tonic (degree 0) or dominant (degree 4/5 depending on the scale).
- Move stepwise rather than in large leaps (use `escala_ascendente`,
  `giro_ornacional`, `descenso_cadencia`).
- Vary by changing 1-2 notes, reversing direction, or changing rhythm.
- Section A's motif returns at the climax; the engine does not connect it automatically,
  so repeat or duplicate the pattern with another `octave`/`instrument`.

## Instrument Synergy

1. **Melody** on a single instrument (use `melody.track`).
2. **Response** from another instrument in the gaps (different pattern).
3. **Accompaniment**: bass + harmony.
4. Melody needs silence; not all instruments play all the time.

## Arrangement: Making Space (verified 2026-10-19)

`drum_grid` and accompaniment patterns are convenient but produce
**mechanical results** when used for an entire song. Measured defects in an actual piece
generated only with `render_song` + `drum_grid` (120 bars):

| Audible symptom | Measurement | Cause |
|---|---|---|
| “overlapping drums” | 960 ticks with 2-3 simultaneous hits | `drum_grid` fires kick+hat+crash in the same step |
| “inappropriate intensity” | 27.0 identical notes/bar across 120 bars | flat `sdyn`, no variation by function |
| “guitars do not come through” | guitar in `arpeggio_up` | arpeggios ≠ power chords; 8-bit timbre |
| “shrill lead that does not fit” | lead reached MIDI 102 | no register cap |
| “8-bit, not metal” | all instruments playing 100% of the time | no space between instruments |

### Rules for Dense Material (metal, orchestra, rock)

1. **Grooves by section function**, not a single grid: write different patterns
   for intro / verse / pre-chorus / chorus / solo / outro.
2. **Separate dynamics per kit piece:** kick on strong beats ≠ hi-hat on
   eighth notes. Do not use one velocity for the whole kit.
3. **Fills only at section boundaries**, never every 4 bars by counter.
4. **Guitars = power chords** (root + fifth + octave) with palm mute and double
   tracking, not arpeggios. Octave 3 (48-71) provides body; octave 2 (36-59)
   doubles the bass.
5. **Silence instruments.** Piano/keyboard should have sections of
   **silence** so guitars can breathe.
6. **Explicit register cap** per track: filter with `if p <= N` rather than relying
   on the chord's base octave. An `r5+12` can easily exceed 90.

For this material, write events **note by note** with your own script
(self-contained reference within the skill: `scripts/example_dense_arrangement.py`)
instead of relying solely on `render_song` patterns.

Mandatory application step: `scripts/composition_guard.py` opens the required
readings, validates decisions, runs the composer, and requires
`scripts/audit_arrangement.py` before publishing. The internal example also
corrects triple attacks and zero-duration notes present in
historical v2. Double attacks do not demonstrate acoustic masking: kick+hi-hat is
allowed. The protocol's register cap, silence, and density rules are a local contract
for dense arrangements; timbre quality and stylistic fidelity require listening.

**Before composing:** read `docs/`
(COMPARATIVA-BATERIA-METAL, TEORIA-Y-ARQUITECTURA) — the verified diagnoses
are there; do not repeat those errors.

## Dynamics and Rendering

Engine velocities: `pp`=20, `p`=35, `mp`=50, `mf`=70, `f`=90, `ff`=110.
With many simultaneous notes, stay at `pp`–`mf` to avoid internal distortion
in FluidSynth. `render` already applies `-g 0.8`; for dense material, you can lower
gain through the `render_audio(..., gain=0.55)` API; the CLI retains 0.8.
PROTOCOL.md's stems workflow uses 0.5 and measures before/after.

Audio normalization (optional, outside the engine):
```bash
ffmpeg -y -i out.wav -af "loudnorm=I=-16:TP=-1.5:LRA=11" -c:a libvorbis -q:a 5 out.ogg
```
