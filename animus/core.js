/*
 * animus_interactive runtime: SVG helpers, the figure registry, click presets, equation-term links, hover tips,
 * data-driven numbers and speaker-view sync. The build (animus/build.py) concatenates it before the deck's own
 * scripts in one <script>, so "use strict" and these globals apply to them.
 *
 * Data: D is the JSON the build inlines (<script type="application/json" id="deck-data">).
 * Figures: fig("name", { build(root, D), set(state), defaults }) registers a figure that lives in <div data-fig="name">
 * on its slide. set(state) merges and redraws; each change is broadcast so the speaker view's copy of the slide
 * follows. Hidden fragments <span class="fragment preset" data-preset='{...}'> set the slide's figure when a click
 * reaches them, so the clicker alone can run every figure. A button .reset on the slide restores the defaults.
 * Terms: an equation term \class{term t-name}{...} highlights on hover or on a fragment with data-hl="t-name", and
 * fires a "term" event figures can listen to. A <dl class="tips"> on the slide (dt "t-name", dd text) gives it a tip.
 * Guides: a <div class="guide"> in a slide is tutorial text: the slide shows only a "?" at the bottom, and
 * hovering it (or a click, which pins it) shows the guide. Presenting, don't hover; reading alone, it guides.
 * Numbers: <span data-num="path.to.value|how"> prints a value from D (see numberFrom).
 * Config: window.ANIMUS = { dataId, channel, reveal }, set by the build; reveal holds Reveal options that override
 * the defaults in boot().
 */
"use strict";
const ANIMUS_CFG = window.ANIMUS || {};
const NS = "http://www.w3.org/2000/svg";
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const D = JSON.parse(document.getElementById(ANIMUS_CFG.dataId || "deck-data").textContent);

function el(tag, attrs = {}, parent) {
  const e = document.createElementNS(NS, tag);
  for (const k in attrs) if (attrs[k] !== undefined) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
function txt(parent, s, attrs) { const t = el("text", attrs, parent); t.textContent = s; return t; }
const css = (v) => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
function lin(d0, d1, r0, r1) {
  const f = (x) => r0 + (x - d0) / (d1 - d0) * (r1 - r0);
  return Object.assign(f, { inv: (y) => d0 + (y - r0) / (r1 - r0) * (d1 - d0), r0, r1, d0, d1 });
}
function logs(d0, d1, r0, r1) { // log10 scale on positive values
  const a = Math.log10(d0), b = Math.log10(d1);
  const f = (x) => r0 + (Math.log10(Math.max(x, 1e-300)) - a) / (b - a) * (r1 - r0);
  return Object.assign(f, { inv: (y) => 10 ** (a + (y - r0) / (r1 - r0) * (b - a)), r0, r1, d0, d1, log: true });
}
function path(xs, ys, x, y) {
  let d = "", pen = false;
  for (let i = 0; i < xs.length; i++) {
    const a = xs[i], b = ys[i];
    if (a == null || b == null || !isFinite(a) || !isFinite(b)) { pen = false; continue; }
    d += (pen ? "L" : "M") + x(a).toFixed(1) + "," + y(b).toFixed(1); pen = true;
  }
  return d;
}
function fmt(v, n = 3) {
  if (v == null || !isFinite(v)) return "–";
  if (v === 0) return "0";
  const e = Math.floor(Math.log10(Math.abs(v)));
  if (e >= -2 && e <= 3) return (+v.toPrecision(n)).toString();
  return (v / 10 ** e).toFixed(1) + "×10" + sup(e);
}
const sup = (e) => String(e).replace(/-/g, "⁻").replace(/\d/g, (d) => "⁰¹²³⁴⁵⁶⁷⁸⁹"[d]);
function niceTicks(lo, hi, n = 5) {
  const step0 = (hi - lo) / n, mag = 10 ** Math.floor(Math.log10(step0));
  const step = [1, 2, 2.5, 5, 10].map((s) => s * mag).find((s) => s >= step0) || step0;
  const out = []; for (let v = Math.ceil(lo / step) * step; v <= hi + 1e-9 * step; v += step) out.push(+v.toPrecision(10));
  return out;
}
function axes(g, x, y, o = {}) {
  const xt = o.xt || (x.log ? decades(x.d0, x.d1) : niceTicks(x.d0, x.d1, o.nx || 5));
  const yt = o.yt || (y.log ? decades(y.d0, y.d1) : niceTicks(Math.min(y.d0, y.d1), Math.max(y.d0, y.d1), o.ny || 4));
  const a = el("g", { class: "axes" }, g);
  const ylo = Math.max(y.r0, y.r1), yhi = Math.min(y.r0, y.r1);
  const ylabs = yt.map((v) => (o.yf ? o.yf(v) : (y.log ? "10" + sup(Math.round(Math.log10(v))) : fmt(v, 4))));
  yt.forEach((v, i) => {
    el("line", { class: "gridline", x1: x.r0, x2: x.r1, y1: y(v), y2: y(v) }, a);
    txt(a, ylabs[i], { class: "tick", x: x.r0 - 8, y: y(v) + 5, "text-anchor": "end" });
  });
  xt.forEach((v) => txt(a, o.xf ? o.xf(v) : (x.log ? "10" + sup(Math.round(Math.log10(v))) : fmt(v, 4)), { class: "tick", x: x(v), y: ylo + 21, "text-anchor": "middle" }));
  el("line", { class: "ax", x1: x.r0, x2: x.r1, y1: ylo, y2: ylo }, a);
  el("line", { class: "ax", x1: x.r0, x2: x.r0, y1: ylo, y2: yhi }, a);
  if (o.xl) xLabel(a, o.xl, (x.r0 + x.r1) / 2, ylo + 46);
  if (o.yl) yLabel(a, o.yl, Math.max(16, x.r0 - 8.5 * Math.max(0, ...ylabs.map((t) => t.length)) - 26), (ylo + yhi) / 2);
  return a;
}
/* axis titles: x centred under the plot; y rotated to run up the y axis */
function xLabel(g, s, x, y) { return txt(g, s, { class: "axlab", x, y, "text-anchor": "middle" }); }
function yLabel(g, s, x, y) { return txt(g, s, { class: "axlab", transform: `translate(${x},${y}) rotate(-90)`, "text-anchor": "middle" }); }
function decades(a, b) { const out = []; for (let e = Math.ceil(Math.log10(a) - 1e-9); e <= Math.floor(Math.log10(b) + 1e-9); e++) out.push(10 ** e); return out; }
function svgPoint(svg, ev) { const p = svg.createSVGPoint(); p.x = ev.clientX; p.y = ev.clientY; return p.matrixTransform(svg.getScreenCTM().inverse()); }
function onDrag(svg, fn) {
  let on = false;
  svg.addEventListener("pointerdown", (e) => { e.preventDefault(); on = true; svg.setPointerCapture(e.pointerId); fn(svgPoint(svg, e), e); });
  svg.addEventListener("pointermove", (e) => { if (on) fn(svgPoint(svg, e), e); });
  svg.addEventListener("pointerup", () => { on = false; });
  svg.addEventListener("pointercancel", () => { on = false; });
}
function diverging(z, lim = 2.5) { // blue (negative) - paper - orange (positive)
  const t = Math.max(-1, Math.min(1, z / lim)), f = Math.abs(t);
  const a = t < 0 ? [31, 111, 196] : [212, 115, 15], w = [240, 241, 237];
  return `rgb(${a.map((c, i) => Math.round(w[i] + (c - w[i]) * f)).join(",")})`;
}
function control(id, onPick) { // segmented buttons <span class="seg" id=...><button data-v>...</button></span>
  const btns = $$("#" + id + " button");
  const val = (b) => b.dataset.v ?? b.textContent;
  const pick = (v) => btns.forEach((b) => b.setAttribute("aria-pressed", String(val(b) === String(v))));
  btns.forEach((b) => b.addEventListener("click", () => { pick(val(b)); onPick(val(b)); }));
  return pick;
}
function slider(id, onInput) { const s = document.getElementById(id); s.addEventListener("input", () => onInput(+s.value)); return s; }

/* ---------- figure registry, sync, presets ---------- */
const FIGS = {};
const chan = "BroadcastChannel" in window ? new BroadcastChannel(ANIMUS_CFG.channel || "animus") : null;
let remote = false;
function fig(name, spec) {
  FIGS[name] = spec;
  const inner = spec.set;
  spec.state = { ...spec.defaults };
  spec.set = (s) => {
    Object.assign(spec.state, s);
    inner.call(spec, spec.state);
    if (chan && !remote) chan.postMessage({ fig: name, state: spec.state });
  };
}
if (chan) chan.onmessage = (e) => { const f = FIGS[e.data.fig]; if (!f || !f.ready) return; remote = true; try { f.set(e.data.state); } finally { remote = false; } };

function figOn(slide) { const host = slide && $("[data-fig]", slide); return host ? FIGS[host.dataset.fig] : null; }
function applyPresets(slide) {
  const f = figOn(slide); if (!f || !f.ready) return;
  const shown = $$(".fragment.preset.visible", slide);
  if (shown.length) f.set(JSON.parse(shown[shown.length - 1].dataset.preset));
  else if ($$(".fragment.preset", slide).length) f.set({ ...f.defaults });
}
function termFragments(slide) {
  if (!slide) return;
  $$(".term", slide).forEach((t) => t.classList.remove("hl"));
  const cur = $(".fragment.current-fragment[data-hl]", slide);
  if (cur) cur.dataset.hl.split(" ").forEach((c) => $$("." + c, slide).forEach((t) => t.classList.add("hl")));
}
/* Hover tips: a <dl class="tips"> on a slide pairs a term class (dt) with its meaning (dd); hovering that term shows it. */
const tipBox = (() => { const d = document.createElement("div"); d.className = "tipbox"; d.hidden = true; document.body.appendChild(d); return d; })();
function linkTerms() {
  $$(".term").forEach((t) => {
    const cls = [...t.classList].find((c) => c.startsWith("t-")); if (!cls) return;
    if (t instanceof SVGGElement) { // a transparent box over the whole term (sized by sizeHits), so the gaps between glyphs respond
      const hit = document.createElementNS(NS, "rect");
      hit.setAttribute("class", "hitbox"); hit.setAttribute("fill", "transparent"); hit.setAttribute("pointer-events", "all");
      t.insertBefore(hit, t.firstChild);
    }
    const slide = t.closest("section"), dt = slide && [...slide.querySelectorAll(".tips dt")].find((x) => x.textContent.trim() === cls);
    const tip = dt ? dt.nextElementSibling.textContent : null;
    const fire = (on) => { $$("." + cls, slide || document).forEach((x) => x.classList.toggle("hl", on)); document.dispatchEvent(new CustomEvent("term", { detail: { cls, on } })); };
    t.addEventListener("mouseenter", (e) => { fire(true); if (tip) { tipBox.textContent = tip; tipBox.hidden = false; placeTip(e); } });
    t.addEventListener("mousemove", (e) => { if (tip) placeTip(e); });
    t.addEventListener("mouseleave", () => { fire(false); tipBox.hidden = true; });
  });
}
function sizeHits(slide) { // hidden slides measure zero: size a slide's term boxes when it is shown
  if (!slide) return;
  slide.querySelectorAll(".term > rect.hitbox").forEach((hit) => {
    const g = hit.parentNode; hit.setAttribute("width", 0);
    const bb = g.getBBox(); ["x", "y", "width", "height"].forEach((k) => hit.setAttribute(k, bb[k]));
  });
}
function placeTip(e) {
  const w = tipBox.offsetWidth, h = tipBox.offsetHeight;
  tipBox.style.left = Math.min(e.clientX + 16, innerWidth - w - 8) + "px";
  tipBox.style.top = (e.clientY + 18 + h > innerHeight ? e.clientY - h - 12 : e.clientY + 18) + "px";
}
function boot() {
  for (const host of $$("[data-fig]")) {
    const f = FIGS[host.dataset.fig];
    if (!f) { console.error("no figure", host.dataset.fig); continue; }
    try { f.build(host, D); f.ready = true; f.set({ ...f.defaults }); } catch (err) { console.error(host.dataset.fig, err); host.textContent = "Figure failed: " + err.message; }
    const reset = host.closest("section")?.querySelector(".reset");
    if (reset) reset.addEventListener("click", () => f.set({ ...f.defaults }));
  }
  for (const n of $$("[data-num]")) n.textContent = numberFrom(n.dataset.num);
  linkTerms();
  addGuides();
  const deck = new Reveal({
    width: 1280, height: 720, margin: 0.02, hash: true, center: false, touch: false, controls: true, progress: true,
    slideNumber: "c/t", transition: "fade", transitionSpeed: "fast", backgroundTransition: "none", pdfMaxPagesPerSlide: 1,
    keyboardCondition: () => !(document.activeElement && document.activeElement.type === "range"),
    keyboard: { 68: toggleTheme }, // D: light/dark, whatever the laptop's setting
    plugins: window.RevealNotes ? [RevealNotes] : [],
    ...(ANIMUS_CFG.reveal || {})
  });
  window.deck = deck;
  deck.initialize().then(() => { applyPresets(deck.getCurrentSlide()); termFragments(deck.getCurrentSlide()); sizeHits(deck.getCurrentSlide()); });
  deck.on("slidechanged", (e) => { document.activeElement?.blur?.(); tipBox.hidden = true; unpinGuides(); applyPresets(e.currentSlide); termFragments(e.currentSlide); sizeHits(e.currentSlide); });
  for (const ev of ["fragmentshown", "fragmenthidden"]) deck.on(ev, () => { applyPresets(deck.getCurrentSlide()); termFragments(deck.getCurrentSlide()); });
}
/* Guides: a "?" button before each slide's .guide; CSS shows the guide while the button is hovered or focused,
   or while the guide is pinned by a click. */
function addGuides() {
  for (const g of $$(".reveal .slides section > .guide")) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "guide-q"; b.textContent = "?"; b.setAttribute("aria-label", "Guide to this slide");
    b.addEventListener("click", () => { const on = !g.classList.contains("pinned"); unpinGuides(); g.classList.toggle("pinned", on); });
    g.before(b);
  }
}
function unpinGuides() { $$(".guide.pinned").forEach((g) => g.classList.remove("pinned")); }
function toggleTheme() {
  const root = document.documentElement, dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
  for (const f of Object.values(FIGS)) if (f.ready) f.set({}); // redraw colours read from the theme
}
/* numbers printed in slide text come from the data: data-num="results.tables.13_simple_starling_more.rows[beat map].speedup|x" */
function numberFrom(spec) {
  const [p, how] = spec.split("|");
  let v = D;
  for (const part of p.split(".")) {
    const m = part.match(/^(.+?)\[(.+)\]$/);
    if (m) { v = v[m[1]]; v = Array.isArray(v) ? v.find((r) => r.method === m[2]) ?? v[+m[2]] : v[m[2]]; }
    else v = v[part];
    if (v == null) return "?";
  }
  if (how === "x") return fmt(v, 3) + "×";
  if (how === "s2") return String(+v.toPrecision(2)); // two significant figures, no unit
  if (how === "i") return String(Math.round(v));
  if (how === "pct") return (v * 100).toFixed(1) + " %";
  return fmt(v, 3);
}
