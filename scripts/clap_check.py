#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""clap_check.py — Verifica si un audio va por el estilo pedido, usando CLAP.

CLAP (laion/larger_clap_music_and_speech) compara audio contra descripciones de
texto y devuelve similitud. Sirve como BRÚJULA DE ESTILO antes de renderizar:
si la descripción pedida no gana, estás a tiempo de corregir sin gastar CPU.

NO juzga calidad ni gusto. Solo dice si el audio se parece a lo descrito.
La escucha humana sigue siendo el veredicto final.

Uso:
    python3 clap_check.py audio.ogg "power metal with double bass drum"
    python3 clap_check.py audio.ogg --candidates a.ogg b.ogg   # comparar varios
    python3 clap_check.py audio.ogg --compare "desc1" "desc2"   # varias descripciones

Requiere: venv ~/.hermes/venvs/hermes-3.12 (torch + transformers) y soundfile.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
import torch

CLAP_PATH = "/home/gerardo/Modelo/clap"


def load_model():
    from transformers import ClapModel, ClapProcessor
    proc = ClapProcessor.from_pretrained(CLAP_PATH)
    model = ClapModel.from_pretrained(CLAP_PATH)
    model.eval()
    return proc, model


def decode_mono48k(audio_path: str) -> tuple[np.ndarray, int]:
    """CLAP se entrenó con audio mono a 48 kHz. Decodifica con ffmpeg."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fh:
        wav = fh.name
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", audio_path, "-ar", "48000", "-ac", "1", wav],
        check=True, capture_output=True,
    )
    data, sr = sf.read(wav)
    Path(wav).unlink(missing_ok=True)
    return data.astype("float32"), sr


def audio_vector(proc, model, samples, sr, seconds: float = 10.0):
    """Embedding de un segmento de audio (hasta 10 s, lo que CLAP acepta)."""
    seg = samples[: int(sr * seconds)]
    inputs = proc(audio=seg, sampling_rate=sr, return_tensors="pt")
    with torch.no_grad():
        out = model.get_audio_features(**inputs)
    return out.pooler_output[0].numpy()


def text_vector(proc, model, text: str):
    inputs = proc(text=[text], return_tensors="pt", padding=True)
    with torch.no_grad():
        out = model.get_text_features(**inputs)
    return out.pooler_output[0].numpy()


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(a @ b)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("audio", help="archivo de audio a evaluar")
    ap.add_argument("description", nargs="?", help="descripción del estilo pedido")
    ap.add_argument("--candidates", nargs="+", metavar="AUDIO",
                    help="comparar varios archivos de audio entre sí")
    ap.add_argument("--compare", nargs="+", metavar="DESC",
                    help="comparar varias descripciones contra el audio")
    ap.add_argument("--seconds", type=float, default=10.0,
                    help="segundos de audio a evaluar (máx. 10, defecto 10)")
    args = ap.parse_args()

    if not Path(args.audio).is_file():
        print(f"ERROR: no existe {args.audio}", file=sys.stderr)
        return 1

    print(f"Cargando CLAP ({CLAP_PATH})...")
    proc, model = load_model()
    samples, sr = decode_mono48k(args.audio)
    print(f"Audio: {args.audio} | {len(samples) / sr:.1f}s @ {sr} Hz")

    # Un solo archivo, varias descripciones
    if args.compare:
        a = audio_vector(proc, model, samples, sr, args.seconds)
        print(f"\n=== CLAP: {Path(args.audio).name} ===")
        scored = sorted(((cosine(a, text_vector(proc, model, d)), d)
                         for d in args.compare), reverse=True)
        for score, desc in scored:
            print(f"  {score * 100:6.1f}  {desc}")
        print(f"\nMEJOR: {scored[0][1]}")
        return 0

    # Varios archivos, una descripción
    if args.candidates:
        if not args.description:
            print("ERROR: --candidates necesita una descripción", file=sys.stderr)
            return 1
        t = text_vector(proc, model, args.description)
        print(f"\n=== CLAP: ¿cuál suena más a «{args.description}»? ===")
        scored = []
        for path in args.candidates:
            if not Path(path).is_file():
                print(f"  (falta: {path})")
                continue
            s, r = decode_mono48k(path)
            scored.append((cosine(audio_vector(proc, model, s, r, args.seconds), t), path))
        for score, path in sorted(scored, reverse=True):
            print(f"  {score * 100:6.1f}  {path}")
        if scored:
            print(f"\nMEJOR: {max(scored)[1]}")
        return 0

    if not args.description:
        print("ERROR: falta una descripción (o usa --compare / --candidates)",
              file=sys.stderr)
        return 1

    # Caso simple: un archivo, una descripción
    a = audio_vector(proc, model, samples, sr, args.seconds)
    t = text_vector(proc, model, args.description)
    score = cosine(a, t)
    verdict = "COINCIDE" if score > 0.30 else "DUDOSO" if score > 0.10 else "NO COINCIDE"
    print(f"\n=== CLAP: {Path(args.audio).name} ===")
    print(f"  descripción: {args.description}")
    print(f"  similitud:   {score * 100:.1f}")
    print(f"  veredicto:   {verdict}")
    print("\nLÍMITE: CLAP evalúa parecido de estilo, no calidad ni gusto.")
    print("La escucha humana es el veredicto final.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
