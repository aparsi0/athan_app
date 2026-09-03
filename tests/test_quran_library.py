# -*- coding: utf-8 -*-
"""The local-recordings index, and the player's choice of source.

The fixture file names are the real ones from a macOS folder, stored NFD
(decomposed) exactly as that filesystem hands them out — a plain "إ" in the
source will NOT match them unless quran_library normalises first. That is a
bug this suite has already caught once.

VLC is stubbed: what is under test is WHICH source the player picks, never
decoding. Run: python3 tests/test_quran_library.py
"""

import os
import sys
import tempfile
import types

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

FIXTURE_NAMES = [
    'Mustafa_Najm.Qamar.Qesar_1971.mp3',
    'الشيخ محمد رفعت - سورة الاعلى كامله.m4a',
    'الشيخ محمد رفعت - سورة الانسان كامله.m4a',
    'الشيخ محمد رفعت - سورة البلد كامله.m4a',
    'الشيخ محمد رفعت - سورة التكاثر.m4a',
    'الشيخ محمد رفعت - سورة الرحمن كامله.m4a',
    'الشيخ محمد رفعت - سورة الطارق كامله.m4a',
    'الشيخ محمد رفعت - سورة العاديات.m4a',
    'الشيخ محمد رفعت - سورة العصر.m4a',
    'الشيخ محمد رفعت - سورة الفاتحة كامله.m4a',
    'الشيخ محمد رفعت - سورة الفيل.m4a',
    'الشيخ محمد رفعت - سورة القارعه.m4a',
    'الشيخ محمد رفعت - سورة القدر.m4a',
    'الشيخ محمد رفعت - سورة الهمزه.m4a',
    'الشيخ محمد رفعت - سورة قريش.m4a',
    'الشيخ محمد رفعت - من 1 - 17 هود.m4a',
    'الشيخ محمد رفعت - من 1 - 23 المرسلات.m4a',
    'الشيخ محمد رفعت - من 1 -14 الرعد.m4a',
    'الشيخ محمد رفعت - من 128 - 139 النساء.m4a',
    'الشيخ محمد رفعت - من 154 - 159 النساء.m4a',
    'الشيخ محمد رفعت - من 16 - 18 التوبه.m4a',
    'الشيخ محمد رفعت - من 170 - 173 النساء.m4a',
    'الشيخ محمد رفعت - من 28 - 51 آل عمران.m4a',
    'الشيخ محمد رفعت - من 31 - 32 النحل.m4a',
    'الشيخ محمد رفعت - من 33 - 35 المائده.m4a',
    'الشيخ محمد رفعت - من 33 - 39 النمل.m4a',
    'الشيخ محمد رفعت - من 39 - 41 ابراهيم.m4a',
    'الشيخ محمد رفعت - من 51 - 73 البقرة.m4a',
    'الشيخ محمد رفعت - من 58 - 79 النساء.m4a',
    'الشيخ محمد رفعت - من 6 - 20 آل عمران.m4a',
    'الشيخ محمد رفعت - من 62 - 66 النحل.m4a',
    'الشيخ محمد رفعت - من 68 - 71 النحل.m4a',
    '\u200e\u2068الحجرات ق الطارق الشرح طنطا 1961م\u2069.mp3',
    '\u200e\u2068الشيخ_محمد_رفعت_ما_تيسر_من_سورة_آل_عمران_قرآن_المغرب\u2069.mp3',
    '\u200e\u2068الشيخ_مصطفى_إسماعيل_الفرقان_والطارق_والحاقه_والشمس_اسكندريه\u2069.mp3',
    '\u200e\u2068الشيخ_مصطفى_إسماعيل_سور_الأعراف_والبلد_والاخلاص_جودة_أصلية\u2069.mp3',
]

# The 14 file names that are one complete surah, and the number each carries.
EXPECTED_SURAHS = [1, 55, 76, 86, 87, 90, 97, 100, 101, 102, 103, 104, 105, 106]


# ----- a VLC that records instead of playing -----------------------------

played = []


class _Media:
    def __init__(self, mrl):
        self.mrl = mrl


class _EventManager:
    def event_attach(self, *a, **k):
        pass


class _Player:
    def event_manager(self):
        return _EventManager()

    def set_media(self, media):
        played.append(media.mrl)

    def play(self):
        pass

    def stop(self):
        pass

    def set_pause(self, _v):
        pass

    def audio_set_volume(self, _v):
        pass

    def release(self):
        pass


class _Instance:
    def media_player_new(self):
        return _Player()

    def media_new(self, mrl):
        return _Media(mrl)

    def release(self):
        pass


_vlc = types.ModuleType("vlc")
_vlc.Instance = lambda *a, **k: _Instance()
_vlc.EventType = types.SimpleNamespace(
    MediaPlayerEndReached=1, MediaPlayerEncounteredError=2
)
sys.modules["vlc"] = _vlc

from core import quran_player as qp                      # noqa: E402
from core.quran_library import scan_library              # noqa: E402


class Config:
    def __init__(self, store):
        self.store = dict(store)

    def get(self, key, default=None):
        return self.store.get(key, default)

    def set(self, key, value):
        self.store[key] = value


failures = []


def check(label, got, want):
    if got == want:
        print("  ok   " + label)
        return
    failures.append(label)
    print("  FAIL " + label)
    print("        got : %r" % (got,))
    print("        want: %r" % (want,))


def build_fixture(directory):
    """Empty files with the real names. The scanner reads names, not audio."""
    for name in FIXTURE_NAMES:
        with open(os.path.join(directory, name), "wb"):
            pass


def main():
    with tempfile.TemporaryDirectory() as lib_dir:
        build_fixture(lib_dir)

        print("--- scanner ---")
        library = scan_library(lib_dir)
        classified = sum(
            len(e["surahs"]) + len(e["recitals"]) for e in library.values()
        )
        check("every file is classified, none skipped", classified, len(FIXTURE_NAMES))
        check("رفعت complete surahs", sorted(library["refat"]["surahs"]), EXPECTED_SURAHS)
        check("رفعت recitals", len(library["refat"]["recitals"]), 18)
        check("مصطفى recitals", len(library["mustafa"]["recitals"]), 4)
        check("مصطفى contributes no numbered surah", len(library["mustafa"]["surahs"]), 0)
        check(
            "the طنطا 1961 session is filed under مصطفى, not رفعت",
            len([r for r in library["mustafa"]["recitals"] if "طنطا" in r["title"]]),
            1,
        )
        check(
            "verse ranges never become surahs",
            len([r for r in library["refat"]["recitals"] if r["title"].startswith("من ")]),
            17,
        )

        print("--- recitals are ordered by the mushaf, not the alphabet ---")
        titles = [r["title"] for r in library["refat"]["recitals"]]
        check("البقرة before آل عمران",
              titles.index("من 51 - 73 البقرة") < titles.index("من 6 - 20 آل عمران"), True)
        check("verse 6 before verse 28 in the same surah",
              titles.index("من 6 - 20 آل عمران") < titles.index("من 28 - 51 آل عمران"), True)
        check("آل عمران before النساء",
              titles.index("من 28 - 51 آل عمران") < titles.index("من 58 - 79 النساء"), True)
        check("النساء 58 before النساء 128 (numeric, not string, order)",
              titles.index("من 58 - 79 النساء") < titles.index("من 128 - 139 النساء"), True)
        check("المرسلات (77) last of the verse ranges",
              titles.index("من 1 - 23 المرسلات"), len(titles) - 2)
        check("a session with no verse range sorts after them",
              titles[-1].startswith("ما تيسر"), True)

        print("--- source selection ---")
        player = qp.QuranPlayer(Config({"audio_settings.quran_library_path": lib_dir}))
        check("library indexed", player.library_dir, lib_dir)
        player.select_reciter("refat")
        tracks = player._tracks()
        streamed = set(qp.reciter_surahs(player.active()))
        check("track list is streamed ∪ local, sorted",
              tracks, sorted(streamed | set(library["refat"]["surahs"])))
        check("a local-only surah is a real addition",
              set(EXPECTED_SURAHS) - streamed <= set(tracks), True)

        def source(number):
            return player._url_for(tracks.index(number))

        check("a local surah plays off disk", os.path.isfile(source(105)), True)
        remote = sorted(streamed - set(EXPECTED_SURAHS))[0]
        check("a surah with no local file still streams",
              source(remote).startswith("http"), True)
        check("streamed names are zero-padded",
              source(remote).endswith("%03d.mp3" % remote), True)

        print("--- recitals stay out of the mushaf ---")
        player.play(tracks.index(105))
        mushaf_position = player.track_index
        check("mushaf plays the local file", played[-1], source(105))
        check("surah number is known during the mushaf",
              player.current_surah_number(), 105)
        player.play_recital(0)
        check("a recital claims no surah number", player.current_surah_number(), None)
        check("a recital is labelled by title",
              player.current_label(), player.recitals()[0]["title"])
        check("a recital does not move the mushaf position",
              player.track_index, mushaf_position)
        player._advance()
        check("one recital runs into the next",
              played[-1], player.recitals()[1]["path"])
        player.play_recital(len(player.recitals()) - 1)
        player._advance()
        check("after the last recital the mushaf resumes where it was",
              played[-1], source(105))
        check("recital mode is cleared", player._recital_index, None)

        print("--- a reciter with recitals but no local surahs ---")
        player.select_reciter("mustafa")
        check("recital count", len(player.recitals()), 4)
        check("the full streamed mushaf is still offered",
              len(player._tracks()), len(qp.reciter_surahs(player.active())))
        check("surah 1 streams", player._url_for(0).startswith("http"), True)

    print("--- no library at all ---")
    player = qp.QuranPlayer(Config({"audio_settings.quran_library_path": "/no/such/dir"}))
    check("a missing folder is survivable", player.library, {})
    player.select_reciter("refat")
    check("falls back to pure streaming", player._url_for(0).startswith("http"), True)
    check("no recitals without a library", player.recitals(), [])

    print()
    if failures:
        print("FAILED: %d" % len(failures))
        return 1
    print("ALL PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
