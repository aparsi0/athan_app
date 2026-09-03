"""
Quran playback for the desktop app — the morning Quran window, and the same
reciter rotation the web app has.

Deliberately a SECOND, independent VLC player. The athan pipeline owns
AudioPlayer.media_player, and that one player is stopped and reused for every
athan, duaa and azkar. Sharing it would mean prayer audio destroying the
Quran's position every time, with nothing to resume. A separate player can be
paused and resumed while the athan has the floor.

The reciter table comes from docs/assets/reciters.json — the SAME file the web
app reads, so the two can never drift apart. Adding a reciter is one edit
there.
"""

import json
import logging
import os
import threading
from pathlib import Path
from typing import Callable, List, Optional

try:
    import vlc
except ImportError:      # lets the module import on machines without VLC
    vlc = None

from core.quran_library import scan_library
from utils.app_paths import get_bundle_root, get_project_root

logger = logging.getLogger(__name__)

# Where to look for local recordings when the config does not name a folder.
# Checked in order; the first that exists wins. A missing folder is normal —
# the player streams instead.
DEFAULT_LIBRARY_DIRS = [
    "~/Music/Athan Quran",
    "~/Downloads/القران الكريم بصوت الشيخ محمد رفعت",
]


def _reciter_data_path() -> Optional[Path]:
    """docs/assets/reciters.json, from a source checkout or a frozen bundle."""
    for root in (get_project_root(), get_bundle_root()):
        for rel in ("docs/assets/reciters.json", "assets/reciters.json"):
            candidate = Path(root) / rel
            if candidate.is_file():
                return candidate
    return None


def load_reciters() -> tuple:
    """Return (surah_names, reciters). Empty on any failure — the caller must
    cope, because the athan must keep working even if the Quran side cannot."""
    path = _reciter_data_path()
    if not path:
        logger.warning("reciters.json not found; Quran playback disabled")
        return [], []
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        names = data.get("surah_names") or []
        reciters = data.get("reciters") or []
        if len(names) != 114:
            logger.error("reciters.json: expected 114 surah names, got %d", len(names))
            return [], []
        if not reciters:
            logger.error("reciters.json: no reciters listed")
            return [], []
        logger.info("Loaded %d reciters from %s", len(reciters), path)
        return names, reciters
    except Exception as exc:
        logger.error("Could not read %s: %s", path, exc)
        return [], []


def reciter_surahs(reciter: dict) -> List[int]:
    """Surah numbers this reciter offers. Real numbers, not list positions —
    محمد رفعت has only 31, and position 5 in his list is surah 18 (الكهف)."""
    listed = reciter.get("surahs")
    return list(listed) if listed else list(range(1, 115))


class QuranPlayer:
    """Streams a mushaf, one surah into the next, one reciter into the next."""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.surah_names, self.reciters = load_reciters()

        self.reciter_index = 0
        self.track_index = 0
        # When a تلاوة is playing, track_index indexes the recital list instead
        # of the surah list. Kept separate so a recital never overwrites the
        # saved mushaf position.
        self._recital_index = None
        self.is_playing = False
        self._suspended = False          # paused because prayer audio has the floor
        self._lock = threading.RLock()
        self.on_status = None            # optional Callable[[str], None] for the log

        # Local recordings, indexed before _restore_position() because that
        # validates the saved index against the track list, which the library
        # can lengthen.
        self.library = {}
        self.library_dir = None
        self._load_library()

        self._instance = None
        self._player = None
        if vlc is not None and self.reciters:
            self._init_vlc()

        self._restore_position()

    # ----- setup ---------------------------------------------------------

    def _load_library(self):
        """Index the local recordings folder, if there is one."""
        configured = self._cfg('audio_settings.quran_library_path') or ''
        candidates = [configured] if configured else list(DEFAULT_LIBRARY_DIRS)
        for candidate in candidates:
            if not candidate:
                continue
            path = os.path.expanduser(candidate)
            if not os.path.isdir(path):
                continue
            try:
                self.library = scan_library(path)
            except Exception as exc:
                logger.error("Could not index %s: %s", path, exc)
                self.library = {}
                return
            self.library_dir = path
            total_surahs = sum(len(e['surahs']) for e in self.library.values())
            total_recitals = sum(len(e['recitals']) for e in self.library.values())
            logger.info(
                "Local Quran library: %s -> %d surah file(s), %d recital(s)",
                path, total_surahs, total_recitals,
            )
            return
        if configured:
            logger.warning("Quran library folder not found: %s", configured)

    def set_library_path(self, path: str):
        """Point at a different folder and re-index. Empty clears the override."""
        self._set_cfg('audio_settings.quran_library_path', path or '')
        with self._lock:
            self.library = {}
            self.library_dir = None
            self._load_library()
            tracks = self._tracks()
            if self.track_index >= len(tracks):
                self.track_index = 0

    def _local(self, reciter_id: str) -> dict:
        return self.library.get(reciter_id) or {"surahs": {}, "recitals": []}

    def recitals(self, reciter_id: Optional[str] = None) -> List[dict]:
        """The تلاوات — verse ranges and multi-surah sessions. These are NOT
        part of the mushaf rotation: they have no single surah number and would
        corrupt the numbered order."""
        if reciter_id is None:
            reciter_id = self.active().get('id', '')
        return list(self._local(reciter_id)["recitals"])

    def _init_vlc(self):
        try:
            self._instance = vlc.Instance(
                ['--intf', 'dummy', '--no-video', '--quiet', '--no-osd']
            )
            self._player = self._instance.media_player_new()
            manager = self._player.event_manager()
            manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end)
            manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)
            logger.info("Quran player initialized (separate from the athan player)")
        except Exception as exc:
            logger.error("Could not initialize the Quran VLC player: %s", exc)
            self._player = None

    @property
    def available(self) -> bool:
        return self._player is not None and bool(self.reciters)

    def _log(self, message: str):
        logger.info(message)
        if callable(self.on_status):
            try:
                self.on_status(message)
            except Exception:
                pass

    # ----- config ---------------------------------------------------------

    def _cfg(self, key: str, default=None):
        if not self.config_manager:
            return default
        try:
            return self.config_manager.get(key, default)
        except Exception:
            return default

    def _set_cfg(self, key: str, value):
        if not self.config_manager:
            return
        try:
            self.config_manager.set(key, value)
        except Exception as exc:
            logger.debug("Could not persist %s: %s", key, exc)

    def _restore_position(self):
        saved_id = self._cfg('audio_settings.reciter_id')
        if saved_id:
            for i, reciter in enumerate(self.reciters):
                if reciter.get('id') == saved_id:
                    self.reciter_index = i
                    break
        try:
            index = int(self._cfg('audio_settings.quran_last_index', 0) or 0)
        except (TypeError, ValueError):
            index = 0
        self.track_index = index if 0 <= index < len(self._tracks()) else 0

    # ----- current selection ---------------------------------------------

    def active(self) -> dict:
        return self.reciters[self.reciter_index] if self.reciters else {}

    def _tracks(self) -> List[int]:
        """Surah numbers for the active reciter, streamed and local combined.

        A local file for a surah the host does not serve is a real addition, so
        the two sets are unioned rather than one replacing the other.
        """
        if not self.reciters:
            return []
        reciter = self.active()
        numbers = set(reciter_surahs(reciter))
        numbers.update(self._local(reciter.get('id', ''))["surahs"])
        return sorted(numbers)

    def current_surah_number(self) -> Optional[int]:
        if self._recital_index is not None:
            return None      # a recital spans several surahs, or part of one
        tracks = self._tracks()
        if not tracks:
            return None
        return tracks[self.track_index] if 0 <= self.track_index < len(tracks) else tracks[0]

    def current_label(self) -> str:
        if self._recital_index is not None:
            items = self.recitals()
            if 0 <= self._recital_index < len(items):
                return items[self._recital_index]['title']
            return ""
        number = self.current_surah_number()
        if number is None:
            return ""
        name = self.surah_names[number - 1] if 0 < number <= len(self.surah_names) else str(number)
        return f"سورة {name}"

    def _url_for(self, index: int) -> Optional[str]:
        """Where to read track `index` from. A local file beats the stream:
        it starts instantly and survives the host being down."""
        tracks = self._tracks()
        if not tracks:
            return None
        if not 0 <= index < len(tracks):
            index = 0
        number = tracks[index]
        local = self._local(self.active().get('id', ''))["surahs"].get(number)
        if local and os.path.isfile(local):
            return local
        server = self.active().get('server', '')
        if not server:
            return None       # local-only reciter with a gap; skip, do not 404
        return f"{server}{number:03d}.mp3"

    def select_reciter(self, reciter_id: str) -> bool:
        for i, reciter in enumerate(self.reciters):
            if reciter.get('id') == reciter_id:
                with self._lock:
                    if i != self.reciter_index:
                        self.reciter_index = i
                        self.track_index = 0        # position is per reciter
                        self._set_cfg('audio_settings.reciter_id', reciter_id)
                        self._set_cfg('audio_settings.quran_last_index', 0)
                return True
        return False

    # ----- playback -------------------------------------------------------

    def play(self, index: Optional[int] = None) -> bool:
        if not self.available:
            return False
        with self._lock:
            self._recital_index = None
            if index is not None:
                self.track_index = index
            url = self._url_for(self.track_index)
            if not url:
                return False
            try:
                media = self._instance.media_new(url)
                self._player.set_media(media)
                self._apply_volume()
                self._player.play()
                self.is_playing = True
                self._suspended = False
                self._set_cfg('audio_settings.quran_last_index', self.track_index)
                self._log(f"🕌 {self.active().get('sheikh', '')} — {self.current_label()}")
                return True
            except Exception as exc:
                logger.error("Quran playback failed for %s: %s", url, exc)
                return False

    def play_recital(self, index: int) -> bool:
        """Play تلاوة `index` for the active reciter.

        The mushaf position is left untouched: when the recital list runs out,
        playback returns to the surah the mushaf was on.
        """
        if not self.available:
            return False
        with self._lock:
            items = self.recitals()
            if not 0 <= index < len(items):
                return False
            item = items[index]
            if not os.path.isfile(item['path']):
                logger.warning("Recital file is gone: %s", item['path'])
                return False
            try:
                media = self._instance.media_new(item['path'])
                self._player.set_media(media)
                self._apply_volume()
                self._player.play()
                self.is_playing = True
                self._suspended = False
                self._recital_index = index
                self._log(f"🕌 {self.active().get('sheikh', '')} — {item['title']}")
                return True
            except Exception as exc:
                logger.error("Recital playback failed for %s: %s", item['path'], exc)
                return False

    def _apply_volume(self):
        try:
            volume = float(self._cfg('audio_settings.quran_volume', 0.8) or 0.8)
            self._player.audio_set_volume(int(max(0.0, min(1.0, volume)) * 100))
        except Exception:
            pass

    def set_volume(self, volume: float):
        self._set_cfg('audio_settings.quran_volume', max(0.0, min(1.0, float(volume))))
        if self._player:
            self._apply_volume()

    def stop(self):
        """Full stop. Forgets that it was playing, so nothing auto-resumes."""
        with self._lock:
            self.is_playing = False
            self._suspended = False
            self._recital_index = None
            if self._player:
                try:
                    self._player.stop()
                except Exception:
                    pass

    def suspend(self):
        """Prayer audio has the floor. Remembers, so resume() can restore."""
        with self._lock:
            if not self.is_playing:
                return
            self._suspended = True
            self.is_playing = False
            if self._player:
                try:
                    self._player.set_pause(1)
                except Exception:
                    pass

    def resume(self) -> bool:
        """Undo suspend(). No-op unless suspend() actually paused something."""
        with self._lock:
            if not self._suspended or not self._player:
                return False
            self._suspended = False
            self.is_playing = True
            try:
                self._player.set_pause(0)
                return True
            except Exception:
                return False

    @property
    def suspended(self) -> bool:
        return self._suspended

    # ----- rotation -------------------------------------------------------

    def _on_end(self, _event):
        # VLC calls this from its own thread and forbids blocking here, so hand
        # the work to a normal thread before touching the player again.
        threading.Thread(target=self._advance, daemon=True).start()

    def _advance(self):
        with self._lock:
            if not self.is_playing:
                return          # stopped or suspended between the event and now
            if self._recital_index is not None:
                nxt_recital = self._recital_index + 1
                if nxt_recital < len(self.recitals()):
                    self.play_recital(nxt_recital)
                else:
                    # التلاوات finished; hand back to the mushaf where it was.
                    self._log("🕌 انتهت التلاوات — العودة إلى المصحف.")
                    self.play()
                return
            tracks = self._tracks()
            nxt = self.track_index + 1
            if nxt < len(tracks):
                self.track_index = nxt
                self.play()
                return
            finished = self.active().get('sheikh', '')
            self.reciter_index = (self.reciter_index + 1) % len(self.reciters)
            self.track_index = 0
            self._set_cfg('audio_settings.reciter_id', self.active().get('id'))
            self._set_cfg('audio_settings.quran_last_index', 0)
            self._log(
                f"🕌 {finished} — انتهى المصحف. التالي: {self.active().get('sheikh', '')}."
            )
            self.play()

    def _on_error(self, _event):
        threading.Thread(target=self._skip_failed, daemon=True).start()

    def _skip_failed(self):
        with self._lock:
            if not self.is_playing:
                return
            self._failures = getattr(self, '_failures', 0) + 1
            # Same guard the web player needed twice: a dead host must not walk
            # the whole mushaf. Only real playback clears the streak.
            if self._failures >= 5:
                self._log("⚠️ Quran — nothing is loading from the audio host; stopping.")
                self.is_playing = False
                self._failures = 0
                return
            self._advance()

    def note_playing(self):
        """Called on real playback to clear the failure streak."""
        self._failures = 0

    def cleanup(self):
        self.stop()
        try:
            if self._player:
                self._player.release()
            if self._instance:
                self._instance.release()
        except Exception:
            pass
