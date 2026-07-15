/**
 * Prayer scheduler — computes today's audio events from the fetched prayer
 * times and the config (mirroring the desktop scheduler), then ticks every
 * second and fires events as their time arrives. Refreshes itself at midnight.
 */
const Scheduler = {
  prayerData: null,     // result of PrayerTimesAPI.fetch
  events: [],           // [{name, kind, time: Date, label}]
  lastTick: null,
  timer: null,
  dateKey: null,
  onEvent: null,        // callback(event)
  onRefresh: null,      // callback() after a (re)build

  /** (Re)build today's schedule from prayerData + config. */
  build(prayerData) {
    this.prayerData = prayerData;
    this.events = [];
    this.dateKey = new Date().toDateString();

    const times = prayerData.prayer_times;
    const enabled = Config.get('prayer_settings.enabled_prayers', {});
    const toDate = (hhmm, offsetMinutes = 0) => {
      const [h, m] = hhmm.split(':').map(Number);
      if (Number.isNaN(h) || Number.isNaN(m)) return null;
      const d = new Date();
      d.setHours(h, m, 0, 0);
      d.setMinutes(d.getMinutes() + offsetMinutes);
      return d;
    };

    // Prayer athans + pre-prayer woduaa reminders
    const woduaa = Config.get('special_audio_settings.pre_prayer_woduaa', {});
    for (const prayer of PRAYER_NAMES) {
      if (!times[prayer] || enabled[prayer] === false) continue;
      const at = toDate(times[prayer]);
      if (!at) continue;
      this.events.push({
        name: `athan:${prayer}`,
        kind: 'athan',
        prayer,
        time: at,
        label: `${PRAYER_LABELS[prayer].en} Athan`
      });
      if (woduaa.enabled) {
        const lead = Number(woduaa.lead_minutes ?? 15);
        this.events.push({
          name: `pre_prayer_woduaa:${prayer}`,
          kind: 'woduaa',
          prayer,
          time: toDate(times[prayer], -lead),
          label: `Woduaa reminder (${lead} min before ${PRAYER_LABELS[prayer].en})`
        });
      }
    }

    // Relative special events: friday_before_dhuhr, morning_audio, night_audio
    for (const eventName of ['friday_before_dhuhr', 'morning_audio', 'night_audio']) {
      const cfg = Config.get(`special_audio_settings.${eventName}`, {});
      if (!cfg.enabled) continue;

      // Config stores Python weekday (Mon=0 … Sun=6); JS getDay() is Sun=0 … Sat=6.
      if (cfg.weekday != null) {
        const jsTarget = (Number(cfg.weekday) + 1) % 7;
        if (new Date().getDay() !== jsTarget) continue;
      }

      const reference = times[cfg.reference_time];
      if (!reference) continue;
      const at = toDate(reference, Number(cfg.offset_minutes || 0));
      if (!at) continue;

      const labels = {
        friday_before_dhuhr: 'Surat Al-Kahf (Friday)',
        morning_audio: 'Morning Azkar',
        night_audio: 'Night Azkar'
      };
      this.events.push({ name: eventName, kind: eventName, time: at, label: labels[eventName] });
    }

    this.events.sort((a, b) => a.time - b.time);
    this.onRefresh?.();
  },

  start() {
    this.stop();
    this.lastTick = new Date();
    this.timer = setInterval(() => this._tick(), 1000);

    // Background tabs get their page timers throttled (or frozen) by the
    // browser. Web Worker timers are exempt from intensive throttling, so a
    // tiny worker acts as a reliable clock while the tab is hidden.
    try {
      const workerSrc = URL.createObjectURL(new Blob(
        ["setInterval(() => postMessage('tick'), 1000);"],
        { type: 'application/javascript' }
      ));
      this.worker = new Worker(workerSrc);
      this.worker.onmessage = () => this._tick();
    } catch (e) {
      console.warn('Timer worker unavailable, using page timer only', e);
    }

    // If the tab was suspended anyway, catch up the moment it wakes.
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') this._tick();
    });
    window.addEventListener('focus', () => this._tick());
  },

  stop() {
    if (this.timer) clearInterval(this.timer);
    this.timer = null;
    if (this.worker) { this.worker.terminate(); this.worker = null; }
  },

  _tick() {
    const now = new Date();

    // Midnight rollover → signal that a fresh fetch/build is needed.
    if (now.toDateString() !== this.dateKey) {
      this.lastTick = now;
      this.onEvent?.({ name: 'daily_refresh', kind: 'refresh', time: now, label: 'Daily refresh' });
      return;
    }

    // Fire events whose time was crossed since the last tick. Events already
    // in the past when the page loaded are NOT fired (matches the desktop
    // app skipping already-passed times). If the tab slept through an event,
    // it still plays if the event is recent (grace window); much older missed
    // events are only reported, so a long-suspended tab doesn't fire hours of
    // backlogged audio at once.
    const GRACE_MS = 10 * 60 * 1000;
    for (const event of this.events) {
      if (event.time > this.lastTick && event.time <= now) {
        if (now - event.time > GRACE_MS) {
          this.onEvent?.({ ...event, missed: true });
        } else {
          this.onEvent?.(event);
        }
      }
    }
    this.lastTick = now;
  },

  nextPrayer() {
    const now = new Date();
    const upcoming = this.events.find((e) => e.kind === 'athan' && e.time > now);
    if (upcoming) return upcoming;
    return null; // all prayers passed — next is Fajr tomorrow
  },

  upcomingEvents() {
    const now = new Date();
    return this.events.filter((e) => e.time > now);
  }
};
