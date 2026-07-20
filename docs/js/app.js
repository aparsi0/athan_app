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
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }

    AudioManager.onStateChange = (label) => this.renderNowPlaying(label);

    Scheduler.onEvent = (event) => this.handleEvent(event);
    Scheduler.onRefresh = () => this.renderSchedule();

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
    const method = Config.get('prayer_settings.calculation_method', 2);
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
    } catch (e) {
      console.error(e);
      this.logStatus('⚠️ Could not fetch prayer times. Retrying in 60 s…');
      setTimeout(() => this.loadPrayerTimes(), 60000);
    }
  },

  // ---------- scheduled events ----------

  async handleEvent(event) {
    if (event.kind === 'refresh') {
      this.logStatus('Midnight — refreshing prayer times for the new day…');
      await this.loadPrayerTimes();
      return;
    }

    if (event.missed) {
      this.logStatus(`⏰ Missed ${event.label} at ${this.fmtTime(event.time)} — the tab was suspended by the browser. Keep the tab open (not just minimized), or see the tips in the panel below.`);
      this.renderSchedule();
      return;
    }

    this.logStatus(`▶ ${event.label} — ${this.fmtTime(event.time)}`);
    this.notify(event.label);
    Podcast.pause(); // prayer audio takes priority over the podcast

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
      this.renderSchedule();
      return;
    }

    const cfgKey = event.kind === 'woduaa' ? 'pre_prayer_woduaa' : event.kind;
    const cfg = Config.get(`special_audio_settings.${cfgKey}`, {});
    if (cfg.audio_file) {
      await AudioManager.play(cfg.audio_file, cfg.volume, event.label);
    }
    this.renderSchedule();
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

    Podcast.init();

    document.getElementById('testBtn').addEventListener('click', () => this.testNextAthan());
    this.updateTestButton();

    document.getElementById('stopBtn').addEventListener('click', () => {
      AudioManager.stop();
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

  async testNextAthan() {
    const i = Number(localStorage.getItem(this._testIndexKey) || 0) % PRAYER_NAMES.length;
    const prayer = PRAYER_NAMES[i];
    const files = Config.get('audio_settings.athan_files', {});
    const file = files[prayer] || Config.get('audio_settings.audio_file');
    const label = `${PRAYER_LABELS[prayer].en} Athan (test)`;

    localStorage.setItem(this._testIndexKey, String((i + 1) % PRAYER_NAMES.length));
    this.updateTestButton();
    this.logStatus(`Testing ${PRAYER_LABELS[prayer].en} athan (${i + 1}/${PRAYER_NAMES.length}) — its own audio file.`);

    await AudioManager.unlock();
    AudioManager.startKeepAlive();
    Podcast.pause();
    AudioManager.play(file, Config.get('audio_settings.athan_volume', 0.8), label);
  },

  updateTestButton() {
    const i = Number(localStorage.getItem(this._testIndexKey) || 0) % PRAYER_NAMES.length;
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
    Config.set('special_audio_settings.pre_prayer_woduaa.lead_minutes', Number(document.getElementById('woduaaLead').value));

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
