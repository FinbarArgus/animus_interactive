"""
Every range input in a built deck must change the state of some figure on its slide when moved.

    python -m animus.checks.slider_check dist/deck.html      # prints "<input id>: ok" or ": NO EFFECT"
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import open_deck  # noqa: E402

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = open_deck(b, Path(sys.argv[1]))
    res = pg.evaluate("""() => [...document.querySelectorAll('input[type=range]')].map(inp => {
        const figs = [...inp.closest('section').querySelectorAll('[data-fig]')].map((h) => FIGS[h.dataset.fig]);
        const before = JSON.stringify(figs.map((f) => f.state));
        inp.value = inp.value === inp.max ? inp.min : inp.max; inp.dispatchEvent(new Event('input'));
        const after = JSON.stringify(figs.map((f) => f.state));
        figs.forEach((f) => f.set({ ...f.defaults }));
        return inp.id + ': ' + (before !== after ? 'ok' : 'NO EFFECT');
      })""")
    print("\n".join(res))
    b.close()
sys.exit(1 if any("NO EFFECT" in r for r in res) else 0)
