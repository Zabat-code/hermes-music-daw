# Research: actual power metal characteristics (2026-10-19)

Compiled for v3 of "Iron Determination." Goal: stop guessing the genre and use documented traits as a foundation. Sources are cited at the end of each block.

## Tempo and meter
- Typical range **160–200 BPM**; the extreme (DragonForce, "Through the Fire and Flames") reaches **~200 BPM**, with eighth notes at 400. European power metal typically falls within 160–190.
- Almost always 4/4; some passages use 6/8 or 12/8 for a "galloping" feel.
- **Applied in v3:** 185 BPM, 4/4, 140 bars → 181.6 s.

## Drums — the genre's signature
- **Continuous double kick in sixteenth notes** as a rhythmic foundation. It is *the* most identifiable characteristic of power metal.
- Snare on **2 and 4** (backbeat) over the double kick.
- Crash at section starts; ride or hi-hat on eighth notes.
- Fills exist but are **transitions**, not a fixed cycle: they mark section changes.
- **Error to avoid (measured in v1):** kick + hi-hat + crash at the same instant. The ear cannot separate the three, and it sounds like noise; the auditor flags it as "3+ pieces" (masking).
- **Applied in v3:** sixteenth-note double kick with quarter-note accents, variation by phrase (gap in verse bar 3, syncopation in chorus bar 4) so no pattern dominates; maximum 2 kit pieces per instant.

## Guitars — the riff
- **Gallop riff:** an eighth note followed by two sixteenth notes ("ta-ka-ka" pattern). **NOT triplets:** triplets produce a shuffle feel and undermine the genre.
- **Palm mute** (damping with the palm) on low notes; produces the percussive "chug."
- **Pedal tone:** the guitar holds a low note while the harmony changes underneath.
- **Power chords** (root + 5th, sometimes + octave) as the foundation; metal does not use complete triads in the rhythm part (the lead carries the 3rd).
- **Twin guitars** (two guitars): the canonical harmony is in **diatonic thirds**, not blindly parallel thirds (which produce out-of-scale errors).
- **Applied in v3:** 2 rhythm guitars L/R (fifths + pedal tone + gallop, panned 22/105) and 2 leads harmonized in diatonic thirds (panned 40/88).

## Harmony and tonality
- Natural minor with a **raised 7th (harmonic minor)** = the "neoclassical" color (Malmsteen/Yngwie influence). Used as an **event** during the solo, not throughout.
- Emblematic progression: **♭VI–♭VII–i** (in A minor: F–G–Am). This "ascending" cadence is the genre's most frequently used gesture.
- **Slow harmonic rhythm in the chorus:** a chord held for 2 bars. Energy comes from rhythm and vocals, not harmonic change. A chorus that changes chords every bar sounds like pop, not power metal.
- **The final chorus rises** a tone or semitone (modulation) = culmination.
- **Applied in v3:** Am with F–G–Am; chorus with 1 chord per 2 bars; final chorus modulated Am→Bm; harmonic-minor solo.

## Structure (power metal single)
intro → verse → pre-chorus → **chorus** → verse2 → pre-chorus2 → **chorus2** → bridge → **solo** → **final chorus (modulated)** → outro.
- The solo comes **after the bridge**, not before.
- The chorus repeats **3 times**, with the last one transposed upward.
- **Applied in v3:** 11 sections, 140 bars, chorus x3 with the third in B minor.

## Bass
- In **eighth notes**, linked to the drums; rises an octave in the chorus to "open up" the sound.
- Ascending fills (root–2nd–3rd–5th) at section transitions.
- **Applied in v3:** eighth notes, octave up in the chorus, 4-note fills at boundaries.

## Cited listening references
- **DragonForce** — extreme tempo (~200 BPM), neoclassical solos harmonized in thirds, continuous double kick.
- **Metallica** — palm-muted riffs and pedal tone (although it is thrash/heavy, this is the reference the user requested; its influence on the gallop riff is direct).

## What GM cannot guarantee
- The General MIDI SoundFont does **not** reproduce palm mute, actual distortion, or metal guitar timbre. It sounds like a "mockup," not a production.
- Sound quality requires human listening; the auditor only certifies **structure**.
- The auditor states this explicitly: "it does not prove timbre, acoustic masking, palm mute, correct harmony, or musical quality."

## Sources
- Web searches on genre characteristics, tempo, double kick, and structure (findings consolidated in this session; cited traits, no invented URLs).
- `the skill's references/genre_configs.json` (profile `power_metal`: tempo 120–160, 4/4, density 12).
- `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md` (mechanical drum diagnosis, CC0 reference by nene).
- `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md` (Boddington/Jordan/Herbst on metal harmony; Garza on riff types).
