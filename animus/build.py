"""
Build a deck into one offline HTML file.

Inlines reveal.js 5.1.0 (with its speaker-notes plugin), MathJax 3.2.2 (SVG output, so no font files), three web
fonts (Space Grotesk, Public Sans, JetBrains Mono) as data URIs, animus's style.css and core.js, then the deck's own
styles, data and scripts. The libraries and fonts are downloaded once into a vendor cache (gitignored) and reused.

A deck calls it from its own short build script:

    from animus.build import build
    build(deck=SRC / "deck.html", scripts=[SRC / "figs.js"], styles=[SRC / "style.css"], data=HERE / "data.json",
          title="My talk", out=HERE / "dist" / "my_talk.html", artifact="--artifact" in sys.argv,
          check="--check" in sys.argv)

artifact=True writes a claude.ai page: no document skeleton, no URL hash routing. check=True first fails on a
script syntax error (one would stop the whole deck loading) and on any problem the deck's own check hook reports.
"""
import base64
import json
import re
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable, Iterable

HERE = Path(__file__).resolve().parent
VENDOR = HERE.parent / "vendor"
LIBS = {
    "reveal.css": "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.css",
    "reveal.js": "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/reveal.min.js",
    "notes.js": "https://cdnjs.cloudflare.com/ajax/libs/reveal.js/5.1.0/plugin/notes/notes.min.js",
    "mathjax.js": "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg-full.js",
}
FONTS = ("https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700"
         "&family=Public+Sans:ital,wght@0,400;0,600;1,400&family=JetBrains+Mono:wght@400;600&display=swap")
KEEP_SUBSETS = ("latin", "latin-ext", "greek")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

MATHJAX_CONFIG = """window.MathJax = {
  tex: { inlineMath: [["\\\\(", "\\\\)"]], displayMath: [["\\\\[", "\\\\]"]] },
  svg: { fontCache: "global" },
  options: { enableMenu: false },
  startup: { pageReady: () => MathJax.startup.defaultPageReady().then(boot) }
};"""


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def vendored(name: str, vendor: Path = VENDOR) -> str:
    path = vendor / name
    if not path.exists():
        vendor.mkdir(parents=True, exist_ok=True)
        path.write_bytes(fetch(LIBS[name]))
    return path.read_text(encoding="utf-8")


def fonts_css(vendor: Path = VENDOR) -> str:
    """The Google Fonts CSS with the kept subsets' woff2 files inlined as data URIs."""
    path = vendor / "fonts.css"
    if path.exists():
        return path.read_text()
    css = fetch(FONTS).decode()
    out = []
    for comment, block in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face\s*{[^}]*})", css):
        if comment not in KEEP_SUBSETS:
            continue
        url = re.search(r"url\((https://[^)]+)\)", block).group(1)
        data = base64.b64encode(fetch(url)).decode()
        out.append(block.replace(url, "data:font/woff2;base64," + data))
    vendor.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(out))
    return path.read_text()


def script(code: str) -> str:
    return "<script>" + code.replace("</script", "<\\/script") + "</script>"


def data_uri(path: Path, mime: str = "image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def check_scripts(code: str) -> str:
    """node --check on the concatenated scripts: the error text, or '' if they parse."""
    with tempfile.TemporaryDirectory() as tmp:
        js = Path(tmp) / "deck_scripts.js"
        js.write_text(code)
        r = subprocess.run(["node", "--check", str(js)], capture_output=True, text=True)
    return r.stderr if r.returncode else ""


def build(deck: Path, scripts: Iterable[Path], out: Path, *, styles: Iterable[Path] = (), data: Path | None = None,
          title: str = "Deck", artifact: bool = False, check: bool = False,
          check_hook: Callable[[str], list[str]] | None = None, replacements: dict[str, str] | None = None,
          channel: str = "animus", vendor: Path = VENDOR) -> Path:
    """
    Write `out`: deck.html (the reveal <div class="reveal">...</div>) with `replacements` applied, base and deck
    styles, the JSON `data` as D, core.js and then `scripts` in one <script>, MathJax last (its pageReady boots the
    deck). `channel` names the BroadcastChannel the speaker view syncs over. `check_hook(deck_html)` returns
    problems that fail a check build.
    """
    html = Path(deck).read_text()
    for k, v in (replacements or {}).items():
        html = html.replace(k, v)
    code = "\n".join([(HERE / "core.js").read_text()] + [Path(f).read_text() for f in scripts])
    if check:
        problems = check_hook(html) if check_hook else []
        if problems:
            raise SystemExit(f"deck check failed: {problems}")
        err = check_scripts(code)
        if err:
            raise SystemExit("scripts do not parse:\n" + err)
    config = {"dataId": "deck-data", "channel": channel}
    if artifact:
        config["reveal"] = {"hash": False}
    css = [fonts_css(vendor), vendored("reveal.css", vendor), (HERE / "style.css").read_text()]
    css += [Path(f).read_text() for f in styles]
    style_tags = "".join(f"<style>{c}</style>\n" for c in css)
    head = (f"<title>{title}</title>\n" + style_tags) if artifact else (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
        f"<title>{title}</title>\n" + style_tags + "</head><body>\n")
    data_json = Path(data).read_text() if data else "{}"
    body = (html + "\n<script type=\"application/json\" id=\"deck-data\">" + data_json.replace("</", "<\\/") + "</script>\n"
            + script(vendored("reveal.js", vendor)) + "\n" + script(vendored("notes.js", vendor)) + "\n"
            + script("window.ANIMUS = " + json.dumps(config) + ";") + "\n"
            + script(code) + "\n"
            + script(MATHJAX_CONFIG) + "\n" + script(vendored("mathjax.js", vendor)) + "\n"
            + ("" if artifact else "</body></html>\n"))
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(head + body)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")
    return out
