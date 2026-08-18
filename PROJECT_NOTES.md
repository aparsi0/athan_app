# Athan App — Project Summary

> Compact reference: current features, full folder map, and a condensed changelog.
> Read this first in any new session — it replaces re-deriving context from scratch.
> Last updated: **2026-08-18**.

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
`CACHE_VERSION` in `docs/sw.js` (currently **v23**) so visitors' service workers refresh promptly.
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
    ├── index.html             page shell: sound/location gate, 8 tabs, all panels   (325 lines)
    ├── manifest.webmanifest   PWA metadata
    ├── sw.js                  service worker — cache version v23                     (75 lines)
    ├── README.md              web-app-specific readme
    ├── css/style.css          full site styling, responsive, RTL Arabic support     (368 lines)
    ├── js/
    │   ├── config.js            defaults + localStorage persistence, Safari-safe helpers (165)
    │   ├── location.js          browser geolocation → reverse-geocode → IP fallback    (92)
    │   ├── prayer-times.js      Aladhan API client + per-day cache                      (88)
    │   ├── scheduler.js         builds/fires today's event list, midnight rollover     (157)
    │   ├── audio.js             single reusable <audio> element, keep-alive loop        (177)
    │   ├── scene.js             ★ 20-frame living-sky engine (see §5)                  (410)
    │   ├── podcast.js           Quran tab 1 — YouTube playlist, seek bar, resume logic  (365)
    │   ├── audio-players.js     ★ Quran tabs 2 & 3 — المصحف المعلم + live Cairo radio  (396)
    │   └── app.js               wires everything, UI rendering, settings, Test Athan    (410)
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

**Two more Quran tabs** (`audio-players.js`, added 2026-08-18) — both plain HTML5 `<audio>`,
no iframe, so no visible player is required:
- **المصحف المعلم** — Sheikh Mahmoud Khalil Al-Hosary's teaching mushaf, all 114 surahs in order,
  streamed as direct MP3s from `https://www.el-hosary.com/Elmoalem/001.mp3` … `114.mp3`
  (zero-padded 3 digits). Full seek bar, auto-advance, loops An-Nas → Al-Fatiha.
- **إذاعة القرآن الكريم من القاهرة** — the live 98.2 FM Cairo station (the Radio Garden
  `GQxvGBNK` channel). Live, so no seek bar: after an athan it **rejoins at the live edge**
  rather than resuming. Falls through a list of stream addresses if one is unreachable:
  `n12` / `n0b` / `stream.radiojar.com/8s5u5tpdtwzuv`, then the
  `radio.garden/api/ara/content/listen/GQxvGBNK/channel.mp3` resolver.
- Both share one `makeAudioPlayer` engine plus a **`QuranPlayers` registry**: only one Quran
  source can sound at a time across all three tabs — starting one silences the others.
- Each has its **own persisted volume** (`audio_settings.moalem_volume`, `…radio_volume`) and its
  own stall watchdog, same shape as the YouTube player's. Athan priority is unchanged: every
  player pauses when prayer audio starts and resumes (or rejoins) after the full chain finishes.

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
- **CSP and redirecting streams**: `media-src` must list `https://*.radiojar.com` as a wildcard,
  not individual hosts. The Radio Garden resolver 302-redirects to whichever Radiojar edge is
  healthy (`n12`, `n0b`, `n0e`…), and CSP validates the *redirect target* — pinning single hosts
  silently blocked the radio. Adding any new audio source means adding its host to `media-src`
  in `docs/index.html`.
- **Third-party audio is a privacy boundary, not a security one**: an `<audio>` element cannot
  execute code, so a hostile audio host can only serve wrong audio — but it does see each
  listener's IP. Hence `preload="none"` (opening a Quran tab sends nothing until play is pressed),
  `<meta name="referrer" content="no-referrer">`, and the Settings privacy note naming the hosts.
  The service worker deliberately ignores cross-origin requests, so streams are never cached.

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
10. **Sun/moon timing fix (2026-08-02)**: re-examined all 20 painted frames directly and re-anchored
    the scene so sun/moon arrive exactly when they should appear/disappear (Sunrise→frame 6, Maghrib→frame 17).
11. **Quran seek bar**: added live duration display, drag-to-scrub playback, fills as video plays.
    Each surah reads its own real duration from the player, so the bar is accurate for all 114.
12. **Playback watchdog recovery**: fixed athan/Quran sometimes stopping and never resuming by adding
    watchdog timers that detect silently-paused or stalled media (browser background-tab throttling,
    network hiccups) and nudge playback back to life. Athan gets 10-minute stuck timeout; Quran gets
    graceful 15-second startup buffering + progressive recovery (gentle nudges before reloading).
13. **Security hardening (2026-08-02)**: added enforced Content-Security-Policy (verified live under
    attack scenarios), privacy note in Settings, and guarded prayer-times fetch retry loop to prevent
    stacking. CSP allows only what's needed: YouTube player, four API origins, blob: Web Worker.
14. **Inaudible keep-alive verified**: confirmed the background audio loop that keeps tabs alive
    during prayer times (original feature from earlier, still active and working).
15. **Two new Quran tabs (2026-08-18)**: المصحف المعلم (Al-Hosary, 114 direct MP3s from
    el-hosary.com) and إذاعة القرآن الكريم من القاهرة (live 98.2 stream). Added
    `docs/js/audio-players.js` with a shared `<audio>` engine and a one-at-a-time `QuranPlayers`
    registry; extended CSP `media-src` to el-hosary.com, radio.garden and `*.radiojar.com`.
    First attempt looked broken because CSP blocked the radio's redirect target — fixed with the
    wildcard, then all sources verified loading under the live policy. Bumped sw.js to v22.
16. **Quran player hardening (2026-08-18)**: fixed a real loop — the 5-strike give-up guard could
    never fire, because the error path's `play()` call reset the counter, so an unreachable host
    walked all 114 surahs forever logging a warning each time. Failure count now clears only on
    actual playback or a real click. Added per-track source fallback (`sources[]` for المصحف
    المعلم, same mechanism the radio already used), exponential reconnect backoff (3→48s, was a
    flat 3s), and a radio give-up message pointing at المصحف المعلم. Privacy: `no-referrer` and a
    Settings note naming the streaming hosts. sw.js v23.

## 8. Possible future ideas (not requested yet)

- Analytics (only if the user changes their mind)
- Custom domain (GitHub Pages supports CNAME)
- Re-enable GitHub Actions deploy (needs `gh auth refresh -s workflow`)
- Monthly prayer-times table view, more languages, in-UI offset controls for Al-Kahf/Azkar timing
- **Mirror hosts for المصحف المعلم**: the fallback mechanism is in place but `sources` holds one
  host, so a single outage still stops that tab. Purpose-built Quran CDNs (mp3quran.net,
  everyayah.com, cdn.islamic.network, quranicaudio.com) expect hotlinking, unlike el-hosary.com —
  each needs its URL shape checked and its host added to `media-src`.
- **Bundle the most-played surahs**: Al-Fatiha, Ya-Sin, Al-Mulk, Al-Waqi'ah and the last juz at
  48–64 kbps mono (~50–100 MB) would play offline and survive any outage. Hosting all 114 is not
  an option — GitHub Pages caps a site at 1 GB and the full teaching mushaf exceeds that.
- **More reciters**: additional full-mushaf sheikhs with a reciter selector, remembered per
  visitor. el-hosary.com already hosts several more mushafs in the same URL shape
  (المجود، المفسر، حفص الإذاعة المصرية، ورش، قالون) — cheapest next source.
- **Morning auto-play**: a chosen Quran source playing automatically between sunrise and the
  morning Azkar, toggleable in Settings.
