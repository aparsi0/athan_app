/**
 * Living scene engine — the Lake Dock landscape (the only theme), rendered
 * macOS-dynamic-wallpaper style: the photograph's sky is transparent
 * (assets/terrain_d.png + treeline profile assets/ridge_d.json), and the
 * engine draws its own sky BEHIND the real terrain, driven by the
 * visitor's real sun/prayer times.
 *
 * Draw order: sky → stars → sun/moon (+their glow) → photo terrain, so the
 * sun and moon rise from and set behind the treeline, stars are occluded
 * by it, and their light reflects on the water.
 */
const Scene = {
  times: { fajr: 285, sunrise: 370, dhuhr: 801, asr: 1030, maghrib: 1231, isha: 1316 },
  canvas: null, ctx: null, off: null, octx: null,
  W: 0, H: 0, DPR: 1,
  stars: [],
  terrainImg: null, ridge: null, ridgeMax: 0.4,

  init() {
    this.canvas = document.getElementById('scene');
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.off = document.createElement('canvas');
    this.octx = this.off.getContext('2d');

    this.terrainImg = new Image();
    this.terrainImg.src = 'assets/terrain_d.png';
    this.terrainImg.onload = () => this.render();
    fetchWithTimeout('assets/ridge_d.json', 15000)
      .then(r => r.json())
      .then(d => { this.ridge = d; this.ridgeMax = Math.max.apply(null, d); this.render(); })
      .catch(() => {});

    let seed = 42;
    const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    this.stars = Array.from({ length: 170 }, () => ({
      x: rnd(), y: rnd() * 0.62, r: rnd() * 1.2 + 0.25, tw: rnd() * 6.28, a: rnd() * 0.6 + 0.4
    }));

    this.resize();
    addEventListener('resize', () => { this.resize(); this.render(); });
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') this.render();
    });
    setInterval(() => this.render(), 30000);
    this.render();
  },

  setTimes(map) {
    for (const k of Object.keys(map)) {
      if (Number.isFinite(map[k])) this.times[k] = map[k];
    }
    this.render();
  },

  resize() {
    this.DPR = Math.min(2, window.devicePixelRatio || 1);
    this.W = innerWidth; this.H = innerHeight;
    for (const [c, cx] of [[this.canvas, this.ctx], [this.off, this.octx]]) {
      c.width = this.W * this.DPR; c.height = this.H * this.DPR;
      cx.setTransform(this.DPR, 0, 0, this.DPR, 0, 0);
    }
    this.canvas.style.width = this.W + 'px';
    this.canvas.style.height = this.H + 'px';
  },

  /* ---------- palette ---------- */
  _lerp(a, b, t) { return a + (b - a) * t; },
  _clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); },
  _rgb(h) { return [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)]; },
  _mixHex(h1, h2, t) {
    const a = this._rgb(h1), b = this._rgb(h2);
    return '#' + [0, 1, 2].map(i => Math.round(this._lerp(a[i], b[i], t)).toString(16).padStart(2, '0')).join('');
  },
  _mixC(h1, h2, t) {
    const a = this._rgb(h1), b = this._rgb(h2);
    return `rgb(${Math.round(this._lerp(a[0], b[0], t))},${Math.round(this._lerp(a[1], b[1], t))},${Math.round(this._lerp(a[2], b[2], t))})`;
  },

  _anchors() {
    const T = this.times, mid = (a, b) => (a + b) / 2;
    return [
      [T.fajr - 90,            '#040711', '#070c1a', '#0b1326', 0.16, 'Deep night'],
      [T.fajr,                 '#0a1228', '#161f3c', '#3c3a58', 0.26, 'Fajr — first light'],
      [mid(T.fajr, T.sunrise), '#152048', '#333a6e', '#b06a4e', 0.42, 'Dawn'],
      [T.sunrise,              '#2b4a7c', '#7a7ba9', '#f5a55c', 0.60, 'Sunrise'],
      [T.sunrise + 50,         '#4a7ab8', '#8bacd2', '#f7cc90', 0.82, 'Morning'],
      [T.dhuhr,                '#3f88d5', '#79b5e8', '#d3e8f8', 1.00, 'Midday'],
      [T.asr,                  '#3d7ec8', '#83b1e1', '#ead9a9', 0.93, 'Afternoon'],
      [T.maghrib - 50,         '#3a62a2', '#9c88a2', '#f5ad62', 0.76, 'Golden hour'],
      [T.maghrib,              '#253560', '#7c5a7a', '#ee6f3c', 0.52, 'Sunset'],
      [mid(T.maghrib, T.isha), '#101a3a', '#343060', '#7c465e', 0.36, 'Dusk'],
      [T.isha,                 '#070c1e', '#101632', '#1e2446', 0.24, 'Night falls'],
      [T.isha + 80,            '#040711', '#070c1a', '#0b1326', 0.16, 'Night']
    ];
  },

  paletteAt(minute) {
    const A = this._anchors();
    let m = minute;
    if (m < A[0][0]) m += 1440;
    let i = 0;
    while (i < A.length - 1 && m >= A[i + 1][0]) i++;
    if (i >= A.length - 1) i = A.length - 2;
    const t = this._clamp((m - A[i][0]) / Math.max(1, A[i + 1][0] - A[i][0]), 0, 1);
    const P = A[i], Q = A[i + 1];
    return {
      top: this._mixHex(P[1], Q[1], t), mid: this._mixHex(P[2], Q[2], t), hor: this._mixHex(P[3], Q[3], t),
      amb: this._lerp(P[4], Q[4], t), phase: t < 0.5 ? P[5] : Q[5]
    };
  },

  _nowMinutes() {
    const d = new Date();
    return d.getHours() * 60 + d.getMinutes() + d.getSeconds() / 60;
  },

  /* ---------- render ---------- */
  render() {
    if (!this.ctx) return;
    const minute = this._nowMinutes();
    const pal = this.paletteAt(minute);
    const phaseEl = document.getElementById('phaseText');
    if (phaseEl) phaseEl.textContent = pal.phase;

    const { ctx, W, H, times: T } = this;
    ctx.clearRect(0, 0, W, H);

    /* sky */
    const sky = ctx.createLinearGradient(0, 0, 0, H * 0.9);
    sky.addColorStop(0, pal.top); sky.addColorStop(0.55, pal.mid); sky.addColorStop(1, pal.hor);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    /* stars */
    const starA = this._clamp((0.38 - pal.amb) / 0.22, 0, 1);
    if (starA > 0) {
      for (const s of this.stars) {
        ctx.globalAlpha = starA * s.a * (0.75 + 0.25 * Math.sin(minute * 0.5 + s.tw));
        ctx.fillStyle = '#e9eeff';
        ctx.beginPath(); ctx.arc(s.x * W, s.y * H, s.r, 0, 7); ctx.fill();
      }
      ctx.globalAlpha = 1;
    }

    /* horizon geometry from the real treeline */
    const ready = this.terrainImg.complete && this.terrainImg.naturalWidth > 0;
    const box = ready ? this._terrainBox() : null;
    const horizonY = ready && this.ridge
      ? box.dy + this.ridgeMax * box.dh + H * 0.06
      : H * 0.7;
    const peakY = Math.min(H * 0.24, horizonY - H * 0.3);
    const arc = (f) => [this._lerp(W * 0.07, W * 0.93, f), horizonY - Math.sin(Math.PI * f) * (horizonY - peakY)];

    /* sun — dramatic warm bloom near the horizon, subtle glare high up */
    let sunInfo = null, moonInfo = null;
    if (minute >= T.sunrise - 40 && minute <= T.maghrib + 40) {
      const frac = (minute - T.sunrise) / (T.maghrib - T.sunrise);
      const [sx, sy] = arc(this._clamp(frac, -0.06, 1.06));
      const warm = 1 - Math.sin(Math.PI * this._clamp(frac, 0, 1));
      const glowC = this._mixC('#fff3d8', '#ffb765', warm);
      ctx.globalCompositeOperation = 'lighter';
      const glow = ctx.createRadialGradient(sx, sy, 0, sx, sy, H * (0.14 + 0.38 * warm));
      glow.addColorStop(0, glowC.replace('rgb', 'rgba').replace(')', `,${0.18 + 0.5 * warm})`));
      glow.addColorStop(0.4, glowC.replace('rgb', 'rgba').replace(')', `,${0.06 + 0.12 * warm})`));
      glow.addColorStop(1, 'rgba(255,200,120,0)');
      ctx.fillStyle = glow;
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'source-over';
      ctx.fillStyle = this._mixC('#fffbef', '#ffd27a', warm);
      ctx.beginPath(); ctx.arc(sx, sy, H * (0.016 + 0.010 * warm), 0, 7); ctx.fill();
      sunInfo = { sx, sy, warm };
    }

    /* moon — crescent on its own sprite so the cut never erases the sky */
    const nightLen = (T.fajr + 1440 - T.isha) % 1440;
    let nf = null;
    if (minute >= T.isha + 20) nf = (minute - T.isha - 20) / (nightLen + 40);
    else if (minute <= T.fajr + 20) nf = (minute + 1440 - T.isha - 20) / (nightLen + 40);
    if (nf != null && starA > 0.05) {
      const [mx, my] = arc(this._clamp(nf, 0, 1));
      ctx.globalCompositeOperation = 'lighter';
      const mg = ctx.createRadialGradient(mx, my, 0, mx, my, H * 0.16);
      mg.addColorStop(0, 'rgba(205,216,255,0.35)'); mg.addColorStop(1, 'rgba(205,216,255,0)');
      ctx.fillStyle = mg;
      ctx.fillRect(0, 0, W, H);
      ctx.globalCompositeOperation = 'source-over';
      const mr = H * 0.015;
      const spr = document.createElement('canvas');
      spr.width = spr.height = Math.ceil(mr * 2.4);
      const sc = spr.getContext('2d'), c = spr.width / 2;
      sc.fillStyle = '#f2f3ea';
      sc.beginPath(); sc.arc(c, c, mr, 0, 7); sc.fill();
      sc.globalCompositeOperation = 'destination-out';
      sc.beginPath(); sc.arc(c + mr * 0.45, c - mr * 0.28, mr * 0.86, 0, 7); sc.fill();
      ctx.drawImage(spr, mx - c, my - c);
      moonInfo = { mx, my };
    }

    /* the real terrain — drawn last so it occludes sun, moon and stars */
    if (ready) this._drawTerrain(pal, box, sunInfo, moonInfo);
  },

  _terrainBox() {
    const iw = this.terrainImg.naturalWidth, ih = this.terrainImg.naturalHeight;
    const s = Math.max(this.W / iw, this.H / ih);
    return { dx: (this.W - iw * s) / 2, dy: this.H - ih * s, dw: iw * s, dh: ih * s };
  },

  _ridgeYat(fx, box) {
    if (!this.ridge) return this.H * 0.6;
    const imgFx = this._clamp((fx * this.W - box.dx) / box.dw, 0, 1);
    return box.dy + this.ridge[this._clamp(Math.round(imgFx * 127), 0, 127)] * box.dh;
  },

  _drawTerrain(pal, box, sunInfo, moonInfo) {
    const { octx, W, H } = this;
    const dayness = this._clamp((pal.amb - 0.16) / 0.84, 0, 1);
    octx.clearRect(0, 0, W, H);
    octx.filter = `brightness(${(0.36 + 0.72 * dayness).toFixed(3)}) saturate(${(0.55 + 0.55 * dayness).toFixed(3)})`;
    octx.drawImage(this.terrainImg, box.dx, box.dy, box.dw, box.dh);
    octx.filter = 'none';
    octx.globalCompositeOperation = 'source-atop';
    octx.fillStyle = `rgba(16,26,58,${(0.45 * (1 - dayness)).toFixed(3)})`;
    octx.fillRect(0, 0, W, H);
    if (sunInfo && sunInfo.warm > 0.15) {
      const wa = sunInfo.warm;
      octx.fillStyle = `rgba(255,150,70,${(0.14 * wa).toFixed(3)})`;
      octx.fillRect(0, 0, W, H);
      const ry = this._ridgeYat(sunInfo.sx / W, box);
      const wg = octx.createRadialGradient(sunInfo.sx, ry, 0, sunInfo.sx, ry, H * 0.5);
      wg.addColorStop(0, `rgba(255,180,90,${(0.34 * wa).toFixed(3)})`);
      wg.addColorStop(1, 'rgba(255,180,90,0)');
      octx.fillStyle = wg;
      octx.fillRect(0, ry - H * 0.02, W, H);
    }
    if (moonInfo) {
      const ry = this._ridgeYat(moonInfo.mx / W, box);
      const mgw = octx.createRadialGradient(moonInfo.mx, ry, 0, moonInfo.mx, ry, H * 0.4);
      mgw.addColorStop(0, 'rgba(200,215,255,0.20)');
      mgw.addColorStop(1, 'rgba(200,215,255,0)');
      octx.fillStyle = mgw;
      octx.fillRect(0, ry - H * 0.02, W, H);
    }
    octx.globalCompositeOperation = 'source-over';
    this.ctx.drawImage(this.off, 0, 0, W, H);
  }
};
