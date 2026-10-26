#!/usr/bin/env python3
"""
Genre-aware arrangement engine using genre_engine + hermesmusic.
Produces multi-track arrangements from a harmonic plan with explicit notes.
"""
from __future__ import annotations

import argparse
import json
import os
import random
from pathlib import Path
from typing import Dict, List, Any

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import genre_engine
from hermesmusic import (
    build_scale,
    scale_pcs,
    chord_midis,
    name_to_midi,
    midi_to_name,
    DYNAMICS,
    render_song,
)


SCALE_MAP = {
    "mayor": "mayor",
    "major": "mayor",
    "menor": "menor_natural",
    "minor": "menor_natural",
    "menor_natural": "menor_natural",
    "minor_natural": "menor_natural",
    "eolico": "menor_natural",
    "dorian": "dorico",
    "frisio": "frigio",
    "lidio": "lidico",
    "mixolidio": "mixolidio",
    "locrio": "locrio",
}


def _norm_scale(s: str) -> str:
    if not s:
        return "mayor"
    s = s.lower().strip()
    return SCALE_MAP.get(s, s)


def _role_to_program(role: str) -> int:
    r = role.lower()
    if r in ("bass", "bajo"):
        return 34
    if r in ("lead", "melody", "solo", "guitarra_solista"):
        return 27
    if r in ("guitar", "rhythm_guitar", "guitarra"):
        return 26
    if r in ("piano", "piano_acoustic", "harmony"):
        return 0
    if r in ("epiano", "electric_piano"):
        return 4
    if r in ("pad", "synth_pad"):
        return 88
    if r in ("strings", "strings_section"):
        return 48
    if r in ("violin",):
        return 40
    if r in ("cello",):
        return 42
    if r in ("brass",):
        return 56
    if r in ("arp", "arpeggio"):
        return 81
    if r in ("organ",):
        return 16
    return 0


def _role_channel(role: str) -> int:
    r = role.lower()
    if r == "bass":
        return 2
    if r == "lead":
        return 1
    if r in ("guitar", "rhythm_guitar", "piano", "harmony", "pad", "strings"):
        return 0
    return None


def _get_dynamics_for_energy(energy: float) -> str:
    if energy >= 0.9:
        return "f"
    if energy >= 0.75:
        return "mf"
    if energy >= 0.5:
        return "mp"
    if energy >= 0.3:
        return "p"
    return "pp"


class Arranger:
    def __init__(self, genre: str, key: str = "C", scale: str = "mayor",
                 variant: str = None, seed: int = 42, bpm: int = 120,
                 meter: List[int] = None):
        self.genre = genre
        self.key = key
        self.scale = _norm_scale(scale)
        self.variant = variant
        self.seed = seed
        self.bpm = bpm
        self.rng = random.Random(seed)
        try:
            self.plan = genre_engine.plan_song(genre, key=key, variant=variant,
                                               seed=seed)
        except Exception:
            # try without variant
            try:
                self.plan = genre_engine.plan_song(genre, key=key, seed=seed)
            except Exception:
                self.plan = genre_engine.plan_song(genre, key=key, variant=None, seed=seed)
        self.scale_notes = build_scale(self.key, self.scale, 4)
        self.pcs = scale_pcs(self.key, self.scale)
        if meter:
            self.plan["meter"] = meter

    def build_spec(self, roles: List[Dict[str, Any]] = None,
                   title: str = None, with_drums: bool = False) -> Dict[str, Any]:
        if roles is None:
            roles = self._default_roles()
        sections_spec = []
        meter = self.plan["meter"]
        beats_per_bar = meter[0] * 4 / meter[1]
        for si, s in enumerate(self.plan["sections"]):
            prog = [b["symbol"] for b in s["bars"]]
            section_spec = {
                "name": s["name"],
                "bars": len(s["bars"]),
                "progression": prog,
                "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5)),
            }
            melodies = []
            for role in roles:
                role_name = role["name"]
                track_name = role_name
                inst = role.get("instrument", _role_to_program(role_name))
                ch = role.get("channel", _role_channel(role_name))
                notes = []
                for bi, sym in enumerate(prog):
                    try:
                        chord_notes = chord_midis(sym, role.get("octave", 3))
                    except Exception:
                        try:
                            # try to clean
                            chord_notes = chord_midis(sym, role.get("octave", 3))
                        except Exception:
                            chord_notes = [60]
                    if role_name == "bass":
                        if chord_notes:
                            notes.append({
                                "bar": bi, "beat": 0.0, "dur": beats_per_bar,
                                "note": midi_to_name(chord_notes[0] - 12),
                                "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5))
                            })
                    elif role_name in ("pad", "strings", "choir"):
                        # create silence in some sections for dense contract if requested
                        if self.rng.random() < 0.1 and bi % 4 == 0:
                            continue
                        for j, cn in enumerate(chord_notes[:4]):
                            notes.append({
                                "bar": bi, "beat": 0.0, "dur": beats_per_bar,
                                "note": midi_to_name(cn),
                                "dynamics": "p" if s.get("energy", 0.5) < 0.6 else "mp"
                            })
                    elif role_name in ("harmony", "piano"):
                        # leave silence in at least one measure somewhere for dense
                        if si == 2 and bi == 0:  # section B first bar silence for harmonic
                            continue
                        for j, cn in enumerate(chord_notes[:3]):
                            notes.append({
                                "bar": bi, "beat": j * 0.02, "dur": beats_per_bar - 0.1,
                                "note": midi_to_name(cn),
                                "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5))
                            })
                    elif role_name in ("lead", "melody", "solo"):
                        base = chord_notes[0] if chord_notes else self.scale_notes[0]
                        # vary pattern per section
                        for k in range(4 if meter[0] == 4 else meter[0]):
                            if si % 3 == 0 and k % 2 == 1:
                                n = self.scale_notes[(bi + si + k + 2) % len(self.scale_notes)] + 12
                            elif si % 2 == 0 and k == 0:
                                n = self.scale_notes[(bi + si + k + 4) % len(self.scale_notes)] + 12
                            else:
                                n = self.scale_notes[(bi + si + k) % len(self.scale_notes)] + 12
                            notes.append({
                                "bar": bi, "beat": k * (beats_per_bar / meter[0]),
                                "dur": beats_per_bar / meter[0] * (0.8 if k % 2 == 0 else 0.6),
                                "note": midi_to_name(min(100, max(36, n))),
                                "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5))
                            })
                    elif role_name in ("arp", "arpeggio"):
                        for j, cn in enumerate(chord_notes[:4]):
                            notes.append({
                                "bar": bi, "beat": j * 0.25, "dur": 0.25,
                                "note": midi_to_name(cn + 12),
                                "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5))
                            })
                    else:
                        for j, cn in enumerate(chord_notes[:2]):
                            notes.append({
                                "bar": bi, "beat": j * 0.01, "dur": beats_per_bar,
                                "note": midi_to_name(cn),
                                "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5))
                            })
                mel = {
                    "track": track_name,
                    "instrument": inst,
                    "notes": notes,
                    "dynamics": _get_dynamics_for_energy(s.get("energy", 0.5)),
                }
                if ch is not None:
                    mel["channel"] = ch
                if notes:  # only add if has notes
                    melodies.append(mel)
            if melodies:
                section_spec["melodies"] = melodies
            sections_spec.append(section_spec)
        spec = {
            "title": title or f"{self.genre.title()} - Arrangement",
            "key": self.key,
            "scale": self.scale,
            "tempo": self.bpm,
            "meter": meter,
            "humanize": {"seed": self.seed, "velocity": 0.25, "ticks": 6},
            "sections": sections_spec,
            "tracks": [],
        }
        if with_drums:
            # build varied drum grid
            tracks = []
            section_names = [s["name"] for s in self.plan["sections"]]
            # create a drum track with variation
            grid = {}
            # basic pattern - avoid 3 simultaneous attacks
            grid["kick"] = [0.9, 0, 0, 0.6, 0, 0, 0.9, 0, 0.6, 0, 0, 0, 0.9, 0, 0, 0]
            grid["snare"] = [0, 0, 0, 0, 0.9, 0, 0, 0, 0, 0, 0, 0, 0, 0.9, 0, 0]  # moved from pos 12 to 13
            grid["hihat"] = [0.6, 0, 0.6, 0, 0.6, 0, 0.6, 0, 0.6, 0, 0.6, 0, 0.6, 0, 0.6, 0]
            # add variation - create dyn_map for different sections
            dyn_map = {}
            for i, name in enumerate(section_names):
                if i == 0:  # intro - lighter
                    dyn_map[name] = "p"
                    # lighter drums for intro
                    g2 = {
                        "kick": [[0.7, 0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0.7, -0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0.5, 0.02], [0, 0], [0, 0], [0, 0]],
                        "snare": [[0, 0], [0, 0], [0, 0], [0, 0], [0.7, 0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0.7, -0.01], [0, 0], [0, 0]],
                        "hihat": [[0.4, 0], [0, 0.02], [0.4, -0.01], [0, 0.01], [0.4, 0], [0, 0.02], [0.4, -0.01], [0, 0.01], [0.4, 0], [0, 0.02], [0.4, -0.01], [0, 0.01], [0.4, 0], [0, 0.02], [0.4, -0.01], [0, 0.01]],
                    }
                    tracks.append({
                        "role": "drums_intro",
                        "pattern": "drum_grid",
                        "grid": g2,
                        "dynamics": "mp",
                        "dyn_map": {name: "mp"},
                        "sections": [name]
                    })
                elif i == len(section_names) - 1:  # outro - lighter
                    dyn_map[name] = "p"
                    g2 = {
                        "kick": [[0.5, 0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0.4, -0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0.3, 0.02], [0, 0], [0, 0], [0, 0]],
                        "snare": [[0, 0], [0, 0], [0, 0], [0, 0], [0.4, 0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                        "hihat": [[0.3, 0], [0, 0.02], [0.3, -0.01], [0, 0.01], [0.3, 0], [0, 0.02], [0.2, -0.01], [0, 0.01], [0.2, 0], [0, 0.02], [0.2, -0.01], [0, 0.01], [0.2, 0], [0, 0.02], [0.2, -0.01], [0, 0.01]],
                    }
                    tracks.append({
                        "role": "drums_outro",
                        "pattern": "drum_grid",
                        "grid": g2,
                        "dynamics": "p",
                        "dyn_map": {name: "p"},
                        "sections": [name]
                    })
                elif 'bridge' in name.lower() or 'break' in name.lower():  # bridge/break - minimal
                    dyn_map[name] = "mp"
                    g2 = {
                        "kick": [[0.6, 0.01], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0.6, -0.01], [0, 0], [0, 0], [0, 0]],
                        "snare": [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                        "hihat": [[0.3, 0], [0, 0.02], [0.3, -0.01], [0, 0.01], [0, 0], [0, 0], [0.3, -0.01], [0, 0.01], [0, 0], [0, 0.02], [0.3, -0.01], [0, 0.01], [0.3, 0], [0, 0], [0, 0], [0, 0]],
                    }
                    tracks.append({
                        "role": "drums_bridge",
                        "pattern": "drum_grid",
                        "grid": g2,
                        "dynamics": "mp",
                        "dyn_map": {name: "mp"},
                        "sections": [name]
                    })
            # main pattern for others
            tracks.append({
                "role": "drums",
                "pattern": "drum_grid",
                "grid": grid,
                "dynamics": "mf",
                "sections": [n for n in section_names if n not in dyn_map]
            })
            spec["tracks"] = tracks
        return spec

    def _default_roles(self):
        genre = self.genre.lower()
        if genre in ("power_metal", "heavy_metal", "thrash_metal", "death_metal"):
            return [
                {"name": "bass", "instrument": 34, "octave": 2},
                {"name": "guitar", "instrument": 30, "octave": 3},
                {"name": "lead", "instrument": 27, "octave": 4},
                {"name": "strings", "instrument": 48, "octave": 4},
            ]
        if genre in ("jazz",):
            return [
                {"name": "bass", "instrument": 32, "octave": 2},
                {"name": "piano", "instrument": 0, "octave": 4},
                {"name": "lead", "instrument": 65, "octave": 5},
            ]
        if genre in ("ambient",):
            return [
                {"name": "pad", "instrument": 88, "octave": 3},
                {"name": "strings", "instrument": 48, "octave": 4},
                {"name": "piano", "instrument": 0, "octave": 4},
            ]
        if genre in ("blues",):
            return [
                {"name": "bass", "instrument": 34, "octave": 2},
                {"name": "piano", "instrument": 0, "octave": 4},
                {"name": "guitar", "instrument": 27, "octave": 4},
            ]
        return [
            {"name": "bass", "instrument": 34, "octave": 2},
            {"name": "harmony", "instrument": 0, "octave": 4},
            {"name": "lead", "instrument": 40, "octave": 5},
        ]

    def render(self, out_path: str, roles: List[Dict[str, Any]] = None, with_drums: bool = False):
        spec = self.build_spec(roles, with_drums=with_drums)
        return render_song(spec, out_path)


def main():
    p = argparse.ArgumentParser(description="Arranger engine")
    p.add_argument("--genre", required=True)
    p.add_argument("--key", default="C")
    p.add_argument("--scale", default="mayor")
    p.add_argument("--variant")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--bpm", type=int, default=120)
    p.add_argument("--out", required=True)
    p.add_argument("--roles", help="JSON file with roles")
    p.add_argument("--drums", action="store_true")
    args = p.parse_args()
    roles = None
    if args.roles:
        with open(args.roles) as f:
            roles = json.load(f)
    arr = Arranger(args.genre, key=args.key, scale=args.scale,
                   variant=args.variant, seed=args.seed, bpm=args.bpm)
    out = arr.render(args.out, roles, with_drums=args.drums)
    print(out)


if __name__ == "__main__":
    main()
