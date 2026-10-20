# Research: actual power metal characteristics (2026-10-19)

Compiled for v3 of "Iron Determination." These are historical arrangement choices
and research notes, not universal genre rules. The original web searches were
not preserved as precise citations; the source list below does not independently
establish every trait or tempo claim. The v3 artifacts are not bundled here.

## Tempo and meter
- Working tempo range for this arrangement: **160–200 BPM**; the cited DragonForce
  recording was a listening reference, not a measured tempo source in this repository.
- Selected meter: 4/4. Compound meters such as 6/8 or 12/8 are separate choices;
  they do not define the eighth-plus-two-sixteenths gallop below.
- **Applied in v3:** 185 BPM, 4/4, 140 bars → 181.6 s.

## Drums — the genre's signature
- **Sixteenth-note double kick** was selected as a rhythmic foundation for v3;
  it is not a requirement for every power metal arrangement.
- Snare on **2 and 4** (backbeat) over the double kick.
- Crash at section starts; ride or hi-hat on eighth notes.
- Fills exist but are **transitions**, not a fixed cycle: they mark section changes.
- **Contract violation measured in v1:** kick + hi-hat + crash at the same instant.
  The auditor rejects this as "3+ pieces" under its local clarity contract;
  MIDI simultaneity does not prove acoustic masking or perceptual inseparability.
- **Applied in v3:** sixteenth-note double kick with quarter-note accents, variation by phrase (gap in verse bar 3, syncopation in chorus bar 4) so no pattern dominates; maximum 2 kit pieces per instant.

## Guitars — the riff
- **Gallop riff:** an eighth note followed by two sixteenth notes ("ta-ka-ka" pattern).
  This figure uses straight subdivision, not triplets. Triplet figures are a
  different rhythmic choice and are not prohibited across the genre.
- **Palm mute** (damping with the palm) on low notes; produces the percussive "chug."
- **Pedal tone:** a low note is held or repeated while the surrounding harmony changes.
- **Power chords** (root + 5th, sometimes + octave) were selected as the foundation;
  this does not prohibit full triads in metal rhythm parts.
- **Twin guitars:** v3 uses **diatonic thirds**. A fixed chromatic transposition
  can leave the selected scale; other harmonizations are also valid.
- **Applied in v3:** 2 rhythm guitars L/R (fifths + pedal tone + gallop, panned 22/105) and 2 leads harmonized in diatonic thirds (panned 40/88).

## Harmony and tonality
- Natural minor with a **raised 7th (harmonic minor)** = the "neoclassical" color (Malmsteen/Yngwie influence). Used as an **event** during the solo, not throughout.
- Selected progression: **♭VI–♭VII–i** (in A minor: F–G–Am). No frequency ranking
  of this gesture across the genre was measured here.
- **Slow harmonic rhythm in the chorus:** v3 holds each chord for 2 bars to
  contrast with the rhythmic activity. One chord per bar is also a valid choice.
- **Final chorus:** an upward modulation was chosen for the climax; it is optional.
- **Applied in v3:** Am with F–G–Am; chorus with 1 chord per 2 bars; final chorus modulated Am→Bm; harmonic-minor solo.

## Structure (power metal single)
intro → verse → pre-chorus → **chorus** → verse2 → pre-chorus2 → **chorus2** → bridge → **solo** → **final chorus (modulated)** → outro.
- In this design, the solo follows the bridge.
- The chorus repeats **3 times**, with the last one transposed upward; this is
  the v3 form, not a mandatory genre structure.
- **Applied in v3:** 11 sections, 140 bars, chorus x3 with the third in B minor.

## Bass
- In **eighth notes**, linked to the drums; rises an octave in the chorus to "open up" the sound.
- Ascending fills (root–2nd–3rd–5th) at section transitions.
- **Applied in v3:** eighth notes, octave up in the chorus, 4-note fills at boundaries.

## Cited listening references
- **DragonForce** — extreme tempo (~200 BPM), neoclassical solos harmonized in thirds, continuous double kick.
- **Metallica** — user-requested reference for palm-muted riffs and pedal tone;
  this note does not establish a historical origin for the gallop figure.

## What GM cannot guarantee
- The General MIDI SoundFont does **not** reproduce palm mute, actual distortion, or metal guitar timbre. It sounds like a "mockup," not a production.
- Sound quality requires human listening; the auditor only certifies **structure**.
- The auditor states this explicitly: "it does not prove timbre, acoustic masking, palm mute, correct harmony, or musical quality."

## Sources
- Web searches on genre characteristics, tempo, double kick, and structure (findings consolidated in this session; cited traits, no invented URLs).
- `references/genre_configs.json` (profile `power_metal`: tempo 120–160, 4/4, density 12;
  metadata that the renderer does not enforce, and a different range from the v3 design).
- `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md` (mechanical drum diagnosis, CC0 reference by nene).
- `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md` (Boddington/Jordan/Herbst on metal harmony; Garza on riff types).
