# HermesMusic: auditoría musical y mapa de géneros (19 oct 2026)

## Alcance y honestidad
Análisis estático de `~/.hermes/skills/hermes-music/{SKILL.md,scripts/hermesmusic.py,references/genre_configs.json}`, `~/.hermes/skills/midi-rhythm-genre/rhythm_genre.py`, el MIDI `~/.hermes/cache/scratch/power_metal_ddm.mid` y el OGG `~/Desktop/power_metal_dancing_mad.ogg`. No se re-renderizó ni se hizo escucha crítica en esta auditoría. Los apuntes por género de abajo son **especificaciones candidatas**; no son 100 géneros ya implementados, ni rasgos universales, ni 100 validaciones etnomusicológicas independientes. Musicalmente, BPM y timbre por sí solos no definen un género.

## Evidencia dura del artefacto
- El MIDI existente tiene **42 compases de 4/4 a 140 BPM, 72 s, 7 pistas**. El OGG dura **76.37 s** incluyendo cola de render. El comentario del script `compose_power_metal.py` dice «5–6 minutos», incompatible con esa duración; además ese script apunta a un archivo *enhanced* ausente, por lo que **no debe atribuirse su arreglo detallado al OGG presente**.
- Pistas MIDI: drums 1092 notas, piano_comp 336, rhythm_guitar 336, strings 141, brass_booster 144, `MT_Epic_Lead` **0 notas**. No hay pista de bajo ni solo de guitarra con notas. Guitarra rítmica = arpegio `arpeggio_up`, no riffs de palm mute/power chords; su densidad es 8 notas por compás, siempre igual. Batería repite 26 ataques por compás en los 42 compases. En `MT_Epic_Lead` solo hay metaeventos y cambio de programa: una pista con nombre no es una melodía.
- El script *enhanced* en scratch describe `lead_guitar` y `choir`, pero **no hay MIDI/OGG *enhanced* producido** en las rutas previstas. `add_mt_melody` solo copia eventos de la pista 0 en canal 0 del archivo MT y omite tiempos relativos de otros mensajes; esa ruta requiere prueba real antes de prometer lead.
- El metadato `genre=power_metal` solo modifica `drum_grid`, registra `instruments` en `_genre_instruments` (sin ningún lector posterior), y no impone `tempo`, `meter`, `density_per_bar`, armonía, voces, bajo, riffs, secciones ni solos. `tracks` los define la persona/autora en el JSON de composición. `midi-rhythm-genre` clasifica una huella rítmica, no certifica la estética musical completa.
- **100 etiquetas** en `genre_configs.json`, pero solo **15 plantillas de batería distintas** y **40 combinaciones distintas de plantilla + lista de instrumentos**. Ninguna plantilla usa `cymbal`; no hay columna `tom`. `classical`, `romantic`, `waltz` y `comedy_music` comparten el patrón pop kick-snare-hihat. Incluso `baroque` tiene kick/snare/hihat; no se puede interpretar como orquestación barroca. `power_metal` comparte plantilla con `samba`, `bachata`, `vallenato`, `prog_rock` y otras.
- **Veredicto:** el usuario tiene razón en el problema central. El archivo es una pieza instrumental con timbres metal/orquestales, NO una realización convincente de power metal; no basta cambiar BPM ni GM program. Tampoco todo metal requiere compás aditivo: eso es especialmente útil para **prog/math**, no un requisito del power metal.

## Contrato de género propuesto
Para cada etiqueta: (1) núcleo identificable — ritmo/célula y acentos sobre 1–4 compases, no solo 16 pulsos; (2) roles: percusión, bajo, acompañamiento, melodía/voz y espacio; (3) lenguaje armónico/melódico y articulaciones; (4) forma con variaciones, fills, silencios, contraste y transiciones; (5) estilos excluidos y variantes legítimas; (6) pruebas MIDI + render + escucha. Reglas **parametrizables y de familia**, no estereotipos obligatorios. Vocales no se pueden verificar con MIDI instrumental; si el género depende fuertemente de canto/letra, declarar «instrumental inspirado en…», no «reproducción fiel».

### Catálogo completo: 100 etiquetas → núcleo a investigar/implementar
Estas son hipótesis de arreglo, no presets que ya existan. Significado de `/`: variantes válidas, no combinaciones obligatorias.

**Metal y derivados**
- `metal`: riffs distorsionados, bajo alineado/contrapunto, kit acústico y contraste de secciones.
- `power_metal`: impulso de doble bombo cuando corresponda, riffs/power chords, bajo real, melodía destacada con desarrollos y harmonías de guitarras, coros o lead instrumental, solo compuesto y clímax; no limitar a menor armónica. La investigación de Boddington et al. encuentra color dórico y dominantes secundarias/disminuidos en su muestra, no una ley universal [1].
- `speed_metal`: pulsación rápida, riffs precisos, leads y ataque sostenido; no idéntico a power por velocidad.
- `thrash_metal`: riff sincopado/entrecortado, picking y cortes de acento, batería cambiante.
- `death_metal`: riff extremo y contrastes técnicos, blast/doble bombo opcionales por variante, bajo y voz específicos si hay vocal.
- `black_metal`: tremolo picking/textura densa; modalismo menor y acordes no diatónicos para atmósfera [1].
- `doom_metal`: riffs graves lentos con espacio, peso armónico, no patrón backbeat pop.
- `sludge_metal`: arrastre pesado, riffs saturados/disonancia y acentos hardcore.
- `stoner_metal`: riff repetitivo con groove y textura psicodélica; variación gradual.
- `post_metal`: desarrollo largo por capas, tensión y contraste dinámico; clímax estructural.

**Rock, guitarras e híbridos**
- `rock`: backbeat, bajo/guitarra en diálogo y riff/hook con forma.
- `hardcore`: ataque punk agresivo, cambios de acento/breakdowns según variante; no es `speed_metal`.
- `punk`: riff simple y directo, batería incisiva, forma breve y energía; complejidad no obligatoria.
- `grunge`: dinámica quiet/loud, guitarras rugosas y fraseo menos pulido.
- `alternative`: etiqueta paraguas: exigir subestilo de referencia antes de fijar reglas.
- `indie`: etiqueta de escena/producción, no ritmo único; pedir referencia de arreglo.
- `prog_rock`: secciones contrastantes, desarrollo temático y métricas irregulares cuando aporten.
- `math_rock`: acentos desplazados, células asimétricas, ostinati entrelazados.
- `post_rock`: crecimiento tímbrico y formal, repetición con transformación y clímax.
- `trap_rock`: 808/hats o diseño trap articulado con riff/bajo/guitarra rock; dos tradiciones distinguibles.
- `blues`: fraseo con inflexión blues, call-response y bajo/acompañamiento acordes con el subestilo; 12 compases es frecuente, no universal.

**Jazz, R&B y canción**
- `jazz`: elegir subestilo; voz melódica, interacción rítmica, reharmonización/improvisación simulada solo si compuesta musicalmente.
- `swing`: ride/hi-hat articulados y walking bass/comping, subdivisión swing no swing=valor fijo [2].
- `funk`: bajo sincopado como eje, batería con ghost notes y stabs/cortes de guitarra/teclado.
- `soul`: fraseo expresivo/call-response, bajo, órgano/piano y metales opcionales; no confundir con backbeat genérico.
- `rnb`: especificar época/subestilo; pocket, voz/lead y armonías/síncopas.
- `gospel`: llamada-respuesta, armonías corales y desarrollo dinámico; instrumento depende tradición.
- `doo_wop`: voces armonizadas y bajo vocal/melodía; MIDI sin voces solo imita disposición.
- `pop`: hook reconocible y cambios de textura entre verso/estribillo; no existe un único patrón pop.

**Electrónica de baile y breaks**
- `disco`: pulso cuatro-al-piso, bajo con movimiento, contratiempos de guitarra/strings.
- `nu_disco`: cita disco con diseño de synth/bajo moderno y arreglo de producción.
- `house`: bombo estable, clap/snares, hats a contratiempo y groove de bajo/acordes.
- `techno`: repetición hipnótica con automatización/timbre, reducción armónica deliberada.
- `trance`: arpegios/pads, builds y releases, sidechain/energía programada.
- `electronic`: paraguas; requiere rama de producción antes de declarar identidad.
- `breakbeat`: break recortado/reordenado como material principal, no four-on-floor renombrado [3].
- `breaks`: variante de breakbeat con fraseo de pista y bajo; definir referencia concreta.
- `drum_and_bass`: breaks rápidos y sub-bass con espacio y fills, relaciones kick/snare variables [3].
- `dubstep`: pulso percibido a medio tiempo, sub-bass y diseño de bajos/espacios; no basta BPM.
- `gabber`: distorsión de bombo como motor y pulsación intensa; diseño sonoro decisivo.
- `industrial`: percusión mecánica/timbres abrasivos y arreglo según subtradición.
- `idm`: experimentación estructural del ritmo/timbre; no patrón fijo generalizable.
- `footwork`: ritmo sincopado fragmentado con cambios frecuentes, samples/voz opcionales.
- `juke`: célula percusiva rápida y cortes/samples; separar de footwork con referencias de escena.
- `synthwave`: timbres retro, bajo/arpegios y batería electrónica con forma de canción.

**Hip-hop y Caribe urbano**
- `hiphop`: pocket de break/beat, bajo y espacio para rap; no rellenar todas las subdivisiones.
- `trap`: hats articulados/rolls, 808 afinado y bombo/silencios; variación sobre el loop.
- `drill`: sub-bass/808 glides y acentos de beat desplazados; especificar drill UK/Chicago/Brooklyn.
- `trip_hop`: beat pausado con breaks, bajo oscuro y capas espaciales; no es solo tempo lento.
- `lo_fi`: estética de producción/imperfección intencional, no ritmo único.
- `reggae`: bajo central, offbeat de skank, espacio/dub y batería según one-drop/rockers/steppers.
- `ska`: contratiempo rápido de guitarra/teclado, bajo caminante e impulso rítmico.
- `reggaeton`: dembow y bajo articulados en ciclos; breaks y acentos varían según época; no four-on-floor ni confundir con salsa.

**Latinoamericano y Brasil**
- `salsa`: elegir son/clave 2-3 o 3-2 y orientar bajo (tumbao), piano (montuno), conga/campana/metales; frase de al menos dos compases; no invertir la clave arbitrariamente [4].
- `mambo`: interacción montunos, secciones de metales y patrones afro-cubanos [4].
- `cha_cha`: marcar pulsación/danza y güiro/campana/piano, con estructura afro-cubana; no usar clave automática sin determinar variante.
- `rumba`: especificar rumba cubana/flamenca/otra; son tradiciones diferentes, no un preset.
- `bossa_nova`: patrón sutil de guitarra y bajo/pandereta o kit suave, síncopa brasileña; no plantilla samba con BPM menor [2].
- `samba`: articulación de múltiples percusiones y bajo/surdo, ciclos/acento de danza; variantes pagode/enredo distintas [2].
- `bachata`: interacción de requinto/guitarra rítmica, bajo, bongó y güira; secuencias y remates por sección.
- `bolero`: acompañamiento lento con fraseo cantabile, bajo/percusión adecuados a bolero cubano/mexicano.
- `cumbia`: elegir tradición colombiana/andina/villera/etc.; percusión y bajo cíclicos, acordeón opcional.
- `vallenato`: diálogo entre acordeón, caja y guacharaca; elegir aire (paseo/merengue/son/puya), no equiparar a cumbia.
- `tango`: fraseo y acentos de orquesta/guitarras/bandoneón; rubato y marcato según arreglo.
- `mariachi`: trompetas y cuerdas con vihuela/guitarrón y métrica acorde al son/ranchera/huapango.
- `flamenco`: escoger palo y compás antes de programar guitarra/palmas/cajón; no imponer 4/4 y backbeat al azar.

**África, Caribe y criollo**
- `afrobeat`: ostinati interdependientes, bajo, batería, percusión/guitarras/metales; crecimiento por capas, no patrón de cuatro golpes [4].
- `highlife`: guitarras entrelazadas, bajo y percusión bailable; elegir tradición/época.
- `calypso`: fraseo vocal narrativo (si no hay voz: inspirado), percusión y acompañamiento caribeño.
- `soca`: producción de carnaval, percusión/bajo motriz y hooks; no reutilizar highlife por tempo.
- `zydeco`: acordeón, frottoir y groove de baile con bajo/kit; contexto de Luisiana.

**Folk, country y danzas europeas**
- `folk`: paraguas regional, exigir origen/instrumentación antes de generar.
- `country`: groove, guitarra/steel/fiddle y fraseo según honky-tonk/bluegrass/contemporáneo.
- `bluegrass`: banjo/mandolina/guitarra, bajo y breaks solistas acústicos; batería no obligatoria.
- `reel`: melodía de danza en 4/4 de fiddle/instrumento regional, fraseo repetido.
- `jig`: fraseo ternario compuesto frecuente (6/8), no 4/4 a BPM alterado.
- `waltz`: tres tiempos por compás y fraseos de baile, no backbeat 4/4.
- `mazurka`: tres tiempos con acento desplazado característico, diferente del vals.
- `minuet`: danza en triple y estructura formal/fraseo de época, no kick/snare.
- `polka`: baile binario con bajo/contratiempo (oom-pah), timbre según tradición.
- `tarantella`: danza viva de subdivisión compuesta según tradición; programar fraseos reales.
- `march`: métrica y acentuación de marcha, caja/bombo/metales si banda; no un único tempo.

**Histórico, contemplativo y etiquetas funcionales**
- `classical`: etiqueta de época/uso ambiguo: si clasicismo, forma temática/función tonal/orquestación; percusión solo si pide partitura.
- `baroque`: contrapunto/continuo y organización formal según danza/fuga/concierto; prohibir kit pop como default.
- `romantic`: desarrollo temático/cromatismo/dinámica y rubato según obra, no pop con cuerdas.
- `ambient`: texturas largas y espacio con baja actividad; bombo no obligatorio.
- `drone`: nota/acorde sostenido y evolución espectral, no loop de bombo por defecto.
- `meditation`: finalidad funcional; pedir timbre/duración/dinámica deseada, no género musical verificable.
- `mantra`: repetición vocal/textual o referente instrumental explícito; sin voz, transparencia sobre limitación.
- `new_age`: timbres suaves y desarrollo sencillo, pero etiqueta amplia y variable.
- `psybient`: capas ambientales con producción psicodélica/micro-ritmos, no ambient renombrado.
- `downtempo`: rango de producción más que género único; seleccionar patrón de referencia.
- `chillout`: finalidad/escena, no reglas musicales únicas; definir subestilo.
- `chillwave`: texturas nostálgicas lo-fi/synth y estructura pop/electrónica según referencia.
- `vaporwave`: manipulación de muestras y tiempo/timbre; no realizable fielmente solo con GM MIDI.
- `darkwave`: synth/guitarras y atmósfera oscura; elegir vertiente post-punk/electrónica.
- `goth`: etiqueta de escena: escoger goth rock/darkwave/etc. antes de componer.
- `experimental`: no hay plantilla identitaria; pedir restricción/idea formal y evaluar frente a ella.
- `comedy_music`: efecto narrativo de incongruencia/humor, no patrón fijo de batería.
- `spoken_word`: voz/texto y acompañamiento que deja espacio; MIDI instrumental no representa el elemento esencial.

## Pruebas de aceptación propuestas (antes de declarar que un género «funciona»)
1. Validador de **roles** por género: `power_metal` exige bombo/caja/platos, bajo, guitarra rítmica con riffs, lead/coro/tema; solo solo si la sección se llama solo. No permitir pistas vacías ni roles descritos pero ausentes.
2. Validador **rítmico y formal**: diferencias observables intro/verso/puente/solo/clímax; alternancia de patrones/fills; fraseos de 2–8 compases según género; lectura de compás real; clave no invertida y swing/células compuestas si se declararon.
3. Validador **armónico/melódico**: riffs vs arpegios, motivos recurrentes transformados, notas de lead realmente presentes, bajo que dialogue con bombo/guitarra. No imponer solos o métricas aditivas a todo metal.
4. Validación de **render**: ejecutar composición y render, inspeccionar pistas, BPM/compases/duración, ausencias y audición A/B con referencias autorizadas; MIDI con timbre GM es prototipo, no garantía de calidad final.
5. **Semáforo:** catálogo de etiquetas = soportado en metadatos; plantilla rítmica = parcial; perfil completo + pruebas = implementado; escucha humana = aceptado. Nunca llamar «100 géneros fieles» al estado actual.

## Prioridad técnica
1. Corregir descripción engañosa de skill y lista de `genre` como metadatos/plantillas; añadir advertencia en composición/render.
2. Reparar la canción power metal en prototipo separado: bajo real, riff palm mute/power chords, batería con variaciones y fills, lead compuesto con articulaciones, forma comprobada; no reutilizar el título/pista MT vacía como evidencia de solo.
3. Implementar arquitectura de perfiles por **familias musicales** más capas por género y variante, con validators y fixtures de 4–8 compases; comenzar por power metal + salsa + jazz swing + bossa + house para forzar soluciones realmente diferentes.
4. Extender después a las 100 etiquetas con fuentes por tradición y muestras auditivas; etiquetas no documentadas permanecen «experimental/no verificado».

## Fuentes primarias consultadas
[1] Boddington, Jordan y Herbst, *Harmonic structures in twenty-first-century metal music*, Metal Music Studies 9(1), 2023, DOI 10.1386/mms_00093_1, portal de investigación University of Huddersfield: https://pure.hud.ac.uk/en/publications/harmonic-structures-in-twenty-first-century-metal-music-a-harmoni
[2] Antonio J. García, docente de jazz, *Basic Swing & Bossa/Samba Drumming* (demostración y patrones): https://garciamusic.com/educator/articles/swing.bossa.samba.drum.html
[3] Ableton, entrevista de producción y programación de breaks a Paradox: https://www.ableton.com/en/blog/paradox-breakbeat-mastery/ y tutorial de DJ Fracture sobre DnB/sub-bass: https://www.ableton.com/en/blog/dnb-beats-and-sub-bass-tutorial-dj/
[4] Smithsonian Folkways, *Braiding Rhythms*, material didáctico original sobre rumba clave, cáscara y patrones de campana 6/8: https://folkways.si.edu/braiding-rhythms-the-role-of-bell-patterns-in-west-african-and-afro-caribbean-music/tools-for-teaching/smithsonian
**Límite de fuentes:** los apuntes de los otros géneros son propuestas preliminares de diseño; no atribuirlos falsamente a [1]–[4]. Para declararlos validados falta investigación de cada tradición y escucha comparativa.
