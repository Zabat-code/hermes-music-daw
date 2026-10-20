# MIDI drum comparison: Ash to Dawn vs. metal reference (2026-10-19)

## Provenance and licensing

- Reference: “Boss Battle #9 [Metal],” **nene**, OpenGameArt, published 2023-04-27. Page inspected in Brave: `https://opengameart.org/content/boss-battle-9-metal`; it advertises an included MIDI and a **CC0/Public Domain** license. File published at `https://opengameart.org/sites/default/files/boss_battle_9.mid`.
- Local download: `~/<project>/reference_nene_boss_battle_9.mid` (17,524 bytes, SHA-256 `d9848be9fb7d4e9d1a1f6c7e2882f806dac4ca90b3db462e97b2f5fff3bdee38`). HTTP 200 response, `audio/midi`, `MThd` header; saved bytes were verified against the response. The page was viewed in the actual Brave browser, and the download came directly from its confirmed file link.
- Compared against `~/<project>/Ash_to_Dawn_demo.mid`, the source MIDI for the previously delivered OGG. **The original song, Desktop OGG, and engine were not altered.**

## MIDI observations (not a listening assessment)

| Variable | nene reference | Ash to Dawn |
|---|---:|---:|
| Musical duration | 59.47 s | 120.00 s |
| Initial tempo | ~113 BPM (530,973 μs/quarter note) | 156 BPM |
| Meter | 4/4 | 4/4 |
| Bars | 28 | 78 |
| Drum hits | 540 | 1435 |
| Distinct per-bar percussion attack patterns* | 22/28 | 8/78 |
| Most repeated pattern* | 4 bars | 45 bars |
| Kick GM36 | 247 | 584 |
| Snare GM38 | 119 | 156 |
| Recurring cymbal | GM55 splash: 91 | GM51 ride: 544; GM42 hi-hat: 48 |
| Toms and other cymbals | Present and distributed | Four-tom fills at the end of every four-bar block |
| Bass / guitars | 240 bass notes; two guitars with 383 each and lead with 404 | 584 bass notes; two guitars with 1284 each, lead with 262 |

\*Pattern signature = set of hits by GM instrument and phase within the bar, excluding dynamics and duration. This count does not determine musical quality or count pitched instruments.

### Observed grooves

- In the reference, bars 5–7 place kick hits at offbeat sixteenth-note positions (0.25, 0.75, 1.25 ...), snare on 0, 0.5, 1 ...; bar 9 switches to snare on beats 1 and 3 (zero-based) and kick with sixteenth notes and rests. Other sections alternate variations, kick rolls, and toms. The opening is an introductory fill, not the main grid. Caution: this reference is NOT a universal model: snare appears on every eighth note in some bars, GM55 (splash) frequently serves as a regular pulse, and the exported drums use an almost constant velocity of 95, so it can also sound artificial with a GM sound bank.
- In **Ash to Dawn**, all 68 bars of dense sections contain **exactly eight kick and eight ride hits per bar**, both triggered together at beats 0, 0.5, 1, 1.5, 2, 2.5, 3, and 3.5. Snare repeats two hits per bar (1 and 3). The change after the intro consists almost entirely of replacing hi-hat GM42 with ride GM51; there are no gaps, kick syncopations, or phrasing shaped by guitar or bass. Across the 78 bars, the most repeated pattern occurs 45 times, and the two most common total 62. Periodic fills recur with the same GM47-45-43-41 pitches and an anticipated crash at 3.75, without responding to cadences or breathing room in riffs.

## Likely diagnosis (inference, not auditory certainty)

The drums feeling “odd” is consistent with **a uniform mechanical grid + perpetual ride + an identical fill every four bars**. When rendered with FluidR3 GM, the GM51 cymbal repeated over every kick may further emphasize the synthesized effect. The CC0 reference contains changes in groove and small rhythmic figures within phrases, though it does not by itself demonstrate human performance. No isolated drum recordings were compared and no human A/B listening was performed: do not attribute each user impression to a definitive acoustic cause.

## Suggested correction before rebuilding the piece (NOT applied)

1. Write 3–4 intentional grooves by function (threat, riff, buildup, climax), with local variations and rests. Avoid kick/cymbal hits on every offbeat throughout the song.
2. Align kick with actual riff and bass accents; reserve sixteenth notes/double kick for pushes, alternating with more open patterns to make the contrast audible.
3. Separate snare, hi-hat, and ride dynamics; do not use ride GM51 continuously throughout entire sections. Introduce crashes at phrase starts and fills only at relevant transitions, not every fourth bar by counter.
4. Test the new piece and the reference with the same SoundFont and submit the result to human comparative listening before declaring it “metal.”

This study justifies adjusting the algorithm; **no complete riffs or patterns were copied from the reference**, and no game file was changed.
