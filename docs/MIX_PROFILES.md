# Mix profiles: exact settings

These are starting values, not genre validation. Run `list_profiles()` for the same
settings over MCP. Role tuples are compressor `(threshold dB, ratio, attack ms, release ms)`.
Levels are linear multipliers, gain/EQ are dB. Balance is linear side attenuation,
not equal-power panning or mid/side processing. A centered mono lead uses `lead_guitar`;
`lead_guitar_L/R` are alternative separate doubles, not automatically generated layers.

## power_metal

| WAV basename | HPF Hz | Low shelf Hz/dB | Presence Hz/dB | Compressor | Gain dB | Balance | Level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `drums` | 35 | — | — | (-12, 3.0, 5, 80) | 1.5 | 0.0 | 0.95 |
| `electric_bass` | 40 | (120, 3.0) | — | (-14, 4.0, 8, 100) | 0 | 0.0 | 0.9 |
| `rhythm_guitar_L` | 90 | — | (2400, 2.5) | (-16, 2.5, 10, 120) | 0 | -0.55 | 0.72 |
| `rhythm_guitar_R` | 90 | — | (2400, 2.5) | (-16, 2.5, 10, 120) | 0 | 0.55 | 0.72 |
| `lead_guitar_L` | 200 | — | (3200, 3.0) | (-18, 3.0, 6, 90) | 0 | -0.3 | 0.6 |
| `lead_guitar_R` | 200 | — | (3200, 3.0) | (-18, 3.0, 6, 90) | 0 | 0.3 | 0.6 |
| `lead_guitar` | 200 | — | (3200, 3.0) | (-18, 3.0, 6, 90) | 0 | 0.0 | 0.6 |
| `synth_piano` | 180 | — | (1800, 1.0) | (-20, 2.0, 12, 130) | 0 | 0.15 | 0.45 |

Bus: HPF 28 Hz; mud peak EQ (300, -1.5) Hz/dB (Q 0.8); air shelf (8000, 1.5) Hz/dB;
compressor (-10, 2.0, 20, 200); trim -3 dB; sample limiter -1.0 dBFS / release 80 ms.

## balanced

| WAV basename | HPF Hz | Low shelf Hz/dB | Presence Hz/dB | Compressor | Gain dB | Balance | Level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `drums` | 30 | — | — | (-14, 2.5, 8, 90) | 0.0 | 0.0 | 0.9 |
| `electric_bass` | 38 | (100, 2.0) | — | (-16, 3.0, 10, 110) | 0 | 0.0 | 0.85 |
| `rhythm_guitar_L` | 80 | — | (2000, 1.5) | (-18, 2.0, 12, 130) | 0 | -0.5 | 0.68 |
| `rhythm_guitar_R` | 80 | — | (2000, 1.5) | (-18, 2.0, 12, 130) | 0 | 0.5 | 0.68 |
| `lead_guitar_L` | 180 | — | (2800, 2.0) | (-20, 2.5, 8, 100) | 0 | -0.25 | 0.58 |
| `lead_guitar_R` | 180 | — | (2800, 2.0) | (-20, 2.5, 8, 100) | 0 | 0.25 | 0.58 |
| `lead_guitar` | 180 | — | (2800, 2.0) | (-20, 2.5, 8, 100) | 0 | 0.0 | 0.58 |
| `synth_piano` | 150 | — | (1800, 0.5) | (-22, 1.8, 15, 150) | 0 | 0.1 | 0.48 |

Bus: HPF 25 Hz; mud peak EQ (250, -1.0) Hz/dB (Q 0.8); air shelf (9000, 1.0) Hz/dB;
compressor (-12, 1.8, 25, 220); trim -3 dB; sample limiter -1.0 dBFS / release 80 ms.

## Rationale and limits

HPFs reduce low-frequency competition; guitar presence helps parts stand out;
bass shelving adds weight; softer compression and EQ in balanced reduce the
amount of processing. The piano settings leave room for guitars. These are
explicit engineering assumptions without listening-based profile validation.

Unknown names abort. Subsets are allowed. No default duration of three minutes:
mixing uses the longest stem unless seconds are explicitly requested. Mono is
duplicated and stems are resampled to 44100 Hz. Final mastering adds another bus
stage and FFmpeg loudnorm; inspect before/after metrics and listen.

Pedalboard limiting is sample-based here. FFmpeg measures true peak and LUFS
during master/release_check. The release thresholds currently do not vary by
profile; profile selection is validated and included in the result.
