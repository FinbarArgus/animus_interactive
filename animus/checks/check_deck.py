"""
Load a built deck headless and check every slide: console errors, content past the 1280x720 canvas, unresolved
data-num, failed figures. Steps every click on slides with fragments. Screenshots every slide and every click's end
state to <out>/<scheme>_<index>_<id>.png (and ..._end.png).

    python -m animus.checks.check_deck dist/deck.html --out shots [--scheme dark] [--frozen]

Prints one line per slide (flags only where there is a problem) and the console errors. --frozen stubs the clock and
turns off CSS transitions, so two builds' screenshots can be compared pixel by pixel (compare_shots.py). --guides
flags slides without a tutorial guide (dividers excepted).
"""
import argparse
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import open_deck  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("deck", type=Path)
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--scheme", default="light", choices=["light", "dark"])
ap.add_argument("--frozen", action="store_true")
ap.add_argument("--guides", action="store_true", help="flag slides with no .guide (dividers excepted)")
a = ap.parse_args()
a.out.mkdir(parents=True, exist_ok=True)
for old in a.out.glob(f"{a.scheme}_*.png"):
    old.unlink()

with sync_playwright() as p:
    b = p.chromium.launch()
    errs = []
    pg = open_deck(b, a.deck, scheme=a.scheme, frozen=a.frozen, errors=errs)
    pg.wait_for_timeout(500)
    n = pg.evaluate("deck.getTotalSlides()")
    report = []
    for i in range(n):
        pg.evaluate(f"deck.slide({i}, 0, -1)")
        pg.wait_for_timeout(900)
        info = pg.evaluate("""() => {
          const s = deck.getCurrentSlide(); const r = s.getBoundingClientRect(); const sc = deck.getScale();
          const over = []; for (const e of s.querySelectorAll('*')) { const q = e.getBoundingClientRect();
            if (q.width && (q.bottom > r.top + 720*sc + 2 || q.right > r.left + 1280*sc + 2)) over.push((e.id||e.className||e.tagName).toString().slice(0,40)); }
          const missing = [...s.querySelectorAll('[data-num]')].filter(e => e.textContent.includes('?')).map(e => e.dataset.num);
          const failed = [...s.querySelectorAll('[data-fig]')].filter(e => e.textContent.startsWith('Figure failed')).map(e => e.textContent);
          return { id: s.id, over: [...new Set(over)].slice(0, 6), missing, failed, frags: s.querySelectorAll('.fragment').length,
                   noguide: !s.querySelector(':scope > .guide') && !s.classList.contains('divider') };
        }""")
        pg.screenshot(path=str(a.out / f"{a.scheme}_{i:02d}_{info['id'] or 'x'}.png"))
        report.append((i, info))
    # step all fragments on interactive slides: presets must not throw
    for i, info in report:
        if info["frags"]:
            pg.evaluate(f"deck.slide({i}, 0, -1)")
            for _ in range(info["frags"]):
                pg.evaluate("deck.next()")
                pg.wait_for_timeout(300 if a.frozen else 120)
            pg.screenshot(path=str(a.out / f"{a.scheme}_{i:02d}_{info['id'] or 'x'}_end.png"))
    b.close()
bad = 0
for i, info in report:
    flag = ((" OVER " + str(info["over"]) if info["over"] else "") + (" MISSING " + str(info["missing"]) if info["missing"] else "")
            + (" FAILED " + str(info["failed"]) if info["failed"] else "") + (" NO GUIDE" if a.guides and info["noguide"] else ""))
    bad += bool(flag)
    print(i, info["id"], flag)
print("console:", json.dumps(errs[:20], indent=0))
sys.exit(1 if bad or errs else 0)
