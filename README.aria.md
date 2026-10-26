# Aria Integration

## Installation
Aria is installed in venv at `/home/gerardo/.hermes/venvs/aria` with:
- `transformers==4.45.2` (required for custom model)
- `ariautils`, `miditoolkit`
- CPU torch

Model located at `/media/gerardo/1C02208A02206ACA1/.hermes/modelos-musica/aria-medium-gen` (658M params). Symlink `model.safetensors` points to `model-gen.safetensors`.

Source cloned to `/tmp/opencode/aria_src`.

## Usage
```bash
cd /home/gerardo/.hermes/repos/hermes-music-daw
PYTHONPATH=/home/gerardo/.hermes/repos/hermes-music-daw:/home/gerardo/.hermes/repos/hermes-music-daw/scripts \
/home/gerardo/.hermes/venvs/aria/bin/python scripts/aria_generate.py \
  --prompt /path/to/prompt.mid \
  --out /tmp/aria_out.mid \
  --max-new-tokens 64 \
  --prompt-tokens 512
```

The wrapper patches Aria for CPU inference (handles missing `prepare_inputs_for_generation` and `.cuda()` in `precompute_causal_mask`).

## Notes
- Aria is a solo piano continuation model; converts to MIDI via `ariautils`'s `MidiDict.to_midi()`.
- Generation is slow on CPU (tens of seconds per 16 tokens); use reasonable `max-new-tokens`.
- For longer generations, expect significant time.
