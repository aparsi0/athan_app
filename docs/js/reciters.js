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

/* The reciter table and the 114 surah names now live in ONE file,
   assets/reciters.json, which the desktop app reads too — so adding a reciter
   is a single edit and the two apps cannot drift apart. Loaded at init(); the
   service worker precaches it as a critical asset. */
const SURAH_NAMES = [];
const RECITERS = [];

let _reciterDataPromise = null;
function loadReciterData() {
  if (!_reciterDataPromise) _reciterDataPromise = _fetchReciterData();
  return _reciterDataPromise;
}

async function _fetchReciterData() {
  const res = await fetchWithTimeout('assets/reciters.json', 8000);
  if (!res.ok) throw new Error(`reciters.json: HTTP ${res.status}`);
  const data = await res.json();
  if (!Array.isArray(data.surah_names) || data.surah_names.length !== 114) {
    throw new Error('reciters.json: surah_names must hold exactly 114 entries');
  }
  if (!Array.isArray(data.reciters) || !data.reciters.length) {
    throw new Error('reciters.json: no reciters');
  }
  // Filled in place, not reassigned: audio-players.js captured SURAH_NAMES by
  // reference at load time for المصحف المعلم.
  SURAH_NAMES.length = 0; SURAH_NAMES.push(...data.surah_names);
  RECITERS.length = 0;    RECITERS.push(...data.reciters);
}

/** Surah numbers a reciter offers (all 114 unless the entry narrows it). */
function reciterSurahs(r) {
  return r.surahs || Array.from({ length: 114 }, (_, i) => i + 1);
}

const Reciters = {
  player: null,
  current: 0,          // index into RECITERS

  init() {
    if (!RECITERS.length) return;   // loadReciterData() must have run first
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
      trackNumbers: () => reciterSurahs(Reciters.active()),
      onPlaylistEnd: () => Reciters.advanceReciter(),
      // Last surah played on this device, at any hour. The morning window
      // resumes from it; it is not morning-specific.
      onTrackChange: (i) => Config.set('audio_settings.quran_last_index', i),
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

  /** Position i in THIS reciter's list -> its real surah number -> a URL.
   *  A surah listed in `local` is served from this repo instead of streamed —
   *  that is how محمد رفعت's 8 extra surahs work, since the streaming host
   *  does not carry them at all. */
  srcFor(i) {
    const reciter = this.active();
    const nums = reciterSurahs(reciter);
    const n = nums[i] != null ? nums[i] : nums[0];
    const local = reciter.local && reciter.local[String(n)];
    if (local) return `assets/audio/${reciter.id}/${local}`;
    return reciter.server + String(n).padStart(3, '0') + '.mp3';
  },

  _syncSelect() {
    const sel = document.getElementById('reciterSelect');
    if (sel) sel.value = String(this.current);
  },

  /** Switch reciter. autoplay starts surah 0 immediately (a real click).
   *  Selecting the reciter that is ALREADY current is a no-op — it must not
   *  reset the saved position, or resuming mid-morning is impossible. */
  select(i, autoplay) {
    const next = ((i % RECITERS.length) + RECITERS.length) % RECITERS.length;
    if (next === this.current) {
      if (autoplay) this.player.play(0, true);
      return;
    }
    this.current = next;
    Config.set('audio_settings.reciter_id', this.active().id);
    this._syncSelect();
    // A position is only meaningful within one reciter's list.
    Config.set('audio_settings.quran_last_index', 0);
    this.player.setTracks(this.trackNames());
    this.renderHeader();
    if (autoplay) this.player.play(0, true);
  },

  /** End of this mushaf -> first surah of the next reciter, wrapping forever. */
  advanceReciter() {
    const finished = this.active().sheikh;
    this.current = (this.current + 1) % RECITERS.length;
    Config.set('audio_settings.reciter_id', this.active().id);
    Config.set('audio_settings.quran_last_index', 0);
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
