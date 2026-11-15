"""The build: the template deck builds, artifact pages turn off hash routing, and a check build catches problems.

Needs the vendor cache (downloaded on the first build) and node. Run from the repo root: python3 -m pytest tests
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from animus.build import build  # noqa: E402

T = ROOT / "template"
ARGS = dict(deck=T / "src" / "deck.html", styles=[T / "src" / "style.css"], data=T / "data" / "deck_data.json")


def test_template_builds(tmp_path):
    out = build(scripts=[T / "src" / "figs.js"], out=tmp_path / "deck.html", check=True, channel="c1", **ARGS)
    html = out.read_text()
    assert html.startswith("<!doctype html>")
    assert '<script type="application/json" id="deck-data">{"omega"' in html
    assert 'window.ANIMUS = {"dataId": "deck-data", "channel": "c1"};' in html
    assert html.index("function boot()") < html.index('fig("oscillator"')  # core runs before the deck's figures


def test_artifact_has_no_skeleton_and_no_hash(tmp_path):
    html = build(scripts=[T / "src" / "figs.js"], out=tmp_path / "a.html", artifact=True, **ARGS).read_text()
    assert html.startswith("<title>")
    assert '"reveal": {"hash": false}' in html


def test_check_fails_on_syntax_error(tmp_path):
    bad = tmp_path / "bad.js"
    bad.write_text("const y = -(2)**2;\n")
    with pytest.raises(SystemExit, match="do not parse"):
        build(scripts=[bad], out=tmp_path / "x.html", check=True, **ARGS)


def test_check_hook_and_replacements(tmp_path):
    with pytest.raises(SystemExit, match="deck check failed"):
        build(scripts=[], out=tmp_path / "x.html", check=True, check_hook=lambda h: ["typed number"], **ARGS)
    html = build(scripts=[], out=tmp_path / "y.html", replacements={"A damped oscillator": "A spring"}, **ARGS).read_text()
    assert "A spring, one slider" in html
