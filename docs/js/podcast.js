/**
 * Quran tab — audio-style player for the complete mushaf of Sheikh Mahmoud
 * Ali Al-Banna (Egyptian Radio recordings), playing the IDENTICAL videos from
 * the user's YouTube playlist (PL8475A8813886C6A5): its first 114 items are
 * exactly surahs 1–114 in Quran order.
 *
 * Presented as a pure audio player (prev / play-pause / next + surah list).
 * YouTube's terms require its player to remain visible, so it lives as a
 * small corner thumbnail that can be tapped to enlarge.
 *
 * The global object keeps the name `Podcast` because the athan pipeline
 * calls Podcast.pause() to give prayer audio priority.
 */
const PODCAST = {
  spotifyUrl: 'https://open.spotify.com/show/5d4FhdBUAYt220XU5seoUy',
  youtubeUrl: 'https://www.youtube.com/playlist?list=PL8475A8813886C6A5',
  videoIds: [
    'PDNxisGeW1c', 'n4POhvaC2ws', 'Qlq6fKG2L48', '0TbNuYZXEFM', '-yqEU5iGzRc', 'EmP2aIMk23U',
    'rPp5xJVeguo', 'JwCMdyjGEek', 'TOs4bxGC1RI', '-FBpwMHLJjo', 'jOp6XWEbQOc', 'UrfZzWuD5oA',
    '9D4afDgTXTQ', '60xrw5xP5Gc', 'OxQMlURn3qE', 'loctyVUJlnM', 'dqeI29oH2SI', 'MrKtfra1GdE',
    'gbkQJ_YRXtQ', 'UF9HYWKTH20', 'KhzTu4TqlsA', 'DTJPEiYKn_8', 'hvogfFpzfss', 'CjtEU4mgY5g',
    'Kf9oHLc8Ow8', 'WfxeQTljhOM', 'bEaKPB9wJB4', 'BHRUHc9ceIs', 'lDZz3WWG7uk', 'E81U5BORdRY',
    'wg5R0OKfcmY', 'yryPuRX0LA8', 'Spk5iTyka3s', '_tyhdjxA5aQ', 'sbnFzKh-BDk', 'VCZkoCb2U1s',
    'ls0iLFrBINo', 'DbX7oUTjRak', 'DwSYcJKN7Iw', 'gzo5qAwUqus', 'Lnstc9EzGf4', '-sGCWeMV2gk',
    'OG6iVYFX1jI', 'EdVC1DZpL1c', 'q0PTLRorVMk', 'eOalQ-hUuOU', 'UgWbHH7wcMg', '9Rx6cWdUcLI',
    'QfDUzHJKtjE', 'prADpCHLv_4', '6Xi-TBRl1HY', 'f4tRUA6K1OQ', 'mnAfJ7sDXx4', 'X-5Yy0d_Y5o',
    'rGdWGQvAmdo', 'hRMRK6rebuU', 'OK4B_4jRL8c', 'lw0hR6OLjRA', 'OQzGVHGWP-Y', '9vltXa4pnoE',
    'CAcAEMQZe_8', '_WoH7OVgqGQ', 'gCH59cgEJEw', 'K2azv4hmMqc', 'MSSbwG5MqKk', 'yDdHYCbWZMU',
    '9KralHHjcl8', 't3mr7iTQYEg', 'bxsIOGBgB1c', 'xfiFkTd_QnI', '4wooeJxyQ-k', 't8-Q-DFX0vQ',
    'YI25XiTryKQ', 'Rymb-hcJqw8', 'bzIPVB4VUWQ', 'Q0JD06MsUzo', 'CWTmCFA5G0A', 'G25igasmzPo',
    'ZbCFAGmBgZI', 'CUzwEyxouPI', '_k2HK-gBXAQ', '9RcfnX5n_70', 'TKa3SKE-iQg', 'CUl3tWbEAhw',
    'poz_EJvxQ14', 'lwWTuR3Q04w', 'HSYy9crpNGg', 'nUPm5d2QKIc', '7FthaIXP9NQ', 'rX9Dwx2KUd8',
    'vd-TPhgkBbY', 'tkhlUH-tG_A', 'OCW-7OaR8go', 'HFN27o7VW2Q', 'uJJjpPj607U', 'Yw_N_33z9Ik',
    'aS5PIu00qqg', 'PMmZr3TKEWY', 'OOjh9VlR4bI', '0hOam_cSiUo', '7gLDkN-q2P8', 'lkZFbP2mOVM',
    '2pHj4HPs1zI', 'OgMf2_ygNkk', 'k9p4c5DB3Vo', 'EqSlJMmrLiY', '4jJ0HXtn-Yw', 'FtDyMi9oeXk',
    'cl4daXdFX_k', 'hs2_7dVCgBc', 'CuVKObfXWeo', 'rl4zIYgfWJg', 'dzQWP9_Y_js', 'Q8y0JCWFT0A'
  ],
  surahs: [
    'الفاتحة', 'البقرة', 'آل عمران', 'النساء', 'المائدة', 'الأنعام', 'الأعراف', 'الأنفال',
    'التوبة', 'يونس', 'هود', 'يوسف', 'الرعد', 'إبراهيم', 'الحجر', 'النحل',
    'الإسراء', 'الكهف', 'مريم', 'طه', 'الأنبياء', 'الحج', 'المؤمنون', 'النور',
    'الفرقان', 'الشعراء', 'النمل', 'القصص', 'العنكبوت', 'الروم', 'لقمان', 'السجدة',
    'الأحزاب', 'سبأ', 'فاطر', 'يس', 'الصافات', 'ص', 'الزمر', 'غافر',
    'فصلت', 'الشورى', 'الزخرف', 'الدخان', 'الجاثية', 'الأحقاف', 'محمد', 'الفتح',
    'الحجرات', 'ق', 'الذاريات', 'الطور', 'النجم', 'القمر', 'الرحمن', 'الواقعة',
    'الحديد', 'المجادلة', 'الحشر', 'الممتحنة', 'الصف', 'الجمعة', 'المنافقون', 'التغابن',
    'الطلاق', 'التحريم', 'الملك', 'القلم', 'الحاقة', 'المعارج', 'نوح', 'الجن',
    'المزمل', 'المدثر', 'القيامة', 'الإنسان', 'المرسلات', 'النبأ', 'النازعات', 'عبس',
    'التكوير', 'الانفطار', 'المطففين', 'الانشقاق', 'البروج', 'الطارق', 'الأعلى', 'الغاشية',
    'الفجر', 'البلد', 'الشمس', 'الليل', 'الضحى', 'الشرح', 'التين', 'العلق',
    'القدر', 'البينة', 'الزلزلة', 'العاديات', 'القارعة', 'التكاثر', 'العصر', 'الهمزة',
    'الفيل', 'قريش', 'الماعون', 'الكوثر', 'الكافرون', 'النصر', 'المسد', 'الإخلاص',
    'الفلق', 'الناس'
  ]
};

const Podcast = {
  idx: null,
  player: null,
  ready: false,
  playing: false,
  _pendingIdx: null,
  _apiRequested: false,

  init() {
    const ol = document.getElementById('surahList');
    if (!ol || ol.childElementCount) return;
    PODCAST.surahs.forEach((name, i) => {
      const li = document.createElement('li');
      li.dataset.i = i;
      li.innerHTML = `<span class="snum">${i + 1}</span><span class="sname">سورة ${name}</span>`;
      li.addEventListener('click', () => this.play(i));
      ol.appendChild(li);
    });
    document.getElementById('playBtn').addEventListener('click', () => {
      if (this.idx == null) { this.play(0); return; }
      if (!this.ready) return;
      if (this.playing) { this._shouldBePlaying = false; this.player.pauseVideo(); }
      else { this._shouldBePlaying = true; this.player.playVideo(); }
    });
    document.getElementById('prevBtn').addEventListener('click', () => {
      if (this.idx != null && this.idx > 0) this.play(this.idx - 1);
    });
    document.getElementById('nextBtn').addEventListener('click', () => {
      if (this.idx != null && this.idx < PODCAST.videoIds.length - 1) this.play(this.idx + 1);
    });
    document.getElementById('ytThumb').addEventListener('click', () =>
      document.getElementById('ytThumb').classList.toggle('expanded'));

    // Separate Quran volume (independent of the athan volume), persisted
    // per-visitor and applied straight to the YouTube player.
    const vol = document.getElementById('quranVolume');
    vol.value = Config.get('audio_settings.quran_volume', 0.8);
    vol.addEventListener('input', () => {
      Config.set('audio_settings.quran_volume', Number(vol.value));
      this._applyVolume();
    });

    this._bindSeek();
    this._startWatchdog();
  },

  /** Seek bar: shows this surah's duration, fills as it plays, and can be
   *  dragged forward or back — each surah has its own length, read live
   *  from the player, so the bar always matches the surah currently playing. */
  _bindSeek() {
    const seek = document.getElementById('quranSeek');
    const cur = document.getElementById('piCurrent');
    const dur = document.getElementById('piDuration');
    this._seekEl = seek; this._curEl = cur; this._durEl = dur;

    const startSeeking = () => { this._seeking = true; };
    seek.addEventListener('pointerdown', startSeeking);
    seek.addEventListener('touchstart', startSeeking, { passive: true });

    // Live feedback while dragging (label + fill), without spamming YouTube.
    seek.addEventListener('input', () => {
      this._paintSeek(Number(seek.value), Number(seek.max));
    });

    const commit = () => {
      if (!this._seeking) return;
      this._seeking = false;
      if (this.ready && this.player?.seekTo) {
        try { this.player.seekTo(Number(seek.value), true); } catch { /* player may be gone */ }
      }
    };
    seek.addEventListener('change', commit);
    seek.addEventListener('pointerup', commit);
    seek.addEventListener('touchend', commit);

    setInterval(() => this._pollProgress(), 500);
  },

  _pollProgress() {
    if (this._seeking || !this.ready || this.idx == null || !this.player?.getCurrentTime) return;
    let current, duration;
    try {
      current = this.player.getCurrentTime();
      duration = this.player.getDuration();
    } catch { return; }
    if (!Number.isFinite(current) || !Number.isFinite(duration)) return;
    const seek = this._seekEl;
    if (duration > 0) {
      seek.disabled = false;
      const maxWhole = Math.floor(duration);
      if (Number(seek.max) !== maxWhole) seek.max = maxWhole;
    }
    seek.value = Math.floor(current);
    this._paintSeek(current, duration);
  },

  _paintSeek(current, duration) {
    const seek = this._seekEl;
    const pct = duration > 0 ? Math.min(100, (current / duration) * 100) : 0;
    seek.style.background = `linear-gradient(to right, var(--gold) ${pct}%, rgba(255,255,255,0.15) ${pct}%)`;
    this._curEl.textContent = this._fmtTime(current);
    if (duration > 0) this._durEl.textContent = this._fmtTime(duration);
  },

  _fmtTime(s) {
    if (!Number.isFinite(s) || s < 0) s = 0;
    const m = Math.floor(s / 60), sec = Math.floor(s % 60);
    return `${m}:${String(sec).padStart(2, '0')}`;
  },

  _applyVolume() {
    if (this.ready && this.player?.setVolume) {
      try {
        this.player.setVolume(Math.round(Config.get('audio_settings.quran_volume', 0.8) * 100));
      } catch { /* player may be gone */ }
    }
  },

  play(i) {
    // Athan takes priority: don't interrupt a live athan/duaa broadcast.
    if (AudioManager.isPlaying()) {
      App.logStatus('⚠️ Prayer audio is playing — the Quran will not interrupt it.');
      return;
    }
    this._resumeWanted = false; // manual start supersedes any pending auto-resume
    this._shouldBePlaying = true;
    this._consecErrors = 0;
    // Reset stall-tracking for the new surah — otherwise a stale currentTime
    // left over from whatever was playing before could make the watchdog
    // misjudge this fresh video as already "stuck".
    this._lastYtTime = null;
    this._lastYtTimeAt = null;
    this._stallNudges = 0;
    this._loadedAt = Date.now();
    this.idx = i;
    document.getElementById('ytThumb').style.display = 'block';
    document.getElementById('piTitle').textContent = `سورة ${PODCAST.surahs[i]}`;
    document.getElementById('piSub').textContent = `${i + 1} / 114 · Sheikh Mahmoud Ali Al-Banna`;
    document.querySelectorAll('.surah-list li').forEach(el =>
      el.classList.toggle('playing', Number(el.dataset.i) === i));
    // Reset the seek bar for the new surah — its duration is read fresh
    // from the player once the new video loads, via _pollProgress().
    if (this._seekEl) {
      this._seeking = false;
      this._seekEl.value = 0;
      this._seekEl.max = 0;
      this._seekEl.disabled = true;
      this._paintSeek(0, 0);
    }
    if (this.ready) this.player.loadVideoById(PODCAST.videoIds[i]);
    else { this._pendingIdx = i; this._ensure(); }
    App.logStatus(`🎙 Playing سورة ${PODCAST.surahs[i]} (${i + 1}/114)`);
  },

  _ensure() {
    if (this._apiRequested) return;
    this._apiRequested = true;
    const create = () => {
      this.player = new YT.Player('ytPlayerHost', {
        width: '100%',
        videoId: PODCAST.videoIds[this._pendingIdx ?? 0],
        playerVars: { autoplay: 1, rel: 0, playsinline: 1, controls: 0 },
        events: {
          onReady: () => {
            this.ready = true;
            this._applyVolume();
            if (this._pendingIdx != null) {
              this.player.loadVideoById(PODCAST.videoIds[this._pendingIdx]);
              this._pendingIdx = null;
            }
          },
          onStateChange: (e) => {
            this.playing = e.data === YT.PlayerState.PLAYING;
            if (this.playing) { this._applyVolume(); this._consecErrors = 0; }
            document.getElementById('playBtn').textContent = this.playing ? '⏸' : '▶';
            if (e.data === YT.PlayerState.ENDED) {
              // Loop the playlist: after سورة الناس (114), start again at الفاتحة.
              const next = (this.idx + 1) % PODCAST.videoIds.length;
              if (next === 0) App.logStatus('🎙 Playlist completed — starting again from سورة الفاتحة.');
              this.play(next);
            }
          },
          onError: () => {
            // Guard against a tight failure loop (e.g. connection is down and
            // every surah errors instantly) instead of hammering forever.
            this._consecErrors = (this._consecErrors || 0) + 1;
            if (this._consecErrors >= 5) {
              App.logStatus('⚠️ The Quran keeps failing to load — check your internet connection, then press play to try again.');
              this._shouldBePlaying = false;
              return;
            }
            App.logStatus(`⚠️ سورة ${PODCAST.surahs[this.idx]} could not play — skipping to the next one.`);
            this.play((this.idx + 1) % PODCAST.videoIds.length);
          }
        }
      });
    };
    if (window.YT && window.YT.Player) create();
    else {
      window.onYouTubeIframeAPIReady = create;
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(s);
    }
  },

  /** Pause Quran playback (called when prayer audio starts). Remembers that
   *  it was playing so it can resume once the prayer audio finishes. */
  pause() {
    if (this.ready && this.player?.pauseVideo) {
      if (this.playing) this._resumeWanted = true;
      this._shouldBePlaying = false; // deliberate pause — the watchdog must not fight it
      try { this.player.pauseVideo(); } catch { /* player may be gone */ }
    }
  },

  /** Resume Quran playback if it was interrupted by prayer audio and the
   *  prayer audio has fully finished. */
  maybeResume() {
    if (this._resumeWanted && this.ready && this.player?.playVideo && !AudioManager.isPlaying()) {
      this._resumeWanted = false;
      this._shouldBePlaying = true;
      // Resuming can also involve a brief re-buffer — give it the same grace
      // period a fresh surah gets before the stall watchdog judges it.
      this._loadedAt = Date.now();
      this._lastYtTime = null;
      this._lastYtTimeAt = null;
      this._stallNudges = 0;
      try {
        this.player.playVideo();
        App.logStatus('🎙 Prayer audio finished — resuming the Quran.');
      } catch { /* player may be gone */ }
    }
  },

  /** Forget any pending auto-resume (user pressed Stop — they want silence). */
  cancelResume() {
    this._resumeWanted = false;
    this._shouldBePlaying = false;
  },

  /**
   * YouTube's iframe can be silently paused or stalled by the browser
   * (background-tab throttling, a network hiccup) without ever firing a
   * state-change or error event we'd otherwise react to. This watchdog
   * compares what SHOULD be happening (`_shouldBePlaying`) against what the
   * player actually reports, and nudges it back to life when they disagree.
   */
  _startWatchdog() {
    if (this._watchdog) return;
    this._watchdog = setInterval(() => this._checkStuck(), 6000);
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible') this._checkStuck();
    });
  },

  _checkStuck() {
    if (!this._shouldBePlaying || !this.ready || this.idx == null || !this.player?.getPlayerState) return;
    let state, current;
    try {
      state = this.player.getPlayerState();
      current = this.player.getCurrentTime();
    } catch { return; }

    // Should be playing, but YouTube reports paused/unstarted/cued — nudge it.
    // (Numeric literals, not YT.PlayerState — that global may not exist yet
    // in every edge case, and the values are a stable part of the API:
    // 1 = playing, 3 = buffering.)
    if (state !== 1 && state !== 3) {
      try { this.player.playVideo(); } catch { /* player may be gone */ }
      return;
    }

    if (!Number.isFinite(current)) return;
    const now = Date.now();

    if (this._lastYtTime == null || current !== this._lastYtTime) {
      this._lastYtTime = current;
      this._lastYtTimeAt = now;
      this._stallNudges = 0; // real progress — clear any nudge streak
      return;
    }

    // currentTime hasn't moved since the last check. A fresh surah gets a
    // grace period first — a brief pause in the first ~15s after loading is
    // normal buffering, not a stall, and judging it too early was exactly
    // what caused "stuck at a few seconds, forever": seeking to the position
    // it's already frozen at doesn't fetch anything new, so it just recreated
    // the same hiccup on repeat.
    const justLoaded = this._loadedAt && now - this._loadedAt < 15000;
    if (justLoaded) return;
    if (!this._lastYtTimeAt || now - this._lastYtTimeAt < 15000) return;

    this._stallNudges = (this._stallNudges || 0) + 1;
    if (this._stallNudges <= 2) {
      // Gentle first: just ask it to keep playing, no re-seek.
      try { this.player.playVideo(); } catch { /* ignore */ }
    } else {
      // Still frozen after gentle nudges — request a genuinely fresh stream
      // at the same position, rather than repeating an ineffective same-spot seek.
      try { this.player.loadVideoById(PODCAST.videoIds[this.idx], current); } catch { /* ignore */ }
      this._loadedAt = Date.now(); // give the fresh load its own grace period
      this._stallNudges = 0;
    }
    this._lastYtTimeAt = now; // avoid renudging every tick
  }
};
