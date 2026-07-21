/**
 * Scene — 19-image live day/night sky, anchored to SOLAR moments.
 * ---------------------------------------------------------------------------
 * Self-contained vanilla JS. No frameworks, no build step, no CDNs.
 * Renders 19 hand-painted skies (assets/sky_01.jpg … sky_19.jpg, same
 * composition, only the light changes) into a fixed full-screen <canvas
 * id="scene"> that sits BEHIND the page content, cross-fading continuously
 * between the two images that bracket the current instant so the whole day
 * reads as one flowing animation.
 *
 * PUBLIC API (all image timing derives from these):
 *   Scene.init()
 *   Scene.setTimes({ fajr, sunrise, dhuhr, asr, maghrib, isha })  // minutes
 *                                                                 // since midnight
 *
 * IMAGE ↔ SOLAR MAP (01 = deepest night … 19 = late night, then wraps to 01):
 *   01 deep night (mid Isha→Fajr)     11 early afternoon (noon→sunset 25%)
 *   02 late night (75% → Fajr)        12 mid-afternoon (40%)
 *   03 Fajr — first light             13 late afternoon (60%)
 *   04 dawn (mid Fajr→sunrise)        14 golden hour (~80%)
 *   05 sunrise                        15 just before sunset (96%)
 *   06 morning (sunrise→noon 25%)     16 sunset (Maghrib)
 *   07 morning (50%)                  17 dusk (mid sunset→Isha)
 *   08 late morning (75%)             18 Isha — nightfall
 *   09 approaching noon (95%)         19 night (Isha + ~1h)
 *   10 solar noon (Dhuhr)
 *
 * Overlays (drawn at runtime, kept subtle so they never fight the paintings):
 *   drifting clouds by day · twinkling stars + occasional shooting star at
 *   night · birds at dawn/dusk · gentle light shimmer on the water.
 * Performance: only the current + next image are fetched (never all 19);
 *   requestAnimationFrame; rendering pauses while the tab is hidden.
 */
const Scene = {
  IMG_COUNT: 20,
  IMG_PATH: i => `assets/sky_${String(i).padStart(2, '0')}.jpg`,

  // Cross-fade behavior: each painting HOLDS solid for most of its segment,
  // then fades to the next over a short window at the segment boundary
  // (max 30 seconds, at most 35% of the segment). Kept deliberately brief:
  // most night frames each paint the moon at a different sky position, so
  // any longer blend shows two moons at once (the same issue as "two suns"
  // during the day) — a 30-second window is quick enough that it isn't
  // noticeable, while every arrival time below still lands exactly on time.
  FADE_MAX_MIN: 0.5,
  FADE_MAX_FRAC: 0.35,

  // Fallback prayer times (minutes since midnight) until the app calls setTimes.
  times: { fajr: 300, sunrise: 372, dhuhr: 786, asr: 1005, maghrib: 1200, isha: 1290 },

  canvas: null, ctx: null, W: 0, H: 0, DPR: 1,
  cache: {}, anchors: [], t0: 0, raf: 0, paused: false,
  stars: [], clouds: [], shoot: null, nextShoot: 6,

  /* ============================ INIT ============================ */
  init() {
    this.canvas = document.getElementById('scene');
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    this.t0 = performance.now();

    this._buildAnchors();

    // Deterministic overlay fields.
    let s1 = 42; const r1 = () => (s1 = (s1 * 16807) % 2147483647) / 2147483647;
    this.stars = Array.from({ length: 170 }, () => ({ x: r1(), y: r1() * 0.5, r: r1() * 1.2 + 0.2, tw: r1() * 6.28, a: r1() * 0.5 + 0.4 }));
    let s2 = 7; const r2 = () => (s2 = (s2 * 16807) % 2147483647) / 2147483647;
    this.clouds = Array.from({ length: 6 }, () => ({ x: r2(), y: 0.07 + r2() * 0.26, s: 0.7 + r2() * 1.0, sp: 0.0025 + r2() * 0.006, p: r2() }));

    this.resize();
    addEventListener('resize', () => this.resize());
    document.addEventListener('visibilitychange', () => {
      this.paused = document.hidden;
      if (!this.paused) { this.t0 = performance.now() - this._elapsed; this._loop(); }
    });

    this._loop();
  },

  setTimes(map) {
    for (const k of Object.keys(map || {})) if (Number.isFinite(map[k])) this.times[k] = map[k];
    this._buildAnchors();
  },

  resize() {
    const c = this.canvas; if (!c) return;
    this.DPR = Math.min(2, window.devicePixelRatio || 1);
    this.W = innerWidth; this.H = innerHeight;
    c.width = this.W * this.DPR; c.height = this.H * this.DPR;
    c.getContext('2d').setTransform(this.DPR, 0, 0, this.DPR, 0, 0);
    c.style.width = this.W + 'px'; c.style.height = this.H + 'px';
  },

  /* ============================ SOLAR ANCHORS ============================ */
  // Build anchor times on a monotonic timeline that starts at Fajr and runs
  // one full solar day to Fajr+1440.
  //
  // These anchors follow an exact spec (each arrival tied to a prayer/solar
  // moment, matched against what's actually painted in each frame):
  //   1  — Fajr itself (frame 1 must be on screen when the Fajr athan plays),
  //        holds for 20 minutes.
  //   2,3,4,5 — divide the remaining time from Fajr+20 up to Sunrise into
  //        four equal spans, one frame each; frame 5 holds until Sunrise.
  //   6  — Sunrise (the frame where the sun disc rises); sun visible 6-16.
  //   7-16 — sunrise → solar noon (Dhuhr) → Maghrib, as before.
  //   17 — arrives 1 minute BEFORE Maghrib (sun must already be gone by the
  //        time Maghrib is called).
  //   18 — dusk; arrives partway through the evening and holds until Isha.
  //   19 — must already be on screen the moment Isha is called (the brief
  //        default fade below lands it exactly on time without a long
  //        two-moon blend along the way).
  //   20 — the user's moon-mid-sky bridge frame, mid-way through the night.
  // 19 → 20 → 1 span the whole night (early/mid/deep) and 1 arrives exactly
  // at the next Fajr, closing the loop.
  _buildAnchors() {
    const T = this.times;
    const F = T.fajr, SR = T.sunrise, N = T.dhuhr, MG = T.maghrib, I = T.isha;
    const nextF = F + 1440;
    const nightLen = nextF - I;
    const lerp = (a, b, t) => a + (b - a) * t;

    // Fajr holds 20 minutes, then 2/3/4/5 evenly split what's left until Sunrise.
    const dawnStart = F + 20;
    const dawnSpan = SR - dawnStart;

    // index -> absolute minute on the [F, F+1440] timeline
    const at = {
      1: F,                              // Fajr — frame 1 must be on screen
      2: dawnStart,
      3: dawnStart + dawnSpan * 0.25,
      4: dawnStart + dawnSpan * 0.50,
      5: dawnStart + dawnSpan * 0.75,     // holds until Sunrise
      6: SR,                             // Sunrise — sun disc rises
      7: lerp(SR, N, 0.25),
      8: lerp(SR, N, 0.50),
      9: lerp(SR, N, 0.75),
      10: N,                             // solar noon (Dhuhr)
      11: lerp(N, MG, 0.16),
      12: lerp(N, MG, 0.32),
      13: lerp(N, MG, 0.48),
      14: lerp(N, MG, 0.64),
      15: lerp(N, MG, 0.80),
      16: lerp(N, MG, 0.93),             // sun still visible, low on horizon
      17: MG - 1,                        // 1 minute before Maghrib — sun gone
      18: lerp(MG - 1, I - 20, 0.5),      // dusk; holds until Isha-20
      19: I,                             // Isha — frame 19 must already be on screen
      20: I + nightLen * 0.5             // moon mid-sky bridge, mid-night
    };
    // Ordered sequence (image index + time), Fajr → … → Fajr+1440 (wrap = img 1).
    const order = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20];
    this.anchors = order.map(i => ({ i, t: at[i] }));
    this.anchors.push({ i: 1, t: nextF }); // wrap sentinel
    this._fajr = F;

    // Per-segment fade-duration overrides (minutes), keyed by the ARRIVING
    // frame's index — unused for now. Frame 18 already holds until Isha-20
    // via its own anchor above; the transition into 19 then uses the same
    // brief default fade as everywhere else, so it still lands exactly on
    // frame 19 at Isha without a long two-moon blend along the way.
    this._fadeOverride = {};
  },

  // Returns { a, b, frac, ci } — bracketing image indices, blend fraction, and
  // a continuous position (0..19) used to drive the overlays.
  _position(nowMin) {
    const F = this._fajr;
    let t = nowMin;
    if (t < F) t += 1440;                 // pre-dawn belongs to previous night
    if (t >= F + 1440) t -= 1440;
    const A = this.anchors;
    for (let k = 0; k < A.length - 1; k++) {
      if (t >= A[k].t && t <= A[k + 1].t) {
        const span = A[k + 1].t - A[k].t || 1;
        const raw = (t - A[k].t) / span;
        // Hold solid, then fade only inside the boundary window — a short
        // default window, or an explicit override for specific arrivals.
        const override = this._fadeOverride && this._fadeOverride[A[k + 1].i];
        const fadeLen = override != null
          ? Math.min(override, span)
          : Math.min(this.FADE_MAX_MIN, span * this.FADE_MAX_FRAC);
        const fadeStart = A[k + 1].t - fadeLen;
        let frac = 0;
        if (t >= fadeStart) {
          const f = (t - fadeStart) / (fadeLen || 1);
          frac = f * f * (3 - 2 * f); // smoothstep inside the fade window
        }
        return { a: A[k].i, b: A[k + 1].i, frac, ci: k + raw };
      }
    }
    return { a: 1, b: 1, frac: 0, ci: 0 };
  },

  /* ============================ IMAGE CACHE (current + next only) ============================ */
  _img(idx) {
    let e = this.cache[idx];
    if (!e) {
      const im = new Image();
      e = this.cache[idx] = { im, ready: false };
      im.onload = () => { e.ready = true; };
      im.decoding = 'async';
      im.src = this.IMG_PATH(idx);
    }
    return e;
  },
  // Keep only the two active images resident (plus a tiny grace set), so we
  // never hold all 19 at once.
  _evictExcept(keep) {
    for (const k of Object.keys(this.cache)) {
      if (!keep.includes(+k)) delete this.cache[k];
    }
  },

  /* ============================ MATH ============================ */
  _clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); },
  _smooth(a, b, x) { const t = this._clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); },
  _gauss(x, mu, sig) { const d = (x - mu) / sig; return Math.exp(-d * d); },

  _phaseName(ci) {
    const names = {
      1: 'Fajr — first light', 2: 'Dawn', 3: 'Dawn', 4: 'Dawn', 5: 'Dawn',
      6: 'Sunrise', 7: 'Morning', 8: 'Morning', 9: 'Late morning', 10: 'Midday',
      11: 'Early afternoon', 12: 'Afternoon', 13: 'Afternoon', 14: 'Late afternoon',
      15: 'Golden hour', 16: 'Golden hour', 17: 'Sunset', 18: 'Dusk', 19: 'Nightfall', 20: 'Night'
    };
    // nearest anchor in the ordered sequence
    const A = this.anchors, k = Math.round(this._clamp(ci, 0, A.length - 1));
    return names[A[k] ? A[k].i : 1] || '';
  },

  /* ============================ LOOP ============================ */
  _loop() {
    cancelAnimationFrame(this.raf);
    const step = () => {
      // Never break the rAF chain — a break while hidden left the scene
      // frozen forever. When the tab is hidden the browser stops servicing
      // rAF anyway, so keeping the chain alive costs nothing.
      if (!this.paused) {
        this._elapsed = performance.now() - this.t0;
        this.render();
      }
      this.raf = requestAnimationFrame(step);
    };
    step();
    // Safety net: also render on a slow interval (covers rAF quirks and
    // big clock jumps while the tab was asleep).
    if (!this._safety) {
      this._safety = setInterval(() => { if (!document.hidden) this.render(); }, 30000);
    }
  },

  _nowMinutes() {
    if (Number.isFinite(this._debugMinutes)) return this._debugMinutes;
    const d = new Date();
    return d.getHours() * 60 + d.getMinutes() + d.getSeconds() / 60;
  },

  /* ============================ RENDER ============================ */
  render() {
    if (!this.ctx) return;
    const { ctx, W, H } = this;
    const time = (performance.now() - this.t0) / 1000;
    const nowMin = this._nowMinutes();

    const pos = this._position(nowMin);

    // Only fetch the two active frames; drop the rest.
    const cur = this._img(pos.a), nxt = this._img(pos.b);
    this._evictExcept([pos.a, pos.b]);

    ctx.clearRect(0, 0, W, H);
    if (cur.ready) { ctx.globalAlpha = 1; this._cover(cur.im); }
    else { ctx.fillStyle = '#0a1326'; ctx.fillRect(0, 0, W, H); }
    if (nxt.ready && pos.b !== pos.a && pos.frac > 0.001) {
      ctx.globalAlpha = pos.frac; this._cover(nxt.im); ctx.globalAlpha = 1;
    }

    this._overlays(ctx, time, nowMin, pos.ci);
    this._readout(nowMin, pos.ci);
  },

  _cover(img) {
    const { ctx, W, H } = this;
    const iw = img.naturalWidth || img.width, ih = img.naturalHeight || img.height;
    if (!iw) return;
    const s = Math.max(W / iw, H / ih);
    const w = iw * s, h = ih * s;
    ctx.drawImage(img, (W - w) / 2, (H - h) * 0.5, w, h);
  },

  /* ---------- overlays (all subtle) ---------- */
  _overlays(ctx, t, nowMin, ci) {
    const { W, H } = this;
    const T = this.times, F = T.fajr, SR = T.sunrise, MG = T.maghrib, I = T.isha;

    // Night factor for stars (dark sky only).
    let night = 0;
    if (nowMin >= MG) night = this._smooth(MG + 10, I + 30, nowMin);
    else if (nowMin <= SR) night = 1 - this._smooth(F - 20, SR, nowMin);
    const day = this._clamp(this._smooth(SR - 10, SR + 55, nowMin) * (1 - this._smooth(MG - 55, MG + 10, nowMin)), 0, 1);
    const dt = Math.min(0.1, t - (this._prevT == null ? t : this._prevT)); // seconds since last frame (clamped for tab resume)
    this._prevT = t;

    // Stars (upper sky), very light so painted stars stay dominant.
    if (night > 0.04) {
      for (const s of this.stars) {
        ctx.globalAlpha = night * s.a * (0.4 + 0.6 * Math.abs(Math.sin(t * 1.4 + s.tw))) * 0.5;
        ctx.fillStyle = '#eaf0ff';
        ctx.beginPath(); ctx.arc(s.x * W, s.y * H * 0.9, s.r, 0, 7); ctx.fill();
      }
      ctx.globalAlpha = 1;
      // Shooting star: one every ~30s across the whole night (after Maghrib →
      // before sunrise), each with a fresh random direction.
      this.nextShoot -= dt;
      if (!this.shoot && this.nextShoot <= 0) {
        const fromLeft = Math.random() < 0.5;
        const ang = 0.15 + Math.random() * 0.5;                  // downward slope
        const speed = W * (0.5 + Math.random() * 0.35);          // px/sec
        this.shoot = {
          x: fromLeft ? -W * 0.05 + Math.random() * W * 0.3 : W * 1.05 - Math.random() * W * 0.3,
          y: Math.random() * H * 0.35,
          vx: (fromLeft ? 1 : -1) * Math.cos(ang) * speed,
          vy: Math.sin(ang) * speed, life: 0
        };
        this.nextShoot = 30;
      }
      if (this.shoot) {
        const sh = this.shoot; sh.life += dt; sh.x += sh.vx * dt; sh.y += sh.vy * dt;
        const p = sh.life / 0.8;
        if (p >= 1 || sh.x < -W * 0.2 || sh.x > W * 1.2) this.shoot = null;
        else {
          const mag = Math.hypot(sh.vx, sh.vy) || 1, tail = 92;
          const tx = sh.x - sh.vx / mag * tail, ty = sh.y - sh.vy / mag * tail;
          const g = ctx.createLinearGradient(tx, ty, sh.x, sh.y);
          const a = Math.max(night, 0.6) * (1 - p) * 0.95;
          g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, `rgba(255,255,255,${a.toFixed(2)})`);
          ctx.strokeStyle = g; ctx.lineWidth = 2; ctx.lineCap = 'round';
          ctx.beginPath(); ctx.moveTo(tx, ty); ctx.lineTo(sh.x, sh.y); ctx.stroke();
        }
      }
    }

    // Drifting clouds by day — faint wisps that add motion without hiding art.
    if (day > 0.08) {
      for (const cl of this.clouds) {
        cl.x += cl.sp / 60; if (cl.x > 1.3) cl.x = -0.3;
        const cx = cl.x * W, cy = cl.y * H, sc = cl.s * H * 0.05;
        ctx.globalAlpha = day * (0.05 + 0.05 * cl.p);
        for (const [ox, oy, r] of [[-1.5, 0.2, 1], [-0.6, -0.3, 1.2], [0.5, -0.2, 1.35], [1.5, 0.15, 1], [0, 0.3, 1.5]]) {
          const g = ctx.createRadialGradient(cx + ox * sc, cy + oy * sc, 0, cx + ox * sc, cy + oy * sc, r * sc);
          g.addColorStop(0, 'rgba(255,255,255,0.9)'); g.addColorStop(1, 'rgba(255,255,255,0)');
          ctx.fillStyle = g; ctx.beginPath(); ctx.arc(cx + ox * sc, cy + oy * sc, r * sc, 0, 7); ctx.fill();
        }
      }
      ctx.globalAlpha = 1;
    }

    // Birds: one flock every ~30s, from before Asr until Maghrib, each flock in
    // a fresh random direction.
    const birdOn = nowMin >= (T.asr - 45) && nowMin <= MG;
    if (this.nextBird == null) this.nextBird = Math.random() * 6;
    if (birdOn) {
      this.nextBird -= dt;
      if (!this.bird && this.nextBird <= 0) {
        const dir = Math.random() < 0.5 ? 1 : -1;
        this.bird = { dir, y: H * (0.13 + Math.random() * 0.22), x: dir > 0 ? -0.1 : 1.1, speed: 0.05 + Math.random() * 0.04, phase: Math.random() * 6 };
        this.nextBird = 30;
      }
      if (this.bird) {
        const b = this.bird; b.x += b.dir * b.speed * dt;
        if (b.x < -0.2 || b.x > 1.2) this.bird = null;
        else {
          ctx.globalAlpha = 0.8; ctx.strokeStyle = 'rgba(20,20,28,0.85)'; ctx.lineWidth = 1.5; ctx.lineCap = 'round';
          for (let i = 0; i < 5; i++) {
            const bx = (b.x - i * 0.022 * b.dir) * W;
            const by = b.y + Math.abs(i - 2) * 10 + Math.sin(t * 4 + i + b.phase) * 3, w = 6 + (i % 3) * 2;
            ctx.beginPath(); ctx.moveTo(bx - w, by); ctx.quadraticCurveTo(bx, by - w * 0.6, bx + 1, by); ctx.quadraticCurveTo(bx + 2, by - w * 0.6, bx + w + 2, by); ctx.stroke();
          }
          ctx.globalAlpha = 1;
        }
      }
    }

    // Gentle shimmer on the water (lower ~third), brighter with day/moon.
    const waterTop = H * 0.6, shimmer = 0.06 + 0.06 * Math.max(day, night * 0.7);
    ctx.globalCompositeOperation = 'overlay';
    for (let i = 0; i < 5; i++) {
      const yy = waterTop + (i + 0.5) / 5 * (H - waterTop);
      const a = shimmer * (0.5 + 0.5 * Math.sin(t * 0.8 + i * 1.3)) * (1 - i / 6);
      ctx.globalAlpha = this._clamp(a, 0, 0.18);
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, yy, W, 1.5);
    }
    ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  },

  /* ---------- readout: local time + phase name ---------- */
  _readout(nowMin, ci, phaseOverride) {
    const phase = phaseOverride || this._phaseName(ci);
    const el = document.getElementById('phaseText');
    if (el) el.textContent = phase;
    const out = document.getElementById('sceneReadout');
    if (out) {
      const h = Math.floor(nowMin / 60) % 24, m = Math.floor(nowMin % 60);
      const hr = ((h % 12) || 12), ap = h < 12 ? 'AM' : 'PM';
      out.textContent = `${hr}:${String(m).padStart(2, '0')} ${ap} · ${phase}`;
    }
  }
};

if (typeof window !== 'undefined') window.Scene = Scene;
