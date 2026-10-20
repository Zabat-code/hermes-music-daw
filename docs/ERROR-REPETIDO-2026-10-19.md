# REPEATED ERROR: dense composition without consulting audited documentation

**Date:** 2026-10-19
**Tool:** `hermes-music` skill (`hermesmusic.py` engine)
**Severity:** high — the error occurred **twice**, and the correction was documented but not applied.

---

## What happened (facts, not interpretation)

The user requested a power metal workout song (3:00, 2 guitars, bass, drums, synth piano).
I generated v1 with `render_song()` + `drum_grid`. The user rejected it after listening, with five complaints.
All were correct, and **all had already been diagnosed** in `~/.hermes/documentacion/hermesmusic/`
earlier that day (previous work on the piece "Ash to Dawn").

### Occurrence 1 — "Ash to Dawn" (earlier the same day)

- Piece generated with the same approach (`render_song` + drum grid).
- Diagnosis documented in `COMPARATIVA-BATERIA-METAL-2026-10-19.md`:
  - 68 dense bars with **exactly 8 kick and 8 ride hits per bar**, both triggered together.
  - Most repeated pattern: 45 of 78 bars. No gaps or syncopation.
  - Identical fills every 4 bars, without responding to cadences.
- Correction proposed in the same document (4 points) — **NOT applied to the engine**.
- A v2 of that piece (`ash_to_dawn_drums_v2.py`) was created with handwritten grooves,
  but **as a standalone project file, not as an engine or skill rule**.

### Occurrence 2 — "Iron Determination" (this session)

- I generated v1 with the same `render_song` + `drum_grid` → **repeated the same defects**.
- The user detected it again by listening.

## Why it recurred (root cause)

1. **The correction lives in an unread `.md`.** `COMPARATIVA-BATERIA-METAL-2026-10-19.md`
   and `HALLAZGOS.md` contain the diagnosis, but **nothing in the
   workflow requires opening them** before composing.
2. **The `hermes-music` skill does not mention those documents.** Its `SKILL.md` and `references/`
   do not link to `documentacion/hermesmusic/`, so an agent loading the skill never sees them.
3. **The engine did not change.** `drum_grid` still produces a mechanical grid; `render_song` still
   has no rules for register, space between instruments, or dynamic variation.
4. **"Success" was declared using metrics that do not detect the problem.** `validate_midi` finds
   no orphan notes or incorrect duration → "no problems." The classifier said "metal." None of that
   measures whether drums overlap, whether there is space, or whether the timbre sounds 8-bit.
5. **Occurrence 1's v2 was not generalized.** It was a patch for one piece, not a reusable
   rule; the next piece started from scratch with the defective pattern.

## Measured defects (Iron Determination v1, 120 bars)

| Audible symptom (user) | Objective measurement | Cause in code |
|---|---|---|
| “the drums overlap” | 960 ticks with 2–3 simultaneous hits | `drum_grid` emits kick+hihat+crash in the same step |
| “the intensity is inappropriate” | **Identical** 27.0 notes/bar across all 120 bars; only 2 velocities (90/110) | flat `sdyn` per section, no variation by function |
| “the guitars do not come through” | rhythm guitar with `arpeggio_up` | arpeggios instead of power chords |
| “a piercing sound that does not fit” | `lead_guitar` reached MIDI 102 | no register cap |
| “it sounds more like 8-bit music than metal” | 5 instruments playing 100% of the time | no space / silence rules |

## What the validation pipeline did NOT detect

- `validate_midi` → "no problems" (only checks orphan notes and duration).
- `classify_genre` → "metal" (checks onsets and tempo, not overlap or space).
- `ffprobe`/`astats` → correct duration and peak.
- **None of these checks measures the five actual defects.** The entire pipeline reported "ready."

## Correction applied in this session

- v2 **written note by note** (`compose_gym_power_metal_v2.py`), grooves by section function,
  separate velocities per kit piece, fills only at boundaries, double-tracked panned power chords,
  piano silent during verses and the solo, lead limited to 76–88.
- Rules added to `references/teoria-composicion.md` (section "Arrangement: Making Space").
- **Pending:** make those rules a **mandatory guardrail** within the skill,
  rather than another paragraph an agent might skip.
