/**
 * Podcast playlist — the Quran mushaf of Sheikh Mahmoud Ali Al-Banna
 * (Egyptian Radio recordings), the same recordings as the Spotify show.
 * Spotify's embed can only list episodes newest-first (An-Nas → Al-Fatiha),
 * so this playlist presents them in the inverse — proper Quran order,
 * Al-Fatiha (1) → An-Nas (114) — with full-length on-site playback.
 * Audio served by mp3quran.net (CORS-open, range requests supported).
 */
const PODCAST = {
  title: 'المصحف المرتل — الشيخ محمود علي البنا',
  subtitle: 'تسجيلات الإذاعة المصرية · Egyptian Radio recordings',
  spotifyUrl: 'https://open.spotify.com/show/5d4FhdBUAYt220XU5seoUy',
  audioBase: 'https://server8.mp3quran.net/bna/',
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
  audio: null,

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
    }
  },

  renderList() {
    const list = document.getElementById('podcastList');
    if (list.childElementCount) return; // already rendered
    PODCAST.surahs.forEach((name, i) => {
      const num = i + 1;
      const li = document.createElement('li');
      li.className = 'podcast-item';
      li.dataset.index = i;
      li.innerHTML = `<span class="pc-num">${num}</span><span class="pc-name">سورة ${name}</span><span class="pc-state"></span>`;
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
    const num = String(i + 1).padStart(3, '0');
    const player = document.getElementById('podcastPlayer');
    player.src = `${PODCAST.audioBase}${num}.mp3`;
    player.style.display = 'block';
    player.play().catch(() => App.logStatus('⚠️ Could not start podcast playback.'));
    this.currentIndex = i;
    this.markCurrent();
    App.logStatus(`🎙 Playing سورة ${PODCAST.surahs[i]} (${i + 1}/114)`);
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
    const player = document.getElementById('podcastPlayer');
    // Auto-advance through the playlist in order.
    player.addEventListener('ended', () => {
      if (this.currentIndex != null && this.currentIndex < PODCAST.surahs.length - 1) {
        this.playIndex(this.currentIndex + 1);
      }
    });
    document.getElementById('podcastTitle').textContent = PODCAST.title;
    document.getElementById('podcastSubtitle').textContent = PODCAST.subtitle;
  }
};
