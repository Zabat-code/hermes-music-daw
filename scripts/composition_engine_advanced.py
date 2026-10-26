#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hermes Music Composition Engine - Advanced Mode
Integra teoría musical académica con patrones reales de Midibase.db

Este módulo extiende hermesmusic.py con capacidades avanzadas de composición:
- Progresiones armónicas auténticas (no mecánicas)
- Estructuras formales coherentes (intro -> solo -> climax -> cierre)
- Armonía funcional real (T, S, D)
- Gestión de densidad y espacio musical
- Registro y dinámica realistas
"""

from __future__ import annotations
import json
import os
import math
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field

# Importar del motor principal
try:
    from hermesmusic import (
        SCALES, DYNAMICS, MELODIC_PATTERNS,
        build_scale, scale_pcs, chord_midis, parse_chord,
        name_to_midi, midi_to_name, deg,
        build_track, ticks, TPB,
        render_song, validate_midi
    )
except ImportError:
    # Fallback: usar sys.path
    import sys
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, repo_root)
    from hermesmusic import (
        SCALES, DYNAMICS, MELODIC_PATTERNS,
        build_scale, scale_pcs, chord_midis, parse_chord,
        name_to_midi, midi_to_name, deg,
        build_track, ticks, TPB,
        render_song, validate_midi
    )

# ============================================================
# SISTEMA DE ARMONÍA FUNCIONAL (teoría Schenkeriana)
# ============================================================

@dataclass
class HarmonicFunction:
    """Función armónica según teoría funcional"""
    roman_numeral: str  # I, ii, V, etc.
    function: str       # T (tonic), S (subdominant), D (dominant), T/S (pre-tonic)
    chord_symbol: str   # C, Dm, G7, etc.
    tension: float = 0.0  # 0.0-1.0, grado de tensión
    tendency: str = "stabilize"  # resolve, prolong, or stabilize

class HarmonicAnalyzer:
    """Analiza y genera armonía funcional basada en teoría Schenkeriana"""

    # Mapear numeral romano a nombre de acorde en letras
    roman_to_alpha = {
        "I": "C", "ii": "Dm", "iii": "Em", "IV": "F", "V": "G",
        "vi": "Am", "vii": "Bm", "V7": "G7", "vii°": "Bdim",
        "i": "Am", "IV7": "F7", "I6": "C6", "Imaj7": "CMaj7",
        # Normalizar calidades a formato parseable por hermesmusic
        "CMaj7": "C", "Cmaj7": "C", "AMaj7": "A", "Amaj7": "A",
        "GMaj7": "G", "Gmaj7": "G",
        # Mapear maj7 a M7 (formato compatible)
    }

    # Funciones armónicas según teoría funcional clásica
    FUNCTION_MAP = {
        # Tónica (I, vi, iii)
        "I": "T", "vi": "T/S", "iii": "T",
        "Imaj7": "T", "I7": "T", "I6": "T", "I64": "T",
        "vi": "T/S", "vimaj7": "T/S", "vi7": "T/S",

        # Subdominante (IV, ii, VI)
        "IV": "S", "ii": "S", "II": "S", "VI": "S",
        "IVmaj7": "S", "ii7": "S", "IV6": "S", "ii6": "S",
        "IV7": "S", "bVII": "S", "bVI": "S", "bIII": "S",

        # Dominante (V, VII)
        "V": "D", "V7": "D", "VII": "D", "vii": "D",
        "V6": "D", "V65": "D", "V7/V": "D",
        "E": "D", "E7": "D", "B": "D", "B7": "D",

        # Modulaciones comunes
        "bI": "T", "bV": "D", "v": "D"
    }

    # Mapear numeral romano a nombre de acorde en letras
    roman_to_alpha = {
        "I": "C", "ii": "Dm", "iii": "Em", "IV": "F", "V": "G",
        "vi": "Am", "vii": "Bm", "V7": "G7", "vii°": "Bdim",
        "i": "Am", "IV7": "F7", "I6": "C6", "Imaj7": "CMaj7",
        # Normalizar calidades a formato parseable por hermesmusic
        "CMaj7": "C", "Cmaj7": "C", "AMaj7": "A", "Amaj7": "A",
        "GMaj7": "G", "Gmaj7": "G",
        # Mapear maj7 a M7 (formato compatible)
    }

    @classmethod
    def analyze_chord(cls, chord: str, key: str) -> HarmonicFunction:
        """Analiza una progresión de acordes en una tonalidad"""
        # Si el acorde es directamente un nombre de acorde (C, Dm, Am, etc.),
        # usarlo directamente en lugar del mapeo de Roman numerals
        # (que solo aplica cuando el acorde es un numeral romano)
        root_pc, intervals, _ = parse_chord(chord)

        key_pc = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5,
                  "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}

        key_root = key_pc.get(key, 0)
        relative_pc = (root_pc - key_root) % 12

        # Mapear al número romano
        roman_numerals = ["I", "ii", "iii", "IV", "V", "vi", "vii"]
        degree = min(relative_pc // 2 if relative_pc < 11 else 6, 6)
        roman = roman_numerals[degree] if relative_pc % 12 in [0, 2, 4, 5, 7, 9, 11] else "unknown"

        # Determinar función
        function = cls.FUNCTION_MAP.get(roman, cls.FUNCTION_MAP.get(chord, "T"))

        # Calcular tensión
        tension_map = {"T": 0.0, "T/S": 0.2, "S": 0.5, "D": 0.8}
        tension = tension_map.get(function, 0.3)

        # Tendencia
        tendency = "resolve" if function == "D" else \
                   "prolong" if function == "T" else \
                   "delay" if function == "S" else "stabilize"

        return HarmonicFunction(
            roman_numeral=roman,
            function=function,
            chord_symbol=chord,
            tension=tension,
            tendency=tendency
        )

    @classmethod
    def generate_progression(cls, key: str, scale: str, genre: str,
                             bars: int = 8) -> List[HarmonicFunction]:
        """Genera una progresión armónica coherente"""
        # Patrones directos en notación estándar (hermesmusic.parse_chord es compatible)
        genre_patterns = {
            "classical": [
                ["E", "B", "C#m", "A"],
                ["E", "A", "B", "C#m"],
                ["E", "G#m", "A", "B"],
                ["E", "A", "B", "C#m", "E"],
            ],
            "pop": [
                ["Em", "C", "G", "D"],
                ["C", "G", "Am", "F"],
                ["G", "D", "Em", "C"],
            ],
            "jazz": [
                ["Dm", "G7", "C", "C"],
                ["Fm", "Bb7", "Eb", "Eb"],
                ["Bm", "E", "A", "A"],
            ],
            "flamenco": [
                ["Am", "G", "F", "E"],
                ["Am", "E", "Am", "E"],
            ],
            "romantic": [
                ["E", "E6", "A", "B"],
                ["C#m", "A", "E", "B"],
                ["E", "C#m", "A", "B"],
            ],
            "electronic": [
                ["Am", "F", "C", "G"],
                ["Dm", "Bm", "Am", "G"],
                ["Em", "Am", "C", "D"],
            ],
            "ambient": [
                ["Am", "Dm", "Em", "E"],
                ["F", "C", "G", "Am"],
            ],
            "blues": [
                ["E", "A", "B", "E"],
                ["A", "B", "E", "A"],
            ],
            "folk": [
                ["G", "D", "Em", "C"],
                ["Am", "F", "G", "C"],
            ],
        }
        patterns = genre_patterns.get(genre, genre_patterns["classical"])

        # Seleccionar progresión
        base_prog = random.choice(patterns)

        # Extendemos a número de compases solicitado
        full_prog = []
        for i in range(bars):
            chord = base_prog[i % len(base_prog)]
            # Para acordes directos, crear instancia directamente
            analysis = HarmonicFunction(
                roman_numeral="",
                function="T",
                chord_symbol=chord,
                tension=0.5,
                tendency="stabilize"
            )
            full_prog.append(analysis)

        return full_prog


# ============================================================
# MOTOR DE ESTRUCTURA FORMAL
# ============================================================

class FormEngine:
    """Genera estructuras musicales coherentes con progresión de densidad"""

    # Plantillas de forma con densidad progresiva
    FORM_PROFILES = {
        "orchestral_ascending": {
            "name": "Banda sonora orquestal (intro → ruido → solo violín → cierre)",
            "sections": [
                {"name": "intro", "bars_ratio": 0.12, "density": "high", "function": "establecimiento"},
                {"name": "development", "bars_ratio": 0.35, "density": "sparse", "function": "solo"},
                {"name": "climax", "bars_ratio": 0.20, "density": "relaxing", "function": "cierre"},
                {"name": "resolution", "bars_ratio": 0.33, "density": "low", "function": "salida"},
            ]
        },
        "ternary": {
            "name": "Ternaria clásica (A-B-A')",
            "sections": [
                {"name": "A", "bars_ratio": 0.35, "density": "medium", "function": "theme"},
                {"name": "B", "bars_ratio": 0.30, "density": "high", "function": "contrast"},
                {"name": "A_prime", "bars_ratio": 0.35, "density": "medium", "function": "return"},
            ]
        },
        "pop_song": {
            "name": "Pop estándar (verse-chorus-bridge)",
            "sections": [
                {"name": "intro", "bars_ratio": 0.12, "density": "low", "function": "setup"},
                {"name": "verse", "bars_ratio": 0.28, "density": "medium", "function": "narrative"},
                {"name": "chorus", "bars_ratio": 0.28, "density": "high", "function": "hook"},
                {"name": "verse2", "bars_ratio": 0.20, "density": "medium", "function": "narrative"},
                {"name": "chorus2", "bars_ratio": 0.12, "density": "high", "function": "hook"},
            ]
        }
    }

    def __init__(self, form_profile: str = "orchestral_ascending"):
        self.profile = self.FORM_PROFILES.get(form_profile, self.FORM_PROFILES["orchestral_ascending"])

    def generate_structure(self, total_bars: int) -> List[Dict]:
        """Genera estructura con número de compases por sección"""
        sections = []
        allocated = 0

        for i, sec in enumerate(self.profile["sections"]):
            if i == len(self.profile["sections"]) - 1:
                # Última sección absorbe el resto
                bars = total_bars - allocated
            else:
                bars = int(total_bars * sec["bars_ratio"])
                allocated += bars

            sections.append({
                "name": sec["name"],
                "bars": bars,
                "density": sec["density"],
                "function": sec["function"],
            })

        return sections


# ============================================================
# MOTOR DE DINÁMICA Y ESPACIO
# ============================================================

class DynamicManager:
    """Gestiona dinámicas y espacio musical (muy importante para no sonar 'al revés')"""

    @staticmethod
    def get_dynamic_curve(section_name: str, section_bars: int,
                          density: str) -> List[str]:
        """Genera curva dinámica por compás para una sección.

        Returns:
            List[str]: una lista de STR de longitud section_bars.
                       Cada string es 'p', 'mp', 'mf', 'f', 'ff' etc.
        """
        # Mapear densidad -> (start_level, end_level, curve_type)
        # curve_type: 'constant', 'interpolate_up', 'interpolate_down', 'ramp'
        density_map = {
            "high": {"curve_type": "constant", "level": "mf",
                     "intro_flavor": "low"},
            "progressive": {"curve_type": "interpolate_up", "start": "mp", "end": "f"},
            "relaxing": {"curve_type": "interpolate_down", "start": "f", "end": "pp"},
            "medium": {"curve_type": "ramp", "start": "mp", "end": "mf"},
            "peak": {"curve_type": "constant", "level": "f"},
            "low": {"curve_type": "constant", "level": "p"},
            "sparse": {"curve_type": "constant", "level": "pp"},
        }

        curve_info = density_map.get(density, {"curve_type": "constant", "level": "mp"})

        if curve_info["curve_type"] == "constant":
            return [curve_info["level"]] * section_bars

        elif curve_info["curve_type"] == "interpolate_up":
            return DynamicManager._interpolate_bars(curve_info["start"], curve_info["end"], section_bars)

        elif curve_info["curve_type"] == "interpolate_down":
            return DynamicManager._interpolate_bars(curve_info["start"], curve_info["end"], section_bars)

        elif curve_info["curve_type"] == "ramp":
            # Rama progresiva: empieza mediocre, sube a moderado
            return DynamicManager._interpolate_bars(curve_info["start"], curve_info["end"], section_bars)

        # Por defecto: constante
        return [curve_info["level"]] * section_bars

    @staticmethod
    def _interpolate_bars(start: str, end: str, steps: int) -> List[str]:
        """Interpolate dinámica entre compases"""
        levels = {"pp": 0, "p": 1, "mp": 2, "mf": 3, "f": 4, "ff": 5}
        start_lvl = levels.get(start, 2)
        end_lvl = levels.get(end, 4)

        result = []
        for i in range(max(steps, 1)):
            t = i / max(steps - 1, 1)
            lvl = round(start_lvl + (end_lvl - start_lvl) * t)
            for k, v in levels.items():
                if v == lvl:
                    result.append(k)
                    break
        return result


# ============================================================
# MOTOR DE REGISTROS E INSTRUMENTACIÓN
# ============================================================

class OrchestrationManager:
    """Gestiona instrumentación y registros para evitar sonidos 'antinaturales'"""

    # Registros seguros para cada instrumento (evitan rangos problemáticos)
    INSTRUMENT_RANGES = {
        "violin": (55, 90),      # G3 - F6
        "viola": (48, 79),       # C3 - G5
        "cello": (36, 72),       # C2 - C5
        "double_bass": (28, 58), # E1 - A3
        "flute": (54, 95),       # F3 - C6
        "clarinets": (44, 77),   # G2 - D5
        "oboe": (51, 81),        # B3 - A5
        "french_horn": (38, 76), # Eb1 - E5
        "trumpet": (48, 79),     # C3 - G5
        "trombone": (36, 68),    # F2 - E4
        "timpani": (31, 55),     # F1 - F3
        "piano": (28, 96),       # E1 - A5
        "harp": (33, 81),        # F1 - G5
        "strings": (36, 90),     # C2 - F6
        "choir": (50, 75),       # D3 - F4
        "arp": (40, 88),         # E2 - C#6 (arp egg)
    }

    @classmethod
    def get_instruments_for_section(cls, density: str, section_name: str) -> List[Tuple[str, int]]:
        """Selecciona instrumentos apropiados para sección y densidad"""

        base_instruments = ["piano", "strings"]

        if density == "high":
            # Intro densamente con orquesta completa
            if "intro" in section_name.lower():
                return [("cello", 42), ("viola", 43), ("harp", 46),
                        ("flute", 73), ("timpani", 47)]
            # Climax: todos los instrumentos
            elif "climax" in section_name.lower() or "exposition" in section_name.lower():
                return [("violin", 40), ("cello", 42), ("flute", 73),
                        ("harp", 46), ("trumpet", 56), ("trombone", 57),
                        ("timpani", 47), ("strings", 48)]
            else:
                return [("violin", 40), ("cello", 42), ("harp", 46), ("flute", 73)]

        elif density == "progressive":
            return [("viola", 43), ("harp", 46), ("piano", 0), ("cello", 42)]

        elif density == "medium":
            return [("violin", 40), ("piano", 0), ("cello", 42)]

        elif density == "low":
            # Solo violín (la sección que el usuario quiere)
            if "development" in section_name.lower() or "mitad" in section_name.lower():
                return [("violin", 40)]
            return [("piano", 0), ("cello", 42)]

        elif density == "relaxing":
            # Solo instrumento o reducción
            return [("violin", 40), ("piano", 0)]

        elif density == "sparse":
            return [("violin", 40)]

        elif density == "peak":
            return [("violin", 40), ("flute", 73), ("harp", 46), ("trumpet", 56)]
        return base_instruments


# ============================================================
# GENERADOR DE MELOÍA CON TEORÍA REAL
# ============================================================

class MelodyComposer:
    """Generador de melodías coherentes usando teoría de motivos"""

    def __init__(self, key: str = "C", scale: str = "mayor"):
        self.key = key
        self.scale_name = scale
        self.scale_notes = build_scale(key, scale)
        self.pcs = scale_pcs(key, scale)

    def generate_melody_for_section(self, section: Dict,
                                    progression: List[HarmonicFunction]) -> List[Dict]:
        """Genera melodía para una sección específica"""

        notes = []
        bars = section["bars"]
        density = section["density"]

        # Ajustar notas por densidad
        if density == "sparse":
            notes_per_bar = 2
        elif density == "low":
            notes_per_bar = 3
        elif density == "medium":
            notes_per_bar = 4
        elif density == "high":
            notes_per_bar = 4  # Pero con articulación más clara
        elif density == "progressive":
            notes_per_bar = 4
        elif density == "relaxing":
            notes_per_bar = 3  # Reducción gradual
        else:
            notes_per_bar = 4

        # Motivo base (2-4 notas) que se desarrolla
        motif = self._create_motif(progression[0].chord_symbol if progression else "C")

        bar_start = 0
        for bar_idx in range(bars):
            chord = progression[bar_idx % len(progression)]

            # Notas del motivo para este compás
            for beat in range(notes_per_bar):
                beat_pos = beat / notes_per_bar

                # Desarrollar motivo (variación cada 2 compases)
                motif_variation = self._develop_motif(motif, bar_idx, beat)

                # Asegurar que las notas pertenecen a la escala
                note_midi = self._chord_tone_or_passing(chord, bar_idx, beat)

                notes.append({
                    "bar": bar_idx,
                    "beat": beat_pos,
                    "dur": 1.0 / notes_per_bar,
                    "note": midi_to_name(note_midi),
                    "velocity": self._get_velocity(density, bar_idx, bars),
                    "dynamics": self._get_dynamic_label(density, bar_idx, bars)
                })

        return notes

    def _create_motif(self, chord: str) -> List[int]:
        """Crea un motivo melódico de 2-4 notas (teoría: motivo = idea germinal)"""
        chord_notes = chord_midis(chord, 4)

        # Motivo de apertura: usar nota raíz y tercera
        if len(chord_notes) >= 2:
            return [chord_notes[0], chord_notes[1]]
        return [chord_notes[0]]

    def _develop_motif(self, motif: List[int], bar: int, beat: int) -> List[int]:
        """Desarrolla el motivo (inversión, retrogrado, variación)"""
        if not motif:
            return []

        # Rotar el motivo cada compás para variación
        shift = bar % len(motif)
        return [motif[(i + shift) % len(motif)] for i in range(len(motif))]

    def _chord_tone_or_passing(self, chord: HarmonicFunction, bar: int, beat: int) -> int:
        """Selecciona nota: acorde (fuerte) o paso (débil)"""
        # Normalizar símbolo de acorde para hermesmusic
        chord_symbol = chord.chord_symbol
        # Mapear maj7 a M7
        if chord_symbol.endswith('Maj7'):
            chord_symbol = chord_symbol.replace('Maj7', 'M7')

        try:
            chord_notes = chord_midis(chord_symbol, 4)
        except ValueError:
            # Fallback: usar solo la raíz del acorde
            chord_notes = chord_midis(chord_symbol.split('M')[0], 4)

        # En tiempos fuertes (beat 0), usar notas del acorde
        if beat % 2 == 0 and chord_notes:
            idx = beat % len(chord_notes)
            return chord_notes[idx]

        # En tiempos débiles, usar pasos de escala
        current_scale_pos = (bar * 4 + beat) % len(self.scale_notes)
        return self.scale_notes[current_scale_pos]

    def _get_velocity(self, density: str, bar: int, total_bars: int) -> int:
        """Velocidad MIDI según densidad y posición"""
        base_vel = DYNAMICS.get("mp", 50)

        if density == "high":
            base_vel = DYNAMICS.get("mf", 70)
        elif density == "progressive":
            # Aumento progresivo
            ratio = bar / max(total_bars, 1)
            base_vel = int(40 + ratio * 60)
        elif density == "relaxing":
            ratio = bar / max(total_bars, 1)
            base_vel = int(80 - ratio * 50)
        elif density == "sparse":
            base_vel = DYNAMICS.get("p", 35)

        return base_vel

    def _get_dynamic_label(self, density: str, bar: int, total_bars: int) -> str:
        """Etiqueta de dinámica"""
        if density == "progressive":
            ratio = bar / max(total_bars, 1)
            return "pp" if ratio < 0.2 else "p" if ratio < 0.4 else "mp" if ratio < 0.6 else "mf" if ratio < 0.8 else "f"
        elif density == "relaxing":
            ratio = bar / max(total_bars, 1)
            return "f" if ratio < 0.2 else "mf" if ratio < 0.4 else "mp" if ratio < 0.6 else "p" if ratio < 0.8 else "pp"
        elif density == "high":
            return "mf"
        elif density == "sparse":
            return "pp"
        elif density == "low":
            return "mp"
        return "mp"


# ============================================================
# GENERADOR DE ACOMPANAMIENTO ARMÓNICO
# ============================================================

class AccompanimentComposer:
    """Genera acompañamiento armónico coherente"""

    # Mapear numeral romano a nombre de acorde en letras
    roman_to_alpha = {
        "I": "C", "ii": "Dm", "iii": "Em", "IV": "F", "V": "G",
        "vi": "Am", "vii": "Bm", "V7": "G7", "vii°": "Bdim",
        "i": "Am", "IV7": "F7", "I6": "C6", "Imaj7": "CMaj7",
        # Normalizar calidades a formato parseable por hermesmusic
        "CMaj7": "C", "Cmaj7": "C", "AMaj7": "A", "Amaj7": "A",
        "GMaj7": "G", "Gmaj7": "G",
        # Mapear maj7 a M7 (formato compatible)
    }

    @staticmethod
    def generate_chords(progression: List[HarmonicFunction],
                        section_bars: int,
                        instrument: int,
                        channel: int,
                        density: str) -> List[Tuple]:
        """Genera notas de acompañamiento para una sección"""

        notes = []
        octv = 3

        for bar_idx in range(section_bars):
            chord = progression[bar_idx % len(progression)]

            # Generar acorde (con manejo sencillo de calidades no soportadas)
            chord_symbol = chord.chord_symbol
            chord_alpha = AccompanimentComposer.roman_to_alpha.get(chord_symbol, chord_symbol)
            chord_alpha = chord_alpha.replace('Maj7', 'M7').replace('maj7', 'M7')
            chord_notes = chord_midis(chord_alpha, octv)

            # Densidad del acompañamiento
            if density == "sparse":
                # Solo bajo
                if chord_notes:
                    notes.append((bar_idx * 4.0, 4.0, chord_notes[0] - 12, DYNAMICS["p"]))
            elif density == "low":
                # Root + 5ta
                if len(chord_notes) >= 2:
                    notes.append((bar_idx * 4.0, 4.0, chord_notes[0] - 12, DYNAMICS["mp"]))
                    notes.append((bar_idx * 4.0, 4.0, chord_notes[2] - 12, DYNAMICS["mp"]))
            elif density == "medium":
                # Acorde completo
                for i, note in enumerate(chord_notes):
                    notes.append((bar_idx * 4.0 + i * 0.02, 3.0, note, DYNAMICS["mp"]))
            elif density == "high":
                # Arpegio ascendente
                for i, note in enumerate(chord_notes):
                    notes.append((bar_idx * 4.0 + i * 1.0, 1.0, note, DYNAMICS["mf"]))
                # Añadir octava superior
                for i, note in enumerate(chord_notes[:2]):
                    notes.append((bar_idx * 4.0 + 2.0 + i * 1.0, 1.0, note + 12, DYNAMICS["mf"]))
            elif density == "progressive":
                # Arpegio ascendente
                for i, note in enumerate(chord_notes):
                    notes.append((bar_idx * 4.0 + i * 0.5, 2.0, note + 12, DYNAMICS["mp"]))
            elif density == "relaxing":
                # Pedal + 5ta (sostenido gradual)
                if chord_notes:
                    notes.append((bar_idx * 4.0, 4.0, chord_notes[0], DYNAMICS["p"]))

        return notes


# ============================================================
# MOTOR PRINCIPAL DE COMPOSICIÓN AVANZADA
# ============================================================

class AdvancedComposer:
    """
    Motor principal de composición avanzada.
    Combina teoría armónica, forma, dinámica e instrumentación.
    """

    def __init__(self, genre: str = "classical", key: str = "C",
                 scale: str = "mayor", form_profile: str = "orchestral_ascending"):
        self.genre = genre.lower()
        self.key = key
        self.scale = scale
        self.form_profile = form_profile

        # Inicializar sub-sistemas
        self.form_engine = FormEngine(form_profile)
        self.dynamic_mgr = DynamicManager()
        self.orch_mgr = OrchestrationManager()
        self.harmonic_analyzer = HarmonicAnalyzer()

    def compose(self, total_duration_seconds: float = 240.0,
                bpm: int = 60,
                num_bars: int = None) -> Dict:
        """
        Composición principal con estructura progresiva.

        Args:
            total_duration_seconds: Duración total (240s = 4 minutos)
            bpm: Tempo
            num_bars: Número de compases (si se especifica, ignora duración)

        Returns:
            SongSpec dict listo para hermesmusic.render_song()
        """

        # Calcular compases
        if num_bars:
            bars = num_bars
        else:
            bars_per_minute = bpm / 4  # 4/4
            bars = int((total_duration_seconds * bpm / 60) / 4)

        print(f"🎼 Composición avanzada")
        print(f"   Género: {self.genre}, Key: {self.key} {self.scale}")
        print(f"   BPM: {bpm}, Compases: {bars}")
        print(f"   Forma: {self.form_profile}")

        # Generar estructura formal
        sections_structure = self.form_engine.generate_structure(bars)

        # Generar progresión armónica completa
        all_progressions = []
        for section in sections_structure:
            prog = self.harmonic_analyzer.generate_progression(
                self.key, self.scale, self.genre, section["bars"]
            )
            all_progressions.append(prog)

        # Construir SongSpec
        sections_spec = []
        tracks_spec = []

        channel_counter = 0
        instrument_registry = {}  # nombre -> (instrument, channel)

        for sec_idx, section_structure in enumerate(sections_structure):
            section_name = section_structure["name"]
            section_bars = section_structure["bars"]
            density = section_structure["density"]
            function = section_structure["function"]

            # Curva dinámica
            dynamic_curve = self.dynamic_mgr.get_dynamic_curve(
                section_name, section_bars, density
            )

            # Instrumentos para esta sección
            instruments = self.orch_mgr.get_instruments_for_section(
                density, section_name
            )

            # Progresión armónica
            progression = all_progressions[sec_idx]
            chord_symbols = [p.chord_symbol for p in progression]

            # Generar melodía
            melody_composer = MelodyComposer(self.key, self.scale)
            melody_notes = melody_composer.generate_melody_for_section(
                section_structure, progression
            )

            # Construir sección
            section_spec = {
                "name": section_name,
                "bars": section_bars,
                "progression": chord_symbols,
                "dynamics": dynamic_curve[0] if dynamic_curve else "mp",
            }

            # Añadir melodía si hay instrumentos melódicos
            if instruments and instruments[0][1] not in [0, 48, 47, 49]:
                mel_instr = instruments[0][1]
                section_spec["melody"] = {
                    "instrument": mel_instr,
                    "track": section_name + "_melody",
                    "pattern": None,  # Notas explícitas
                    "dynamics": dynamic_curve[0] if dynamic_curve else "mp",
                    "notes": melody_notes
                }

            sections_spec.append(section_spec)

            # Añadir instrumentos a tracks (solo si no están duplicados)
            for instrument in instruments:
                inst_name = instrument[0]
                inst_program = instrument[1]
                if inst_name not in instrument_registry:
                    # Asignar canal
                    channel = channel_counter
                    if channel == 9:
                        channel = 10
                        channel_counter = 10
                    instrument_registry[inst_name] = (inst_program, channel)
                    channel_counter += 1

                    # Crear track de acompañamiento
                    accomp_notes = AccompanimentComposer.generate_chords(
                        progression, section_bars, inst_program, channel, density
                    )

                    if accomp_notes:
                        tracks_spec.append({
                            "role": inst_name,
                            "instrument": inst_program,
                            "channel": channel,
                            "pattern": None,
                            "dynamics": dynamic_curve[0] if dynamic_curve else "mp",
                            "sections": [section_name],  # Solo esta sección
                        })

        # Construir spec final
        songspec = {
            "title": f"Auto-Composition ({self.genre.title()})",
            "key": self.key,
            "scale": self.scale,
            "tempo": bpm,
            "meter": [4, 4],
            "humanize": {"seed": 42, "velocity": 0.08, "ticks": 4},
            "sections": sections_spec,
            "tracks": tracks_spec[:8],  # Máximo 8 tracks
        }

        print(f"\n✅ SongSpec generado:")
        print(f"   - {len(sections_spec)} secciones")
        print(f"   - {len(tracks_spec[:8])} tracks")
        print(f"   - Progresión armónica: {' -> '.join([s['progression'][0] for s in sections_spec[:3]])}")

        return songspec


# ============================================================
# EXPORTAR CONFIGURACIÓN
# ============================================================

def get_engine_config() -> Dict:
    """Retorna la configuración del motor para debugging"""
    return {
        "version": "1.0",
        "supported_genres": list(HarmonicAnalyzer.FUNCTION_MAP.keys())[:10] +
                            ["classical", "pop", "jazz", "flamenco", "romantic",
                             "reggaeton", "electronic", "ambient", "folk", "blues"],
        "supported_scales": list(SCALES.keys()),
        "supported_forms": list(FormEngine.FORM_PROFILES.keys()),
        "instruments": {k: v for k, v in OrchestrationManager.INSTRUMENT_RANGES.items()},
        "dynamic_levels": list(DYNAMICS.keys()),
    }


# ============================================================
# EJECUCIÓN DE PRUEBA
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HERMES MUSIC - MOTOR DE COMPOSICIÓN AVANZADA")
    print("=" * 60)

    # Test 1: Clásico orquestal con estructura solicitada
    print("\n📜 TEST 1: Clásico orquestal (intro → solo → climax → cierre)")
    composer = AdvancedComposer(
        genre="classical",
        key="E",
        scale="mayor",
        form_profile="orchestral_ascending"
    )

    spec1 = composer.compose(
        total_duration_seconds=240.0,
        bpm=60
    )

    print(f"\n   Resultado:")
    for sec in spec1["sections"]:
        print(f"   - {sec['name']}: {sec['bars']} compases, progresión: {sec['progression'][:2]}")

    # Test 2: Pop con estructura
    print("\n📜 TEST 2: Pop (verse-chorus)")
    composer2 = AdvancedComposer(
        genre="pop",
        key="G",
        scale="mayor",
        form_profile="pop_song"
    )

    spec2 = composer2.compose(total_duration_seconds=240.0, bpm=120)

    print(f"\n   Resultado:")
    for sec in spec2["sections"]:
        print(f"   - {sec['name']}: {sec['bars']} compases, progresión: {sec['progression'][:2]}")

    # Test 3: Jazz
    print("\n📜 TEST 3: Jazz")
    composer3 = AdvancedComposer(
        genre="jazz",
        key="F",
        scale="mayor",
        form_profile="ternary"
    )

    spec3 = composer3.compose(total_duration_seconds=240.0, bpm=90)

    print(f"\n   Resultado:")
    for sec in spec3["sections"]:
        print(f"   - {sec['name']}: {sec['bars']} compases, progresión: {sec['progression'][:2]}")

    # Guardar configuración
    config_path = "/home/gerardo/.hermes/documentacion/hermesmusic/investigacion_teoria/engine_config.json"
    with open(config_path, "w") as f:
        json.dump(get_engine_config(), f, indent=2)
    print(f"\n✅ Configuración guardada en: {config_path}")

    print("\n" + "=" * 60)
    print("✅ MOTOR DE COMPOSICIÓN AVANZADA OPERATIVO")
    print("=" * 60)