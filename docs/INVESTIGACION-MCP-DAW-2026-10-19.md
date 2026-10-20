# MCP DAW: implementation research (2026-10-19)

Historical research snapshot. Sizes, stars, prices and local installation state
were reported in that session and are not current compatibility guarantees.
The architecture below includes proposals; see `ARCHITECTURE.md` and
`scripts/daw_mcp.py` for the implemented interface.

Research to build a DAW that the agent and the human operator can use to **adjust the quality** of generated pieces. MIDI does not capture palm mute, distortion, timbre, or mixing: that is done in the audio domain.

## 1. The real problem
The `hermesmusic.py` engine produces MIDI. FluidSynth converts it to audio with a General MIDI SoundFont. This is a **mockup renderer**: GM instrument selection does not establish realistic guitar articulation or a finished production. Separate stems permit per-role mixing and measurement, but mixing cannot guarantee recording quality or replace the source timbres.

The missing stage: **render each instrument separately (stems) → mix**.

## 2. Options evaluated (verified data)
| Option | What it is | Size | Headless | License | Verdict |
|---|---|---|---|---|---|
| **Pedalboard** (Spotify) | Audio effects + VST3 in Python | **5 MB** | ✅ yes | GPL-3 | ✅ **installed and working** |
| **dawdreamer** | Full Python DAW (JUCE): VST render, timeline | 40 MB | ✅ yes | GPL-3 | ⚪ viable, heavy |
| **REAPER** | Real DAW; mature MCPs (176/181/600+ tools) | 13.7 MB installer | ⚠️ needs GUI/X11 | Commercial ($60) | ⚪ portable install possible |
| **Ardour 8** | Free DAW in apt | 57 MB + deps | ⚠️ GUI | GPL-2 | ⚪ apt available |
| **LMMS** | Already installed | — | ✅ `lmms render` | GPL-2 | ⚪ limited |
| **ffmpeg** | Audio filters (available set depends on build) | already installed | ✅ yes | Build-dependent; see upstream notices | ✅ complement |

**Decision:** start with **Pedalboard + ffmpeg** (0 heavy installs, 100% headless, already working). REAPER stays as phase 2 if interactive editing is wanted.

## 3. Related repos found (real, verified by search)
DAW MCP servers that exist and serve as design references:
| Repo | Stars | What it does | Note |
|---|---|---|---|
| `TwelveTake-Studios/reaper-mcp` | 83 | 176 tools: mixing, mastering, MIDI, EBU measurement | Bridge Lua + JSFX; REAPER stock |
| `xDarkzx/reaper-mcp` | 100 | 181 tools: composition, mixing, mastering, QC | Apache-2.0 |
| `fadelabs/phantom` | 39 | **MCP + audio engineering skills, headless with Pedalboard** | ⭐ **closest to what we want** |
| `HighVoltSound/ableton-auto-mix-mcp` | 1 | Auto-mix/master by genre, 11 style profiles | JSON style profiles |
| `rosasynthesiz/flstudio-mcp` | 94 | 67 tools, "Mix Doctor", FL Studio | Win/macOS only |
| `guvense/hellyee` | 6 | Ableton via OSC, measures and adjusts in a loop | Closes the measure-adjust loop |
| `Cybolic/LinReaper` | — | REAPER installer for Linux (Wine) | Old alternative |

**Common pattern of the good ones:** measure → decide → apply → **measure again**. No guessing. `phantom` and `hellyee` state it explicitly.

## 4. What is already implemented and verified (2026-10-19)
### `scripts/mix_engine.py`
Headless mixing engine with Pedalboard. It actually works:
- Loads WAV stems per role (drums, bass, rhythm_guitar_L/R, lead_guitar_L/R)
- **Per-role chain:** HPF (reduces low-frequency competition), presence EQ, compression
- **Linear stereo balance** applied to audio; no mid/side processing
- **Bus master:** HPF + low-mid mud cut (300 Hz) + air (8 kHz) + bus compression + trim + sample limiter at -1 dBFS; true peak must be measured separately
- **Genre profiles** (`power_metal`, `balanced`) with starting values
- Returns metrics: peak, RMS, stems used/ignored

### Verified with the real piece "Iron Determination v3"
```
6 WAV stems rendered (one per instrument) from the MIDI
mix_engine.py --profile power_metal
  → peak_db: -1.97 (no clipping)
  → rms_db:  -19.3
  → 180.5 s
Final OGG: iron_determination_v3_MEZCLADO.ogg
  → peak -0.61 dB, RMS -15.2 dB, 180.000 s, 44.1 kHz
```

### Technical finding
Correction to the original diagnosis: the floating-point sum may exceed 0 dBFS
without clipping at that stage. The bus applies -3 dB gain before its sample
limiter for headroom. This is not a true-peak guarantee. Measure the written
audio and final codec rather than inferring saturation from the internal sum.

## 5. Proposed MCP DAW architecture
### Phase 1 — Headless mixing (already implementable)

Historical interface sketch, not executable signatures. The current tool is
`analyze_audio`, not `analyze_stem`; `render_stems` takes `midi_path`/`out_dir`,
and `auto_mix` takes `stems_dir`/`out`. Use the current Python signatures or MCP schema.

```
hermes-daw-mcp (FastMCP, stdio)
├── list_profiles()              → available mixing profiles
├── render_stems(midi, outdir)   → splits the MIDI into WAV per instrument
├── analyze_stem(wav)            → peak, RMS, spectrum, stereo correlation
├── analyze_masking(dir)         → which stem pairs mask each other (band overlap)
├── auto_mix(dir, profile)       → applies the profile chain, returns metrics
├── apply_eq(wav, band, gain)    → EQ on a stem
├── apply_comp(wav, ...)         → individual compression
├── master(wav, target_lufs)     → mastering chain with loudness target
├── compare_to_reference(a, b)   → compares against a reference
└── release_check(wav, profile)  → ready/not-ready verdict (LUFS/TP/LRA)
```

Each tool: **measure before → apply → measure after → report the difference**. Never "sounds better" without numeric evidence.

### Phase 2 — Interactive editing (if wanted)
REAPER **portable install** (13.7 MB, runs without installing): allows the operator to edit on the same project the agent mixes. Requires X11 (`DISPLAY=:0` already exists). Would connect with a `reaper-mcp`-type bridge.

### Phase 3 — Perceptual measurement
Proposed `librosa` features (MFCC, spectral centroid, tempo, tonality) for comparison
against power-metal references. Not implemented here; such measurements would
not remove the need for human listening.

## 6. Historical local constraints (not package requirements)
- **Disk at 93%** (8.2 GB free on `/dev/sda6`). A DAW with samples is heavy; the 3-minute stems WAV already occupy 30 MB each. There is a 298 GB external disk and an external disk for heavy material.
- **CPU i3-6006U, no GPU, 16 GB RAM.** Rendering is sequential; it works but is slow (the stems render took ~2 min).
- **No JACK/ALSA for study.** Mixing is offline (files), not real-time. That is an advantage: no sound card needed.

## 7. What the MCP cannot do (honesty)
- **It cannot judge whether it sounds good.** It measures (LUFS, peak, spectrum, correlation) and applies known chains. The aesthetic decision is human.
- **It does not invent timbres.** With GM, a guitar sounds like GM guitar. To sound like real metal, quality samples/VSTs are needed (phase 2+).
- **It does not replace an engineer.** It is an assistant that leaves the mix at a measurable, consistent starting point.

## 8. Next steps proposed at the time

The ten MCP tools, octave-band heuristic and an automated full-loop test now
exist. These bullets record the original proposal, not current missing features.

1. Build the FastMCP with the 10 phase-1 tools.
2. Add real spectral analysis (numpy FFT or librosa) for the masking detector.
3. Test the full loop: MIDI → stems → auto_mix → master → release_check.
4. Evaluate REAPER portable if the operator wants manual editing.
5. Document the flow in the `hermes-music` skill with the corresponding guardrail.
