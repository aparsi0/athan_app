/**
 * Main application — wires location, prayer times, scheduler, audio and UI.
 */
const App = {
  location: null,

  async init() {
    Config.load();
    Scene.init();
    this.bindUI();
    this.logStatus('Starting Athan Web…');

    if ('serviceWorker' in navigator) {
      // Do NOT swallow this error. A CSP that omits 'self' from worker-src
      // blocks sw.js with a SecurityError, which silently disables offline
      // support and PWA install — that went unnoticed for months because the
      // failure was caught and discarded here.
      navigator.serviceWorker.register('sw.js').catch((e) => {
        console.warn('[app] service worker registration failed:', e);
        this.logStatus('⚠️ Offline support unavailable: ' + (e?.message || e));
      });
    }

    AudioManager.onStateChange = (label) => this.renderNowPlaying(label);

    Scheduler.onEvent = (event) => this.handleEvent(event);
    Scheduler.onRefresh = () => {
      this.renderSchedule();
      // Re-evaluate the morning window on every (re)build. This is what makes
      // a page opened mid-morning pick up — a fixed timer after init raced the
      // location prompt and the prayer-times fetch and usually lost, with no
      // retry. It also handles the reverse: a rebuild whose new end time is
      // already in the past can never fire its stop event, so disabling the
      // feature or shortening the window mid-morning has to stop it here.
      if (Scheduler.inMorningWindow()) this.startMorningQuran('within the morning window');
      else this.stopMorningQuran();
    };

    await this.resolveLocation();
    await this.loadPrayerTimes();

    Scheduler.start();
    setInterval(() => this.renderCountdown(), 1000);
    this.renderCountdown();
  },

  // ---------- location ----------

  async resolveLocation() {
    const cfg = Config.get('location');
    if (cfg.auto_detect) {
      this.logStatus('Detecting your location…');
      const detected = await LocationService.detect();
      if (detected) {
        this.location = { ...cfg, ...detected };
        Config.set('location', this.location);
        this.logStatus(`Location: ${this.describeLocation()} (${this.location.location_source})`);
      } else {
        this.location = cfg;
        this.logStatus(`Location detection failed — using saved location: ${this.describeLocation()}`);
      }
    } else {
      this.location = cfg;
      this.logStatus(`Using manual location: ${this.describeLocation()}`);
    }
    document.getElementById('locationText').textContent = this.describeLocation();
  },

  /** Explicitly request the browser's precise location and rebuild the schedule. */
  async useMyLocation(quiet) {
    if (!quiet) this.logStatus('Requesting your precise location…');
    const precise = await LocationService._fromBrowserGeolocation();
    if (!precise) {
      if (!quiet) this.logStatus('⚠️ Location permission denied or unavailable — using ' + this.describeLocation() + '. You can set coordinates manually in Settings.');
      return;
    }
    const named = await LocationService._reverseGeocode(precise.latitude, precise.longitude);
    this.location = { ...Config.get('location'), ...precise, ...named };
    Config.set('location', this.location);
    document.getElementById('locationText').textContent = this.describeLocation();
    this.logStatus(`📍 Location set to ${this.describeLocation()} — updating prayer times…`);
    await this.loadPrayerTimes();
  },

  describeLocation() {
    const l = this.location || Config.get('location');
    const parts = [l.city, l.state || l.country].filter(Boolean);
    return parts.length ? parts.join(', ') : `${l.latitude.toFixed(3)}, ${l.longitude.toFixed(3)}`;
  },

  // ---------- prayer times ----------

  async loadPrayerTimes() {
    // Only one fetch at a time. The old code cancelled the pending retry timer
    // instead, which stopped timers stacking but not CALLERS stacking: while
    // the scheduler was stuck in its rollover branch this ran ~2x/second, each
    // call clearing the 60s retry a moment after it was set, so the backoff
    // never actually elapsed and the API was hammered continuously.
    const method = Config.get('prayer_settings.calculation_method', 2);
    const key = `${this.location?.latitude},${this.location?.longitude},${method},${new Date().toDateString()}`;
    if (this._loadingTimes) {
      // Only coalesce a request for the SAME coordinates, method and day.
      // Blindly returning the in-flight promise dropped the refetch that the
      // location prompt, the 📍 button and a calculation-method change each
      // trigger — leaving the user on the previous location's times all day,
      // since loadPrayerTimes is the only caller of Scheduler.build().
      if (this._loadingKey === key) return this._loadingTimes;
      this._pendingReload = true;   // re-run once the in-flight fetch settles
      return this._loadingTimes;
    }
    if (this._retryTimer) { clearTimeout(this._retryTimer); this._retryTimer = null; }
    let resolveInFlight;
    this._loadingKey = key;
    this._pendingReload = false;
    this._loadingTimes = new Promise((r) => { resolveInFlight = r; });
    try {
      this.logStatus('Fetching today\'s prayer times…');
      const data = await PrayerTimesAPI.fetch(this.location.latitude, this.location.longitude, method);
      Scheduler.build(data);
      this.renderHijriDate(data);
      // feed the living scene the real sun times (minutes since midnight)
      const mins = {};
      for (const [k, v] of Object.entries(data.prayer_times)) {
        const [h, m] = (v || '').split(':').map(Number);
        if (Number.isFinite(h) && Number.isFinite(m)) mins[k] = h * 60 + m;
      }
      Scene.setTimes(mins);
      this.logStatus('Prayer times loaded ✓');
      this._timesBackoff = 0;
    } catch (e) {
      console.error(e);
      // Exponential backoff, capped at 10 minutes: a flat 60s retry against a
      // provider that is down just burns requests all day.
      const wait = Math.min(60000 * Math.pow(2, this._timesBackoff || 0), 600000);
      this._timesBackoff = (this._timesBackoff || 0) + 1;
      this.logStatus(`⚠️ Could not fetch prayer times. Retrying in ${Math.round(wait / 1000)} s…`);
      this._retryTimer = setTimeout(() => { this._retryTimer = null; this.loadPrayerTimes(); }, wait);
    } finally {
      this._loadingTimes = null;
      this._loadingKey = null;
      resolveInFlight();
      // A caller asked for different coordinates/method/day while this fetch
      // was open. Honour it now rather than dropping it.
      if (this._pendingReload) { this._pendingReload = false; this.loadPrayerTimes(); }
    }
  },

  // ---------- scheduled events ----------

  async handleEvent(event) {
    if (event.kind === 'morning_quran_end') {
      this.stopMorningQuran();
      return;
    }

    if (event.kind === 'refresh') {
      this.logStatus('Midnight — refreshing prayer times for the new day…');
      await this.loadPrayerTimes();
      return;
    }

    if (event.missed) {
      this.logStatus(`⏰ Missed ${event.label} at ${this.fmtTime(event.time)} — the tab was suspended by the browser. Keep the tab open (not just minimized), or see the tips in the panel below.`);
      // A suspended tab is the most likely way to reach mid-morning, so a
      // Fajr we slept through must still open the morning Quran window.
      if (event.kind === 'athan' && event.prayer === 'fajr') {
        this.startMorningQuran('Fajr passed while the tab was suspended');
      }
      this.renderSchedule();
      return;
    }

    // Reminders yield to prayer audio. AudioManager.play() stops whatever is
    // sounding, so without this a woduaa/azkar landing on a prayer minute cut
    // the athan off after milliseconds — and because the athan's promise then
    // resolved 'stopped' rather than 'ended', its after-prayer duaa was
    // silently skipped too. The athan itself still pre-empts everything.
    if (event.kind !== 'athan' && AudioManager.isPlaying()) {
      this.logStatus(`⏭ Skipped ${event.label} — prayer audio is playing and takes priority.`);
      this.renderSchedule();
      return;
    }

    this.logStatus(`▶ ${event.label} — ${this.fmtTime(event.time)}`);
    this.notify(event.label);
    QuranPlayers.pauseAll();  // prayer audio takes priority over every Quran player

    if (event.kind === 'athan') {
      const files = Config.get('audio_settings.athan_files', {});
      const file = files[event.prayer] || Config.get('audio_settings.audio_file');
      const volume = Config.get('audio_settings.athan_volume', 0.8);
      const outcome = await AudioManager.play(file, volume, `${PRAYER_LABELS[event.prayer].en} Athan`);

      const duaa = Config.get('special_audio_settings.after_prayer_duaa', {});
      if (duaa.enabled && outcome === 'ended') {
        this.logStatus(`▶ After-prayer Duaa (${PRAYER_LABELS[event.prayer].en})`);
        await AudioManager.play(duaa.audio_file, duaa.volume, 'After-prayer Duaa');
      }
      QuranPlayers.resumeAll(); // Quran continues where it was interrupted
      // The morning Quran starts the moment the Fajr chain is done, not at a
      // clock time — "right after Fajr" means after the athan AND its duaa.
      if (event.prayer === 'fajr') this.startMorningQuran('the Fajr athan finished');
      this.renderSchedule();
      return;
    }

    const cfgKey = event.kind === 'woduaa' ? 'pre_prayer_woduaa' : event.kind;
    const cfg = Config.get(`special_audio_settings.${cfgKey}`, {});
    if (cfg.audio_file) {
      await AudioManager.play(cfg.audio_file, cfg.volume, event.label);
    }
    QuranPlayers.resumeAll(); // Quran continues where it was interrupted
    this.renderSchedule();
  },

  /** Start (or resume) the morning Quran, if it is enabled and we are inside
   *  today's window. Safe to call repeatedly — it never restarts a player
   *  that is already going, and never plays over prayer audio. */
  startMorningQuran(why) {
    const cfg = Config.get('special_audio_settings.morning_quran', {});
    if (!cfg.enabled) return;
    if (typeof Reciters === 'undefined' || !Reciters.player) return;
    if (!Scheduler.inMorningWindow()) return;
    if (AudioManager.isPlaying()) return;          // athan/azkar always wins
    // Never override a deliberate choice. This has to consider EVERY Quran
    // player, not just the reciters tab: someone who fell asleep to the Cairo
    // radio, or to المصحف المعلم, has chosen what they want playing, and the
    // morning auto-play would otherwise silence it and switch to رفعت.
    // `playing` alone is not enough — it is set by the audio element's own
    // event, which cannot have fired when this runs straight after
    // resumeAll(); _shouldBePlaying and _resumeWanted are set synchronously.
    if (QuranPlayers.anyActive()) return;
    // Nothing can play before the visitor has tapped the sound gate; trying
    // anyway logs a scary failure and leaves the watchdog nudging forever.
    if (!AudioManager.unlocked) return;

    // Read the saved position BEFORE switching reciter — selecting a
    // different one deliberately clears it.
    const saved = Number(Config.get('audio_settings.quran_last_index', 0)) || 0;
    const wanted = cfg.reciter_id || RECITERS[0].id;
    const sameReciter = Reciters.active().id === wanted;
    Reciters.selectById(wanted);
    const at = sameReciter ? saved : 0;

    const sheikh = Reciters.active().sheikh;
    const until = Scheduler.morningWindow ? this.fmtTime(Scheduler.morningWindow.end) : '';
    this.logStatus(`🕌 Morning Quran — ${sheikh}${until ? ` until ${until}` : ''} (${why}).`);
    Reciters.player.play(at);
  },

  /** Stop the morning Quran for good. Unconditional on purpose: if another
   *  event paused the player first, `playing` and `_shouldBePlaying` are both
   *  false while `_resumeWanted` is still true, so guarding on them let the
   *  next resumeAll() restart the Quran after its window had closed. */
  stopMorningQuran() {
    if (typeof Reciters === 'undefined' || !Reciters.player) return;
    const wasOn = Reciters.player.playing || Reciters.player._shouldBePlaying
      || Reciters.player._resumeWanted;
    Reciters.player.pause();
    Reciters.player.cancelResume();
    if (wasOn) this.logStatus('🕌 Morning Quran window has ended.');
  },

  notify(body) {
    if (!Config.get('ui_settings.show_notifications', true)) return;
    if ('Notification' in window && Notification.permission === 'granted') {
      try {
        new Notification('🕌 Athan Web', { body, icon: 'assets/icons/icon.svg' });
      } catch { /* some mobile browsers require SW notifications */ }
    }
  },

  // ---------- rendering ----------

  renderHijriDate(data) {
    const hijri = data.date?.hijri;
    const el = document.getElementById('hijriDate');
    if (hijri?.day) {
      el.textContent = `${hijri.day} ${hijri.month?.en || ''} ${hijri.year} AH`;
    } else {
      el.textContent = '';
    }
    document.getElementById('gregorianDate').textContent =
      new Date().toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  },

  renderSchedule() {
    const times = Scheduler.prayerData?.prayer_times || {};
    const enabled = Config.get('prayer_settings.enabled_prayers', {});
    const now = new Date();
    const list = document.getElementById('prayerList');
    list.innerHTML = '';

    const rows = ['fajr', 'sunrise', 'dhuhr', 'asr', 'maghrib', 'isha'];
    const next = Scheduler.nextPrayer();

    for (const name of rows) {
      if (!times[name]) continue;
      const [h, m] = times[name].split(':').map(Number);
      const at = new Date(); at.setHours(h, m, 0, 0);
      const isPrayer = name !== 'sunrise';
      const isNext = next && next.prayer === name;
      const passed = at < now;

      const li = document.createElement('li');
      li.className = [
        'prayer-row',
        isPrayer ? '' : 'sunrise-row',
        isNext ? 'next' : '',
        passed && !isNext ? 'passed' : '',
        isPrayer && enabled[name] === false ? 'disabled' : ''
      ].join(' ').trim();
      li.innerHTML = `
        <span class="p-ar">${PRAYER_LABELS[name].ar}</span>
        <span class="p-en">${PRAYER_LABELS[name].en}</span>
        <span class="p-time">${this.fmt12(times[name])}</span>`;
      list.appendChild(li);
    }

    // Special events list
    const specials = document.getElementById('specialList');
    specials.innerHTML = '';
    for (const event of Scheduler.events) {
      if (event.kind === 'athan') continue;
      const li = document.createElement('li');
      li.className = 'special-row' + (event.time < now ? ' passed' : '');
      li.innerHTML = `<span>${event.label}</span><span class="p-time">${this.fmtTime(event.time)}</span>`;
      specials.appendChild(li);
    }
  },

  renderCountdown() {
    const el = document.getElementById('countdown');
    const nameEl = document.getElementById('nextPrayerName');
    const next = Scheduler.nextPrayer();
    if (!next) {
      nameEl.textContent = 'Fajr';
      el.textContent = 'tomorrow, إن شاء الله';
      return;
    }
    nameEl.textContent = `${PRAYER_LABELS[next.prayer].ar} · ${PRAYER_LABELS[next.prayer].en}`;
    const diff = Math.max(0, next.time - new Date());
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const s = Math.floor((diff % 60000) / 1000);
    el.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  },

  renderNowPlaying(label) {
    const bar = document.getElementById('nowPlaying');
    const text = document.getElementById('nowPlayingText');
    if (label) {
      text.textContent = `Now playing: ${label}`;
      bar.classList.add('visible');
    } else {
      bar.classList.remove('visible');
    }
  },

  logStatus(message) {
    const log = document.getElementById('statusLog');
    const line = document.createElement('div');
    line.textContent = `[${this.fmtTime(new Date())}] ${message}`;
    log.prepend(line);
    while (log.children.length > 50) log.removeChild(log.lastChild);
  },

  fmtTime(date) {
    return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
  },

  fmt12(hhmm) {
    const [h, m] = hhmm.split(':').map(Number);
    const d = new Date(); d.setHours(h, m, 0, 0);
    return this.fmtTime(d);
  },

  // ---------- UI bindings ----------

  bindUI() {
    // Sound gate — required once per visit by browser autoplay policy.
    const gate = document.getElementById('soundGate');
    document.getElementById('enableSoundBtn').addEventListener('click', async () => {
      const ok = await AudioManager.unlock();
      AudioManager.startKeepAlive();
      gate.classList.add('hidden');
      this.logStatus(ok ? '🔊 Sound enabled — athan will play automatically.' : '⚠️ Sound could not be enabled.');
      // Nothing could autoplay before this tap, so if we are already inside
      // the morning window this is the first moment it can actually start.
      if (ok) this.startMorningQuran('sound enabled during the morning window');
      if (Config.get('ui_settings.show_notifications', true) && 'Notification' in window && Notification.permission === 'default') {
        Notification.requestPermission();
      }
      // Ask for the visitor's precise location (user gesture makes the
      // browser permission prompt most reliable here).
      if (Config.get('location.auto_detect', true) && this.location?.location_source !== 'browser_geolocation') {
        this.useMyLocation(true);
      }
    });

    document.getElementById('locateBtn').addEventListener('click', () => this.useMyLocation(false));

    Reciters.init();
    Moalem.init();
    QuranRadio.init();

    document.getElementById('testBtn').addEventListener('click', () => this.testNextAthan());
    this.updateTestButton();

    document.getElementById('stopBtn').addEventListener('click', () => {
      AudioManager.stop();
      // Every Quran player is in the registry now, so this reaches all of them.
      QuranPlayers.pauseAll();
      QuranPlayers.cancelAll();
      this.logStatus('Playback stopped.');
    });

    // Tab bar — Settings tab repopulates its fields on open
    document.getElementById('tabs').addEventListener('click', (e) => {
      const btn = e.target.closest('button');
      if (!btn) return;
      document.querySelectorAll('nav.tabs button').forEach((b) => b.classList.toggle('active', b === btn));
      document.querySelectorAll('.panel').forEach((p) => p.classList.toggle('active', p.id === 'panel-' + btn.dataset.tab));
      if (btn.dataset.tab === 'settings') this.openSettings();
    });

    document.getElementById('saveSettings').addEventListener('click', () => this.saveSettings());
    document.getElementById('resetSettings').addEventListener('click', () => {
      Config.reset();
      this.openSettings();
      this.logStatus('Settings reset to defaults.');
    });
  },

  /**
   * Test button cycles through the five prayers, playing each prayer's own
   * athan file in turn (Fajr → Dhuhr → Asr → Maghrib → Isha → Fajr …),
   * so every configured file can be verified — not just the general one.
   */
  _testIndexKey: 'athan_web_test_index',

  /** Touching window.localStorage THROWS (not returns null) when the browser
   *  is set to block all site data, and setItem throws in old Safari private
   *  mode. These ran inside bindUI(), before the scheduler was started, so the
   *  throw propagated out of init() and left the whole app dead: no tab bar,
   *  no Stop button, no prayer times, no athan. */
  _testIndexGet() {
    let i;
    try { i = Number(localStorage.getItem(this._testIndexKey) || 0) % PRAYER_NAMES.length; }
    catch { i = this._testIndexFallback || 0; }
    // A junk stored value gives NaN, and PRAYER_NAMES[NaN] is undefined —
    // which throws out of bindUI() and kills init(), the very outcome the
    // try/catch above exists to prevent.
    return Number.isFinite(i) ? i : 0;
  },
  _testIndexSet(i) {
    this._testIndexFallback = i;
    try { localStorage.setItem(this._testIndexKey, String(i)); } catch { /* no site data */ }
  },

  async testNextAthan() {
    const i = this._testIndexGet();
    const prayer = PRAYER_NAMES[i];
    const files = Config.get('audio_settings.athan_files', {});
    const file = files[prayer] || Config.get('audio_settings.audio_file');
    const label = `${PRAYER_LABELS[prayer].en} Athan (test)`;

    this._testIndexSet((i + 1) % PRAYER_NAMES.length);
    this.updateTestButton();
    this.logStatus(`Testing ${PRAYER_LABELS[prayer].en} athan (${i + 1}/${PRAYER_NAMES.length}) — its own audio file.`);

    await AudioManager.unlock();
    AudioManager.startKeepAlive();
    QuranPlayers.pauseAll();
    AudioManager.play(file, Config.get('audio_settings.athan_volume', 0.8), label)
      .then(() => QuranPlayers.resumeAll());
  },

  updateTestButton() {
    const i = this._testIndexGet();
    document.getElementById('testBtn').textContent = `▶ Test Athan (${PRAYER_LABELS[PRAYER_NAMES[i]].en})`;
  },

  openSettings() {
    // Prayers
    for (const p of PRAYER_NAMES) {
      document.getElementById(`en_${p}`).checked = Config.get(`prayer_settings.enabled_prayers.${p}`, true) !== false;
    }
    // Method
    const methodSel = document.getElementById('calcMethod');
    if (!methodSel.options.length) {
      for (const [id, label] of Object.entries(CALCULATION_METHODS)) {
        methodSel.add(new Option(label, id));
      }
    }
    methodSel.value = String(Config.get('prayer_settings.calculation_method', 2));

    // Volumes & special events
    document.getElementById('athanVolume').value = Config.get('audio_settings.athan_volume', 0.8);
    for (const key of ['friday_before_dhuhr', 'after_prayer_duaa', 'pre_prayer_woduaa', 'morning_audio', 'night_audio']) {
      document.getElementById(`sp_${key}`).checked = !!Config.get(`special_audio_settings.${key}.enabled`, true);
      document.getElementById(`vol_${key}`).value = Config.get(`special_audio_settings.${key}.volume`, 0.8);
    }

    // Morning Quran
    const mq = Config.get('special_audio_settings.morning_quran', {});
    document.getElementById('sp_morning_quran').checked = mq.enabled !== false;
    document.getElementById('mq_end').value = mq.end_after_azkar_minutes ?? 60;
    const mqSel = document.getElementById('mq_reciter');
    mqSel.innerHTML = RECITERS.map((r) =>
      `<option value="${r.id}">${r.sheikh} — ${r.mushaf}</option>`).join('');
    mqSel.value = mq.reciter_id || RECITERS[0].id;
    document.getElementById('woduaaLead').value = Config.get('special_audio_settings.pre_prayer_woduaa.lead_minutes', 15);

    // Location
    document.getElementById('autoDetect').checked = Config.get('location.auto_detect', true);
    document.getElementById('manualLat').value = Config.get('location.latitude', '');
    document.getElementById('manualLon').value = Config.get('location.longitude', '');
    document.getElementById('showNotifs').checked = Config.get('ui_settings.show_notifications', true);
  },

  async saveSettings() {
    for (const p of PRAYER_NAMES) {
      Config.set(`prayer_settings.enabled_prayers.${p}`, document.getElementById(`en_${p}`).checked);
    }
    Config.set('prayer_settings.calculation_method', Number(document.getElementById('calcMethod').value));
    Config.set('audio_settings.athan_volume', Number(document.getElementById('athanVolume').value));

    for (const key of ['friday_before_dhuhr', 'after_prayer_duaa', 'pre_prayer_woduaa', 'morning_audio', 'night_audio']) {
      Config.set(`special_audio_settings.${key}.enabled`, document.getElementById(`sp_${key}`).checked);
      Config.set(`special_audio_settings.${key}.volume`, Number(document.getElementById(`vol_${key}`).value));
    }

    Config.set('special_audio_settings.morning_quran.enabled',
      document.getElementById('sp_morning_quran').checked);
    Config.set('special_audio_settings.morning_quran.reciter_id',
      document.getElementById('mq_reciter').value);
    const mqEndRaw = Number(document.getElementById('mq_end').value);
    Config.set('special_audio_settings.morning_quran.end_after_azkar_minutes',
      Number.isFinite(mqEndRaw) && mqEndRaw >= 0 ? Math.min(mqEndRaw, 240) : 60);
    // The field is min=1 max=120, but an EMPTY input gives Number('') === 0,
    // which would schedule the reminder at the exact prayer minute (where the
    // scheduler now drops it) and silently remove all five woduaa reminders.
    // Clamp to the same range the input advertises.
    const leadRaw = Number(document.getElementById('woduaaLead').value);
    const lead = Number.isFinite(leadRaw) && leadRaw >= 1 ? Math.min(leadRaw, 120) : 15;
    if (lead !== leadRaw) {
      document.getElementById('woduaaLead').value = lead;
      this.logStatus(`Woduaa lead must be 1–120 minutes — using ${lead}.`);
    }
    Config.set('special_audio_settings.pre_prayer_woduaa.lead_minutes', lead);

    const auto = document.getElementById('autoDetect').checked;
    Config.set('location.auto_detect', auto);
    if (!auto) {
      const lat = parseFloat(document.getElementById('manualLat').value);
      const lon = parseFloat(document.getElementById('manualLon').value);
      if (!Number.isNaN(lat) && !Number.isNaN(lon)) {
        Config.set('location.latitude', lat);
        Config.set('location.longitude', lon);
        Config.set('location.city', '');
        Config.set('location.state', '');
        Config.set('location.location_source', 'manual');
      }
    }
    Config.set('ui_settings.show_notifications', document.getElementById('showNotifs').checked);

    this.logStatus('Settings saved — rebuilding schedule…');
    await this.resolveLocation();
    await this.loadPrayerTimes();
  }
};

window.addEventListener('DOMContentLoaded', () => App.init());
