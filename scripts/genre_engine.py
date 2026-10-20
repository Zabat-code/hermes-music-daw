#!/usr/bin/env python3
"""Inspectable, seeded harmonic-form planner; NOT a genre-faithful audio generator.

Profiles prescribe *candidate* style constraints. A harmonic guide is only a
piano reference; drums, articulation, lyrics and production remain separate.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import random
import re

PROFILE_FILE = Path(__file__).resolve().parents[1] / "references" / "genre_profiles.json"
NOTES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
PITCH = {n: i for i, n in enumerate(NOTES)} | {"Db": 1, "Eb": 3, "Gb": 6, "Ab": 8, "Bb": 10}
DEGREES = {
    "I": (0, ""), "I7": (0, "7"), "Imaj7": (0, "maj7"),
    "i": (0, "m"), "iv": (5, "m"), "IV": (5, ""), "IV7": (5, "7"),
    "V": (7, ""), "V7": (7, "7"), "v": (7, "m"),
    "vi": (9, "m"), "vi7": (9, "m7"), "ii": (2, "m"), "ii7": (2, "m7"),
    "iii": (4, "m"), "iii7": (4, "m7"),
    "bII": (1, ""), "bIII": (3, ""), "bVI": (8, ""),
    "bVII": (10, ""), "bVII7": (10, "7"),
}
STRATEGIES = {
    "functional_major": (("I", "vi", "ii", "V"), ("I", "IV", "V", "I"), ("I", "iii", "IV", "V")),
    "functional_minor": (("i", "bVI", "iv", "V"), ("i", "bVII", "bVI", "V"), ("i", "iv", "V", "i")),
    "modal_dorian": (("i", "IV", "bVII", "i"), ("i", "bVII", "IV", "i"), ("i", "IV", "i", "bVII")),
    "riff_minor": (("i", "bVII", "bVI", "bVII"), ("i", "i", "bVI", "bVII"), ("i", "bVI", "bVII", "i")),
    "loop": (("I", "V", "vi", "IV"), ("vi", "IV", "I", "V"), ("I", "bVII", "IV", "I")),
    "jazz_cycle": (("Imaj7", "vi7", "ii7", "V7"), ("iii7", "vi7", "ii7", "V7")),
    "vamp": (("I", "I", "IV", "I"), ("i", "i", "bVII", "i"), ("I", "bVII", "IV", "I")),
    "blues_12": (("I7", "I7", "I7", "I7", "IV7", "IV7", "I7", "I7", "V7", "IV7", "I7", "V7"),),
    "drone": (("i", "i", "i", "i"),),
    "phrygian": (("i", "bII", "i", "bII"), ("i", "bII", "bVII", "i")),
}
CHORD = re.compile(r"^([A-G](?:#|b)?)(maj7|m7|dim|m|7)?$")


@lru_cache(maxsize=1)
def _catalog() -> dict:
    data = json.loads(PROFILE_FILE.read_text(encoding="utf-8"))
    assert data["schema_version"] == 1
    return data


def load_profiles() -> dict:
    return deepcopy(_catalog()["profiles"])


def get_profile(name: str, variant: str | None = None) -> dict:
    profiles = _catalog()["profiles"]
    if name not in profiles:
        raise ValueError(f"Género desconocido: {name}")
    profile = deepcopy(profiles[name])
    if variant:
        if variant not in profile["variants"]:
            raise ValueError(f"Variante desconocida para {name}: {variant}; disponibles: {', '.join(profile['variants'])}")
        details = profile["variants"][variant]
        profile["minimum_identity"].extend(details["minimum_identity"])
        profile["harmony_strategy"] = details["harmony_strategy"]
        profile["meter"] = details.get("meter", profile["meter"])
        profile["variant"] = variant
    return profile


def _root_key(key: str) -> str:
    bare = key[:-1] if key.endswith("m") and len(key) > 1 else key
    if bare not in PITCH:
        raise ValueError(f"Tonalidad inválida: {key}")
    return bare


def _symbol(key: str, degree: str) -> str:
    semis, suffix = DEGREES[degree]
    return NOTES[(PITCH[key] + semis) % 12] + suffix


def _user_motif(motif: list[str], key: str, strategy: str) -> tuple[str, ...]:
    if len(motif) != (12 if strategy == "blues_12" else 4):
        raise ValueError("Motivo: 4 acordes, salvo blues de 12 compases")
    by_symbol = {_symbol(key, d): d for seq in STRATEGIES[strategy] for d in seq}
    for chord in motif:
        if not CHORD.fullmatch(chord) or chord not in by_symbol:
            raise ValueError(f"Acorde ajeno a la estrategia/tonalidad: {chord}")
    return tuple(by_symbol[x] for x in motif)


def _score_sequence(reference: tuple[str, ...], candidate: tuple[str, ...],
                    strategy: str, energy: float) -> tuple[float, dict]:
    """Transparent heuristic, not a prediction of artistic preference."""
    similarity = sum(a == b for a, b in zip(reference, candidate)) / len(reference)
    roots = [DEGREES[d][0] for d in candidate]
    motion = sum(min((b - a) % 12, (a - b) % 12) for a, b in zip(roots, roots[1:]))
    avg_motion = motion / max(1, len(roots) - 1)
    dominant_share = sum(d.startswith('V') or d == 'bII' for d in candidate) / len(candidate)
    tension_fit = 1 - abs(dominant_share - energy * .4)
    stagnation = 0 if strategy in ('drone', 'vamp', 'blues_12') else sum(
        a == b for a, b in zip(candidate, candidate[1:])) / max(1, len(candidate) - 1)
    continuity = 1 - min(avg_motion, 6) / 6
    score = round(3 * similarity + continuity + tension_fit - stagnation, 4)
    return score, {'motif_similarity': round(similarity, 3),
                   'voice_leading_continuity': round(continuity, 3),
                   'tension_fit': round(tension_fit, 3),
                   'stagnation_penalty': round(stagnation, 3)}


def _vary(reference: tuple[str, ...], strategy: str, energy: float,
          rng: random.Random, excluded: set[tuple[str, ...]] | None = None) -> tuple[tuple[str, ...], int | None]:
    if strategy == 'drone':
        return reference, None
    positions = [1] if strategy == 'blues_12' else list(range(1, len(reference)-1))
    degrees = {'I7', 'IV7'} if strategy == 'blues_12' else {d for seq in STRATEGIES[strategy] for d in seq}
    candidates = []
    for idx in positions:
        for degree in sorted(degrees - {reference[idx]}):
            sequence = reference[:idx] + (degree,) + reference[idx+1:]
            if excluded and sequence in excluded:
                continue
            score, _ = _score_sequence(reference, sequence, strategy, energy)
            candidates.append((score, rng.random(), sequence, idx))
    if not candidates:
        return reference, None
    candidates.sort(reverse=True)
    top = candidates[:max(2, min(6, len(candidates)))]
    _, _, chosen, idx = rng.choice(top)
    return chosen, idx


def _contrast(reference: tuple[str, ...], strategy: str, rng: random.Random) -> tuple[str, ...]:
    options = list(STRATEGIES[strategy])
    if strategy == 'drone':
        return reference
    if strategy == 'blues_12':
        return tuple('IV7' if i == 1 else d for i, d in enumerate(reference))
    pool = [tuple(x) for x in options if len(x) == len(reference)
            and sum(a != b for a, b in zip(x, reference)) >= 2]
    if not pool:
        degrees = sorted({d for x in options for d in x})
        for a in degrees:
            for b in degrees:
                seq = (a, b) + reference[2:]
                if sum(x != y for x, y in zip(seq, reference)) >= 2:
                    pool.append(seq)
    if not pool:
        raise ValueError(f'Sin contraste armónico válido para {strategy}')
    return rng.choice(pool)


def _section(name: str, motif: str, degrees: tuple[str, ...], key: str, meter: list[int],
             energy: float, origin: str, cadence_forced: bool = False,
             changed_at: int | None = None) -> dict:
    beats = meter[0] * 4 / meter[1]
    bars = []
    for i, degree in enumerate(degrees):
        bars.append({"bar": i + 1, "degree": degree, "symbol": _symbol(key, degree),
                     "duration_beats": beats,
                     "origin": "permutación_acotada" if i == changed_at else origin})
    return {"name": name, "motif": motif, "energy": energy,
            "cadence_forced": cadence_forced, "bars": bars}


def plan_song(genre: str, key: str = "C", variant: str | None = None,
              seed: int = 0, motif: list[str] | None = None) -> dict:
    profile = get_profile(genre, variant)
    if profile["requires_choice"] and not variant:
        raise ValueError(f"{genre} es una familia/escena ambigua: indica --variant y referencia estilística")
    key = _root_key(key)
    strategy = profile["harmony_strategy"]
    rng = random.Random(seed)
    templates = STRATEGIES[strategy]
    base = _user_motif(motif, key, strategy) if motif is not None else tuple(rng.choice(templates))
    other = _contrast(base, strategy, rng)
    meter = profile["meter"]
    func = strategy.startswith("functional") or strategy == "jazz_cycle"
    sections = [_section("intro", "intro", base[:2], key, meter, .25, "apertura")]
    sections.append(_section("A", "A", base, key, meter, .63, "motivo_inicial"))
    sections.append(_section("B", "B", other, key, meter, .78, "contraste", cadence_forced=func))
    used_returns: set[tuple[str, ...]] = set()
    def return_variant(name: str, energy: float) -> dict:
        seq, idx = _vary(base, strategy, energy, rng, used_returns)
        used_returns.add(seq)
        return _section(name, "A", seq, key, meter, energy,
                        "retorno_del_motivo", changed_at=idx)
    sections.append(return_variant("A_prima", .73))
    bridge = tuple(reversed(other)) if strategy not in ("blues_12", "drone") else other
    if func and len(bridge) >= 4:
        bridge = bridge[:-2] + (("ii", "V") if strategy == "functional_major" else ("iv", "V") if strategy == "functional_minor" else ("ii7", "V7"))
    sections.append(_section("puente", "C", bridge, key, meter, .86, "puente", cadence_forced=func))
    sections.append(return_variant("A_final", .95))
    ending = ("V", "I") if strategy == "functional_major" else ("V", "i") if strategy == "functional_minor" else ("V7", "Imaj7") if strategy == "jazz_cycle" else base[-2:]
    sections.append(_section("coda", "coda", ending, key, meter, .35,
                             "cierre", cadence_forced=func))
    for s in sections:
        degrees = tuple(b["degree"] for b in s["bars"])
        comparison = base[:len(degrees)] if len(degrees) <= len(base) else base
        s["score"], s["score_components"] = _score_sequence(comparison, degrees, strategy, s["energy"])
        s["transformations"] = [
            {"bar": i+1, "before": prior, "after": new}
            for i, (prior, new) in enumerate(zip(comparison, degrees)) if prior != new
        ]
    return {"schema_version": 1, "profile_id": genre, "variant": variant,
            "strategy": strategy, "key": key, "meter": meter, "seed": seed,
            "genre_claim": "guía de armonía, NO canción terminada del género",
            "verified_audio": False, "required_roles": profile["required_roles"],
            "minimum_identity": profile["minimum_identity"],
            "sections": sections}


def export_harmony_midi(song: dict, path: str | Path) -> Path:
    """Render a plain keyboard chord guide; never certify genre from this file."""
    import mido
    path = Path(path).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    bpm = 120
    beats = song["meter"][0] * 4 / song["meter"][1]
    midi = mido.MidiFile(ticks_per_beat=480)
    meta = mido.MidiTrack([mido.MetaMessage("track_name", name="Guia_armonica_NO_genero_final"),
                           mido.MetaMessage("time_signature", numerator=song["meter"][0], denominator=song["meter"][1]),
                           mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm))])
    midi.tracks.append(meta)
    events = []; start = 0
    for section in song["sections"]:
        for bar in section["bars"]:
            m = CHORD.fullmatch(bar["symbol"])
            if not m:
                raise ValueError(f"Acorde inválido en planificación: {bar['symbol']}")
            root, quality = m.groups()
            intervals = [0, 3, 6] if quality == "dim" else [0, 3, 7] if quality in ("m", "m7") else [0, 4, 7]
            if quality in ("7", "m7", "maj7"): intervals.append(11 if quality == "maj7" else 10)
            ticks = round(bar["duration_beats"] * midi.ticks_per_beat)
            for n in intervals:
                pitch = 48 + PITCH[root] + n
                events.extend([(start, 1, mido.Message("note_on", note=pitch, velocity=60, channel=0)),
                               (start + ticks - 12, 0, mido.Message("note_off", note=pitch, velocity=0, channel=0))])
            start += ticks
    track = mido.MidiTrack([mido.MetaMessage("track_name", name="Piano_guide_only"),
                            mido.Message("program_change", channel=0, program=0)])
    last = 0
    for tick, _, msg in sorted(events, key=lambda x: (x[0], x[1], x[2].note)):
        track.append(msg.copy(time=tick - last));last = tick
    midi.tracks.append(track)
    midi.save(path)
    return path


def to_hermes_spec(song: dict, tracks: list[dict]) -> dict:
    """Opt-in bridge. Existing renderer only plays four-beat, one-chord bars."""
    if song["meter"] != [4, 4]:
        raise ValueError("El renderer HermesMusic actual no soporta este compás; usar guía MIDI")
    if not tracks:
        raise ValueError("Proporcionar instrumentación explícita; género no crea pistas")
    return {"title": f"borrador_{song['profile_id']}_NO_VALIDADO", "key": song["key"],
            "bpm": 120, "meter": song["meter"], "genre": song["profile_id"],
            "sections": [{"name": s["name"], "bars": len(s["bars"]),
                          "progression": [b["symbol"] for b in s["bars"]]} for s in song["sections"]],
            "tracks_global": tracks}


def _cli() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("list", "profile", "plan", "guide"))
    parser.add_argument("--genre", help="Id exacto de genre_profiles.json")
    parser.add_argument("--variant")
    parser.add_argument("--key", default="C")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--motif", help="Cuatro acordes CSV; doce para blues")
    parser.add_argument("--out", type=Path, help="Para guide: ruta .mid; para plan: .json")
    args = parser.parse_args()
    if args.command == "list":
        print("\n".join(load_profiles()));return
    if not args.genre:parser.error("Falta --genre")
    if args.command == "profile":
        print(json.dumps(get_profile(args.genre, args.variant), ensure_ascii=False, indent=2));return
    motif = args.motif.split(",") if args.motif else None
    song = plan_song(args.genre, key=args.key, variant=args.variant, seed=args.seed, motif=motif)
    if args.command == "guide":
        if not args.out:parser.error("guide requiere --out RUTA.mid")
        export_harmony_midi(song, args.out)
        print(f"Guía armónica (NO canción {args.genre} terminada): {args.out}");return
    text = json.dumps(song, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n", encoding="utf-8")
        print(args.out)
    else:print(text)


if __name__ == "__main__":
    _cli()
