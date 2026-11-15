"""
Build the template deck into dist/deck.html (open it in a browser; S for the speaker view, D for light/dark).

    python3 template/build_deck.py [--check] [--artifact]

Copy template/ to start a deck. In a deck's own repo, animus_interactive is a git submodule: point ANIMUS at it.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ANIMUS = HERE.parent  # in a deck's repo: HERE / "animus_interactive"
sys.path.insert(0, str(ANIMUS))
from animus.build import build  # noqa: E402

if __name__ == "__main__":
    artifact = "--artifact" in sys.argv
    build(deck=HERE / "src" / "deck.html", scripts=[HERE / "src" / "figs.js"], styles=[HERE / "src" / "style.css"],
          data=HERE / "data" / "deck_data.json", title="Template deck",
          out=HERE / "dist" / ("deck_artifact.html" if artifact else "deck.html"), artifact=artifact,
          check="--check" in sys.argv, channel="animus-template")
