/**
 * Quran tab - several complete mushafs behind one reciter selector.
 *
 * Every recitation is a direct MP3 from mp3quran.net, three-digit zero-padded
 * (001.mp3 ... 114.mp3) - the same URL shape المصحف المعلم already uses, so this
 * reuses makeAudioPlayer() from audio-players.js rather than adding an engine.
 *
 * Sequencing: a surah auto-advances to the next; when a reciter's mushaf
 * finishes, playback rolls on to the FIRST surah of the next reciter, and past
 * the last reciter back to the first - so it never stops.
 *
 * Sheikh محمد رفعت is deliberately a PARTIAL mushaf. He died in 1950 and never
 * recorded a complete one; only these 31 surahs survive, as live حفلات from the
 * 1930s-40s. His "end of mushaf" is سورة العاديات, not سورة الناس.
 *
 * All four sources were verified loading on 2026-09-02 under the live CSP.
 * Adding a reciter is one entry below plus its host in the media-src CSP.
 */

/** The 114 surah names, in Quran order. Shared by every player in the app. */
const SURAH_NAMES = [
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
];

const RECITERS = [
  {
    id: 'refat',
    sheikh: 'محمد رفعت',
    mushaf: 'تسجيلات حفلات - الإذاعة المصرية',
    server: 'https://server14.mp3quran.net/refat/',
    // Real surah numbers, not list positions. Only these survive.
    surahs: [1, 10, 11, 12, 17, 18, 19, 20, 48, 54, 55, 56, 69, 72, 73, 75, 76,
             77, 78, 79, 81, 82, 83, 85, 86, 87, 88, 89, 96, 98, 100],
    note: 'المصحف غير كامل - 31 سورة هي كل ما سُجّل'
  },
  {
    id: 'husr-warsh',
    sheikh: 'محمود خليل الحصري',
    mushaf: 'ورش عن نافع - مرتل',
    server: 'https://server13.mp3quran.net/husr/Rewayat-Warsh-A-n-Nafi/'
  },
  {
    id: 'mustafa',
    sheikh: 'مصطفى إسماعيل',
    mushaf: 'حفص عن عاصم - مرتل',
    server: 'https://server8.mp3quran.net/mustafa/'
  },
  {
    id: 'bna',
    sheikh: 'محمود علي البنا',
    mushaf: 'حفص عن عاصم - مرتل',
    server: 'https://server8.mp3quran.net/bna/'
  }
];

/** Surah numbers a reciter offers (all 114 unless the entry narrows it). */
function reciterSurahs(r) {
  return r.surahs || Array.from({ length: 114 }, (_, i) => i + 1);
}

const Reciters = {
  player: null,
  current: 0,          // index into RECITERS

  init() {
    const saved = Config.get('audio_settings.reciter_id', RECITERS[0].id);
    const at = RECITERS.findIndex((r) => r.id === saved);
    this.current = at >= 0 ? at : 0;

    this.player = makeAudioPlayer({
      name: 'Quran',
      icon: '🕌',
      get reciter() { return Reciters.active().sheikh; },
      tracks: this.trackNames(),
      volumeKey: 'audio_settings.quran_volume',
      srcFor: (i) => Reciters.srcFor(i),
      onPlaylistEnd: () => Reciters.advanceReciter(),
      // Remember the position so a reload mid-morning resumes the same surah.
      onTrackChange: (i) => Config.set('audio_settings.morning_quran_index', i),
      ids: {
        list: 'surahList', play: 'playBtn', prev: 'prevBtn', next: 'nextBtn',
        title: 'piTitle', sub: 'piSub', volume: 'quranVolume',
        seek: 'quranSeek', current: 'piCurrent', duration: 'piDuration'
      }
    });
    this.player.init();

    const sel = document.getElementById('reciterSelect');
    if (sel) {
      sel.innerHTML = RECITERS.map((r, i) =>
        '<option value="' + i + '">' + r.sheikh + ' - ' + r.mushaf + '</option>').join('');
      sel.value = String(this.current);
      sel.addEventListener('change', () => this.select(Number(sel.value), true));
    }
    this.renderHeader();
  },

  active() { return RECITERS[this.current]; },

  trackNames() {
    return reciterSurahs(this.active()).map((n) => SURAH_NAMES[n - 1]);
  },

  /** Position i in THIS reciter's list -> its real surah number -> a URL. */
  srcFor(i) {
    const nums = reciterSurahs(this.active());
    const n = nums[i] != null ? nums[i] : nums[0];
    return this.active().server + String(n).padStart(3, '0') + '.mp3';
  },

  _syncSelect() {
    const sel = document.getElementById('reciterSelect');
    if (sel) sel.value = String(this.current);
  },

  /** Switch reciter. autoplay starts surah 0 immediately (a real click). */
  select(i, autoplay) {
    const next = ((i % RECITERS.length) + RECITERS.length) % RECITERS.length;
    if (next === this.current && this.player.idx != null && !autoplay) return;
    this.current = next;
    Config.set('audio_settings.reciter_id', this.active().id);
    this._syncSelect();
    Config.set('audio_settings.morning_quran_index', 0);
    this.player.setTracks(this.trackNames());
    this.renderHeader();
    if (autoplay) this.player.play(0, true);
  },

  /** End of this mushaf -> first surah of the next reciter, wrapping forever. */
  advanceReciter() {
    const finished = this.active().sheikh;
    this.current = (this.current + 1) % RECITERS.length;
    Config.set('audio_settings.reciter_id', this.active().id);
    this._syncSelect();
    this.player.setTracks(this.trackNames());
    this.renderHeader();
    App.logStatus('🕌 ' + finished + ' - انتهى المصحف. التالي: ' + this.active().sheikh + '.');
    // NOT user-initiated: keeps the give-up guard armed if the next host is down.
    this.player.play(0);
  },

  renderHeader() {
    const r = this.active();
    const note = document.getElementById('reciterNote');
    if (note) note.textContent = r.note || '';
    const h = document.getElementById('quranHeading');
    if (h) h.textContent = r.sheikh + ' · ' + r.mushaf;
  },

  /** Force a specific reciter by id (used by the morning auto-play). */
  selectById(id) {
    const i = RECITERS.findIndex((r) => r.id === id);
    if (i >= 0) this.select(i);
    return i >= 0;
  }
};
