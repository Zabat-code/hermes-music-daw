# Hermes Music + DAW — A MIDI composer that refuses to ship a bad arrangement

Python MIDI composition with **executable arrangement checks**, plus a headless
MCP server for offline mixing and mastering. CPU only.

**English:** [README.md](../README.md) · **Español:** [README.es.md](../README.es.md)

---

## What it is

A Python toolkit that composes MIDI by genre and **refuses to deliver a defective
arrangement**. It also renders audio stems and mixes/masters them offline
through an MCP server.

```
MIDI ──▶ 8 arrangement gates ──▶ certified MIDI ──▶ stems ──▶ mix ──▶ master ──▶ OGG
              (exit 1 if bad)     (SHA-256 receipt)
```

## Why the guard exists

The same bad arrangement happened **twice**: mechanical drums with overlapping
attacks, flat dynamics, crowded instruments, and General MIDI guitars that sounded
like an 8-bit mockup.

The correction was already written in Markdown. **It did not change the next
composition.**

So the response was executable: `read → decide → compose → audit → publish`.
Eight arrangement gates abort a defective delivery with exit code 1. An external
audit later found faults in the author's own v2 — those were corrected too.

**The lesson is the reason for this repository:** documentation needs enforcement
at the point where an artifact is delivered.

The guard records the exact MIDI's SHA-256, the plan, the required readings and the
guard code. Editing the MIDI invalidates its receipt. It is an integrity record,
**not a digital signature, aesthetic certificate or security sandbox**.

## What is inside

### The 8 arrangement gates

| Gate | What it verifies |
|---|---|
| `structure` | Notes closed and positive duration |
| `dynamics` | At least 5 velocities and range of 10 |
| `register` | MIDI ranges per role within the contract |
| `space` | At least one harmonic instrument silent for a full measure |
| `overlap` | At most two drum-kit pieces per attack |
| `patterns` | At least 3 patterns; none dominates over 50 % |
| `density` | At least 3 density levels and contrast between sections |
| `fills` | Fills only at section boundaries, not periodic |

### The 10 MCP tools

`list_profiles` · `render_stems` · `analyze_audio` · `analyze_masking` · `auto_mix` ·
`apply_eq` · `apply_comp` · `master` · `compare_to_reference` · `release_check`

All offline. No DAW window, no audio interface, no GPU.

### Try it in three commands

```bash
python -m pip install -e '.[dev]'
python scripts/check_install.py          # 12 dependencies and paths checked
python examples/01_compose.py --work output/demo   # composes and certifies
python examples/03_mix_and_master.py --work output/demo   # stems → mix → master
```

74 tests + 100 subtests pass. CI runs on Python 3.12.

## What makes it different

Most MIDI generators ship a file and hope. This one **measures before it decides,
applies a known chain, and measures again**. The audit is executable and aborts.

That loop — measure → apply → measure — is the same pattern as the mature DAW MCPs
(`reaper-mcp`, `phantom`), but implemented for the arrangement itself.

## What it does NOT do (honest limits)

1. **General MIDI does not reproduce real timbre** — no palm mute, no real distortion.
   It sounds like a mockup, not a production master.
2. **The auditor certifies structure, not musical taste.** A `ready` verdict does not
   mean it sounds good.
3. **Mix profiles are starting values**, not absolute truth.
4. **73 of the genre profiles are `provisional`** — not validated by listening.
5. **Masking analysis is heuristic**: it points where to investigate, it does not
   prove inaudibility.
6. **No perceptual evaluation or human listening** has been run. Verification is
   structural and technical.

## Layout

```
scripts/     composition engine, guard, auditor, MCP server, mix engine
tests/       74 tests + 100 subtests
examples/    3 runnable scripts + a sample MIDI/OGG
references/  100 genres, theory, rendering, effects
docs/        architecture, protocol, research, validation
PROTOCOL.md  the mandatory walkthrough for agents
```

## Contribute

See [CONTRIBUTING.md](../CONTRIBUTING.md). Run `python scripts/check_install.py`
first and `python -m pytest tests/ -q` before opening a pull request.

The biggest open work is splitting the monolithic engine (`hermesmusic.py`, 1,151
lines) into modules — a good first issue.
