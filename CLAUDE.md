# animus_interactive

The engine for Finbar's interactive decks (README.md has the layout and API). The workspace rules in
`~/Documents/git_projects/CLAUDE.md` apply; this file adds this repo's specifics.

- **Branches:** base branch `main` (PRs to it; Finbar merges). Local `devel` holds every feature, merged when its PR
  opens. Work in `.claude/worktrees/<name>`.
- **Private repo.** Decks pin it as a git submodule; a change here must keep every deck that pins it building. Check
  a change against the template and against the QPOpInf talk (`QPopInf_methods_paper`, branch `talk`,
  `docs/talk/`): frozen screenshots before and after must match (README, "A refactor that must not change the
  slides").
- **Checks:** `python3 template/build_deck.py --check`, then the checks in `animus/checks/` with a Python that has
  Playwright + Chromium (one is at `~/.cache/claude-tmp/ci-fix-pypi-venv/bin/python`).

## Finbar's conventions for slides

- Figure-led slides with little text; explanations go in the speaker notes.
- Every plot has x and y axis titles; the y title runs along the axis.
- He drives mode/rank sliders himself: no click steps on slides whose figure is a slider over modes.
- Real data in figures, never empty placeholder matrices.
- Numbers on slides come from the data through `data-num`, never typed in (a deck can enforce it with a check hook,
  as the QPOpInf talk does for its results slides).
- A page or slide set that shows a result opens with a provenance diagram of how it was produced (workspace
  CLAUDE.md, "Result pages").
- His slide numbers often lag the deck by one: confirm which slide he means by its content.

## Traps (each cost time in the first talk)

- Reveal hides `.reveal .controls`: control rows use class `ctl`.
- MathJax can't take HTML inside `\[ \]`: put `data-num` spans outside the maths.
- Hidden slides measure zero: size anything that needs a bounding box on `slidechanged` (core's `sizeHits` does this
  for term hit boxes).
- Drags select text: `preventDefault` on pointerdown (`onDrag` does) and `user-select: none` on plots.
- A hover readout that changes length moves the layout: give it a fixed height.
- Rounding exported data below 7 significant figures made traces jagged.
- `-(x)**2` is a JS syntax error (write `-((x)**2)`), and one syntax error stops the whole deck: build with `--check`.
- A grid that overflows needs `minmax(0, 1fr)` tracks and `min-height: 0` on the children.
- Dark mode needs both the `prefers-color-scheme` media query (guarded by `:not([data-theme="light"])`) and
  `[data-theme="dark"]`, so D works whatever the laptop's setting.
- CSS rule order matters when two rules of equal specificity collide: a deck's style.css loads after the base.
- Figures that time themselves in the browser differ on every load: compare screenshots only with `--frozen`.
