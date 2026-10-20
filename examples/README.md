# Short structural demo

`sample.mid` is the 12-bar excerpt created by `01_compose.py` through the mandatory
guard, using the note-by-note reference in `scripts/example_dense_arrangement.py`.
It has intro/verse/chorus sections at 160 BPM, in 4/4 (18.000 MIDI seconds).
`sample.ogg` is its six FluidSynth stems mixed with `balanced`, mastered to
-16 LUFS and encoded with libvorbis quality 5 at 44100 Hz / stereo.
The synthesized release tail makes the audio 22.526 seconds long.

The plan is in `sample-plan.json`; actual gates and measurements are in
`sample-metrics.json`. No MIDI events were generated outside the guard workflow.
The small sample uses the project's original composition code under MIT. The
FluidR3 SoundFont is installed separately and is not bundled; see
[third-party notices](../THIRD_PARTY_NOTICES.md).

- MIDI SHA-256: `deb1644d57f2f2ebbd8349e276a6722cfc7626831f73a29ed0ae30bab0407b33`
- OGG SHA-256: `0ada25923ce03463e45827ca36928281cedde2f25e453c02db70d9ada27f3e96`
- Master: -16.0 LUFS,
  -2.15 dBTP.
- Encoded OGG: -16.06 LUFS,
  -2.22 dBTP; verdict `ready`.

This is a GM mockup. Structural gates and technical release checks passed;
listening quality remains pending human review. We do not claim studio-quality
guitars or genre fidelity. No listening session was performed during packaging.

Reproduce from the repository root, in a new directory:

```bash
python examples/01_compose.py --work output/sample-reproduction
python examples/02_audit.py --work output/sample-reproduction
python examples/03_mix_and_master.py --work output/sample-reproduction
```

The generated local `demo.mid.audit.json` binds MIDI, readings and guard code.
We do not ship that machine-specific receipt as a portable certificate: it binds
absolute paths and would fail after relocation. Generate your own receipt using
the commands above. The independent summary here is not a guard receipt.
Codec/build differences can change audio hashes; compare measured behavior too.
