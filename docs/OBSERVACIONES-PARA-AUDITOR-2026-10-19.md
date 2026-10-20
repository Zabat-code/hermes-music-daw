# Observations: why another model would repeat this error

Written so an external auditor can understand the failure pattern, not just this specific case.

Historical requirements written before the guard was implemented. The current
guard is an enforced entry point, not a sandbox: arbitrary code can bypass it.
External project and scratch artifacts listed below are not bundled in this checkout.

## Traps that lead any agent to the same error
1. **The easy path "works."** `render_song(spec, out)` + a `drum_grid` produces a valid MIDI with the exact requested duration, classified as "metal." An agent optimizes for "deliver something that passes the tests" and stops there. **Apparent success is the trap.**
2. **Available validation is blind to musical defects.** `validate_midi` (orphan notes, duration) and `classify_genre` (onsets, tempo) return OK. An agent trusting the existing pipeline **has no signal that something is wrong**. There is no failing test.
3. **Corrective documentation lives outside the skill.** The diagnoses live in `~/.hermes/documentacion/hermesmusic/`, but the `hermes-music` skill **does not link to them**. An agent loading the skill (the correct action) still does not see them. Loading the skill *looks* like following the protocol.
4. **Rules are written as prose rather than gates.** "The melody needs silences," "not all instruments play all the time" — this is advice in a `.md`, not checks. An agent can read them and fail to apply them without anything stopping it.
5. **The convenient pattern appears first.** `drum_grid` and `render_song` patterns are the first tools presented; writing notes individually (which produces good results) requires writing a custom script and more work. The path of least resistance is the defective one.
6. **The reference example is buried.** `ash_to_dawn_drums_v2.py` does *exactly* the right thing (phrased grooves, varied velocities, fills only at boundaries) but lives in `~/<project>/`, outside the skill. A new agent does not find it.
7. **The fix was saved as a patch for one case, not as a rule.** The first piece's v2 fixed *that* piece; nothing was generalized to the engine or skill. The next composition started from the defective pattern again.
8. **"Documenting the error" is confused with "fixing the error."** It was documented twice (see `HALLAZGOS.md`), and the same error returned. Documenting without implementing a gate **does not change the next agent's behavior**.

## Guardrail requirements (for the auditor)
The fix must not be another `.md`. It must be a **mandatory, verifiable protocol**
that aborts failures when invoked through the prescribed entry point. Criteria:
1. **Single entry point.** When the `hermes-music` skill is loaded to *compose* (not for reference), the agent must encounter the protocol before writing music.
2. **Explicit step sequence**, not advice: what to read, decide, and write, in what order, and what NOT to do.
3. **Automatic gates that fail visibly.** Checks must measure the actual defects (drum overlap, dynamic variation, space/silences, register limits) and **abort** when requirements are unmet — not merely report them.
4. **Applied immediately, not deferred.** The audit must run on the generated piece and determine acceptability before anything is declared finished.
5. **Engine-level support.** Where possible, code rejects defective configurations (e.g., `drum_grid` triggering 3 pieces in one step, or an accompaniment pattern repeated throughout the song without variation) rather than relying on discipline.
6. **Reference example within the skill**, not in a separate project folder.
7. **Documented and prohibited anti-pattern**: "declare success because validate_midi passed."

## Material the auditor must review
- `SKILL.md`
- `references/teoria-composicion.md` (section "Arrangement: Making Space")
- `references/rendering.md`
- `scripts/hermesmusic.py` (`render_song` function and its `drum_grid` pattern branch; `drum_grid` is not a function)
- `~/.hermes/documentacion/hermesmusic/COMPARATIVA-BATERIA-METAL-2026-10-19.md`
- `~/.hermes/documentacion/hermesmusic/TEORIA-Y-ARQUITECTURA-2026-10-19.md`
- `HALLAZGOS.md`
- `~/.hermes/documentacion/hermesmusic/ERROR-REPETIDO-2026-10-19.md`
- `~/<project>/ash_to_dawn_drums_v2.py` (good example)
- Scratch artifact `compose_gym_power_metal.py` (defective v1, not bundled)
- Scratch artifact `compose_gym_power_metal_v2.py` (corrected v2, not bundled)
