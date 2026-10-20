#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entrada manual al índice de skills — delega en el plugin ``skills-index``.

El dueño canónico de ``<HERMES_HOME>/skills/INDEX.json`` es el plugin
``~/.hermes/plugins/skills-index/``, que además lo auto-mantiene
(``on_session_start`` + ``on_skill_lifecycle`` + fingerprint). Este script se
conserva solo como entrada manual por compatibilidad con ``ENSAMBLE.md``.

Uso:
    python3 build_index.py [--force]
"""
from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path


def _plugin_indexer():
    home = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
    path = home / "plugins" / "skills-index" / "indexer.py"
    if not path.is_file():
        raise SystemExit(
            f"no se encontró el plugin skills-index en {path}\n"
            "Instálalo/habilítalo (hermes plugins enable skills-index) o reconstruye con "
            "el comando /skills-index rebuild."
        )
    spec = importlib.util.spec_from_file_location("skills_index_autoindex", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    indexer = _plugin_indexer()
    result = indexer.rebuild(force="--force" in sys.argv[1:])
    print(f"{indexer.index_path()}: {result['total']} skills ({result['reason']})")


if __name__ == "__main__":
    main()
