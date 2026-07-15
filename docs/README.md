# 🕌 Athan Web

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
- Podcast playlist: the complete mushaf of Sheikh Mahmoud Ali Al-Banna in Quran order (Al-Fatiha → An-Nas), playable on-site, with a link to the Spotify show
- Live next-prayer countdown, Hijri date, activity log
- Settings panel (per-visitor, saved in the browser)
- Browser notifications
- Installable as an app (PWA) with offline caching of audio

## Browser limitations to know

- **One tap needed**: browsers block autoplay, so each visitor taps "Enable Athan Sound" once per visit.
- **Tab must stay open** for audio to fire on time. Installing the PWA (browser menu → "Add to Home Screen" / "Install") gives it its own window.

## Run locally

```bash
python3 -m http.server 8734 --directory docs
# open http://localhost:8734
```

## Deploy / update

Hosted on GitHub Pages. Any push to `main` that touches `docs/` redeploys automatically to the same URL (GitHub Pages serves the `docs/` folder).

```bash
git add -A && git commit -m "Update site" && git push
```
