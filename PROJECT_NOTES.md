# Athan App — Project Notes & History

> Reference document summarizing everything done so far, the current state, and all
> decisions — so any future chat/session can pick up exactly where we left off.
> Last updated: **2026-07-15**.

---

## 1. What this project is

Two versions of an Islamic prayer-time application that plays the athan (and related
audio) automatically at the correct times:

| Version | Where | Status |
|---|---|---|
| **Desktop app** (original) | Repo root: `main.py`, `main_headless.py`, `core/`, `gui/`, `config/`, `utils/` — Python + VLC + Aladhan API | Unchanged, still works |
| **Athan Web** (browser port) | `docs/` folder — vanilla JS PWA, same features | **Live on GitHub Pages** |

## 2. The live website

- **Public link (share this):** https://aparsi0.github.io/athan_app/
- **Repository:** https://github.com/aparsi0/athan_app (public, GitHub account `aparsi0`)
- **Hosting:** GitHub Pages, **branch-based** — serves the `docs/` folder of branch `main`.
  - There is **no Actions workflow**. (One was written initially, but the `gh` OAuth token
    lacked `workflow` scope, so we renamed `web/` → `docs/` and used branch-based Pages instead.)
- **How to update the site:** edit files in `docs/`, then
  `git add -A && git commit -m "..." && git push` — live at the **same URL** ~1 minute later.
- **Cache note:** when changing HTML/CSS/JS, bump `CACHE_VERSION` in `docs/sw.js`
  (currently `athan-web-v4`) so visitors' service workers fetch the new version promptly.
- **Local preview:** `python3 -m http.server 8734 --directory docs`
  (also configured in `.claude/launch.json` as server name `athan-web`).
- `gh` CLI is installed and authenticated on this machine (account `aparsi0`, keyring).

## 3. Web app architecture (`docs/`)

| File | Role |
|---|---|
| `index.html` | Single page: sound/location gate, hero (next prayer + countdown), prayer list, scheduled events, podcast card, activity log, settings side panel |
| `css/style.css` | Dark navy + gold Islamic theme, responsive, RTL support for Arabic text |
| `js/config.js` | Defaults (mirrors the desktop `config.json`) + localStorage persistence (`athan_web_config_v1`) + `CALCULATION_METHODS` list |
| `js/location.js` | Location detection: browser geolocation → reverse geocode (bigdatacloud) → IP fallback (ipapi.co, ipwho.is — same providers as desktop) |
| `js/prayer-times.js` | Aladhan API (`api.aladhan.com/v1/timings`, visitor's timezone via `Intl`), per-day localStorage cache, `PRAYER_NAMES` / `PRAYER_LABELS` (en+ar) |
| `js/audio.js` | `AudioManager`: autoplay unlock, single-player playback, resolves `'ended' | 'stopped' | 'error'` so a manual Stop does **not** chain into the Duaa |
| `js/scheduler.js` | Builds today's event list from prayer times + config; 1-second tick fires events crossed since last tick (already-passed events don't fire on load); midnight rollover triggers refresh |
| `js/podcast.js` | Quran playlist (see §5) via YouTube IFrame API |
| `js/app.js` | Wires everything; UI rendering; settings panel; Test Athan cycling; notifications |
| `sw.js` | Service worker: app shell network-first, audio cache-first (runtime), never caches cross-origin/API |
| `manifest.webmanifest` + `assets/icons/` | PWA install (crescent icon: SVG + 180/192/512 PNG) |
| `assets/audio/*.m4a` | The 11 audio files copied from the desktop app (~63 MB) |

## 4. Features (parity with desktop + web extras)

- **Location**: asked via browser prompt on the welcome tap; 📍 header button re-requests;
  IP fallback; manual lat/lon in Settings. Each visitor gets times for **their** location
  and timezone. Site states explicitly that times are calculated from latitude & longitude.
- **Prayer times**: Aladhan API, ISNA (method 2) default, 13 methods selectable, Hijri date shown.
- **Audio events** (defaults = the user's live desktop config):
  - Athan at each prayer — **each prayer plays its own named file** from
    `audio_settings.athan_files` (fajr/dhuhr/asr/maghrib/isha_athan.m4a), falling back to
    `Azansoundtrack.m4a` only if missing. Volume 0.8.
  - Woduaa 15 min before each prayer (vol 0.65)
  - Duaa right after each athan **ends naturally** (vol 0.8; not after manual Stop)
  - Surat Al-Kahf on **Friday**, Dhuhr **+120 min** (vol 0.8) — weekday stored Python-style (Mon=0, Fri=4); JS conversion `(py+1)%7`
  - **Morning Azkar** (renamed from "Morning audio"): Dhuhr **−240 min** (vol 0.8)
  - **Night Azkar** (renamed from "Night audio"): Asr **+135 min** (vol 0.8)
- **Test Athan button cycles** Fajr → Dhuhr → Asr → Maghrib → Isha → …, playing each
  prayer's own file; button label shows which prayer plays next; index persists in
  localStorage (`athan_web_test_index`).
- **Settings panel**: prayers on/off, method, all volumes, Woduaa lead minutes,
  auto-detect vs manual location, notifications toggle, reset to defaults.
- **Other**: live countdown, activity log, "now playing" bar, browser notifications,
  PWA installable, daily midnight refresh.
- **Background-tab reliability** (added after user reported athan not firing when minimized):
  Web Worker clock (exempt from background timer throttling), inaudible keep-alive audio
  loop started on the welcome tap (marks the tab as playing media → exempt from tab freezing
  / Memory Saver / App Nap), visibility/focus catch-up with a 10-minute grace window
  (recently missed events still play; older ones are logged as missed), and an on-page
  "reliability tips" panel (keep window visible, Chrome Memory Saver exception, play the
  Quran podcast — audible playback is the strongest keep-alive signal —, install as app,
  keep the computer awake).

## 5. Podcast (evolution & current state)

1. User's Spotify show: https://open.spotify.com/show/5d4FhdBUAYt220XU5seoUy
   (المصحف المرتل — الشيخ محمود علي البنا، تسجيلات الإذاعة المصرية).
2. First attempt: Spotify iframe embed → rejected reasons: can't reorder (newest-first =
   An-Nas first) and only 30-s previews for logged-out visitors.
3. Second attempt: mp3quran.net Al-Banna murattal → user said **not identical** to the Spotify recordings.
4. **Current (correct) version**: the user's YouTube playlist
   https://www.youtube.com/playlist?list=PL8475A8813886C6A5 ("ختمة مرتّلة") holds the
   **identical recordings**. Its **first 114 items are exactly surahs 1–114 in Quran order**
   (items 115+ are a duplicate second series — ignored). The 114 video IDs are hardcoded in
   `docs/js/podcast.js` (`PODCAST.videoIds`), verified position-by-position.
   - Playback via **YouTube IFrame API**: click a surah → plays that exact video;
     auto-advance on end; skip on embed error; **pauses automatically when prayer audio starts**;
     athan is never interrupted by the podcast.
   - Playlist UI: 114 rows, Quran order (Al-Fatiha → An-Nas) = the inverse of Spotify's
     newest-first listing. Links to both Spotify and YouTube kept.

## 6. Key decisions & constraints (the "why")

- **Browser autoplay policy**: visitors must tap "🔊 Enable Athan & Location" once per visit
  before audio can play; after that everything is automatic **while the tab stays open**.
  Phones may suspend locked/background tabs — desktop or installed PWA is most reliable.
- **Per-visitor isolation**: all settings live in each visitor's own browser localStorage.
  Person A changing volume/location/etc. never affects person B or the site itself.
  Only the repo owner can change the actual website (public repo, but write access = owner only).
- **No analytics / no tracking** — offered GoatCounter/GA4/Cloudflare; **user chose "No tracking"**
  (2026-07-15). So there is deliberately no visitor data (counts, countries, playtime).
  If ever wanted: user creates the analytics account themselves, then a small snippet gets added.
- **Bug found & fixed during testing**: pressing Stop during the athan used to chain into
  the after-prayer Duaa. `AudioManager.play()` now resolves a reason; Duaa only on `'ended'`.
- The user's personal photo (`*.HEIC`) is **gitignored** — never push it to the public repo.
- Prayer times use latitude/longitude (+timezone) — *not* altitude (user once said "altitude",
  wording on-site says latitude & longitude).

## 7. Timeline of work (all on 2026-07-15)

1. Explored desktop app; copied its behavior/config as web defaults.
2. Built `web/` (now `docs/`): full JS port, PWA, tested end-to-end locally (schedule math,
   athan→duaa chain, settings, mobile layout, all 11 audio files).
3. Installed `gh` CLI (Homebrew); user authorized via device flow (`aparsi0`).
4. Created public repo, hit workflow-scope limit → renamed `web/`→`docs/`, enabled
   branch-based Pages → **live**; verified on public URL.
5. Added: explicit location button + gate wording; Spotify embed (v1 podcast).
6. Replaced podcast with mp3quran playlist (v2) + Morning/Night **Azkar** renames +
   location statement on page.
7. Replaced podcast source with the **YouTube playlist** (v3, identical recordings) +
   **Test Athan per-prayer cycling**. Verified live.
8. Answered: sharing/autoplay behavior, no-analytics decision, per-visitor settings isolation.
9. Wrote this file.
10. **Background-tab reliability fixes** (user reported athan only firing in the focused tab):
    Web Worker clock, inaudible keep-alive loop, 10-min grace catch-up, tips panel (sw v5).
11. Added tip that playing the Quran podcast keeps the tab active (sw v6).

## 9. How updates reach visitors

Site changes go live at the same URL ~1 minute after `git push`. The service worker fetches
the app shell **network-first**, so visitors get the new version on their next page load or
refresh — no reinstall, no cache clearing. Tabs that are already open keep running the old
code until reloaded (one refresh + the usual welcome tap).

## 7b. Living-scene redesign (2026-07-19)

Prototyped in `demo/` (kept for reference; not deployed), then shipped to `docs/`:
- **Layout**: QuantumPT-inspired — centered brand + tab bar (Athan / Schedule / Quran /
  Activity / Settings). Athan is the main tab. Old side-drawer settings became the
  Settings tab; the podcast card became the Quran tab.
- **`docs/js/scene.js`**: canvas scene engine driven by the visitor's REAL sun times.
  Draw order sky → stars → sun/moon(+glow) → terrain, so celestial bodies rise/set
  BEHIND the landscape and stars are occluded by it. Sun is a warm bloom near the
  horizon, subtle glare at midday; moon is a crescent sprite; light reflects on water.
- **2026-07-19 later revision (current)**: user found the sky-cut versions ugly →
  themes now show the ORIGINAL uncropped photos (`assets/photo_a..e.jpg`, small JPEGs) and
  the scene engine does LIGHTING ONLY: brightness/saturation by time of day, cool night
  cast, warm dawn/sunset glow. No drawn sun/moon/stars, no canvas — layered divs
  (#photo/#shade/#glow) with CSS transitions. terrain_*/ridge_* assets deleted; sw v9.
- **Themes = exactly five real-photo landscapes** (user's choice, replacing the earlier
  art/classic set; old saved values migrate to `d`). Values `a`–`e` in `ui_settings.theme`,
  assets `terrain_X.png` + `ridge_X.json`, lazy-loaded per selected theme (sw v8 caches
  them at runtime, not precache). Source photos (Unsplash): a=1464822759023 Alpine Valley,
  b=1458668383970 Above the Clouds, c=1476514525535 Mountain Lake (boat), d=1439066615861
  Lake Dock (default), e=1469474968028 Golden Valley. Segmentation: per-column vertical-
  smoothness scan; d uses the precise blue-sky method (tree-tip detail); a/b/e use a
  windowed low-quantile skyline envelope (clouds kept as terrain in a).
- **Install tab** on the site: per-platform cards (🌙 macOS menu-bar,  M1/2/3, 🖥 Intel,
  🪟 Windows, 🐧 Linux, ⚙️ headless, ✅ verify) hyperlinking to the exact GitHub README
  anchors (verified against GitHub's rendered ids), plus phone add-to-home-screen note.
- **Quran tab**: audio-style player (⏮ ⏯ ⏭ + 114-surah list, auto-advance, skip on embed
  error) controlling a minimized corner YouTube player (YouTube requires its player to be
  visible; tap to enlarge). Global object still named `Podcast` — the athan pipeline calls
  `Podcast.pause()` for priority.
- Sky-segmentation pipeline (venv with Pillow/numpy, per-column blue-sky scan) lives in the
  scratchpad; to swap the photo, re-run it on any image with a clean skyline.
- sw.js v7 (added scene.js, terrain.png ~2.2 MB, ridge.json). All prior behavior preserved.
- User declined an insect-repelling keep-alive frequency after science/hardware/ethics
  explanation (ultrasonics don't repel roaches; speakers can't emit >20 kHz; audible-to-kids
  risk). Keep-alive track confirmed harmless to speakers.

## 8. Possible future ideas (not requested yet)

- Analytics (only if the user changes their mind — see §6).
- Custom domain for the site (Pages supports CNAME).
- Re-adding a GitHub Actions deploy (needs `gh auth refresh -s workflow` re-authorization).
- Monthly prayer-times table view; more languages; adjustable Al-Kahf/Azkar offsets in UI
  (currently config-level defaults only).
