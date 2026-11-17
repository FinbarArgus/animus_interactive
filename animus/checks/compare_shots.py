"""
Compare two directories of screenshots pixel by pixel (same file names), e.g. a deck before and after a refactor,
both taken with check_deck.py --frozen.

    python -m animus.checks.compare_shots before/ after/ [--ignore x0,y0,x1,y1 ...]

Prints each differing image with its changed box, the number of changed pixels and the largest channel difference.
Chromium's anti-aliasing can move a few hundred pixels by under 10/255 between runs of the same build: look at those
before calling them changes (run the baseline twice to see the noise).
"""
import sys
from pathlib import Path

from PIL import Image, ImageChops

import argparse  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("a", type=Path)
ap.add_argument("b", type=Path)
ap.add_argument("--ignore", action="append", default=[], help="x0,y0,x1,y1: a box blanked in both (e.g. an added button)")
args = ap.parse_args()
a, b = args.a, args.b
boxes = [tuple(int(v) for v in s.split(",")) for s in args.ignore]
bad, n = [], 0
names = sorted(p.name for p in a.glob("*.png"))
unmatched = sorted(set(names) ^ {p.name for p in b.glob("*.png")})
for name in names:
    if not (b / name).exists():
        continue
    n += 1
    ia, ib = Image.open(a / name).convert("RGB"), Image.open(b / name).convert("RGB")
    if ia.size != ib.size:
        bad.append(f"{name} size {ia.size} vs {ib.size}")
        continue
    for box in boxes:
        ia.paste((0, 0, 0), box)
        ib.paste((0, 0, 0), box)
    d = ImageChops.difference(ia, ib)
    box = d.getbbox()
    if box:
        h = ImageChops.lighter(ImageChops.lighter(*d.split()[:2]), d.split()[2]).histogram()  # largest channel difference
        bad.append(f"{name} box {box} pixels {sum(h[1:])} max {max(i for i, v in enumerate(h) if v)}")
print(f"{n} compared, {len(bad)} differ, {len(unmatched)} unmatched {unmatched[:10]}")
print("\n".join(bad))
sys.exit(1 if bad or unmatched else 0)
