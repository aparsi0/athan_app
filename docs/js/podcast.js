/**
 * Podcast playlist — the Quran mushaf of Sheikh Mahmoud Ali Al-Banna,
 * playing the IDENTICAL recordings as the Spotify show, sourced from the
 * user's YouTube playlist (PL8475A8813886C6A5, "ختمة مرتّلة").
 * The first 114 playlist items are exactly surahs 1–114 in Quran order —
 * Al-Fatiha (1) → An-Nas (114) — the inverse of Spotify's newest-first
 * listing. Playback uses the YouTube IFrame API with auto-advance.
 */
const PODCAST = {
  title: 'المصحف المرتل — الشيخ محمود علي البنا',
  subtitle: 'تسجيلات الإذاعة المصرية · Egyptian Radio recordings',
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
  open: false,
  currentIndex: null,
  player: null,
  playerReady: false,
  _apiRequested: false,
  _pendingIndex: null,

  toggle() {
    const panel = document.getElementById('podcastPanel');
    const btn = document.getElementById('podcastBtn');
    this.open = !this.open;
    if (this.open) {
      this.renderList();
      panel.classList.add('open');
      btn.textContent = '✕ Hide Playlist';
    } else {
      panel.classList.remove('open');
      btn.textContent = '🎙 Play Podcast';
      this.pause();
    }
  },

  renderList() {
    const list = document.getElementById('podcastList');
    if (list.childElementCount) return;
    PODCAST.surahs.forEach((name, i) => {
      const li = document.createElement('li');
      li.className = 'podcast-item';
      li.dataset.index = i;
      li.innerHTML = `<span class="pc-num">${i + 1}</span><span class="pc-name">سورة ${name}</span><span class="pc-state"></span>`;
      li.addEventListener('click', () => this.playIndex(i));
      list.appendChild(li);
    });
  },

  playIndex(i) {
    // Athan takes priority: don't interrupt a live athan/duaa broadcast.
    if (AudioManager.isPlaying()) {
      App.logStatus('⚠️ Prayer audio is playing — podcast will not interrupt it.');
      return;
    }
    this.currentIndex = i;
    this.markCurrent();
    document.getElementById('podcastPlayerBox').style.display = 'block';

    if (this.playerReady) {
      this.player.loadVideoById(PODCAST.videoIds[i]);
    } else {
      this._pendingIndex = i;
      this._ensurePlayer();
    }
    App.logStatus(`🎙 Playing سورة ${PODCAST.surahs[i]} (${i + 1}/114)`);
  },

  _ensurePlayer() {
    if (this._apiRequested) return;
    this._apiRequested = true;

    const create = () => {
      this.player = new YT.Player('podcastPlayer', {
        width: '100%',
        height: '200',
        videoId: PODCAST.videoIds[this._pendingIndex ?? 0],
        playerVars: { autoplay: 1, rel: 0, playsinline: 1 },
        events: {
          onReady: () => {
            this.playerReady = true;
            if (this._pendingIndex != null) {
              this.player.loadVideoById(PODCAST.videoIds[this._pendingIndex]);
              this._pendingIndex = null;
            }
          },
          onStateChange: (e) => {
            if (e.data === YT.PlayerState.ENDED) this._next();
          },
          onError: () => {
            App.logStatus(`⚠️ سورة ${PODCAST.surahs[this.currentIndex]} could not play — skipping to the next one.`);
            this._next();
          }
        }
      });
    };

    if (window.YT && window.YT.Player) {
      create();
    } else {
      window.onYouTubeIframeAPIReady = create;
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      document.head.appendChild(tag);
    }
  },

  _next() {
    if (this.currentIndex != null && this.currentIndex < PODCAST.videoIds.length - 1) {
      this.playIndex(this.currentIndex + 1);
    }
  },

  /** Pause podcast playback (called when prayer audio starts). */
  pause() {
    if (this.playerReady && this.player?.pauseVideo) {
      try { this.player.pauseVideo(); } catch { /* player may be gone */ }
    }
  },

  markCurrent() {
    document.querySelectorAll('.podcast-item').forEach((el) => {
      const isCurrent = Number(el.dataset.index) === this.currentIndex;
      el.classList.toggle('playing', isCurrent);
      el.querySelector('.pc-state').textContent = isCurrent ? '▶' : '';
      if (isCurrent) el.scrollIntoView({ block: 'nearest' });
    });
  },

  init() {
    document.getElementById('podcastTitle').textContent = PODCAST.title;
    document.getElementById('podcastSubtitle').textContent = PODCAST.subtitle;
  }
};
