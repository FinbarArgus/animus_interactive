"""
Hover every equation term that has a tip (<dl class="tips">) on one slide, as a mouse would, and print whether the
tip shows and its first words. Saves a screenshot of the last tip.

    python -m animus.checks.tip_check dist/deck.html <slide id> [--out tip.png]
"""
import argparse
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import open_deck  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("deck", type=Path)
ap.add_argument("slide")
ap.add_argument("--out", type=Path)
a = ap.parse_args()
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = open_deck(b, a.deck, slide=a.slide)
    pg.wait_for_timeout(900)
    terms = pg.evaluate(f"[...document.querySelectorAll('#{a.slide} .tips dt')].map((d) => d.textContent.trim())")
    bad = 0
    for cls in terms:
        # the centre of a glyph inside the term, where a mouse over the equation would hit it
        box = pg.evaluate(f"(() => {{ const g = document.querySelector('#{a.slide} .{cls} use, #{a.slide} .{cls} path, #{a.slide} .{cls}');"
                          " const r = g.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; })()")
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(100)
        pg.mouse.move(*box)
        pg.wait_for_timeout(150)
        hidden = pg.evaluate("document.querySelector('.tipbox').hidden")
        bad += hidden
        print(cls, "| hidden:", hidden, "|", pg.evaluate("document.querySelector('.tipbox').textContent")[:60])
    if a.out:
        pg.screenshot(path=str(a.out))
    b.close()
sys.exit(1 if bad or not terms else 0)
