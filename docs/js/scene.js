/**
 * Living scene engine — shows each theme's ORIGINAL, uncropped photograph
 * and only adjusts its lighting to match the time of day at the visitor's
 * location: bright at midday, warm at sunrise/sunset, dark and cool at
 * night. No cutting, no drawn sun/moon/stars — just light.
 *
 * Themes (Config 'ui_settings.theme'): a | b | c | d | e
 *   a — Alpine Valley      b — Above the Clouds   c — Mountain Lake
 *   d — Lake Dock (default) e — Golden Valley
 */
const SCENE_THEMES = {
  a: { label: 'Alpine Valley' },
  b: { label: 'Above the Clouds' },
  c: { label: 'Mountain Lake' },
  d: { label: 'Lake Dock' },
  e: { label: 'Golden Valley' }
};

const Scene = {
  theme: 'd',
  times: { fajr: 285, sunrise: 370, dhuhr: 801, asr: 1030, maghrib: 1231, isha: 1316 },

  init() {
    this.photoEl = document.getElementById('photo');
    this.shadeEl = document.getElementById('shade');
    this.glowEl = document.getElementById('glow');
    if (!this.photoEl) return;

    const saved = Config.get('ui_settings.theme', 'd');
    this.theme = SCENE_THEMES[saved] ? saved : 'd';
    this.photoEl.style.backgroundImage = `url('assets/photo_${this.theme}.jpg')`;

    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') this.render();
    });
    setInterval(() => this.render(), 60000);
    this.render();
  },

  setTheme(name) {
    this.theme = SCENE_THEMES[name] ? name : 'd';
    if (this.photoEl) {
      this.photoEl.style.backgroundImage = `url('assets/photo_${this.theme}.jpg')`;
    }
    this.render();
  },

  setTimes(map) {
    for (const k of Object.keys(map)) {
      if (Number.isFinite(map[k])) this.times[k] = map[k];
    }
    this.render();
  },

  _lerp(a, b, t) { return a + (b - a) * t; },
  _clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); },

  /* Lighting keyframes tied to the REAL sun/prayer times:
     [minute, brightness, saturate, shade(rgb array + alpha), glow(rgb array + alpha), phase]
     shade = cool multiply-style dimming layer; glow = warm light near the
     horizon at dawn/golden hour/sunset. */
  _anchors() {
    const T = this.times, mid = (a, b) => (a + b) / 2;
    return [
      [T.fajr - 90,            0.30, 0.55, [16, 26, 58], 0.50, [0, 0, 0], 0.00, 'Deep night'],
      [T.fajr,                 0.38, 0.62, [20, 30, 64], 0.42, [70, 50, 80], 0.10, 'Fajr — first light'],
      [mid(T.fajr, T.sunrise), 0.52, 0.75, [30, 36, 80], 0.30, [200, 110, 60], 0.16, 'Dawn'],
      [T.sunrise,              0.70, 0.92, [60, 70, 110], 0.16, [255, 150, 70], 0.20, 'Sunrise'],
      [T.sunrise + 50,         0.90, 1.02, [255, 255, 255], 0.00, [255, 210, 140], 0.10, 'Morning'],
      [T.dhuhr,                1.04, 1.05, [255, 255, 255], 0.00, [255, 255, 255], 0.00, 'Midday'],
      [T.asr,                  0.98, 1.03, [255, 255, 255], 0.00, [255, 225, 150], 0.06, 'Afternoon'],
      [T.maghrib - 50,         0.86, 1.05, [120, 100, 110], 0.08, [255, 165, 80], 0.16, 'Golden hour'],
      [T.maghrib,              0.72, 0.95, [70, 60, 100], 0.16, [255, 130, 60], 0.26, 'Sunset'],
      [mid(T.maghrib, T.isha), 0.52, 0.75, [36, 36, 80], 0.30, [170, 85, 90], 0.14, 'Dusk'],
      [T.isha,                 0.36, 0.62, [18, 26, 60], 0.44, [60, 48, 90], 0.06, 'Night falls'],
      [T.isha + 80,            0.30, 0.55, [16, 26, 58], 0.50, [0, 0, 0], 0.00, 'Night']
    ];
  },

  _gradeAt(minute) {
    const A = this._anchors();
    let m = minute;
    if (m < A[0][0]) m += 1440;
    let i = 0;
    while (i < A.length - 1 && m >= A[i + 1][0]) i++;
    if (i >= A.length - 1) i = A.length - 2;
    const t = this._clamp((m - A[i][0]) / Math.max(1, A[i + 1][0] - A[i][0]), 0, 1);
    const P = A[i], Q = A[i + 1];
    const mixV = (a, b) => this._lerp(a, b, t);
    const mixRGB = (a, b) => a.map((v, k) => Math.round(this._lerp(v, b[k], t)));
    return {
      bright: mixV(P[1], Q[1]),
      sat: mixV(P[2], Q[2]),
      shade: mixRGB(P[3], Q[3]), shadeA: mixV(P[4], Q[4]),
      glow: mixRGB(P[5], Q[5]), glowA: mixV(P[6], Q[6]),
      phase: t < 0.5 ? P[7] : Q[7]
    };
  },

  _nowMinutes() {
    const d = new Date();
    return d.getHours() * 60 + d.getMinutes() + d.getSeconds() / 60;
  },

  render() {
    if (!this.photoEl) return;
    const g = this._gradeAt(this._nowMinutes());
    const phaseEl = document.getElementById('phaseText');
    if (phaseEl) phaseEl.textContent = g.phase;

    this.photoEl.style.filter = `brightness(${g.bright.toFixed(3)}) saturate(${g.sat.toFixed(3)})`;
    this.shadeEl.style.background = `rgba(${g.shade.join(',')},${g.shadeA.toFixed(3)})`;
    this.glowEl.style.background =
      `linear-gradient(180deg, transparent 35%, rgba(${g.glow.join(',')},${g.glowA.toFixed(3)}) 100%)`;
  }
};
