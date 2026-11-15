/* The template's one figure: x(t) of a damped oscillator, the damping ratio from a slider or a click preset. */
fig("oscillator", {
  defaults: { zeta: 0.1 },
  build(root, D) {
    const svg = el("svg", { viewBox: "0 0 700 500" }, root);
    this.x = lin(0, D.t_end, 90, 680);
    this.y = lin(-1.1, 1.1, 440, 20);
    axes(svg, this.x, this.y, { xl: "time t (s)", yl: "displacement x" });
    this.line = el("path", { class: "trace thick" }, svg);
    this.D = D;
    this.zeta = slider("osc-zeta", (v) => this.set({ zeta: v / 100 }));
  },
  set(s) {
    const { omega, t_end } = this.D, n = 400, ts = [], xs = [];
    for (let i = 0; i <= n; i++) { // exact solution from x = 1, v = 0, any damping ratio
      const t = t_end * i / n, z = s.zeta, a = z * omega;
      let x;
      if (z < 1) { const wd = omega * Math.sqrt(1 - z * z); x = Math.exp(-a * t) * (Math.cos(wd * t) + a / wd * Math.sin(wd * t)); }
      else if (z === 1) x = Math.exp(-omega * t) * (1 + omega * t);
      else { const r = omega * Math.sqrt(z * z - 1), l1 = -a + r, l2 = -a - r; x = (l2 * Math.exp(l1 * t) - l1 * Math.exp(l2 * t)) / (l2 - l1); }
      ts.push(t); xs.push(x);
    }
    this.line.setAttribute("d", path(ts, xs, this.x, this.y));
    this.zeta.value = Math.round(s.zeta * 100);
    $("#osc-zetav").textContent = s.zeta.toFixed(2);
  }
});
