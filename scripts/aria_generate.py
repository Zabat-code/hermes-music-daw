#!/usr/bin/env python3
"""
Aria MIDI generation wrapper for CPU/local use.
Patches transformers generate() for Aria's custom HF implementation.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import types

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_DIR = os.environ.get(
    "ARIA_MODEL_DIR",
    "/media/gerardo/1C02208A02206ACA1/.hermes/modelos-musica/aria-medium-gen",
)
VENV_PY = os.environ.get("ARIA_VENV_PY", "/home/gerardo/.hermes/venvs/aria/bin/python")


def patch_aria(model):
    mod = sys.modules.get(model.__class__.__module__)
    if mod is None:
        return
    if hasattr(mod, "precompute_causal_mask"):
        orig = mod.precompute_causal_mask

        def mask(max_seq_len=None, n=None, *args, **kwargs):
            mlen = max_seq_len if max_seq_len is not None else n
            if mlen is None and args:
                mlen = args[0]
            return torch.tril(torch.ones(mlen, mlen, dtype=torch.bool))

        mod.precompute_causal_mask = mask

    if not hasattr(model, "prepare_inputs_for_generation"):
        def prep(self, input_ids, past_key_values=None, attention_mask=None,
                 inputs_embeds=None, cache_position=None, **kwargs):
            if past_key_values is not None and cache_position is not None:
                try:
                    input_ids = input_ids[:, cache_position]
                except Exception:
                    pass
            return dict(input_ids=input_ids, attention_mask=attention_mask,
                        past_key_values=past_key_values, use_cache=True,
                        cache_position=cache_position)

        model.prepare_inputs_for_generation = types.MethodType(prep, model)


def load_model(model_dir=MODEL_DIR):
    tok = AutoTokenizer.from_pretrained(model_dir, trust_remote_code=True,
                                        local_files_only=True)
    model = AutoModelForCausalLM.from_pretrained(model_dir, trust_remote_code=True,
                                                local_files_only=True,
                                                torch_dtype=torch.float32)
    model.eval()
    patch_aria(model)
    return tok, model


def generate_midi(prompt_mid: str, out_mid: str, max_new_tokens: int = 128,
                  temperature: float = 0.97, top_p: float = 0.95,
                  do_sample: bool = True, seed: int = 42,
                  prompt_tokens: int = 512):
    torch.manual_seed(seed)
    tok, model = load_model()
    prompt = tok.encode_from_file(prompt_mid, return_tensors="pt")
    ids = prompt["input_ids"]
    if ids.shape[1] > prompt_tokens:
        ids = ids[:, :prompt_tokens]
    t0 = time.time()
    with torch.no_grad():
        cont = model.generate(ids, max_new_tokens=max_new_tokens,
                              do_sample=do_sample, temperature=temperature,
                              top_p=top_p, use_cache=True,
                              pad_token_id=tok.pad_token_id or 2,
                              eos_token_id=tok.eos_token_id or 1)
    md = tok.decode(cont[0].tolist())
    try:
        mido = md.to_midi()
        mido.save(out_mid)
    except Exception as e:
        raise
    dt = time.time() - t0
    meta = {"prompt": prompt_mid, "out": out_mid, "prompt_tokens": ids.shape[1],
            "new_tokens": max_new_tokens, "secs": round(dt, 2),
            "shape": list(cont.shape)}
    with open(out_mid + ".json", "w") as f:
        json.dump(meta, f, indent=2)
    return out_mid, meta


def main():
    p = argparse.ArgumentParser(description="Aria MIDI generation (CPU)")
    p.add_argument("--prompt", required=True, help="MIDI prompt file")
    p.add_argument("--out", required=True, help="Output MIDI file")
    p.add_argument("--max-new-tokens", type=int, default=64)
    p.add_argument("--temperature", type=float, default=0.97)
    p.add_argument("--top-p", type=float, default=0.95)
    p.add_argument("--prompt-tokens", type=int, default=512)
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--sample", action="store_true", default=True)
    args = p.parse_args()
    out, meta = generate_midi(args.prompt, args.out,
                              max_new_tokens=args.max_new_tokens,
                              temperature=args.temperature, top_p=args.top_p,
                              prompt_tokens=args.prompt_tokens, seed=args.seed)
    print(json.dumps(meta))


if __name__ == "__main__":
    main()
