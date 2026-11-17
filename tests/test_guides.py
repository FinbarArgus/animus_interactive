"""Guides: the build keeps a slide's .guide, and the runtime adds its "?" (checked headless when Playwright is there)."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from animus.build import build  # noqa: E402

T = ROOT / "template"


@pytest.fixture(scope="module")
def deck(tmp_path_factory):
    return build(deck=T / "src" / "deck.html", scripts=[T / "src" / "figs.js"], styles=[T / "src" / "style.css"],
                 data=T / "data" / "deck_data.json", out=tmp_path_factory.mktemp("g") / "deck.html")


def test_guide_and_styles_are_built(deck):
    html = deck.read_text()
    assert '<div class="guide">' in html and "function addGuides()" in html and ".reveal .guide-q {" in html


def test_question_mark_shows_the_guide_on_hover(deck):
    sync_api = pytest.importorskip("playwright.sync_api")
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.goto(deck.as_uri() + "#/oscillator")
        pg.wait_for_function("window.deck && window.deck.isReady()", timeout=60000)
        vis = "getComputedStyle(document.querySelector('#oscillator .guide')).visibility"
        assert pg.evaluate("document.querySelectorAll('.guide-q').length") == 1  # only the slide with a guide
        assert pg.evaluate(vis) == "hidden"
        pg.hover("#oscillator .guide-q")
        pg.wait_for_timeout(200)
        assert pg.evaluate(vis) == "visible"
        pg.mouse.move(5, 5)
        pg.click("#oscillator .guide-q")  # a click pins it open after the mouse leaves
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(200)
        assert pg.evaluate(vis) == "visible"
        pg.evaluate("deck.slide(2)")  # changing slide unpins it
        pg.wait_for_timeout(200)
        assert pg.evaluate("document.querySelector('#oscillator .guide').classList.contains('pinned')") is False
        b.close()
