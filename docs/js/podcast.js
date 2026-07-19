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
      this.playing ? this.player.pauseVideo() : this.player.playVideo();
    });
    document.getElementById('prevBtn').addEventListener('click', () => {
      if (this.idx != null && this.idx > 0) this.play(this.idx - 1);
    });
    document.getElementById('nextBtn').addEventListener('click', () => {
      if (this.idx != null && this.idx < PODCAST.videoIds.length - 1) this.play(this.idx + 1);
    });
    document.getElementById('ytThumb').addEventListener('click', () =>
      document.getElementById('ytThumb').classList.toggle('expanded'));
  },

  play(i) {
    // Athan takes priority: don't interrupt a live athan/duaa broadcast.
    if (AudioManager.isPlaying()) {
      App.logStatus('⚠️ Prayer audio is playing — the Quran will not interrupt it.');
      return;
    }
    this.idx = i;
    document.getElementById('ytThumb').style.display = 'block';
    document.getElementById('piTitle').textContent = `سورة ${PODCAST.surahs[i]}`;
    document.getElementById('piSub').textContent = `${i + 1} / 114 · Sheikh Mahmoud Ali Al-Banna`;
    document.querySelectorAll('.surah-list li').forEach(el =>
      el.classList.toggle('playing', Number(el.dataset.i) === i));
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
            if (this._pendingIdx != null) {
              this.player.loadVideoById(PODCAST.videoIds[this._pendingIdx]);
              this._pendingIdx = null;
            }
          },
          onStateChange: (e) => {
            this.playing = e.data === YT.PlayerState.PLAYING;
            document.getElementById('playBtn').textContent = this.playing ? '⏸' : '▶';
            if (e.data === YT.PlayerState.ENDED && this.idx < PODCAST.videoIds.length - 1) {
              this.play(this.idx + 1);
            }
          },
          onError: () => {
            App.logStatus(`⚠️ سورة ${PODCAST.surahs[this.idx]} could not play — skipping to the next one.`);
            if (this.idx < PODCAST.videoIds.length - 1) this.play(this.idx + 1);
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

  /** Pause Quran playback (called when prayer audio starts). */
  pause() {
    if (this.ready && this.player?.pauseVideo) {
      try { this.player.pauseVideo(); } catch { /* player may be gone */ }
    }
  }
};
