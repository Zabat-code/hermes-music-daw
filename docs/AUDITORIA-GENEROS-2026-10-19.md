# HermesMusic: musical audit and genre map (19 Oct 2026)

## Scope and honesty

Historical audit: scratch artifacts, the external classifier and the composition
scripts cited below are not bundled here. Their measurements are recorded
evidence, not a description of the current executable examples.

Static analysis of the skill sources (`SKILL.md`, `scripts/hermesmusic.py`, `references/genre_configs.json`), `rhythm_genre.py`, a scratch MIDI, and an output OGG. No re-rendering or critical listening was performed in this audit. The per-genre notes below are **candidate specifications**; they are not 100 implemented genres, universal traits, or 100 independent ethnomusicological validations. Musically, BPM and timbre alone do not define a genre.

## Hard evidence from the artifact
- The existing MIDI has **42 bars of 4/4 at 140 BPM, 72 s, 7 tracks**. The OGG runs **76.37 s**, including the render tail. The `compose_power_metal.py` script comment says "5–6 minutes," incompatible with that duration; the script also points to a missing *enhanced* file, so **its detailed arrangement must not be attributed to the available OGG**.
- MIDI tracks: drums 1092 notes, piano_comp 336, rhythm_guitar 336, strings 141, brass_booster 144, `MT_Epic_Lead` **0 notes**. There is no bass track and no populated guitar solo. Rhythm guitar = `arpeggio_up` arpeggio, not palm mute/power chord riffs; its density is always 8 notes per bar. Drums repeat 26 attacks per bar across all 42 bars. `MT_Epic_Lead` contains only meta-events and a program change: a named track is not a melody.
- The *enhanced* script in scratch describes `lead_guitar` and `choir`, but **no *enhanced* MIDI/OGG was produced** at the expected paths. `add_mt_melody` only copies events from track 0 to channel 0 of the MT file and skips other messages' relative timings; that path needs real testing before promising a lead part.
- The `genre=power_metal` metadata only modifies `drum_grid`, records `instruments` in `_genre_instruments` (with no later reader), and does not impose `tempo`, `meter`, `density_per_bar`, harmony, voices, bass, riffs, sections, or solos. `tracks` are defined by the composer in the composition JSON. `midi-rhythm-genre` classifies a rhythmic fingerprint; it does not certify the complete musical aesthetic.
- **100 labels** in `genre_configs.json`, but only **15 distinct drum templates** and **40 distinct template + instrument-list combinations**. No template uses `cymbal`; there is no `tom` column. `classical`, `romantic`, `waltz`, and `comedy_music` share the pop kick-snare-hihat pattern. Even `baroque` has kick/snare/hihat; it cannot be interpreted as baroque orchestration. `power_metal` shares a template with `samba`, `bachata`, `vallenato`, `prog_rock`, and others.
- **Verdict:** the user is right about the central problem. The file is an instrumental piece with metal/orchestral timbres; it is not a convincing power metal realization. Changing BPM or GM program is insufficient. Nor does all metal require additive meter; that is especially useful for **prog/math**, not a power metal requirement.

## Proposed genre contract
For each label: (1) an identifiable core — rhythm/cell with accents over 1–4 bars, not just 16 pulses; (2) roles: percussion, bass, accompaniment, melody/voice, and space; (3) harmonic/melodic language and articulations; (4) form with variations, fills, silences, contrast, and transitions; (5) excluded styles and legitimate variants; (6) MIDI + rendering + listening tests. **Parametric, family-based rules**, not mandatory stereotypes. Vocals cannot be verified with instrumental MIDI; if the genre depends heavily on singing/lyrics, declare "instrumental inspired by…," not "faithful reproduction."

### Full catalog: 100 labels → core to investigate/implement
These are arrangement hypotheses, not existing presets. Meaning of `/`: valid variants, not mandatory combinations.

**Metal and derivatives**
- `metal`: distorted riffs, aligned/contrapuntal bass, acoustic kit, section contrast.
- `power_metal`: double kick drive where applicable, riffs/power chords, an actual bass part, prominent melody with development and guitar harmonies, vocals or instrumental lead, composed solo and climax; do not restrict harmony to minor. Boddington et al. find Dorian color and secondary/diminished dominants in their sample, not a universal law [1].
- `speed_metal`: fast pulse, precise riffs, leads, and sustained attack; speed alone does not make it identical to power metal.
- `thrash_metal`: syncopated/choppy riffs, picking and accent breaks, changing drums.
- `death_metal`: extreme riffs and technical contrasts, blast beats/double kick optional by variant, specific bass and vocal roles when vocals are present.
- `black_metal`: tremolo picking/dense texture; minor modality and non-diatonic chords for atmosphere [1].
- `doom_metal`: slow, low riffs with space, harmonic weight, no pop backbeat pattern.
- `sludge_metal`: heavy, dragging feel, saturated/dissonant riffs, hardcore accents.
- `stoner_metal`: repetitive riffs with groove and psychedelic texture; gradual variation.
- `post_metal`: extended layered development, tension, and dynamic contrast; structural climax.

**Rock, guitars, and hybrids**
- `rock`: backbeat, bass/guitar dialogue, and riff/hook with form.
- `hardcore`: aggressive punk attack, accent/breakdown changes by variant; not `speed_metal`.
- `punk`: simple, direct riffs, incisive drums, short form, and energy; complexity is not mandatory.
- `grunge`: quiet/loud dynamics, rough guitars, less polished phrasing.
- `alternative`: umbrella label; require a reference substyle before setting rules.
- `indie`: scene/production label, not a unique rhythm; request an arrangement reference.
- `prog_rock`: contrasting sections, thematic development, irregular meters when they contribute.
- `math_rock`: displaced accents, asymmetric cells, interwoven ostinatos.
- `post_rock`: timbral and formal growth, repetition with transformation and climax.
- `trap_rock`: 808/hi-hats or trap production integrated with rock riffs/bass/guitar; two distinguishable traditions.
- `blues`: blues-inflected phrasing, call-and-response, bass/accompaniment consistent with the substyle; 12 bars is common, not universal.

**Jazz, R&B, and song**
- `jazz`: choose a substyle; melodic voice, rhythmic interaction, reharmonization/improvisation simulated only when musically composed.
- `swing`: articulated ride/hi-hat, walking bass/comping, swing or straight subdivision (do not treat swing as a fixed value) [2].
- `funk`: syncopated bass as the center, drums with ghost notes, guitar/keyboard stabs and accent breaks.
- `soul`: expressive phrasing/call-and-response, bass, organ/piano, optional brass; do not confuse it with generic backbeat.
- `rnb`: specify era/substyle; pocket, voice/lead, harmonies/syncopation.
- `gospel`: call-and-response, choral harmonies, dynamic development; instrumentation depends on tradition.
- `doo_wop`: harmonized voices and bass vocal/melody; MIDI without vocals only imitates the arrangement.
- `pop`: recognizable hook and texture changes between verse/chorus; there is no single pop pattern.

**Electronic dance music and breaks**
- `disco`: four-on-the-floor pulse, moving bass, guitar/string syncopation.
- `nu_disco`: disco references with modern synth/bass design and production arrangement.
- `house`: steady kick, claps/snares, offbeat hi-hats, bass/accompaniment groove.
- `techno`: hypnotic repetition with automation/timbre, deliberate harmonic reduction.
- `trance`: arpeggios/pads, builds and releases, sidechain/programmed energy.
- `electronic`: umbrella; require a production substyle before declaring identity.
- `breakbeat`: chopped/reordered breaks as the main material, not renamed four-on-the-floor [3].
- `breaks`: breakbeat variant with dance-track phrasing and bass; define a concrete reference.
- `drum_and_bass`: fast breaks and sub-bass with space and fills, variable kick/snare relationships [3].
- `dubstep`: perceived half-time pulse, sub-bass, and bass/space design; BPM is insufficient.
- `gabber`: distorted kick as the driving force, intense pulse; sound design is decisive.
- `industrial`: mechanical percussion, abrasive timbres, arrangement by subgenre.
- `idm`: structural experimentation with rhythm/timbre; no fixed generalizable pattern.
- `footwork`: fragmented, syncopated rhythm with frequent changes, optional samples/voice.
- `juke`: fast percussive cells and cuts/samples; distinguish it from footwork using scene references.
- `synthwave`: retro timbres, bass/arpeggios, electronic drums with song form.

**Hip-hop and urban Caribbean music**
- `hiphop`: break/beat pocket, bass, and space for rap; do not fill every subdivision.
- `trap`: articulated hi-hats/rolls, tuned 808, kick/silences; variation over the loop.
- `drill`: sub-bass/808 glides and displaced beat accents; specify UK/Chicago/Brooklyn drill.
- `trip_hop`: relaxed beats with breaks, dark bass, spatial layers; not just slow tempo.
- `lo_fi`: intentional production aesthetic/imperfection, not a unique rhythm.
- `reggae`: central bass, offbeat skank, space/dub, drums according to one-drop/rockers/steppers.
- `ska`: fast offbeat guitar/keyboard, walking bass, rhythmic drive.
- `reggaeton`: dembow and articulated bass in cycles; breaks and accents vary by era; not four-on-the-floor and not to be confused with salsa.

**Latin America and Brazil**
- `salsa`: choose 2-3 or 3-2 son clave and orient bass (tumbao), piano (montuno), congas/cowbell/brass; phrases of at least two bars; do not arbitrarily reverse the clave [4].
- `mambo`: interacting montunos, brass sections, Afro-Cuban patterns [4].
- `cha_cha`: mark the dance pulse, güiro/cowbell/piano, with Afro-Cuban structure; do not apply a clave automatically without determining the variant.
- `rumba`: specify Cuban/flamenco/other rumba; these are different traditions, not one preset.
- `bossa_nova`: subtle guitar pattern, bass/pandeiro or soft kit, Brazilian syncopation; not a samba template with lower BPM [2].
- `samba`: articulated percussion ensemble, bass/surdo, dance cycles/accents; distinguish pagode/enredo variants [2].
- `bachata`: interaction between requinto and rhythm guitar, bass, bongos, and güira; sequences and endings by section.
- `bolero`: slow accompaniment with cantabile phrasing, bass/percussion appropriate to Cuban/Mexican bolero.
- `cumbia`: choose Colombian/Andean/villera/etc. tradition; cyclic percussion and bass, optional accordion.
- `vallenato`: dialogue between accordion, caja drum, and guacharaca; choose the rhythmic style (paseo/merengue/son/puya), rather than equating it with cumbia.
- `tango`: orchestral/guitar/bandoneon phrasing and accents; rubato and marcato according to the arrangement.
- `mariachi`: trumpets and strings with vihuela/guitarrón, meter consistent with son/ranchera/huapango.
- `flamenco`: choose the palo and rhythmic cycle before programming guitar/handclaps/cajón; do not arbitrarily impose 4/4 and backbeat.

**Africa, the Caribbean, and Creole traditions**
- `afrobeat`: interdependent ostinatos, bass, drums, percussion/guitars/brass; layered growth, not a four-beat pattern [4].
- `highlife`: interwoven guitars, bass, danceable percussion; choose tradition/era.
- `calypso`: narrative vocal phrasing (without vocals: inspired by), Caribbean percussion and accompaniment.
- `soca`: carnival production, driving percussion/bass, hooks; do not reuse highlife by changing tempo.
- `zydeco`: accordion, frottoir, dance groove with bass/kit; Louisiana context.

**Folk, country, and European dances**
- `folk`: regional umbrella; require origin/instrumentation before generating.
- `country`: groove, guitar/steel guitar/fiddle, phrasing according to honky-tonk/bluegrass/contemporary style.
- `bluegrass`: banjo/mandolin/guitar, bass, acoustic soloists; drums are not mandatory.
- `reel`: dance melody in 4/4 on fiddle/regional instruments, repeated phrasing.
- `jig`: composed compound phrasing (6/8), not 4/4 at an altered BPM.
- `waltz`: three beats per bar, dance phrases, no 4/4 backbeat.
- `mazurka`: three beats with characteristic displaced accents, distinct from the waltz.
- `minuet`: triple-meter dance, formal structure/period phrasing, no kick/snare.
- `polka`: duple-meter dance with bass/offbeat accompaniment (oom-pah), timbre according to tradition.
- `tarantella`: lively dance with compound subdivision according to tradition; program actual phrases.
- `march`: march meter and accents, snare/bass drum/brass for a band; not a single tempo.

**Historical, contemplative, and functional labels**
- `classical`: ambiguous era/usage label; if referring to the Classical period, thematic form/tonal function/orchestration; percussion only when called for by the score.
- `baroque`: counterpoint/continuo and formal organization according to dance/fugue/concerto; prohibit a pop kit by default.
- `romantic`: thematic development/chromaticism/dynamics and rubato according to the work, not pop with strings.
- `ambient`: long textures and space with low activity; kick is not mandatory.
- `drone`: sustained note/chord and spectral evolution, not a kick loop by default.
- `meditation`: functional purpose; request desired timbre/length/dynamics, not a verifiable musical genre.
- `mantra`: explicit vocal/textual repetition or an instrumental reference; without vocals, disclose the limitation.
- `new_age`: soft timbres, simple development, but a broad and variable label.
- `psybient`: ambient layers with psychedelic/microrhythmic production, not renamed ambient.
- `downtempo`: production range rather than a single genre; select a reference pattern.
- `chillout`: purpose/scene, not unique musical rules; define a substyle.
- `chillwave`: nostalgic lo-fi/synth textures and pop/electronic structure according to the reference.
- `vaporwave`: manipulation of samples' time/timbre; not faithfully realizable with GM MIDI alone.
- `darkwave`: synths/guitars, dark atmosphere; choose a post-punk/electronic direction.
- `goth`: scene label; choose goth rock/darkwave/etc. before composing.
- `experimental`: no identity template; request a constraint/formal idea and evaluate against it.
- `comedy_music`: narrative effect of incongruity/humor, no fixed drum pattern.
- `spoken_word`: voice/text with accompaniment that leaves space; instrumental MIDI does not represent the essential element.

## Proposed acceptance tests (before declaring a genre "works")
1. **Roles** validator per genre: `power_metal` requires kick/snare/cymbals, bass, rhythm guitar with riffs, lead/vocals/theme; a section named solo must contain one. Do not allow empty tracks or described-but-absent roles.
2. **Rhythmic/formal** validator: observable intro/verse/bridge/solo/climax differences; alternation of patterns/fills; 2–8 bar phrases by genre; bar reading in actual time; correctly oriented clave, swing/compound cells when declared.
3. **Harmonic/melodic** validator: riffs vs arpeggios, transformed recurring motifs, actual lead notes, bass in dialogue with kick/guitar. Do not impose solos or additive meters on all metal.
4. **Rendering** validation: run composition and rendering, inspect tracks, BPM/bars/duration, missing elements, A/B listening with authorized references; MIDI with GM timbre is a prototype, not a final-quality guarantee.
5. **Status levels:** label catalog = metadata support; rhythmic template = partial; full profile + tests = implemented; human listening = accepted. Never describe the current state as "100 faithful genres."

## Technical priority
1. Correct the misleading skill description and present the `genre` list as metadata/templates; add a warning during composition/rendering.
2. Repair the power metal song in a separate prototype: actual bass, palm mute/power chord riffs, drums with variations and fills, composed lead with articulations, verified form; do not reuse the empty MT title/track as evidence of a solo.
3. Implement profile architecture by **musical families** with more layers per genre and variant, validators, and 4–8 bar fixtures; start with power metal + salsa + jazz swing + bossa + house to force different solutions.
4. Then extend to the 100 labels with sources per tradition and listening samples; undocumented labels remain "experimental/unverified."

## Primary sources consulted
[1] Boddington, Jordan, and Herbst, *Harmonic structures in twenty-first-century metal music*, Metal Music Studies 9(1), 2023, DOI 10.1386/mms_00093_1, University of Huddersfield research portal: https://pure.hud.ac.uk/en/publications/harmonic-structures-in-twenty-first-century-metal-music-a-harmoni
[2] Antonio J. Garcia, jazz educator, *Basic Swing & Bossa/Samba Drumming* (demonstration and patterns): https://garciamusic.com/educator/articles/swing.bossa.samba.drum.html
[3] Ableton, production and break programming interview with Paradox: https://www.ableton.com/en/blog/paradox-breakbeat-mastery/ and DJ Fracture tutorial on DnB/sub-bass: https://www.ableton.com/en/blog/dnb-beats-and-sub-bass-tutorial-dj/
[4] Smithsonian Folkways, *Braiding Rhythms*, original educational material on rumba clave, shell percussion, and 6/8 bell patterns: https://folkways.si.edu/braiding-rhythms-the-role-of-bell-patterns-in-west-african-and-afro-caribbean-music/tools-for-teaching/smithsonian

**Source limitation:** notes on other genres are preliminary design proposals; do not falsely attribute them to [1]–[4]. Validating them requires research on each tradition and comparative listening.
