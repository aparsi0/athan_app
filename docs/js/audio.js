/**
 * Audio playback manager. Browsers block autoplay until the user interacts
 * once, so the app shows an "Enable sound" gate; after that, scheduled
 * playback works while the tab stays open.
 *
 * Safari note: Safari only allows programmatic play() on an element the
 * user has previously activated, so ONE reusable <audio> element is
 * unlocked at the gate tap and reused for every athan/duaa/reminder.
 */
const AudioManager = {
  el: null,             // the single reusable, user-activated element
  currentLabel: null,
  unlocked: false,
  onStateChange: null,  // callback(label|null)
  _keepAlive: null,
  _active: null,        // {token, resolve, stopped, onEnded, onError}
  _token: 0,

  _ensureEl() {
    if (!this.el) {
      this.el = new Audio();
      this.el.preload = 'auto';
    }
    return this.el;
  },

  /** Must be called from a user gesture (click) to satisfy autoplay policy. */
  async unlock() {
    const el = this._ensureEl();
    if (this._active) return true;   // something is already playing on it
    try {
      // volume-0 (NOT muted): Chromium force-pauses muted media in background
      // tabs ("video-only background media"), which made a muted probe fail.
      el.muted = false;
      el.volume = 0;
      el.src = Config.get('audio_settings.audio_file');
      await el.play();
      el.pause();
      el.currentTime = 0;
      el.volume = 1;
      this.unlocked = true;
      return true;
    } catch (e) {
      el.volume = 1;
      console.warn('Audio unlock failed', e);
      return false;
    }
  },

  /**
   * Play a file on the shared element (stops whatever was playing —
   * athan takes priority over reminders). Resolves with
   * 'ended' | 'stopped' | 'error' so callers can decide whether to chain
   * follow-up audio (e.g. Duaa after the athan).
   */
  play(file, volume, label) {
    const el = this._ensureEl();
    this.stop();
    return new Promise((resolve) => {
      const token = ++this._token;
      const onEnded = () => this._finish(token, 'ended');
      const onError = () => this._finish(token, 'error');
      this._active = { token, resolve, stopped: false, onEnded, onError };
      el.addEventListener('ended', onEnded);
      el.addEventListener('error', onError);
      el.volume = Math.max(0, Math.min(1, volume ?? 0.8));
      el.muted = false;
      el.src = file;
      this.currentLabel = label;
      this.onStateChange?.(label);
      el.play().catch((e) => {
        console.warn(`Playback blocked or failed for ${label}:`, e);
        this._finish(token, 'error');
      });
    });
  },

  _finish(token, reason) {
    const a = this._active;
    if (!a || a.token !== token) return;
    this.el.removeEventListener('ended', a.onEnded);
    this.el.removeEventListener('error', a.onError);
    this._active = null;
    this.currentLabel = null;
    this.onStateChange?.(null);
    a.resolve(a.stopped ? 'stopped' : reason);
  },

  stop() {
    if (this._active) {
      this._active.stopped = true;
      try { this.el.pause(); } catch { /* ignore */ }
      this._finish(this._active.token, 'stopped');
    }
  },

  isPlaying() {
    return !!this._active;
  },

  /**
   * Loop an ultra-quiet (inaudible, ~-60 dB) audio signal so the browser
   * treats the tab as playing media. Tabs with active audio are exempt from
   * tab-freezing, Memory Saver discarding and macOS App Nap — the main
   * reasons scheduled athan stopped firing in minimized/background tabs.
   * Must be started from a user gesture (the welcome tap provides one).
   */
  startKeepAlive() {
    if (this._keepAlive) return;
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const buffer = ctx.createBuffer(1, ctx.sampleRate * 5, ctx.sampleRate);
      const data = buffer.getChannelData(0);
      for (let i = 0; i < data.length; i += 449) data[i] = 0.001; // sparse, inaudible
      const source = ctx.createBufferSource();
      source.buffer = buffer;
      source.loop = true;
      source.connect(ctx.destination);
      source.start();
      this._keepAlive = { ctx, source };
      // Some browsers auto-suspend contexts; resume whenever possible.
      setInterval(() => { if (ctx.state === 'suspended') ctx.resume().catch(() => {}); }, 30000);
    } catch (e) {
      console.warn('Keep-alive audio unavailable', e);
    }
  }
};
