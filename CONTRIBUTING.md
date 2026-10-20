# Contributing

Use Python 3.12 and a virtual environment. Install with
`python -m pip install -e '.[dev]'`, then install FluidSynth, FFmpeg and a GM
SoundFont as described in the README. Run `python scripts/check_install.py`.

Before submitting a change:

- Run `python -m pytest tests/ -q` and report the actual output, including skips.
- For workflow changes, run the three examples in a fresh output directory.
- Keep the eight arrangement gates intact. A new musical contract needs an
  explicit profile, a rationale and regression cases; do not weaken gates to
  make a rejected piece pass.
- Use generated fixtures. Do not depend on personal directories, downloaded
  recordings, private projects or a particular sound card.
- Document changed MCP parameters and errors in tool docstrings and PROTOCOL.md.
- Separate measured facts from listening judgments. Do not claim genre fidelity,
  true peak compliance or sonic improvement without matching evidence.

Small focused pull requests are welcome. Include the problem, resulting behavior
and relevant validation. Keep generated WAVs, stems, caches and backups out of
the change. The intentionally included short OGG sample is the only exception.

Original contributions use MIT; retain third-party notices and dependency
licenses. Do not upload SoundFonts or recordings you do not have rights to share.
