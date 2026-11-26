# animus_interactive

Interactive slide decks (and later, tutorials) as one offline HTML file: reveal.js slides with MathJax equations and
live SVG figures driven by sliders, clicks and hover.

It is a template and a set of helpers, not a framework: each deck writes its own figures and content, and this repo
carries the build, the runtime, base styles, headless checks and the conventions (`CLAUDE.md`) learnt making the
first talk.

## Layout

| path | what |
|---|---|
| `animus/build.py` | `build(...)`: inlines reveal.js 5.1.0 (+ notes plugin), MathJax 3.2.2 (SVG), fonts, styles, the deck's JSON data and scripts into one HTML file; `artifact=True` for a claude.ai page; `check=True` fails on a script syntax error or the deck's own check hook |
| `animus/core.js` | the runtime: SVG helpers (`el`, `lin`, `logs`, `axes`, `path`, `fmt`, ...), the figure registry `fig()`, click presets, linked equation terms and hover tips, `data-num` numbers from the data, speaker-view sync, `boot()` |
| `animus/style.css` | base styles: 1280x720 canvas, light/dark tokens, type, layouts, controls, plots, tables, terms and tips |
| `animus/checks/` | headless checks (Playwright + Chromium): `check_deck.py`, `slider_check.py`, `tip_check.py`, `compare_shots.py`, `tile.py` |
| `template/` | a three-slide example deck (title, an equation + slider figure with tips and presets, a divider) and its `build_deck.py` |
| `SKILL.md` | a Claude skill: start a deck from the template |
| `vendor/` | gitignored download cache of the libraries and fonts |

## Use

    python3 template/build_deck.py --check          # writes template/dist/deck.html
    PW=python-with-playwright
    $PW -m animus.checks.check_deck template/dist/deck.html --out shots       # console errors, overflow, screenshots
    $PW -m animus.checks.slider_check template/dist/deck.html                 # every slider moves its figure
    $PW -m animus.checks.tip_check template/dist/deck.html oscillator         # every tip on a slide shows

Run the checks from the repo root (or with it on `PYTHONPATH`). In a deck's repo, add this repo as a git submodule
and call `animus.build.build` from a short build script, as `template/build_deck.py` does.

A refactor that must not change the slides: screenshot before and after with `check_deck.py --frozen` (a stub clock
and no CSS transitions, so self-timing figures and fades come out the same), then
`compare_shots.py before/ after/`. Run the baseline twice first: Chromium's anti-aliasing can move a few hundred
pixels by under 10/255 between runs of the same build.

## Writing a deck

- A slide is a `<section id=...>` in `deck.html`; speaker notes in `<aside class="notes">`.
- A figure: `<div class="plot" data-fig="name">` on the slide, and in a script
  `fig("name", { defaults, build(root, D) { ... }, set(state) { ... } })`. `set` redraws from the whole state.
- Controls: `slider(id, fn)` for `<input type="range">`, `control(id, fn)` for segmented buttons
  (`<span class="seg">`); put them in a `<div class="ctl">` (not `.controls`: reveal hides that class).
- Clicks: `<span class="fragment preset" data-preset='{"zeta": 1}'></span>` sets the slide's figure when reached.
- Terms: `\class{term t-name}{...}` in the maths; `<dl class="tips"><dt>t-name</dt><dd>tip</dd></dl>` on the
  slide; a fragment with `data-hl="t-name"` highlights it.
- Guides: `<div class="guide"><p>...</p></div>` in a slide. The slide shows only a "?" at the bottom centre;
  hovering it shows the guide (a click pins it). The same deck is a talk (don't hover) and a tutorial (read the
  guides). Guides are visible text: numbers in them come from `data-num` too. `check_deck --guides` lists slides
  without one. A guide can hold a quiz: `<p class="q">question</p><ol class="quiz"><li data-right>option<span
  class="why">reason</span></li>...</ol>`; picking an option marks it right or wrong and shows its reason (the
  template's divider has one).
- Numbers from the data: `<span data-num="path.to.value|x"></span>` (`x` adds ×, `s2` two significant figures,
  `i` integer, `pct` percent; `rows[name]` picks the row whose `method` is `name`).
- D toggles light/dark; S opens the speaker view.

## Licence

Apache-2.0: see `LICENSE`.
