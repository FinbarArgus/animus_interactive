---
name: animus-deck
description: Start or extend an interactive slide deck (reveal.js + MathJax + live SVG figures, one offline HTML file) with animus_interactive. Use when Finbar asks for a talk, interactive slides or an interactive tutorial page.
---

# Make a deck with animus_interactive

1. Read `CLAUDE.md` in this repo (Finbar's slide conventions and the traps) and `README.md` (API).
2. In the deck's repo: `git submodule add git@github.com:FinbarArgus/animus_interactive.git <deck dir>/animus_interactive`
   (pin `devel` while developing; the repo is private, so collaborators who build need access).
3. Copy `template/` into the deck dir; in `build_deck.py` set `ANIMUS = HERE / "animus_interactive"`, the title,
   output name and a `channel` name unique to the deck.
4. Write the data the figures need as one JSON file (exported by a script from the real results, at full precision),
   the slides in `src/deck.html`, figures in `src/*.js` with `fig(...)`, and deck styles in `src/style.css`.
5. Build with `--check`, then run `check_deck` (light and dark), `slider_check` and `tip_check`; look at the
   screenshots (`tile.py` puts four on one image) before showing Finbar.
6. For a claude.ai page, build with `--artifact` and publish that file; republish the same path to update it.

Keep figures and talk-specific helpers in the deck. Move a helper into `animus/core.js` only when a second deck needs
it, and check the talk still renders the same (frozen screenshots, `compare_shots.py`).
