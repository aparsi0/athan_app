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
  _fired: new Set(),    // event names already fired today (survives rebuilds)
  _queue: [],           // events waiting to be handled, one at a time
  _draining: false,

  /** (Re)build today's schedule from prayerData + config. */
  build(prayerData) {
    this.prayerData = prayerData;
    this.events = [];
    this.dateKey = new Date().toDateString();

    const times = prayerData.prayer_times;
    const enabled = Config.get('prayer_settings.enabled_prayers', {});
    const today = new Date().toDateString();
    const toDate = (hhmm, offsetMinutes = 0) => {
      // Number.isNaN(undefined) is false, so a string with no colon would slip
      // past a plain isNaN check and produce an Invalid Date. Require finite.
      const [h, m] = String(hhmm ?? '').split(':').map(Number);
      if (!Number.isFinite(h) || !Number.isFinite(m)) return null;
      const off = Number(offsetMinutes);
      if (!Number.isFinite(off)) return null;
      const d = new Date();
      d.setHours(h, m, 0, 0);
      d.setMinutes(d.getMinutes() + off);
      if (Number.isNaN(d.getTime())) return null;
      // A large negative offset (e.g. a 120-minute woduaa lead against a
      // high-latitude summer Fajr) can roll the date back to yesterday. Such
      // an event is permanently in the past: it would never fire, and would
      // render in the Specials list as "passed" showing last night's time.
      if (d.toDateString() !== today) return null;
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
        const woduaaAt = Number.isFinite(lead) && lead > 0 ? toDate(times[prayer], -lead) : null;
        // lead === 0 would schedule the reminder at the exact prayer minute,
        // where it collides with the athan and (see _tick) replaces it.
        if (woduaaAt) {
          this.events.push({
            name: `pre_prayer_woduaa:${prayer}`,
            kind: 'woduaa',
            prayer,
            time: woduaaAt,
            label: `Woduaa reminder (${lead} min before ${PRAYER_LABELS[prayer].en})`
          });
        }
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
    // Claim today up front. dateKey used to be assigned only by build(), which
    // is reached only on a SUCCESSFUL fetch — so if the first fetch failed,
    // dateKey stayed null and _tick's rollover branch matched forever.
    if (!this.dateKey) this.dateKey = new Date().toDateString();
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

    // Fire due events FIRST, before the rollover check. The old order advanced
    // lastTick and returned early, so anything due in the minutes either side
    // of midnight was discarded — not even reported as missed.
    //
    // Events already in the past when the page loaded are NOT fired (matches
    // the desktop app skipping already-passed times). If the tab slept through
    // an event it still plays when recent (grace window); older ones are only
    // reported, so a long-suspended tab doesn't fire hours of backlog at once.
    const GRACE_MS = 10 * 60 * 1000;
    for (const event of this.events) {
      if (event.time > this.lastTick && event.time <= now) {
        // A rebuild (settings save, location change) recomputes event times
        // without rewinding lastTick, so an event that already played today
        // could land in the future again and fire a second time.
        if (this._fired.has(event.name)) continue;
        this._fired.add(event.name);
        this._enqueue(now - event.time > GRACE_MS ? { ...event, missed: true } : event);
      }
    }

    // Midnight rollover → ask for a fresh fetch/build.
    if (now.toDateString() !== this.dateKey) {
      // Claim the new day immediately rather than waiting for a successful
      // build. Previously dateKey only moved inside build(), so a refresh that
      // failed to fetch left this branch matching on every tick — roughly
      // twice a second across the page timer and the worker clock — each one
      // cancelling the pending 60s retry and starting another request, and
      // returning before the event loop so no athan could fire at all.
      this.dateKey = now.toDateString();
      this._fired.clear();
      this._enqueue({ name: 'daily_refresh', kind: 'refresh', time: now, label: 'Daily refresh' });
    }

    this.lastTick = now;
  },

  /** Queue an event and make sure the drain loop is running. */
  _enqueue(event) {
    this._queue.push(event);
    this._drain();
  },

  /** Handle queued events strictly one at a time.
   *  onEvent is async (it awaits the athan finishing so it can chain the
   *  duaa). Firing two due events in the same tick synchronously meant the
   *  second one's AudioManager.play() called stop() on the first — cutting the
   *  athan off after a few milliseconds and, because its promise then resolved
   *  'stopped' rather than 'ended', silently skipping the after-prayer duaa. */
  async _drain() {
    if (this._draining) return;
    this._draining = true;
    try {
      while (this._queue.length) {
        const event = this._queue.shift();
        try { await this.onEvent?.(event); }
        catch (e) { console.error('[scheduler] handler failed for', event.name, e); }
      }
    } finally {
      this._draining = false;
    }
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
