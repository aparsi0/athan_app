"""
Index a folder of local Quran recordings and attribute them to reciters.

The desktop app can play files off disk instead of streaming: instant start,
no network, and it survives an outage of the audio host. This module turns a
messy human-named folder into something the player can use.

Two kinds of thing live in such a folder, and they are NOT interchangeable:

  * complete surahs  — "الشيخ محمد رفعت - سورة الفيل.m4a". These carry a real
    surah number and can replace the streamed copy in the numbered list.
  * recitals (تلاوات) — "من 51 - 73 البقرة", or a live session spanning several
    surahs like "الفرقان والطارق والحاقه والشمس". These have no single surah
    number and must stay out of the numbered list; they get their own section.

Attribution comes from the filename, never from the folder name. A folder
named for one sheikh routinely contains others — and a file dated after a
sheikh's death is definitely not his.
"""

import logging
import os
import re
import unicodedata
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

SURAH_NAMES = [
    "", "الفاتحة", "البقرة", "آل عمران", "النساء", "المائدة", "الأنعام", "الأعراف",
    "الأنفال", "التوبة", "يونس", "هود", "يوسف", "الرعد", "إبراهيم", "الحجر", "النحل",
    "الإسراء", "الكهف", "مريم", "طه", "الأنبياء", "الحج", "المؤمنون", "النور",
    "الفرقان", "الشعراء", "النمل", "القصص", "العنكبوت", "الروم", "لقمان", "السجدة",
    "الأحزاب", "سبأ", "فاطر", "يس", "الصافات", "ص", "الزمر", "غافر", "فصلت", "الشورى",
    "الزخرف", "الدخان", "الجاثية", "الأحقاف", "محمد", "الفتح", "الحجرات", "ق",
    "الذاريات", "الطور", "النجم", "القمر", "الرحمن", "الواقعة", "الحديد", "المجادلة",
    "الحشر", "الممتحنة", "الصف", "الجمعة", "المنافقون", "التغابن", "الطلاق", "التحريم",
    "الملك", "القلم", "الحاقة", "المعارج", "نوح", "الجن", "المزمل", "المدثر",
    "القيامة", "الإنسان", "المرسلات", "النبأ", "النازعات", "عبس", "التكوير",
    "الانفطار", "المطففين", "الانشقاق", "البروج", "الطارق", "الأعلى", "الغاشية",
    "الفجر", "البلد", "الشمس", "الليل", "الضحى", "الشرح", "التين", "العلق", "القدر",
    "البينة", "الزلزلة", "العاديات", "القارعة", "التكاثر", "العصر", "الهمزة", "الفيل",
    "قريش", "الماعون", "الكوثر", "الكافرون", "النصر", "المسد", "الإخلاص", "الفلق",
    "الناس",
]

AUDIO_EXTENSIONS = (".m4a", ".mp3", ".ogg", ".wav", ".aac", ".flac")


# Combining marks: Arabic diacritics, plus the hamza/madda marks that NFD
# splits off أ إ آ. macOS stores filenames decomposed, so a literal "إ" in this
# file will NOT match the same letter as it comes off disk unless we compose
# first and then drop what is left over.
_MARKS = re.compile(r"[\u064b-\u065f\u0670\u06d6-\u06ed]")


def _normalise(text: str) -> str:
    """Fold the spelling variations Arabic filenames use freely."""
    text = unicodedata.normalize("NFC", text)
    text = "".join(ch for ch in text if not unicodedata.category(ch).startswith("C"))
    text = _MARKS.sub("", text)
    for a, b in (("أ", "ا"), ("إ", "ا"), ("آ", "ا"),
                 ("ٱ", "ا"), ("ى", "ي"), ("ة", "ه"),
                 ("ؤ", "و"), ("ئ", "ي"), ("_", " ")):
        text = text.replace(a, b)
    return re.sub(r"\s+", "", text)


_SURAH_LOOKUP = {_normalise(name): i for i, name in enumerate(SURAH_NAMES) if name}

# Filename fragment -> reciter id in reciters.json. Order matters: the first
# match wins, so put anything specific above the general names.
ATTRIBUTION = [
    ("مصطفى إسماعيل", "mustafa"),
    ("مصطفىاسماعيل", "mustafa"),
    ("mustafa", "mustafa"),
    ("طنطا1961", "mustafa"),      # dated after رفعت died in 1950; confirmed مصطفى
    ("محمد رفعت", "refat"),
    ("محمدرفعت", "refat"),
    ("refat", "refat"),
    ("رفعت", "refat"),
    ("الحصري", "husr-warsh"),
    ("البنا", "bna"),
]


def attribute(filename: str) -> Optional[str]:
    """Which reciter is this file? None when the filename does not say."""
    flat = _normalise(filename).lower()
    for needle, reciter_id in ATTRIBUTION:
        if _normalise(needle).lower() in flat:
            return reciter_id
    return None


def complete_surah_number(filename: str) -> Optional[int]:
    """The surah number when the file is ONE complete surah, else None.

    A leading "من 51 - 73" marks a verse range, which is a recital and not a
    surah however much of a surah's name follows it.
    """
    stem = unicodedata.normalize("NFC", os.path.splitext(os.path.basename(filename))[0])
    stem = "".join(c for c in stem if not unicodedata.category(c).startswith("C"))
    body = stem.split(" - ")[-1] if " - " in stem else stem
    if re.search(r"\bمن\s*\d", body) or re.search(r"\d+\s*-\s*\d+", body):
        return None                       # verse range -> recital
    cleaned = _normalise(body)
    for junk in ("سوره", "كامله", "كاملة"):
        cleaned = cleaned.replace(_normalise(junk), "")
    number = _SURAH_LOOKUP.get(cleaned)
    # Guard against a multi-surah recital whose name happens to end in one
    # surah: those list several names, so the cleaned text would not match.
    return number


def pretty_title(filename: str) -> str:
    stem = unicodedata.normalize("NFC", os.path.splitext(os.path.basename(filename))[0])
    stem = "".join(c for c in stem if not unicodedata.category(c).startswith("C"))
    stem = stem.replace("_", " ").strip()
    for prefix in ("الشيخ محمد رفعت - ", "الشيخ مصطفى إسماعيل ", "الشيخ محمد رفعت "):
        if stem.startswith(prefix):
            stem = stem[len(prefix):]
    return stem.strip(" -")


def scan_library(directory: str) -> Dict[str, dict]:
    """Index `directory` into {reciter_id: {'surahs': {n: path}, 'recitals': [...]}}.

    Files whose reciter cannot be determined are reported and skipped rather
    than guessed at — misattributing a recitation is worse than omitting it.
    """
    result: Dict[str, dict] = {}
    if not directory or not os.path.isdir(directory):
        return result

    unattributed: List[str] = []
    for name in sorted(os.listdir(directory)):
        if not name.lower().endswith(AUDIO_EXTENSIONS):
            continue
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue

        reciter_id = attribute(name)
        if not reciter_id:
            unattributed.append(name)
            continue

        entry = result.setdefault(reciter_id, {"surahs": {}, "recitals": []})
        number = complete_surah_number(name)
        if number:
            entry["surahs"][number] = path
        else:
            entry["recitals"].append({"title": pretty_title(name), "path": path})

    if unattributed:
        logger.info(
            "Quran library: %d file(s) skipped, no reciter in the filename: %s",
            len(unattributed), ", ".join(unattributed[:5]),
        )
    for reciter_id, entry in result.items():
        logger.info(
            "Quran library: %s -> %d complete surah(s), %d recital(s)",
            reciter_id, len(entry["surahs"]), len(entry["recitals"]),
        )
    return result
