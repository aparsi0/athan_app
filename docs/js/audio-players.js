/**
 * Two extra Quran tabs, both plain HTML5 <audio> (no YouTube iframe):
 *
 *   Moalem      — المصحف المعلم, Sheikh Mahmoud Khalil Al-Hosary.
 *                 114 surahs in order, direct MP3s from el-hosary.com.
 *   QuranRadio  — إذاعة القرآن الكريم من القاهرة, live 24/7 stream.
 *
 * Both mirror the Podcast API (pause / maybeResume / cancelResume) so the
 * athan pipeline can give prayer audio priority, and all three players are
 * mutually exclusive — starting one silences the others.
 */

/** Every Quran-ish player registers here so only one can sound at a time. */
const QuranPlayers = {
  all: [],
  register(p) { this.all.push(p); },
  silenceOthers(except) {
    for (const p of this.all) {
      if (p !== except && typeof p.stopForOther === 'function') p.stopForOther();
    }
    if (except !== 'podcast' && typeof Podcast !== 'undefined') {
      Podcast.pause();
      Podcast.cancelResume();
    }
  },
  pauseAll() { for (const p of this.all) p.pause(); },
  resumeAll() { for (const p of this.all) p.maybeResume(); },
  cancelAll() { for (const p of this.all) p.cancelResume(); }
};

/**
 * Shared audio engine. `opts.ids` are the DOM ids of this player's controls;
 * a player with no track list (the radio) omits the list/seek ids.
 */
function makeAudioPlayer(opts) {
  const player = {
    idx: null,
    playing: false,
    _resumeWanted: false,
    _shouldBePlaying: false,
    _failStreak: 0,   // consecutive load failures; only a real 'playing' clears it

    init() {
      const el = (id) => document.getElementById(id);
      this.audio = new Audio();
      this.audio.preload = 'none';
      this.playBtn = el(opts.ids.play);

      if (opts.tracks) {
        const ol = el(opts.ids.list);
        if (ol && !ol.childElementCount) {
          opts.tracks.forEach((name, i) => {
            const li = document.createElement('li');
            li.dataset.i = i;
            li.innerHTML = `<span class="snum">${i + 1}</span><span class="sname">سورة ${name}</span>`;
            li.addEventListener('click', () => this.play(i, true));
            ol.appendChild(li);
          });
        }
        el(opts.ids.prev).addEventListener('click', () => {
          if (this.idx != null && this.idx > 0) this.play(this.idx - 1, true);
        });
        el(opts.ids.next).addEventListener('click', () => {
          if (this.idx != null && this.idx < opts.tracks.length - 1) this.play(this.idx + 1, true);
        });
        this._bindSeek();
      }

      this.playBtn.addEventListener('click', () => {
        if (opts.tracks && this.idx == null) { this.play(0, true); return; }
        if (!opts.tracks && !this._started) { this.play(0, true); return; }
        if (this.playing) {
          this._shouldBePlaying = false;
          this.audio.pause();
        } else {
          QuranPlayers.silenceOthers(this);
          this._shouldBePlaying = true;
          this._failStreak = 0;   // pressing play is a fresh start, as above
          this.audio.play().catch(() => {});
        }
      });

      const vol = el(opts.ids.volume);
      vol.value = Config.get(opts.volumeKey, 0.8);
      vol.addEventListener('input', () => {
        Config.set(opts.volumeKey, Number(vol.value));
        this._applyVolume();
      });
      this._volEl = vol;

      this.audio.addEventListener('playing', () => { this._failStreak = 0; this._setPlaying(true); });
      this.audio.addEventListener('pause', () => this._setPlaying(false));
      this.audio.addEventListener('ended', () => {
        this._setPlaying(false);
        if (!opts.tracks) { this._reconnect(); return; }
        const next = (this.idx + 1) % opts.tracks.length;
        if (next === 0) App.logStatus(`${opts.icon} ${opts.name} — finished سورة الناس, starting again from الفاتحة.`);
        this.play(next);
      });
      this.audio.addEventListener('error', () => this._onError());
      this.audio.addEventListener('stalled', () => this._nudge());
      this.audio.addEventListener('timeupdate', () => this._onTime());

      this._startWatchdog();
      QuranPlayers.register(this);
    },

    _setPlaying(on) {
      this.playing = on;
      this.playBtn.textContent = on ? '⏸' : '▶';
    },

    _applyVolume() {
      this.audio.volume = Math.max(0, Math.min(1, Number(Config.get(opts.volumeKey, 0.8))));
    },

    /**
     * Start track `i` (index ignored for the single-stream radio).
     * `userInitiated` marks a real click, which forgives an earlier failure
     * streak — auto-advance and error-recovery must not, or a dead host
     * would loop through all 114 surahs forever.
     */
    play(i, userInitiated) {
      if (AudioManager.isPlaying()) {
        App.logStatus('⚠️ Prayer audio is playing — the Quran will not interrupt it.');
        return;
      }
      QuranPlayers.silenceOthers(this);
      this._resumeWanted = false;
      this._shouldBePlaying = true;
      this._started = true;
      this._srcTry = 0;                       // each new item starts at the primary source
      if (userInitiated) this._failStreak = 0;
      this._lastTime = null;
      this._lastTimeAt = null;
      this._loadedAt = Date.now();

      if (opts.tracks) {
        this.idx = i;
        this.audio.src = opts.srcFor(i, this._srcTry);
        document.getElementById(opts.ids.title).textContent = `سورة ${opts.tracks[i]}`;
        document.getElementById(opts.ids.sub).textContent = `${i + 1} / ${opts.tracks.length} · ${opts.reciter}`;
        document.querySelectorAll(`#${opts.ids.list} li`).forEach((li) =>
          li.classList.toggle('playing', Number(li.dataset.i) === i));
        this._resetSeek();
        App.logStatus(`${opts.icon} ${opts.name} — سورة ${opts.tracks[i]} (${i + 1}/${opts.tracks.length})`);
      } else {
        this.idx = 0;
        this.audio.src = opts.srcFor(0, this._srcTry);
        App.logStatus(`${opts.icon} ${opts.name} — connecting to the live stream…`);
      }
      this._applyVolume();
      this.audio.play().catch(() => {
        App.logStatus(`⚠️ ${opts.name} could not start — press play to try again.`);
      });
    },

    // ---------- seek bar (track players only) ----------

    _bindSeek() {
      const seek = document.getElementById(opts.ids.seek);
      this._seekEl = seek;
      this._curEl = document.getElementById(opts.ids.current);
      this._durEl = document.getElementById(opts.ids.duration);
      const start = () => { this._seeking = true; };
      seek.addEventListener('pointerdown', start);
      seek.addEventListener('touchstart', start, { passive: true });
      seek.addEventListener('input', () => this._paintSeek(Number(seek.value), Number(seek.max)));
      const commit = () => {
        if (!this._seeking) return;
        this._seeking = false;
        if (Number.isFinite(this.audio.duration)) this.audio.currentTime = Number(seek.value);
      };
      seek.addEventListener('change', commit);
      seek.addEventListener('pointerup', commit);
      seek.addEventListener('touchend', commit);
    },

    _resetSeek() {
      if (!this._seekEl) return;
      this._seeking = false;
      this._seekEl.value = 0;
      this._seekEl.max = 0;
      this._seekEl.disabled = true;
      this._paintSeek(0, 0);
    },

    _paintSeek(current, duration) {
      const pct = duration > 0 ? Math.min(100, (current / duration) * 100) : 0;
      this._seekEl.style.background =
        `linear-gradient(to right, var(--gold) ${pct}%, rgba(255,255,255,0.15) ${pct}%)`;
      this._curEl.textContent = fmtClock(current);
      if (duration > 0) this._durEl.textContent = fmtClock(duration);
    },

    _onTime() {
      this._lastTime = this.audio.currentTime;
      this._lastTimeAt = Date.now();
      if (!this._seekEl || this._seeking) return;
      const dur = this.audio.duration;
      if (Number.isFinite(dur) && dur > 0) {
        this._seekEl.disabled = false;
        const whole = Math.floor(dur);
        if (Number(this._seekEl.max) !== whole) this._seekEl.max = whole;
      }
      this._seekEl.value = Math.floor(this.audio.currentTime);
      this._paintSeek(this.audio.currentTime, dur);
    },

    // ---------- athan priority ----------

    pause() {
      if (this.playing) this._resumeWanted = true;
      this._shouldBePlaying = false;
      this.audio.pause();
    },

    maybeResume() {
      if (!this._resumeWanted || AudioManager.isPlaying()) return;
      this._resumeWanted = false;
      this._shouldBePlaying = true;
      this._loadedAt = Date.now();
      if (!opts.tracks) { this._reconnect(); return; } // live radio: rejoin, don't resume
      this.audio.play()
        .then(() => App.logStatus(`${opts.icon} Prayer audio finished — resuming ${opts.name}.`))
        .catch(() => {});
    },

    cancelResume() {
      this._resumeWanted = false;
      this._shouldBePlaying = false;
    },

    /** Another player took over — go quiet and forget any pending resume. */
    stopForOther() {
      this._resumeWanted = false;
      this._shouldBePlaying = false;
      this.audio.pause();
    },

    // ---------- robustness ----------

    /** 3s, 6s, 12s, 24s, 48s — then hold at a minute. */
    _backoffMs() {
      return Math.min(3000 * Math.pow(2, Math.min(this._failStreak || 1, 5) - 1), 60000);
    },

    /** Reload the current track from whichever source `_srcTry` points at. */
    _loadCurrent() {
      this.audio.src = opts.srcFor(this.idx, this._srcTry);
      this._loadedAt = Date.now();
      this._applyVolume();
      this.audio.play().catch(() => {});
    },

    _onError() {
      if (!this._shouldBePlaying) return;
      this._failStreak = (this._failStreak || 0) + 1;

      // A track player tries the same surah from its other sources before it
      // gives up on that surah — a mirror being down is not a missing surah.
      if (opts.tracks) {
        const nSources = (opts.sources && opts.sources.length) || 1;
        if ((this._srcTry || 0) + 1 < nSources) {
          this._srcTry += 1;
          App.logStatus(`⚠️ سورة ${opts.tracks[this.idx]} — trying another source…`);
          this._loadCurrent();
          return;
        }
      }

      if (this._failStreak >= 5) {
        App.logStatus(opts.tracks
          ? `⚠️ ${opts.name} — nothing is loading from the audio host. Check your connection, then press play.`
          : `⚠️ ${opts.name} — every stream address failed. The station may be off air; المصحف المعلم still works.`);
        this._shouldBePlaying = false;
        return;
      }

      if (!opts.tracks) {
        const wait = this._backoffMs();
        App.logStatus(`⚠️ ${opts.name} stream dropped — reconnecting in ${Math.round(wait / 1000)}s…`);
        setTimeout(() => this._reconnect(), wait);
        return;
      }

      App.logStatus(`⚠️ سورة ${opts.tracks[this.idx]} could not play — skipping to the next one.`);
      this.play((this.idx + 1) % opts.tracks.length);
    },

    _reconnect() {
      if (!this._shouldBePlaying) return;
      this._srcTry = ((this._srcTry || 0) + 1) % Math.max(1, opts.sources?.length || 1);
      this.audio.src = opts.srcFor(0, this._srcTry);
      this._loadedAt = Date.now();
      this._applyVolume();
      this.audio.play().catch(() => {});
    },

    _nudge() {
      if (this._shouldBePlaying) this.audio.play().catch(() => {});
    },

    /**
     * Browsers can silently drop an audio element (background throttling, a
     * network hiccup) without an error event. Compare what should be
     * happening against what actually is, and recover.
     */
    _startWatchdog() {
      setInterval(() => this._check(), 6000);
      document.addEventListener('visibilitychange', () => {
        if (document.visibilityState === 'visible') this._check();
      });
    },

    _check() {
      if (!this._shouldBePlaying) return;
      const now = Date.now();
      if (this.audio.paused) { this.audio.play().catch(() => {}); return; }
      if (this._loadedAt && now - this._loadedAt < 15000) return;   // buffering grace
      if (!this._lastTimeAt || now - this._lastTimeAt < 15000) return;
      this._stalls = (this._stalls || 0) + 1;
      if (this._stalls <= 2) this.audio.play().catch(() => {});
      else {
        // Genuinely frozen — fetch a fresh stream at the same position.
        const at = this._lastTime || 0;
        this._stalls = 0;
        if (!opts.tracks) { this._reconnect(); }
        else {
          this.audio.src = opts.srcFor(this.idx, this._srcTry);
          this.audio.currentTime = at;
          this.audio.play().catch(() => {});
          this._loadedAt = Date.now();
        }
      }
      this._lastTimeAt = now;
    }
  };
  return player;
}

function fmtClock(s) {
  if (!Number.isFinite(s) || s < 0) s = 0;
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return h > 0
    ? `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
    : `${m}:${String(sec).padStart(2, '0')}`;
}

/* ---------------- المصحف المعلم — Sheikh Mahmoud Khalil Al-Hosary ---------------- */

const Moalem = makeAudioPlayer({
  name: 'Al-Mos\'haf Al-Moa\'alem',
  icon: '📖',
  reciter: 'الشيخ محمود خليل الحصري',
  tracks: PODCAST.surahs,
  volumeKey: 'audio_settings.moalem_volume',
  // Ordered source list. Only one host today; adding a mirror is one line
  // here plus its host in the index.html `media-src` CSP directive, and the
  // player will fall through to it automatically when a surah fails to load.
  sources: ['https://www.el-hosary.com/Elmoalem'],
  srcFor(i, tryIdx) {
    const base = this.sources[(tryIdx || 0) % this.sources.length];
    return `${base}/${String(i + 1).padStart(3, '0')}.mp3`;
  },
  ids: {
    list: 'moalemList', play: 'moalemPlay', prev: 'moalemPrev', next: 'moalemNext',
    title: 'moalemTitle', sub: 'moalemSub', volume: 'moalemVolume',
    seek: 'moalemSeek', current: 'moalemCurrent', duration: 'moalemDuration'
  }
});

/* ---------------- إذاعة القرآن الكريم من القاهرة — live ---------------- */

const QuranRadio = makeAudioPlayer({
  name: 'Quran Radio Cairo',
  icon: '📡',
  volumeKey: 'audio_settings.radio_volume',
  // The station Radio Garden's GQxvGBNK channel points at. The direct
  // Radiojar edges come first (one hop, no redirect); the Radio Garden
  // resolver is the fallback, since it 302s to whichever edge is healthy.
  sources: [
    'https://n12.radiojar.com/8s5u5tpdtwzuv',
    'https://n0b.radiojar.com/8s5u5tpdtwzuv',
    'https://stream.radiojar.com/8s5u5tpdtwzuv',
    'https://radio.garden/api/ara/content/listen/GQxvGBNK/channel.mp3'
  ],
  srcFor(_i, tryIdx) {
    const base = this.sources[(tryIdx || 0) % this.sources.length];
    // Cache-buster: a live stream must never be served from a stale buffer.
    return base + (base.includes('?') ? '&' : '?') + 'ts=' + Date.now();
  },
  ids: { play: 'radioPlay', volume: 'radioVolume' }
});
