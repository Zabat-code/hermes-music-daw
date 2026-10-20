# Production Effects MIDI Mapper — Implementation Status

This reference describes the experimental standalone utility
`scripts/effects_mapper/effects_apply.py`. Its effect names were inspired by
production techniques discussed in Jaime Altozano's MOTOMAMI analysis. They are
labels for attempted MIDI edits, not implemented audio processors or verified
reproductions of those techniques. Use the MCP audio tools for tested DSP.

## Actual behavior

The utility edits existing messages in tracks containing notes. It does not
create the controllers described by an effect name, render audio or implement
a recipe pipeline. The nine keys in `EFFECT_FUNCTORS` select individual functions.

| Effect key | Current implementation and limitation |
| --- | --- |
| `autotune` | Attempts to assign `pitchbend` to a channel-0 `note_on`; this is not a valid Mido note attribute and does not emit pitch-wheel events. Existing CC1 values may exceed the MIDI range. |
| `pitch_shift` | Reads `msg.pitch` on `note_on` instead of its note number; it cannot perform the advertised transposition and does not update note-offs. |
| `filter` | Rewrites existing CC74/CC71. The formula can produce values above 127; the parameters are not calibrated cutoff frequencies in Hz. |
| `distortion` | Sets existing CC11 and scales note-on velocity; no audio saturation or velocity spikes are generated. |
| `reverb` | Rewrites existing CC91/CC94 and scales note-on velocity. `dry` is unused; the receiving synthesizer decides the audible result. |
| `sidechain` | Attempts a negative CC11 value with the default `duck_amount`; the nested note-off condition is unreachable. No functioning ducking envelope is implemented. |
| `vocoder` | Rewrites existing CC73/CC10 and scales velocity; no carrier/modulator audio processing occurs. |
| `chorus` | Rewrites existing CC66/CC58 and scales velocity; this is not a standard chorus implementation. |
| `flanger` | Rewrites existing CC11/CC106 and scales velocity; no flanger DSP is implemented. |

Controller numbers are not arbitrary effect slots: CC10 is pan, CC11 expression,
CC66 sostenuto, CC73 attack time, and CC94 Effects 4 Depth. CC74 is brightness;
it does not specify an absolute frequency in Hz. See the
[MIDI Association controller table](https://midi.org/midi-1-0-control-change-messages).

## Invocation and errors

Run the standalone script from the repository root. The following demonstrates
valid CLI syntax for MIDI expression/velocity edits; it does not create distortion:

```bash
python3 scripts/effects_mapper/effects_apply.py input.mid output.mid --effect distortion --params '{"intensity": 0.4, "velocity": 0.9}'
```

`--params` requires valid JSON with quoted keys. The documented historical `list`
subcommand is not dispatched by the CLI; the Python function `list_effects()`
prints the metadata. There is no implemented `RECIPES` dictionary or automatic
MOTOMAMI, minimalist or atlas recipe.

`apply_effects` catches per-track failures as warnings and may still save a MIDI
and return 0, even when an effect failed. A successful exit does not demonstrate
that the requested transformation occurred. No arrangement receipt is issued;
this utility is outside the tested composition/audio workflow.

## Verification limits

Inspect warnings, compare input/output events, check note-on/off pairing and
measure duration before rendering. MIDI structure alone does not prove an audible
effect. The implementation defects above remain pending code repair; this
translation/documentation audit does not change their logic.

The other legacy utilities also need repair before musical use:

- `dembow_generator.py` ignores the CLI tempo/bar overrides, fixes the tempo at
  120 BPM, writes absolute event ticks into delta-time fields, and duplicates
  the combined pattern into four named tracks on channels 0–3. The names do not
  represent isolated GM drum stems. Its `latin_cumbia` recipe lacks an `808` entry
  that the generation loop accesses directly.
- `harmonic_circle.py` doubles pitch-class offsets, ignores per-chord
  `chord_types`, and uses growing absolute positions as delta times. It does
  not implement the advertised extended-chord/substitution system.

Use the guarded examples and `genre_engine.py` for the documented current
workflow; legacy script names and effect identifiers remain unchanged.
