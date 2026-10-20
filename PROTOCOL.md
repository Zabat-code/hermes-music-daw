# Operating protocol for agents

Reading entry point: this file → [SKILL.md](SKILL.md) → the guard's required readings.
The README covers installation; [docs/README.md](docs/README.md) distinguishes
current guides from historical evidence. Run from the repository root with the
venv's Python activated. Do not use the author's personal paths.

## 0. Verify installation and prepare the destination

```bash
python scripts/check_install.py
python -m pytest tests/ -q
```

Both must exit with 0 to validate the full environment. If audio support is missing,
install `fluidsynth`, `ffmpeg`, `fluid-soundfont-gm`, or set `MIDI_SOUNDFONT`.
`FLUIDSYNTH`, `FFMPEG`, and `FFPROBE` select executables outside PATH.
An invalid override aborts. The smoke test checks package resources and current
directory permissions; it does not replace running the example.

If the runtime blocks `socketpair.send()` and MCP starts but does not respond,
set `HERMES_DAW_STDIO_POLL=1` in its `env`. This keeps the event loop active
with a 50 ms timer; it opens no ports. The client must also work in that
runtime. The local test keeps both loops active and uses real MCP stdio.

Choose a new directory for each delivery. The guard never overwrites MIDI
or certificates. Keep the plan, composer, readings, log, MIDI, certificate,
audit report, and audio metrics together or easy to locate.

## 1. Read → decide → compose

The guard reads, displays, and hashes five diagnostic documents in `docs/`, theory,
rendering guidance, and the internal example BEFORE running the composer. Logged
reading does not demonstrate understanding: the plan and MIDI must fulfill their claims.

To check the predesigned short workflow, run exactly:

```bash
python examples/01_compose.py --work output/my-first-run
```

This command creates `plan.json`, runs the composer through the guard, and publishes
`demo.mid` plus `demo.mid.audit.json` only after passing the audit and contract. It saves
the complete readings in `composition.log`. It does not treat a failure as a warning.

For a new piece, first record decisions and ALSO adapt the composer:

```bash
mkdir -p output/my-piece
python scripts/example_dense_arrangement.py --plan output/my-piece/plan.json
# Review/edit plan.json and the composer BEFORE generating events.
python scripts/composition_guard.py output/my-piece/plan.json \
  --out output/my-piece/piece.mid -- \
  scripts/example_dense_arrangement.py --out '{draft}' \
  > output/my-piece/composition.log 2>&1
```

The final call uses the full 120-bar / 180 s reference. For another
piece, replace the script with your own composer accepting `--out` and
section markers. The guard runs it with the SAME Python. `{draft}` is a
temporary path; it must never be a public delivery. Check the guard's exit code
before continuing. After a failure, read the end of `composition.log`.

Implemented plan contract:

- `profile: "dense"`, explicit `intent` with genre/variant and timbre limitations.
- `sections`: unique names, integer `bars` >=2, target `groove` and `density`.
  Density means **drum hits per bar**. The auditor averages section bodies,
  excluding the first/last bars and detected fills when possible, with fallback
  to the remaining section bars for short sections.
- `instruments`: names identical to MIDI tracks, `role`, MIDI `min`/`max`
  (except drums), integer `silent_bars` >=0. At least one harmonic instrument must
  remain silent for a full bar without notes or sustain.
- `fill_bars`: list of bars with fills, **numbered from 1**, only at section
  endings. The MIDI must contain the heuristically detected fills in that list.
- 4/4, markers at the exact start of each section, and MIDI ending at the planned bar.

The eight existing arrangement gates check structure, dynamics, register, space,
kit overlap, patterns, density, and fills. Do not remove drums to evade
the contract or change thresholds to obtain a pass. Other styles
need a separately designed and tested contract.

## 2. Audit and verify the certificate

For the short example:

```bash
python examples/02_audit.py --work output/my-first-run
```

For the full reference or your own piece:

```bash
python scripts/audit_arrangement.py output/my-piece/piece.mid \
  --json output/my-piece/review.json
python scripts/composition_guard.py --verify output/my-piece/piece.mid
```

Both must exit with 0. `validate_midi`, a classifier label, and correct duration
alone do NOT approve an arrangement. Do not overwrite `*.audit.json`
with the independent `audit_arrangement` report: the certificate also contains
the plan, reading hashes, and code hashes.

Any subsequent MIDI change requires returning to the guard and publishing under
another name. Current certificates include absolute paths: after moving the
checkout or updating code/readings, rerun the workflow. SHA-256 is not
a digital signature and cannot stop someone with write access from forging a receipt.

## 3. Render and mix

Complete short-example workflow, after steps 1 and 2:

```bash
python examples/03_mix_and_master.py --work output/my-first-run
```

The script runs `verify_delivery` → `render_stems` → `auto_mix` →
`master` → OGG encoding → `release_check` on the OGG, in order, and retains `results.json`.
A missed target or a `needs_work` verdict produces exit 1.

For your own piece, these are the exact audio commands (they require an
editable installation); use paths in the same working directory:

```bash
python - <<'PY'
from hermes_music.scripts.composition_guard import verify_delivery
from hermes_music.scripts.daw_mcp import render_stems, list_profiles
verify_delivery('output/my-piece/piece.mid')
print(list_profiles())
print(render_stems('output/my-piece/piece.mid', 'output/my-piece/stems'))
PY
python scripts/mix_engine.py --stems output/my-piece/stems \
  --out output/my-piece/mix.wav --profile balanced
```

`stems/` must be new or empty. One WAV is produced per track containing notes;
names are safe and unique, with one channel per track. For multichannel type 0 MIDI,
separate instruments first. Keep programs/controllers in each instrument's own track.
The global tempo map and delta times are preserved. A FluidSynth failure
aborts; never infer success from an old WAV's existence.

Call `list_profiles()` before mixing. Supported names:
`drums`, `electric_bass`, `rhythm_guitar_L`, `rhythm_guitar_R`, `lead_guitar`,
`lead_guitar_L`, `lead_guitar_R`, `synth_piano`. A subset is accepted; any
unknown name aborts even if others match. Rename deliberately or
add and test a profile; do not silently discard instruments.

Mono is duplicated to stereo; differing sample rates are resampled to 44100 Hz. Without
`--duration`, the longest stem determines duration to preserve tails. `--duration N`
truncates or zero-pads: disclose any musical truncation in the delivery.
Files with no frames, no signal, corruption, or nonfinite values cause an abort.

## 4. Master and encode

```bash
python - <<'PY'
from hermes_music.scripts.daw_mcp import master
result = master('output/my-piece/mix.wav', 'output/my-piece/master.wav',
                target_lufs=-16.0, profile='balanced')
print(result)
if not result['target_met']:
    raise SystemExit('Master target not met: inspect dynamics and measured loudness')
PY
ffmpeg -nostdin -y -i output/my-piece/master.wav -ar 44100 -ac 2 \
  -c:a libvorbis -q:a 5 output/my-piece/piece.ogg
```

If `FFMPEG` is configured outside PATH, replace `ffmpeg` with that path. The
master applies a bus chain and two-pass `loudnorm`; it returns integrated LUFS,
FFmpeg-measured true peak, and LRA. `target_met` requires ±1 LU of the target and
TP <= -0.9 dBTP (0.1 tolerance relative to the -1 target). It does not guarantee
that every signal can reach the target without changing dynamics. The mix already has a bus;
mastering adds another deliberate chain. Compare before/after to assess whether
additional tonal processing should be omitted under a future policy.

Do not call Pedalboard's sample peak “true peak.” Do not call RMS LUFS.
Force sample rate and channel count on export; `loudnorm` can operate at 192 kHz.
Lossy compression can raise peaks, which is why the FINAL OGG is checked.

## 5. Verify → listen → publish

```bash
python - <<'PY'
from hermes_music.scripts.composition_guard import verify_delivery
from hermes_music.scripts.daw_mcp import release_check
verify_delivery('output/my-piece/piece.mid')
result = release_check('output/my-piece/piece.ogg', profile='balanced')
print(result)
if result['verdict'] != 'ready':
    raise SystemExit('Delivery needs work: inspect issues')
PY
ffprobe -v error -show_entries format=duration:stream=sample_rate,channels \
  -of json output/my-piece/piece.ogg
```

`release_check` measures and flags clipping, peak/true peak headroom, very high RMS,
and suspicious stereo correlation. Its thresholds are general; the `profile`
parameter is validated and reported but does not represent different targets by
genre. LUFS/LRA are reported; the verdict does not certify a loudness target.

Listen in stereo and mono; check balance and timbre. If the agent cannot
listen, deliver as **“structurally audited mockup; sound quality
pending human listening.”** A `ready` verdict does not justify claiming “it sounds good.”

Before sharing: retain actual gate output, metrics, licensing, and
limitations. Publish selected MIDI/OGG files and their provenance notes;
exclude stems/WAV/cache/backups. Uploading to GitHub or Reddit is an owner's action
after review; this protocol does not perform remote publication.

## Common errors and specific repairs

| Error | Diagnosis and repair |
| --- | --- |
| `plan without harmonic-instrument silence` | Declare `silent_bars >= 1` for piano/guitar/pad/strings/choir AND write at least that many full bars without notes/sustain. Silencing only the lead or bass does not count. |
| `fill_bars` outside section endings | Calculate the cumulative sum of `bars`: for 4+4+4 the only boundaries are `[4,8,12]`, not `[3,7,11]`. Include only boundaries with an actual detected fill. Move MIDI fills; do not falsify the list. |
| Detected fills ≠ plan list | Review `fill_bars` in the report. The heuristic detects >=3 tom hits or >=4 snare hits in the last beat. Correct attacks and placement; do not invent fills in the plan or apply periodic fills every 4 bars. |
| `density differs by more than 3 hits` | Compare `density_sections` with intent. This is average drum hits per bar, not total notes or guitar density. Fix the groove or correct a misexpressed target before regenerating; allowed difference <=3. |
| Planned bars ≠ MIDI | Sum sections; check markers at `bar * 4 * ticks_per_beat`, the last `note_off`, and `end_of_track`. Sustain extending beyond the end can add a bar. Align composition and plan; do not truncate notes with a hidden negative delta. |
| Density gate fails despite a wide range | There must be >=3 density levels AND contrast >=2 between sections. Two different sections can have the same hit count. Change kit orchestration musically; do not add jitter. |
| Drum overlap | Maximum two kit pieces per attack; remove duplicates, double cymbal/hi-hat, and snare+tom. Closely spaced attacks are also grouped: jitter does not hide a collision. |
| `Unknown profile` / stem mismatch | Call `list_profiles`, use exact names, or design an explicit profile with tests. Do not ignore stems. |
| `deliveries are not overwritten` | Choose another name/directory. The guard protects evidence from previous deliveries. |
| Invalid certificate / readings or code changed | Regenerate through the guard with a new destination. Retain the previous receipt as historical evidence; do not edit hashes. |
| `Silent audio` / `Empty audio` | Check MIDI notes, program, SoundFont, and subprocess. Do not normalize silence or continue with a missing stem. |
| `needs_work` after OGG encoding | Review `issues` and the final codec's TP; lower the target/gain and remaster/re-encode. For intentional mono, document the exception to the stereo check instead of claiming it passed. |
