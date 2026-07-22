# Athan App — Project Summary

> Compact reference: current features, full folder map, and a condensed changelog.
> Read this first in any new session — it replaces re-deriving context from scratch.
> Last updated: **2026-07-21**.

---

## 1. What this project is

| Version | Where | Status |
|---|---|---|
| **Desktop app** (original) | Repo root — Python + VLC + Aladhan API | Unchanged, still works |
| **Athan Web** (browser port) | `docs/` — vanilla JS PWA | **Live on GitHub Pages** |

**Live link:** https://aparsi0.github.io/athan_app/
**Repo:** https://github.com/aparsi0/athan_app (public, account `aparsi0`, `gh` CLI authed locally)

## 2. How to update the live site

```bash
# edit files under docs/, then:
git add -A && git commit -m "..." && git push
```
Live at the **same URL** ~1 minute later (GitHub Pages, branch-based, serves `docs/` on `main` —
no Actions workflow; the `gh` token lacks `workflow` scope). When changing HTML/CSS/JS, bump
`CACHE_VERSION` in `docs/sw.js` (currently **v18**) so visitors' service workers refresh promptly.
Tabs already open pick up changes on next reload; new visitors get it immediately.

**Local preview:** `python3 -m http.server 8734 --directory docs` (or `.claude/launch.json` →
`athan-web`). Note: the automated browser tool used for testing in this project can hold a stale
HTTP disk-cache per origin/port across server restarts — if verifying a change looks stale,
spin up a fresh unused port rather than trusting a reload.

---

## 3. Folder map

```
athan_app/
├── PROJECT_NOTES.md          ← this file
├── README.md                 desktop-app install guide (all platforms + menu-bar auto-start)
├── main.py / main_headless.py            desktop app entry points (GUI / headless)
├── requirements.txt, requirements-desktop.txt
├── test_core.py, tests/                  desktop app tests
├── install.sh, export_for_sharing.sh
├── config/settings.py                    desktop ConfigManager (JSON config, defaults)
├── core/                                 desktop engine
│   ├── audio_player.py                     VLC playback
│   ├── location_service.py                 geolocation
│   ├── prayer_times.py                     Aladhan API client
│   └── scheduler.py                        event scheduling
├── gui/                                  desktop Tk UI (main window, settings, tray icon)
├── utils/                                app_paths.py, helpers.py
├── macos/                                launchd auto-start (menu-bar + headless variants)
│   ├── com.apa.athan-menubar.plist / install_menubar_agent.sh   ← recommended
│   └── com.apa.athan-app.plist / install_launch_agent.sh        ← headless
├── packaging/                            PyInstaller build scripts (macOS .app, Windows)
├── assets/audio/*.m4a                    11 athan/duaa/azkar recordings (~63 MB, source of truth;
│                                          docs/assets/audio/ is a copy used by the website)
├── demo/                                 design playground, NOT deployed (kept for reference)
│   ├── index.html                          early living-scene prototypes
│   └── candidates/                         theme-photo comparison pages
│
└── docs/                     ★ THE LIVE WEBSITE — GitHub Pages serves this folder ★
    ├── index.html             page shell: sound/location gate, 6 tabs, all panels   (254 lines)
    ├── manifest.webmanifest   PWA metadata
    ├── sw.js                  service worker — cache version v18                     (74 lines)
    ├── README.md              web-app-specific readme
    ├── css/style.css          full site styling, responsive, RTL Arabic support     (367 lines)
    ├── js/
    │   ├── config.js            defaults + localStorage persistence, Safari-safe helpers (165)
    │   ├── location.js          browser geolocation → reverse-geocode → IP fallback    (92)
    │   ├── prayer-times.js      Aladhan API client + per-day cache                      (88)
    │   ├── scheduler.js         builds/fires today's event list, midnight rollover     (157)
    │   ├── audio.js             single reusable <audio> element, keep-alive loop        (127)
    │   ├── scene.js             ★ 20-frame living-sky engine (see §5)                  (410)
    │   ├── podcast.js           Quran player: playlist, seek bar, resume logic          (269)
    │   └── app.js               wires everything, UI rendering, settings, Test Athan    (399)
    └── assets/
        ├── audio/*.m4a           same 11 recordings as desktop (~63 MB)
        ├── icons/                 PWA icons (SVG + 180/192/512 PNG)
        └── sky_01.jpg … sky_20.jpg   the 20 painted day/night frames (~3.6 MB total)
```

**Not tracked in git** (gitignored, machine-local only): `.venv/`, `build/`, `dist/`, `__pycache__/`,
`*.log`, the personal `*.HEIC` photo, and any `*.zip` design deliverables.

---

## 4. Features — current state

**Location & prayer times**
- Browser geolocation on the welcome tap (📍 header button re-requests); reverse-geocode; IP
  fallback; manual lat/lon in Settings. Each visitor gets times for **their own** location/timezone.
- Aladhan API, ISNA default, 13 calculation methods, Hijri date shown.

**Audio events** (each with its own volume, matching the desktop app's live config)
- Athan — **each prayer plays its own named file**, falls back to the default soundtrack only if missing.
- Woduaa 15 min before each prayer · Duaa right after each athan **ends naturally** (not after manual Stop)
- Surat Al-Kahf Fridays, Dhuhr+120 min · **Morning Azkar** Dhuhr−240 min · **Night Azkar** Asr+135 min
- **Test Athan** button cycles Fajr→Dhuhr→Asr→Maghrib→Isha, playing each prayer's real file in turn.

**The living sky (`scene.js`)** — see §5 for full detail. 20 hand-painted frames of one valley,
cross-fading through the visitor's real solar day; sun/moon painted directly into the art.

**Quran player** (`podcast.js`)
- All 114 surahs, Quran order, identical recordings to the user's YouTube playlist
  (`PL8475A8813886C6A5`), played via the YouTube IFrame API (minimized corner thumbnail — YouTube
  requires its player stay visible).
- **Seek bar**: shows each surah's real duration, fills as it plays, drag to scrub forward/back.
- **Separate volume slider** (independent of athan volume) — fixes "can't lower Quran volume from
  the tiny YouTube window."
- **Athan priority**: pauses automatically when prayer audio starts, **auto-resumes** once the full
  chain (athan + duaa) finishes; pressing Stop cancels the pending resume.
- **Loops forever**: An-Nas → back to Al-Fatiha.

**Reliability (background/minimized tabs)**
- Web Worker clock (exempt from background-tab timer throttling)
- Inaudible keep-alive audio loop, started on the welcome tap (keeps the tab exempt from
  freezing/Memory Saver/App Nap)
- 10-minute catch-up grace window for events missed while suspended
- On-page tips panel; Safari-specific fixes (single reusable user-activated `<audio>` element,
  no `structuredClone`/`AbortSignal.timeout`, `-webkit-` prefixes)

**Other:** live countdown, activity log, browser notifications, installable PWA, daily midnight
refresh, **Install tab** linking each platform to the exact README section, per-visitor settings
isolation (localStorage — one visitor's changes never affect another), **no analytics/tracking**
(user's explicit choice).

---

## 5. The living sky — how `scene.js` works

20 hand-painted frames of the same valley (`sky_01.jpg`…`sky_20.jpg`), same composition, only the
light (and sun/moon position) differs. The engine cross-fades continuously between the two frames
bracketing the current instant, **anchored to the visitor's real prayer/solar times** — not fixed
clock hours — via `Scene.setTimes({ fajr, sunrise, dhuhr, asr, maghrib, isha })`.

**Exact per-frame schedule** (each verified to land precisely via `Scene._position()`):

| Frame | Arrives at | Note |
|---|---|---|
| 1 | **Fajr** exactly | holds 20 min |
| 2, 3, 4, 5 | evenly divide Fajr+20 → Sunrise | one frame each |
| 6 | **Sunrise** exactly | sun disc rises — sun visible in frames 6–16 only |
| 7–16 | sunrise → solar noon → Maghrib | proportional spacing |
| 17 | **Maghrib − 1 min** | sun already gone |
| 18 | mid-evening, holds until Isha | dusk |
| 19 | **Isha** exactly | must already be on screen |
| 20 | mid-night | "moon mid-sky" bridge frame |
| → 1 | next **Fajr**, loop closes | |

**Cross-fade length: 30 seconds, uniform everywhere** (`FADE_MAX_MIN = 0.5`). Originally longer
(up to 6 min, and a special 20-min case for the Isha arrival) — shortened after the user reported
two suns/two moons briefly visible together, since consecutive frames paint the sun or moon at
different sky positions. Exact arrival times are untouched; only the blend window shrank.

**Runtime overlays** (drawn on top, not baked into the images): drifting clouds by day, twinkling
stars + an occasional shooting star at night, bird flocks around dusk, water shimmer. Local
time + phase name readout, bottom-left (`#sceneReadout`).

**Performance:** only the current + next frame are loaded (never all 20); pauses when the tab is
hidden. Debug in the browser console: `Scene._debugMinutes = <minutes-since-midnight>` to preview
any moment; `Scene._debugMinutes = undefined` to return to the real clock.

---

## 6. Key decisions & constraints (the "why")

- **Browser autoplay policy**: one tap ("🔊 Enable Athan & Location") unlocks audio per visit;
  after that, everything fires automatically **while the tab stays open**.
- **Per-visitor isolation**: all settings in each visitor's own `localStorage` — no shared state,
  no server. Only the repo owner can change the site itself.
- **No analytics** — user explicitly declined (GoatCounter/GA4/Cloudflare were offered).
- **Sun/moon timing precision**: two rounds of bugs fixed by literally opening each painted frame
  and checking where the sun/moon actually sits, rather than trusting index labels — the anchors
  now match the art exactly.
- Personal `*.HEIC` photo and any `*.zip` deliverables are gitignored — never pushed to the public repo.

---

## 7. Condensed changelog

1. Explored desktop app; built `docs/` (originally `web/`) as a full-parity browser port; deployed
   to GitHub Pages via branch-based serving (Actions workflow blocked by OAuth scope).
2. Podcast iterated three times: Spotify embed (rejected — no reordering, 30s previews) → mp3quran
   (wrong recordings) → **YouTube playlist** (identical recordings, verified position-by-position).
3. Renamed Morning/Night audio → **Azkar**; added Test Athan per-prayer cycling; explicit location
   button; no-tracking decision.
4. **Background-tab reliability**: Web Worker clock, keep-alive audio loop, catch-up grace window,
   on-page tips — after athan silently stopped firing when the tab was minimized.
5. Added macOS menu-bar auto-start install docs (matching the user's actual working launchd setup)
   and an M1/M2/M3 VLC-architecture troubleshooting note.
6. **Living-scene redesign**: tabbed layout (Athan/Schedule/Quran/Install/Activity/Settings);
   several visual iterations (canvas art mountains → 5 real-photo themes → lighting-only mode →
   single Lake Dock photo) before landing on the current approach.
7. **Final scene**: user commissioned 20 custom-painted frames (via Claude design) covering a full
   day/night cycle; integrated with real solar-time anchoring, then debugged twice — first so the
   sun never appears before Sunrise/after Maghrib, then so cross-fades never show two suns/moons
   at once (30-second uniform fade).
8. **Quran player polish**: separate volume slider, auto-resume after prayer audio interrupts it,
   infinite playlist loop, drag-to-seek progress bar with live per-surah duration.
9. **Safari compatibility pass**: removed unsupported APIs, fixed the autoplay-unlock probe, moved
   to one reusable audio element (Safari only allows `play()` on a user-activated element).

## 8. Possible future ideas (not requested yet)

- Analytics (only if the user changes their mind)
- Custom domain (GitHub Pages supports CNAME)
- Re-enable GitHub Actions deploy (needs `gh auth refresh -s workflow`)
- Monthly prayer-times table view, more languages, in-UI offset controls for Al-Kahf/Azkar timing
