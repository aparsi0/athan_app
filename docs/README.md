# 🕌 Athan Web

**Live: <https://aparsi0.github.io/athan_app/>**

The browser version of the Athan desktop app — same features, shareable with anyone via a link, on any computer or phone. No installation, no Python, no VLC.

Prayer times are calculated from each visitor's own location (latitude & longitude) and timezone, so one link is accurate anywhere in the world.

## Features (parity with the desktop app)

- Automatic location detection (browser geolocation → IP fallback → manual coordinates)
- Daily prayer times from the Aladhan API (ISNA by default, 13 methods selectable)
- Per-prayer athan audio with fallback to the default soundtrack
- Woduaa reminder 15 minutes before each prayer
- Duaa right after each athan finishes
- Surat Al-Kahf on Fridays (Dhuhr + 120 min)
- Morning Azkar (Dhuhr − 240 min) and Night Azkar (Asr + 135 min)
- Quran tab: four complete mushafs behind a reciter selector, streamed as direct MP3s from mp3quran.net — محمد رفعت (31 surahs, all that survive), محمود خليل الحصري (ورش عن نافع), مصطفى إسماعيل and محمود علي البنا. A surah rolls into the next; at the end of a mushaf the next reciter starts from الفاتحة, wrapping indefinitely. The chosen reciter is remembered per device.
- Morning Quran: plays on its own from the end of the Fajr athan chain until an hour (configurable) after the Morning Azkar. The Azkar still take priority inside that window.
- Test Athan button cycles through the five prayers, playing each prayer's own athan file in turn
- Live next-prayer countdown, Hijri date, activity log
- Settings panel (per-visitor, saved in the browser)
- Browser notifications
- Live Cairo Quran radio (إذاعة القرآن الكريم, 98.2) and المصحف المعلم on their own tabs
- A 20-frame painted sky that cross-fades through your real solar day, anchored to your
  own prayer times rather than clock hours
- Installable as an app (PWA), with the app shell cached for offline use

## Browser limitations to know

- **One tap needed**: browsers block autoplay, so each visitor taps "Enable Athan & Location" once per visit. Nothing plays before that tap, including the morning Quran.
- **Tab must stay open** for audio to fire on time. Installing the PWA (browser menu → "Add to Home Screen" / "Install") gives it its own window.
- **Settings are per-device.** Everything lives in your own browser's localStorage — there is no server and no account, so one visitor's changes never affect another's. No analytics or tracking of any kind.
- **Third-party audio hosts see your IP** when you press play on a Quran tab (mp3quran.net, el-hosary.com, radiojar). Nothing is sent until you do: the players use `preload="none"` and the page sends no referrer. The hosts are named in Settings.

## Run locally

```bash
python3 -m http.server 8734 --directory docs
# open http://localhost:8734
```

## Deploy / update

Hosted on GitHub Pages, which serves the `docs/` folder on `main`. Any push touching
`docs/` redeploys to the same URL in about a minute.

```bash
git add -A && git commit -m "Update site" && git push
```

**Bump `CACHE_VERSION` in `docs/sw.js` on every HTML/CSS/JS change**, or returning
visitors keep the cached shell.

**Pushing.** GitHub stopped accepting account passwords in 2021. Use a **classic** token
(github.com/settings/tokens, tick the top-level `repo` scope) as the *password*, with
`aparsi0` as the username.

If a push fails with `remote: Permission to aparsi0/athan_app.git denied to aparsi0` —
note that is a 403, meaning it authenticated fine and was refused — a stale read-only
credential is cached. Clear it, or git will not even prompt for the new token:

```bash
printf "protocol=https\nhost=github.com\n\n" | git credential-osxkeychain erase
```

Fine-grained tokens fail the same way unless the repository is explicitly selected *and*
Contents is set to "Read and write". Classic tokens avoid that trap.

## Adding a reciter

One entry in `RECITERS` (`docs/js/reciters.js`) plus its host in the `media-src` CSP
directive in `docs/index.html`. mp3quran.net lists 241 reciters; the catalogue is at
`https://mp3quran.net/api/v3/reciters?language=ar`, and a moshaf's `server` field plus
`NNN.mp3` (three digits, zero-padded) is the whole URL. Verify it loads before shipping.

A reciter with an incomplete mushaf lists real surah numbers in a `surahs` array — that is
how محمد رفعت's 31 surviving recordings address correctly.
