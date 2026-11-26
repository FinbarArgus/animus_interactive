"""check_deck steps a slide's fragments by click, not by element (headless, when Playwright is there)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from animus.build import build  # noqa: E402
from animus.checks.common import open_deck, step_fragments  # noqa: E402

T = ROOT / "template"
# Three fragments shown in two clicks: the first two share an index.
SHARED = """<section id="shared">
  <p class="fragment" data-fragment-index="0">a</p>
  <p class="fragment" data-fragment-index="0">b</p>
  <p class="fragment" data-fragment-index="1">c</p>
</section>
"""


def test_fragments_sharing_an_index_do_not_step_onto_the_next_slide(tmp_path):
    sync_api = pytest.importorskip("playwright.sync_api")
    src = (T / "src" / "deck.html").read_text()
    first = src.index("<section")
    (tmp_path / "deck.html").write_text(src[:first] + SHARED + src[first:])
    deck = build(deck=tmp_path / "deck.html", scripts=[T / "src" / "figs.js"], styles=[T / "src" / "style.css"],
                 data=T / "data" / "deck_data.json", out=tmp_path / "out.html")
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch()
        pg = open_deck(b, deck)
        pg.evaluate("deck.slide(0, 0, -1)")
        assert step_fragments(pg, 0) == 2
        assert pg.evaluate("deck.getCurrentSlide().id") == "shared"
        assert pg.evaluate("deck.getCurrentSlide().querySelectorAll('.fragment.visible').length") == 3
        b.close()
