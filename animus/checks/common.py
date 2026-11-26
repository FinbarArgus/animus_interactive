"""Open a built deck headless in Chromium (Playwright), optionally frozen for screenshot comparisons."""
from pathlib import Path

# A counter clock: every performance.now() / Date.now() call advances it by a fixed step, so figures that time
# themselves print the same numbers on every run.
FROZEN_CLOCK = """(() => {
  let t = 0, d = 1.7e12;
  performance.now = () => (t += 0.25);
  Date.now = () => (d += 1);
})();"""
# No CSS transitions or animations, so a screenshot never catches a fade half way.
FROZEN_STYLE = """addEventListener("DOMContentLoaded", () => {
  const s = document.createElement("style");
  s.textContent = "*, *::before, *::after { transition: none !important; animation: none !important; }";
  document.head.appendChild(s);
});"""


def open_deck(browser, deck: Path, *, scheme: str = "light", frozen: bool = False, slide: str = "", errors=None):
    """A 1280x720 page with the deck loaded and Reveal ready; `slide` is a section id to open at."""
    pg = browser.new_page(viewport={"width": 1280, "height": 720}, color_scheme=scheme)
    if frozen:
        pg.add_init_script(FROZEN_CLOCK)
        pg.add_init_script(FROZEN_STYLE)
    if errors is not None:
        pg.on("console", lambda m: errors.append(f"{m.type}: {m.text}") if m.type in ("error", "warning") else None)
        pg.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
    pg.goto(Path(deck).resolve().as_uri() + (f"#/{slide}" if slide else ""))
    pg.wait_for_function("window.deck && window.deck.isReady && window.deck.isReady()", timeout=60000)
    return pg


def step_fragments(pg, wait_ms: int = 120) -> int:
    """Click through the current slide's fragments and return the number of clicks.

    Fragments that share a data-fragment-index show on one click, so this steps until Reveal has none left
    and never moves to the next slide.
    """
    clicks = 0
    while pg.evaluate("deck.nextFragment()"):
        clicks += 1
        pg.wait_for_timeout(wait_ms)
    return clicks
