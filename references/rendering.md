# Rendering and Export: Current Guide

Apply [PROTOCOL.md](../PROTOCOL.md) first: compose with guard → audit and
certify → stems → mix → master → verify the final format → listen.
A valid MIDI file does not attest to an arrangement, timbre, or musical quality.

## Dependencies and Paths

Python 3.12 with the package dependencies. For audio you need FluidSynth,
FFmpeg (with loudnorm and libvorbis) and a General MIDI SoundFont. On Mint/Ubuntu:

```bash
sudo apt install fluidsynth ffmpeg fluid-soundfont-gm
python scripts/check_install.py
```

The SoundFont is looked up at call time: `MIDI_SOUNDFONT` has priority,
then FluidR3_GM, TimGM6mb, and common `.sf2` locations. An invalid override
aborts. The SoundFont is not included in the package. Binaries are looked up in
PATH, or with `FLUIDSYNTH`, `FFMPEG`, `FFPROBE` for exact locations. On failure,
use the smoke test. The library does not require the author's personal directory.

FluidSynth enumerates SDL devices even in file mode. The offline subprocesses use `SDL_AUDIODRIVER=dummy` by default, which avoids a
PulseAudio blockage observed in the sandbox. No sound card is needed.

## Quick Render vs. Stems

Single render (after audit):

```bash
python scripts/hermesmusic.py render piece.mid piece.ogg
```

The CLI preserves gain 0.8. For dense arrangement,
`render_audio(..., gain=0.55)` from Python, or `render_stems` (default 0.5). Measure
peaks afterwards: a default does not guarantee absence of clipping. General MIDI does
not reproduce palm mute, amplifier distortion, or realistic articulations.

A short note duration only approximates a MIDI articulation.

For mixing per instrument, use the executable example:

```bash
python examples/01_compose.py --work output/render-demo
python examples/02_audit.py --work output/render-demo
python examples/03_mix_and_master.py --work output/render-demo
```

`render_stems` requires safe unique names, one channel per track with notes and
a new/empty folder. Preserve global metadata in their original ticks.
A multichannel type 0 track must be split first; controllers and programs
shared across tracks are not reconstructed automatically.

## Duration and Tails

FluidSynth adds release tail (measured at 4.526 s in the example). The mix without
explicit duration keeps the longest stem. `--duration N` truncates or pads;
it must not be used to hide a poorly written arrangement end. For exact timing
with fade-out, apply the cut/fade before the final measurement and document it.

## Processing and Measurements

The [mix](../docs/MIX_PROFILES.md) profiles are starting points. The per-role
chains apply HPF, EQ, and compression, followed by linear stereo balance and level.
It is not mid/side or constant-power panning. Mono is duplicated and different
rates are resampled to 44100 Hz. Unknown names abort.

The bus works in float, applies EQ/compression, trim -3 dB, and a sample limiter.
A float sum above 0 dBFS is not itself PCM clipping; when writing to a
limited format it can clip. The trim and limiter do not guarantee true peak.
Measure the final file; do not infer guarantees from an effect's name.

`analyze_audio` returns sample peak, RMS dBFS, stereo correlation, and normalized
energy per octave. It does not return LUFS. `analyze_masking` calculates
heuristic similarity per band: it does not test inaudibility. Compare
similar duration/material for a useful tonal comparison.

`master` keeps the Pedalboard chain and adds FFmpeg loudnorm normalization
in two passes: target LUFS and -1 dBTP. Returns later measurements and
`target_met`; some signals limit the achievable target. Do not announce
compliance if it is false. The output preserves the original rate;
`loudnorm` can work internally at 192 kHz.

## Export and Re-Verify

```bash
ffmpeg -nostdin -y -i master.wav -ar 44100 -ac 2 -c:a libvorbis -q:a 5 final.ogg
python - <<'PYCODE'
from hermes_music.scripts.daw_mcp import release_check
print(release_check('final.ogg', profile='balanced'))
PYCODE
```

`release_check` measures integrated LUFS, true peak, and LRA via FFmpeg;
it reports clipping, insufficient headroom, very high RMS, and suspicious stereo
correlation. `ready` is a limited technical filter. Lossy encoding can
raise peaks: measure the OGG, not just the WAV. An intentional mono signal
may receive `needs_work`; record the exception with honesty.

Listen in stereo/mono and compare references before claiming sound quality.
Without listening, deliver as «structurally audited mockup; sonic quality
pending human listening». See the technical history, including fixed errors
in [the initial investigation](../docs/INVESTIGACION-MCP-DAW-2026-10-19.md).
