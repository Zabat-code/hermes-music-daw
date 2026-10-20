# Hermes Music + DAW

Python MIDI composition with executable arrangement checks, plus a headless
MCP server for offline mixing and mastering. CPU only; no DAW window, audio
interface, GPU, model download or cloud account required.

**Español:** [README.es.md](README.es.md)

**Start here:** [agent protocol](PROTOCOL.md) · [architecture](docs/ARCHITECTURE.md) ·
[documentation index](docs/README.md) · [contributing](CONTRIBUTING.md).

This is an early open source toolkit. The composition checks have regression
coverage; the DAW is a hardened prototype, with tests for all ten tools and a
real stdio MCP session. Neither component decides whether music sounds good.

| Component | What you get |
| --- | --- |
| `hermes-music` | MIDI composition, eight arrangement gates and SHA-256 delivery receipts |
| `hermes-daw` | Ten MCP tools for rendering stems, measuring audio, mixing and mastering offline |

The guard exists because written corrections failed to prevent the same defects
in the next composition. It checks a defined structural contract before delivery;
it cannot certify timbre, genre fidelity or listening quality.

## Quick start: install, test, try

From a downloaded or cloned checkout, on Linux with Python 3.12:

```bash
cd hermes-music-daw
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
sudo apt install fluidsynth fluid-soundfont-gm ffmpeg
python scripts/check_install.py
python -m pytest tests/ -q
python examples/01_compose.py --work output/demo
python examples/02_audit.py --work output/demo
python examples/03_mix_and_master.py --work output/demo
```

The example produces an audited MIDI, six WAV stems, a mix, a master, an OGG
and JSON measurements. Use a fresh output directory for each run. FluidSynth,
FFmpeg and a SoundFont are needed for audio and the full integration tests;
the MIDI gates do not require an audio device. See below for configuration and limits.

## Why the guard exists

The same bad arrangement happened twice: mechanical drums, overlapping attacks,
flat dynamics, crowded instruments and GM guitars that sounded like an 8-bit
mockup. The correction was already written in Markdown. It did not change the
next composition.

The response was executable: **read → decide → compose → audit → publish**.
Eight arrangement gates abort a defective delivery with exit code 1. An external
audit then found faults in the author's own v2; those were corrected too.
The lesson is the reason for this repository: documentation needs enforcement
at the point where an artifact is delivered.

The guard records the exact MIDI's SHA-256, the plan, required readings and guard
code. Editing the MIDI invalidates its receipt. This is an integrity record,
**not a digital signature, aesthetic certificate or security sandbox**. Arbitrary
code can bypass it; an agent must use the prescribed entry point.

## Install

Tested with Python 3.12.3 on Linux. The main dependency versions are pinned in
[requirements.txt](requirements.txt): Mido 1.3.3, NumPy 2.5.3, Pedalboard 0.9.26,
FastMCP 4.1.1. The list does not lock transitive dependencies.

`pip install -e .` installs the runtime package without the pytest extra. The
import namespace is `hermes_music.scripts`; console commands include
`hermes-music`, `hermes-daw`, `hermes-mix`, `hermes-music-audit`,
`hermes-music-guard` and `hermes-music-check`. Direct script execution also works.

SoundFont discovery checks `MIDI_SOUNDFONT` first, then common system locations,
including FluidR3_GM and TimGM6mb. An explicitly invalid override is an error.
Executables are discovered on `PATH`; `FLUIDSYNTH`, `FFMPEG` and `FFPROBE` can
override them. No user-specific paths are required.

```bash
export MIDI_SOUNDFONT=/path/to/your/font.sf2  # optional when auto-detected
```

Offline FluidSynth subprocesses default `SDL_AUDIODRIVER` to `dummy` to avoid
audio-device enumeration hangs in containers. This does not affect file synthesis.
Other platforms and dependency combinations have not been verified here.

## Run the small example

These scripts use the actual guard and audio engines, not placeholder media.
Run them in order from the checkout, using a fresh output directory on each run:

```bash
python examples/01_compose.py --work output/demo
python examples/02_audit.py --work output/demo
python examples/03_mix_and_master.py --work output/demo
```

The result is a 12-bar, 18-second MIDI with three contrasting sections, six
stems, a mix, a master, an OGG export and JSON measurements. The audio retains
FluidSynth's release tail. The full required readings and guard output are in
`output/demo/composition.log`. Existing guard deliveries are never overwritten.

Listen to [sample.ogg](examples/sample.ogg), inspect [sample.mid](examples/sample.mid),
and see [sample provenance](examples/README.md). These are GM structural demos;
listening quality has not been certified. Actual run output and verification
details are recorded in `docs/`.

For your own dense arrangement, write and review a decision plan first, then
run your composer through the guard. The reference is a full 120-bar example:

```bash
python scripts/example_dense_arrangement.py --plan plan.json
# Review/adapt the plan AND composer before creating a new piece.
python scripts/composition_guard.py plan.json --out piece.mid -- \
  scripts/example_dense_arrangement.py --out '{draft}'
python scripts/audit_arrangement.py piece.mid --json review.json
python scripts/composition_guard.py --verify piece.mid
```

Follow [PROTOCOL.md](PROTOCOL.md) for rendering, mixing, mastering and publication.
Low-level `hermes-music recipes`, `compose`, `gen`, `validate`, `render` and
`rebuild` remain available. `validate` alone does not approve an arrangement.
Genre plans from `genre_engine.py` are harmonic guides, not finished songs.

## Architecture and file map

```text
readings + decision plan + composer
                  ↓ composition_guard (subprocess, temporary MIDI)
               audit_arrangement: 8 gates
                  ↓ exact MIDI + SHA-256 receipt
           FluidSynth / SoundFont → instrument WAV stems
                  ↓ mix_engine: role chains + stereo balance + bus
              daw_mcp.master: bus chain + FFmpeg loudnorm
                  ↓ WAV → OGG → release_check → human listening
```

| File | Purpose |
| --- | --- |
| `PROTOCOL.md` | Ordered agent workflow, failures and repairs |
| `scripts/hermesmusic.py` | MIDI events, patterns, SongSpec, validation, rendering and CLI |
| `scripts/audit_arrangement.py` | Eight fail-fast arrangement gates |
| `scripts/composition_guard.py` | Required readings, plan contract and hash receipt |
| `scripts/example_dense_arrangement.py` | Note-by-note reference composition |
| `scripts/genre_engine.py` | Experimental harmonic-form planner |
| `scripts/mix_engine.py` | Role/profile DSP chains, stereo balance, duration handling |
| `scripts/daw_mcp.py` | Ten MCP tools; same functions are usable from Python |
| `scripts/audio_utils.py` | Audio validation, discovery, FFmpeg measurements and subprocess errors |
| `scripts/check_install.py` | Dependency, binary, SoundFont and resource smoke check |
| `references/` | Genre data, theory, rendering and SongSpec examples |
| `examples/` | Three executable stages and a small MIDI/OGG sample |
| `tests/` | Composition regressions, DSP checks and real MCP calls |
| `docs/` | Current guides and dated historical evidence |
| `SKILL.md` | Detailed composition workflow and MIDI API; the historical integration guide is not bundled |
| `templates/songspec.json` | Low-level SongSpec schema example |

The legacy dembow, harmonic-circle and MIDI-effect scripts remain in `scripts/`
as experimental standalone utilities with known implementation defects; see the
[MIDI-effect reference](references/effects_mapper.md). They do not issue guard
receipts and are outside the tested composition/audio workflow. `build_index.py` is
a Hermes-specific adapter requiring a separate skills-index plugin.

## MCP tools and clients

Start with `list_profiles`, then follow the protocol. Audio paths are local to
the machine running the server. WAV is the processing format; `analyze_audio`
and `release_check` can also inspect an OGG supported by the installed decoder.

| Tool | Use / result |
| --- | --- |
| `list_profiles` | Supported roles and complete DSP settings |
| `render_stems` | MIDI → named WAVs; audit first; requires FluidSynth and SoundFont |
| `analyze_audio` | Sample peak, RMS, octave energy and stereo correlation |
| `analyze_masking` | Heuristic ranking of spectral overlap between stems |
| `auto_mix` | Role processing, stereo balance and bus chain; output metrics |
| `apply_eq` | Targeted EQ; before/after metrics |
| `apply_comp` | Targeted compression; before/after metrics |
| `master` | Profile chain + two-pass FFmpeg loudnorm; measured LUFS/TP and target status |
| `compare_to_reference` | Candidate-minus-reference level and band deltas |
| `release_check` | Measured loudness/true peak/LRA, issues and ready/needs_work |

The MCP exposes the audio stage. Composition and guard verification run through
the CLI. MCP render tools can process arbitrary MIDI; they do not implicitly
certify it. Bad paths, corrupt/empty/silent audio and unknown profiles return
clear tool errors. All processing occurs in memory; long stems use more RAM.

After installation, this configuration launches the package from any working
directory. Replace the interpreter path with the absolute path of your venv's
Python. Optional `env` settings must be valid on the server host.

```json
{
  "mcpServers": {
    "hermes-daw": {
      "command": "/absolute/path/to/hermes-music-daw/.venv/bin/python",
      "args": ["-m", "hermes_music.scripts.daw_mcp"],
      "env": {"MIDI_SOUNDFONT": "/usr/share/sounds/sf2/FluidR3_GM.sf2"}
    }
  }
}
```

- **Claude Desktop:** Settings → Developer → Edit Config; merge the entry into
  `claude_desktop_config.json`, then restart. See the
  [official local-server guide](https://modelcontextprotocol.io/docs/develop/connect-local-servers).
- **Cursor:** merge the JSON into project `.cursor/mcp.json` or personal
  `~/.cursor/mcp.json`, then restart. See [Cursor's instructions](https://prod.cursor.com/help/customization/mcp).
- **Hermes:** add the following under `mcp_servers` in `~/.hermes/config.yaml`
  and restart Hermes. See [Hermes MCP documentation](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md).

```yaml
mcp_servers:
  hermes-daw:
    command: /absolute/path/to/hermes-music-daw/.venv/bin/python
    args: ["-m", "hermes_music.scripts.daw_mcp"]
    env:
      MIDI_SOUNDFONT: /usr/share/sounds/sf2/FluidR3_GM.sf2
```

Configuration formats were checked against those upstream guides. GUI client
connections were not exercised; the automated test performs handshake,
`tools/list` and calls all ten tools over real stdio MCP. The server needs no
HTTP port or authentication setup. It runs with the host user's file permissions.

In a restricted Linux sandbox that denies `socketpair.send()`, set
`HERMES_DAW_STDIO_POLL=1` in the server's `env`. This enables a 50 ms event-loop
timer so thread-based stdio can wake correctly. The local protocol test uses
this compatibility mode for both server and client; normal desktop use does
not require it.

## Mix profiles

`power_metal` and `balanced` are engineering starting points. Stems must use
exact role names; an unknown name aborts instead of silently losing an instrument.
A subset of roles is allowed. Both profiles now include the reference's
`lead_guitar` and `synth_piano`, alongside the original L/R lead roles.

| Setting | power_metal | balanced |
| --- | --- | --- |
| Drums HPF / compression | 35 Hz / -12 dB, 3:1 | 30 Hz / -14 dB, 2.5:1 |
| Bass HPF / low shelf | 40 Hz / +3 dB at 120 Hz | 38 Hz / +2 dB at 100 Hz |
| Rhythm HPF / presence / L-R balance | 90 Hz / +2.5 dB at 2.4 kHz / ±0.55 | 80 Hz / +1.5 dB at 2 kHz / ±0.50 |
| Lead HPF / presence / L-R balance | 200 Hz / +3 dB at 3.2 kHz / ±0.30 | 180 Hz / +2 dB at 2.8 kHz / ±0.25 |
| Piano HPF / level | 180 Hz / 0.45 | 150 Hz / 0.48 |
| Bus HPF / mud / air | 28 Hz / -1.5 dB at 300 Hz / +1.5 dB at 8 kHz | 25 Hz / -1 dB at 250 Hz / +1 dB at 9 kHz |
| Bus trim / sample limiter | -3 dB / -1 dBFS | -3 dB / -1 dBFS |

HPFs reduce low-frequency competition, shelves shape tonal balance, compression
controls dynamics and balance separates doubled parts. These choices require
listening. [Full parameters and interpretation](docs/MIX_PROFILES.md).

## Honest limits

- **GM is a mockup renderer.** It does not reproduce realistic distorted guitars,
  palm mute, playing technique, convincing vocals or studio production.
- **The auditor checks a structural contract, not taste or genre fidelity.**
  Its dense contract supports 4/4. It intentionally rejects some musically valid
  choices; other styles need separately designed and tested contracts.
- **73 genre profiles are provisional and unaudited by listening.** The catalogue
  has 100 labels and 104 variants, with 22 direct-source and 5 family-source
  profiles. There are only 15 distinct legacy drum grids. The harmonic planner
  does not generate a genre's full instrumentation.
- **Masking is heuristic.** Correlated octave energies do not prove that a part
  is inaudible. RMS is not LUFS; sample peak is not true peak. True peak and LUFS
  are measured separately using FFmpeg.
- **A release verdict is a limited technical screen.** It cannot find every
  audible defect, certify dynamics from a single threshold or replace listening.
  Mastering targets may be constrained; inspect `target_met` and the final codec.
- **Stem rendering expects one named instrument channel per note track.**
  Split multichannel type-0 tracks first. Shared controllers/programs across
  tracks are not reconstructed; keep each instrument's controls in its own track.
- **Receipts currently depend on absolute paths and exact code/readings.**
  Re-run the guard after moving a checkout or changing its bound files. Hashes
  are integrity evidence, not protection against a malicious writer.
- No perceptual reference matching, automated aesthetic judgment, neural audio
  generation, real-time DAW session or validated performance benchmark is claimed.

## Tests and license

```bash
python -m pytest tests/ -q
```

Tests generate audio and regression MIDI locally. Audio integration tests need
the system dependencies above; CI installs them on Python 3.12. The original
33 composition tests and 100 catalogue subtests are retained; private desktop
fixtures were replaced with reproducible defect-class fixtures.

Original source: [MIT](LICENSE). **Pedalboard is GPL-3.0** and FluidR3 has its own
upstream license. Neither is relicensed by this project's MIT notice; see
[third-party notices](THIRD_PARTY_NOTICES.md). The SoundFont is not bundled.
