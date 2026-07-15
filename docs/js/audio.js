/**
 * Audio playback manager. Browsers block autoplay until the user interacts
 * once, so the app shows an "Enable sound" gate; after that, scheduled
 * playback works while the tab stays open.
 */
const AudioManager = {
  current: null,
  currentLabel: null,
  unlocked: false,
  onStateChange: null, // callback(label|null)

  /** Must be called from a user gesture (click) to satisfy autoplay policy. */
  async unlock() {
    try {
      const probe = new Audio(Config.get('audio_settings.audio_file'));
      probe.volume = 0;
      await probe.play();
      probe.pause();
      probe.currentTime = 0;
      this.unlocked = true;
      return true;
    } catch (e) {
      console.warn('Audio unlock failed', e);
      return false;
    }
  },

  /**
   * Play a file. Stops whatever is currently playing (athan takes priority
   * over reminders, matching the single-player behavior of the desktop app).
   * Resolves with 'ended' | 'stopped' | 'error' so callers can decide
   * whether to chain follow-up audio (e.g. Duaa after the athan).
   */
  play(file, volume, label) {
    this.stop();
    return new Promise((resolve) => {
      const audio = new Audio(file);
      audio.volume = Math.max(0, Math.min(1, volume ?? 0.8));
      this.current = audio;
      this.currentLabel = label;
      this.onStateChange?.(label);

      const finish = (reason) => {
        if (audio._finished) return;
        audio._finished = true;
        if (this.current === audio) {
          this.current = null;
          this.currentLabel = null;
          this.onStateChange?.(null);
        }
        resolve(audio._stoppedByUser ? 'stopped' : reason);
      };
      audio.addEventListener('ended', () => finish('ended'));
      audio.addEventListener('error', () => finish('error'));
      audio.play().catch((e) => {
        console.warn(`Playback blocked or failed for ${label}:`, e);
        finish('error');
      });
    });
  },

  stop() {
    if (this.current) {
      const audio = this.current;
      audio._stoppedByUser = true;
      audio.pause();
      audio.src = '';
      this.current = null;
      this.currentLabel = null;
      this.onStateChange?.(null);
    }
  },

  isPlaying() {
    return this.current !== null && !this.current.paused;
  }
};
