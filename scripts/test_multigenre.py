#!/usr/bin/env python3
"""Hermes Music — Prueba de Composición Multigénero"""
import sys
import os
sys.path.insert(0, '/home/gerardo/.hermes/repos/hermes-music-daw/scripts')
sys.path.insert(0, '/home/gerardo/.hermes/documentacion/hermesmusic/investigacion_teoria')

from composition_engine_advanced import AdvancedComposer

# Probar todos los géneros
test_configs = [
    {"genre": "classical", "key": "E", "scale": "mayor", "form": "orchestral_ascending", "bpm": 60},
    {"genre": "classical", "key": "C", "scale": "mayor", "form": "ternary", "bpm": 120},
    {"genre": "pop", "key": "G", "scale": "mayor", "form": "pop_song", "bpm": 120},
    {"genre": "jazz", "key": "F", "scale": "mayor", "form": "ternary", "bpm": 90},
    {"genre": "flamenco", "key": "Am", "scale": "minor", "form": "ternary", "bpm": 110},
    {"genre": "romantic", "key": "C#m", "scale": "minor", "form": "ternary", "bpm": 72},
    {"genre": "electronic", "key": "D", "scale": "minor", "form": "minimalist", "bpm": 128},
    {"genre": "ambient", "key": "E", "scale": "minor", "form": "minimalist", "bpm": 70},
    {"genre": "blues", "key": "E", "scale": "major", "form": "ternary", "bpm": 100},
    {"genre": "folk", "key": "G", "scale": "major", "form": "ternary", "bpm": 90},
]

external_disk = "/mnt/320gb"
dest_dir = f"{external_disk}/musica/hermes/"

print("=" * 60)
print("HERMES MUSIC MULTIGÉNERO TEST REPORT")
print("=" * 60)

passed = 0
failed = 0
errors = []

for i, cfg in enumerate(test_configs):
    print(f"\n[{i+1}/{len(test_configs)}] {cfg['genre'].upper()} | Key: {cfg['key']} | BPM: {cfg['bpm']}")
    
    try:
        composer = AdvancedComposer(
            genre=cfg["genre"],
            key=cfg["key"],
            scale=cfg["scale"],
            form_profile=cfg["form"]
        )
        spec = composer.compose(total_duration_seconds=240.0, bpm=cfg["bpm"])
        
        section_names = [s["name"] for s in spec["sections"]]
        expected_forms = ["introduction", "development", "climax", "resolution"]
        
        has_correct_form = any(any(ef.lower() in s.lower() for ef in expected_forms) 
                              for s in section_names)
        
        total_bars = sum(s["bars"] for s in spec["sections"])
        expected_bars = int(240 * cfg["bpm"] / 60 / 4)  # 4/4 time
        
        duration_ratio = total_bars / expected_bars if expected_bars > 0 else 0
        
        n_tracks = len(spec.get("tracks", []))
        
        result = {
            "genre": cfg["genre"],
            "passed": has_correct_form,
            "section_count": len(spec["sections"]),
            "section_names": section_names,
            "total_bars": total_bars,
            "expected_bars": expected_bars,
            "duration_ratio": round(duration_ratio, 2),
            "track_count": n_tracks,
            "densities": [s.get("density", "unknown") for s in spec["sections"][:3]],
            "progressions": [s["progression"][0] for s in spec["sections"] if s.get("progression")][:4],
        }
        
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"   {status} | Sections: {len(spec['sections'])} | Bars: {total_bars}/{expected_bars} ({duration_ratio:.2f}x) | Tracks: {n_tracks}")
        
        if result["passed"]:
            passed += 1
        else:
            failed += 1
            
    except Exception as e:
        errors.append({"genre": cfg["genre"], "error": str(e)})
        print(f"   ❌ ERROR: {e}")
        failed += 1

# Resumen
print(f"\n{'='*60}")
print("📊 RESUMEN:")
print(f"   Total pruebas: {len(test_configs)}")
print(f"   ✅ Pasadas: {passed}")
print(f"   ❌ Fallidas: {failed}")
print(f"{'='*60}")

if errors:
    print("\n⚠️ Errores:")
    for e in errors:
        print(f"   - {e['genre']}: {e['error']}")

# Guardar resultados
output_path = f"{dest_dir}musica_multigenro_results.json"
os.makedirs(dest_dir, exist_ok=True)
with open(output_path, 'w') as f:
    import json
    json.dump({
        "resultados": [r for r in locals().get('_results', [])],
        "resumen": {"total": len(test_configs), "pasados": passed, "fallidos": failed},
        "errores": errors
    }, f, indent=2)
print(f"\n📁 Resultados guardados: {output_path}")