"""Quizzes in guides: a mouse moving from the ? onto an option keeps the guide open, and picking marks the option."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from animus.build import build  # noqa: E402

T = ROOT / "template"


def test_quiz_marks_the_pick(tmp_path):
    sync_api = pytest.importorskip("playwright.sync_api")
    deck = build(deck=T / "src" / "deck.html", scripts=[T / "src" / "figs.js"], styles=[T / "src" / "style.css"],
                 data=T / "data" / "deck_data.json", out=tmp_path / "deck.html")
    with sync_api.sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 720})
        pg.goto(deck.as_uri())
        pg.wait_for_function("window.deck && window.deck.isReady()", timeout=60000)
        pg.evaluate("deck.slide(2)")
        pg.wait_for_timeout(600)
        q = pg.locator(".divider .guide-q").bounding_box()
        qx, qy = q["x"] + q["width"] / 2, q["y"] + q["height"] / 2
        pg.mouse.move(qx, qy)
        pg.wait_for_timeout(200)

        def pick(i):  # move continuously from the ? to option i, as a hand would, and click it
            o = pg.locator(".divider ol.quiz > li").nth(i).bounding_box()
            pg.mouse.move(qx, qy)
            pg.mouse.move(o["x"] + 20, o["y"] + o["height"] / 2, steps=5)  # a quick move: the hide grace keeps the panel
            pg.mouse.down()
            pg.mouse.up()
            pg.wait_for_timeout(100)
            return pg.evaluate(f"[...document.querySelectorAll('.divider ol.quiz > li')][{i}].className")

        # leaving the ? hides the guide only after a short grace, so a quick move onto the panel keeps it open
        vis = "getComputedStyle(document.querySelector('.divider .guide')).visibility"
        pg.mouse.move(5, 5)
        pg.wait_for_timeout(50)
        assert pg.evaluate(vis) == "visible"
        g = pg.locator(".divider .guide").bounding_box()
        assert pg.evaluate(f"!!document.elementFromPoint({g['x'] + 30}, {g['y'] + 10}).closest('.guide')")  # still takes the pointer
        pg.wait_for_timeout(600)
        assert pg.evaluate(vis) == "hidden"
        assert "wrong" in pick(0)
        assert pg.evaluate("getComputedStyle(document.querySelector('.divider ol.quiz > li .why')).display") == "block"
        assert "right" in pick(1)
        assert pg.evaluate("document.querySelectorAll('.divider ol.quiz > li.picked').length") == 1  # one pick at a time
        assert pg.evaluate("getComputedStyle(document.querySelector('.divider .guide')).visibility") == "visible"
        b.close()
