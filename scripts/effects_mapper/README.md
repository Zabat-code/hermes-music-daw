# Experimental MIDI effect mapper

Standalone utility: `scripts/effects_mapper/effects_apply.py`.
It attempts MIDI controller/velocity edits under nine effect names:
`autotune`, `pitch_shift`, `filter`, `distortion`, `reverb`, `sidechain`,
`vocoder`, `chorus` and `flanger`. It does not process audio or certify an arrangement.

Read the [implementation status](../../references/effects_mapper.md) before use.
Known defects include invalid Mido attributes, controller values outside 0–127,
an unreachable sidechain branch and per-track exceptions that do not force a
nonzero process exit. These are existing code defects, not audio capabilities.

From the repository root, valid CLI syntax for expression/velocity edits is:

```bash
python3 scripts/effects_mapper/effects_apply.py input.mid output.mid --effect distortion --params '{"intensity": 0.4, "velocity": 0.9}'
```

The parameter string must be valid JSON. Inspect warnings and compare events;
this example does not generate distortion. Only Mido is imported as a third-party
runtime dependency by this script; `music21` is not used.

The CLI requires input, output and `--effect`; it does not dispatch a `list`
subcommand. The Python function `list_effects()` prints effect metadata.
There is no implemented recipe engine or `RECIPES` dictionary. Use the main
repository's guarded examples and MCP audio tools for the tested workflow.
