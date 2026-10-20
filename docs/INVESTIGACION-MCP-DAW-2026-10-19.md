# MCP DAW: implementation research (2026-10-19)

Research to build a DAW that the agent and the human operator can use to **adjust the quality** of generated pieces. MIDI does not capture palm mute, distortion, timbre, or mixing: that is done in the audio domain.

## 1. The real problem
The `hermesmusic.py` engine produces MIDI. FluidSynth converts it to audio with a General MIDI SoundFont. It sounds like a **mockup**, not a production: GM has no real distorted guitar, no stem-panned mix, no EQ, no compression, no mastering. The pieces "sound better" but will never sound like a record without a **mixing and mastering stage over separate stems**.

The missing stage: **render each instrument separately (stems) → mix**.

## 2. Options evaluated (verified data)
| Option | What it is | Size | Headless | License | Verdict |
|---|---|---|---|---|---|
| **Pedalboard** (Spotify) | Audio effects + VST3 in Python | **5 MB** | ✅ yes | GPL-3 (free use) | ✅ **installed and working** |
| **dawdreamer** | Full Python DAW (JUCE): VST render, timeline | 40 MB | ✅ yes | GPL-3 | ⚪ viable, heavy |
| **REAPER** | Real DAW; mature MCPs (176/181/600+ tools) | 13.7 MB installer | ⚠️ needs GUI/X11 | Commercial ($60) | ⚪ portable install possible |
| **Ardour 8** | Free DAW in apt | 57 MB + deps | ⚠️ GUI | GPL-2 | ⚪ apt available |
| **LMMS** | Already installed | — | ✅ `lmms render` | GPL-2 | ⚪ limited |
| **ffmpeg** | 160 audio filters | already installed | ✅ yes | LGPL | ✅ complement |

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
### `the skill's scripts/mix_engine.py`
Headless mixing engine with Pedalboard. It actually works:
- Loads WAV stems per role (drums, bass, rhythm_guitar_L/R, lead_guitar_L/R)
- **Per-role chain:** HPF (avoids masking), presence EQ, compression
- **Real mid/side panned** (not just a number in the MIDI)
- **Bus master:** HPF + low-mid mud cut (300 Hz) + air (8 kHz) + bus compression + trim + limiter to -1 dBTP
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
The sum of 6 stems saturates at **0 dB (clipping)** if it is not trimmed before the limiter. A `Gain(trim=-3 dB)` was added in the bus master. Without that trim, the limiter cannot avoid clipping because it enters already saturated.

## 5. Proposed MCP DAW architecture
### Phase 1 — Headless mixing (already implementable)
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
`librosa` for features (MFCC, spectral centroid, tempo, tonality) and comparison against power-metal references. Closes the loop without human ears.

## 6. Real team constraints
- **Disk at 93%** (8.2 GB free on `/dev/sda6`). A DAW with samples is heavy; the 3-minute stems WAV already occupy 30 MB each. There is a 298 GB external disk and an external disk for heavy material.
- **CPU i3-6006U, no GPU, 16 GB RAM.** Rendering is sequential; it works but is slow (the stems render took ~2 min).
- **No JACK/ALSA for study.** Mixing is offline (files), not real-time. That is an advantage: no sound card needed.

## 7. What the MCP cannot do (honesty)
- **It cannot judge whether it sounds good.** It measures (LUFS, peak, spectrum, correlation) and applies known chains. The aesthetic decision is human.
- **It does not invent timbres.** With GM, a guitar sounds like GM guitar. To sound like real metal, quality samples/VSTs are needed (phase 2+).
- **It does not replace an engineer.** It is an assistant that leaves the mix at a measurable, consistent starting point.

## 8. Concrete next steps
1. Build the FastMCP with the 10 phase-1 tools.
2. Add real spectral analysis (numpy FFT or librosa) for the masking detector.
3. Test the full loop: MIDI → stems → auto_mix → master → release_check.
4. Evaluate REAPER portable if the operator wants manual editing.
5. Document the flow in the `hermes-music` skill with the corresponding guardrail.
