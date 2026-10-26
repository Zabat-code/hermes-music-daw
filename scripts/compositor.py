#!/usr/bin/env python3
"""
Compositor para composition_guard.py
Puede usar arrangement_engine con genre_engine o composition_engine_advanced.
"""
import json
import sys
import os
import traceback

repo_path = os.path.dirname(os.path.abspath(__file__))
repo_root = os.path.dirname(repo_path)
sys.path.insert(0, repo_path)
sys.path.insert(0, repo_root)
sys.path.insert(0, "/home/gerardo/.hermes/documentacion/hermesmusic/investigacion_teoria")

try:
    from arrangement_engine import Arranger
    HAS_ARR = True
except Exception:
    HAS_ARR = False

try:
    from composition_engine_advanced import AdvancedComposer
    HAS_ADV = True
except Exception:
    HAS_ADV = False


def main():
    args = sys.argv
    if len(args) < 2:
        print("Uso: compositor.py --out {draft}")
        sys.exit(1)

    out_path = None
    for i, arg in enumerate(args):
        if arg == "--out" and i + 1 < len(args):
            out_path = args[i + 1]

    if not out_path:
        print("❌ No se especificó --out")
        sys.exit(1)

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    spec_path = os.path.join(repo_path, "plan.json")
    spec = None
    if os.path.exists(spec_path):
        try:
            with open(spec_path, 'r') as f:
                spec = json.load(f)
        except Exception:
            spec = None

    # If plan.json contains genre info use arranger
    if spec and HAS_ARR and (spec.get('genre') or spec.get('profile_id')):
        genre = spec.get('genre') or spec.get('profile_id') or 'pop'
        key = spec.get('key', 'C')
        scale = spec.get('scale', 'mayor')
        variant = spec.get('variant')
        seed = spec.get('seed', 42)
        bpm = spec.get('tempo') or spec.get('bpm') or 120
        try:
            arr = Arranger(genre, key=key, scale=scale, variant=variant, seed=seed, bpm=bpm)
            roles = spec.get('roles')
            spec_arr = arr.build_spec(roles)
            try:
                import hermesmusic
                hermesmusic.render_song(spec_arr, out_path)
                print(f"✅ MIDI guardado: {out_path}")
                return
            except Exception as e:
                print(f"⚠️  Error renderizando con arrangement_engine: {e}")
        except Exception as e:
            print(f"⚠️  Error creando arrangement_engine: {e}")

    # Try advanced composer
    if HAS_ADV and spec is None:
        try:
            composer = AdvancedComposer(
                genre=spec.get('genre', 'classical') if spec else 'classical',
                key=spec.get('key', 'E') if spec else 'E',
                scale=spec.get('scale', 'mayor') if spec else 'mayor',
                form_profile=spec.get('form_profile', 'orchestral_ascending') if spec else 'orchestral_ascending'
            )
            compspec = composer.compose(
                total_duration_seconds=spec.get('duration', 240.0) if spec else 240.0,
                bpm=spec.get('bpm', 60) if spec else 60
            )
            spec = compspec
        except Exception as e:
            print(f"⚠️  Error con AdvancedComposer: {e}")

    if not spec:
        print("❌ No se pudo generar spec")
        sys.exit(1)

    # If spec already has render_song compatible structure
    try:
        import hermesmusic
        if hasattr(hermesmusic, 'render_song'):
            print("✅ Generando MIDI con hermesmusic.render_song...")
            hermesmusic.render_song(spec, out_path)
            print(f"✅ MIDI guardado: {out_path}")
            return
    except Exception as e:
        print(f"⚠️  Error: {e}")
        traceback.print_exc()
        sys.exit(1)

    print("❌ No se pudo generar MIDI")
    sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        traceback.print_exc()
        sys.exit(1)
