#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manual entry point for the skills index - delegates to the ``skills-index`` plugin.

The canonical owner of ``<HERMES_HOME>/skills/INDEX.json`` is the plugin
``~/.hermes/plugins/skills-index/``, which also maintains it automatically
(``on_session_start`` + ``on_skill_lifecycle`` + fingerprint). This script is
retained only as a manual entry point for compatibility with ``ENSAMBLE.md``.

Usage:
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
            f"skills-index plugin not found at {path}\n"
            "Install/enable it (hermes plugins enable skills-index) or rebuild with "
            "the /skills-index rebuild command."
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
