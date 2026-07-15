/**
 * Prayer times from the Aladhan API — same endpoint and processing
 * as the desktop app, with a per-day localStorage cache.
 */
const PRAYER_NAMES = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha'];
const PRAYER_LABELS = {
  fajr: { en: 'Fajr', ar: 'الفجر' },
  sunrise: { en: 'Sunrise', ar: 'الشروق' },
  dhuhr: { en: 'Dhuhr', ar: 'الظهر' },
  asr: { en: 'Asr', ar: 'العصر' },
  maghrib: { en: 'Maghrib', ar: 'المغرب' },
  isha: { en: 'Isha', ar: 'العشاء' }
};

const PrayerTimesAPI = {
  baseUrl: 'https://api.aladhan.com/v1',
  cachePrefix: 'athan_web_times_',

  /** date: JS Date. Returns {prayer_times: {fajr..isha, sunrise}, date: {...}} or null. */
  async fetch(latitude, longitude, method, date = new Date()) {
    const dateStr = this._formatDate(date); // DD-MM-YYYY
    const cacheKey = `${this.cachePrefix}${latitude.toFixed(3)}_${longitude.toFixed(3)}_${dateStr}_${method}`;

    const cached = this._readCache(cacheKey);
    if (cached) return cached;

    const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    const params = new URLSearchParams({ latitude, longitude, method, timezone });
    const url = `${this.baseUrl}/timings/${dateStr}?${params}`;

    const res = await fetch(url, { signal: AbortSignal.timeout(10000) });
    if (!res.ok) throw new Error(`Aladhan API HTTP ${res.status}`);
    const payload = await res.json();
    if (payload.code !== 200 || !payload.data) throw new Error('Aladhan API returned an error');

    const processed = this._process(payload.data);
    this._writeCache(cacheKey, processed);
    return processed;
  },

  _process(data) {
    const timings = data.timings || {};
    const clean = (t) => (t || '').split('(')[0].trim();
    return {
      prayer_times: {
        fajr: clean(timings.Fajr),
        sunrise: clean(timings.Sunrise),
        dhuhr: clean(timings.Dhuhr),
        asr: clean(timings.Asr),
        maghrib: clean(timings.Maghrib),
        isha: clean(timings.Isha)
      },
      date: {
        readable: data.date?.readable || '',
        hijri: data.date?.hijri || {}
      },
      fetched_at: new Date().toISOString()
    };
  },

  _formatDate(date) {
    const dd = String(date.getDate()).padStart(2, '0');
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    return `${dd}-${mm}-${date.getFullYear()}`;
  },

  _readCache(key) {
    try {
      const raw = localStorage.getItem(key);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  _writeCache(key, value) {
    try {
      // Keep only today's entries: drop older cache keys.
      for (let i = localStorage.length - 1; i >= 0; i--) {
        const k = localStorage.key(i);
        if (k && k.startsWith(this.cachePrefix) && k !== key) localStorage.removeItem(k);
      }
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      /* cache is best-effort */
    }
  }
};
