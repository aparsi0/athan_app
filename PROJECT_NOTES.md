# Athan App — Project Summary

> Compact reference: current features, full folder map, and a condensed changelog.
> Read this first in any new session — it replaces re-deriving context from scratch.
> Last updated: **2026-09-02**.

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

**Pushing (2026-09-02).** GitHub has not accepted account passwords for git since 2021.
What works on this Mac is a **classic** personal access token
(github.com/settings/tokens, tick the top-level `repo` scope), entered as the *password*
with `aparsi0` as the username. macOS Keychain then remembers it.

Two traps, both of which cost a session:
- A **read-only credential cached in the Keychain** authenticates fine and then fails the
  push with `remote: Permission to aparsi0/athan_app.git denied to aparsi0` — a 403, not an
  auth error. Clear it before retrying, or git never prompts for the new token:
  `printf "protocol=https\nhost=github.com\n\n" | git credential-osxkeychain erase`
- **Fine-grained** tokens need the repository explicitly selected *and* Contents set to
  "Read and write". Miss either and you get exactly the same 403. Classic tokens avoid it.

SSH is the durable alternative (`git remote set-url origin git@github.com:aparsi0/athan_app.git`),
and bypasses the Keychain, token scopes and the Claude GitHub App entirely.
Live at the **same URL** ~1 minute later (GitHub Pages, branch-based, serves `docs/` on `main` —
no Actions workflow; the `gh` token lacks `workflow` scope). When changing HTML/CSS/JS, bump
`CACHE_VERSION` in `docs/sw.js` (currently **v31**) so visitors' service workers refresh promptly.
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
    ├── index.html             page shell: sound/location gate, 8 tabs, all panels   (349 lines)
    ├── manifest.webmanifest   PWA metadata
    ├── sw.js                  service worker — cache version v31                    (104 lines)
    ├── README.md              web-app-specific readme
    ├── css/style.css          full site styling, responsive, RTL Arabic support     (382 lines)
    ├── js/
    │   ├── config.js            defaults + localStorage persistence, Safari-safe helpers (175)
    │   ├── location.js          browser geolocation → reverse-geocode → IP fallback    (129)
    │   ├── prayer-times.js      Aladhan API client + per-day cache                      (88)
    │   ├── scheduler.js         builds/fires today's event list, midnight rollover     (233)
    │   ├── audio.js             single reusable <audio> element, keep-alive loop        (177)
    │   ├── scene.js             ★ 20-frame living-sky engine (see §5)                  (440)
    │   ├── reciters.js          ★ Quran tab — 4 mushafs, selector, endless rotation   (170)
    │   ├── audio-players.js     ★ Quran tabs 2 & 3 — المصحف المعلم + live Cairo radio  (444)
    │   └── app.js               wires everything, UI rendering, settings, Test Athan    (536)
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
- **CSP `worker-src` governs SERVICE workers, not just web workers.** It was set to
  `blob:` alone for the background-clock Worker, which silently blocked `sw.js` for
  months — and because the directive is present there is no fallback to
  `child-src`/`script-src`/`default-src`. It must be `worker-src 'self' blob:`. More
  generally: never `.catch(() => {})` a registration or permission call. That empty catch
  is the only reason a total failure of the offline layer went unnoticed.
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

17. **Correctness pass (2026-09-02)** — a three-way audit of every file under
    `docs/`, plus live testing against the deployed site. Seven real defects, several
    of them long-standing:
    - **The service worker had never registered.** `worker-src` was `blob:` alone;
      that directive governs service workers too, so the same-origin `sw.js` failed the
      check and `register()` threw `SecurityError` on every visit — swallowed by a
      `.catch(() => {})`. Confirmed live: `caches.keys()` was `[]` and
      `getRegistrations()` was `0`. **No offline support, no precache, and no PWA
      installability has ever existed**, and every `CACHE_VERSION` bump from v18 to v23
      was a no-op. Fixed to `worker-src 'self' blob:`; the registration error is now
      logged to the Activity tab instead of discarded.
    - **A failed prayer-times fetch silenced the athan permanently.** `Scheduler.dateKey`
      was set only inside `build()`, reached only after a *successful* fetch, so any
      failure left the midnight-rollover branch matching on every tick — and that branch
      `return`s before the event loop. Harness: 600 ticks produced **600 refresh
      dispatches and 0 athans**. The same branch also advanced `lastTick` before
      returning, discarding any event due around midnight without even reporting it.
    - **The Stop button did not stop the YouTube Quran tab** — it called `cancelResume()`,
      which only set flags, and `Podcast` is not in the `QuranPlayers` registry so
      `pauseAll()` could not cover for it.
    - **The play/pause toggle bypassed the athan-priority guard in all three Quran tabs.**
      `play()` checked `AudioManager.isPlaying()`; the toggle never did. Confirmed live —
      11 seconds of Quran played over a simulated athan.
    - **The give-up guard in `podcast.js` could never fire** — the identical bug fixed in
      `audio-players.js` in item 16 but missed in this file. `play()` reset the counter
      unconditionally and `onError`'s recovery path calls `play()`.
    - **`scene.js` anchors went non-monotonic** whenever Isha falls after local midnight
      (frames 17/18/19 never shown — the scene cut from golden hour to deep night at
      Maghrib) or when twilight is under 20 minutes (frames 2-5 never shown).
    - **The sound gate could be unreachable.** A fixed, non-scrolling flex box with
      `align-items: center` overflows its ~640px card off *both* edges; the Enable button
      is last in the card and is the only way past the gate.
    Also: the Safari wrong-city fix (see §9), exponential backoff and a parameter-keyed
    in-flight guard on the prayer-times fetch, `localStorage` access guarded so blocked
    site data cannot kill `init()`, and the woduaa lead clamped so an empty field cannot
    silently delete all five reminders.

18. **Audio hosts verified for the first time (2026-09-02).** Previous sessions could not
    reach the network, so the changelog's earlier claim that the sources were "verified
    loading" was never actually tested. Probed under the live CSP in a real browser: all
    six load — `el-hosary.com` 001 (72.1 s) and 036 (1590.8 s), and all four radio
    addresses (`n12`, `n0b`, `stream.`, and the radio.garden resolver). المصحف المعلم and
    the radio both play, mutual exclusion works, and pause/resume round-trips correctly.

19. **Quran tab rebuilt around a reciter selector (2026-09-02).** Four complete mushafs, all
    direct MP3s from mp3quran.net (3-digit zero-padded, the same URL shape as المصحف المعلم,
    so `makeAudioPlayer` was reused rather than replaced):

    | id | sheikh | mushaf | server | surahs |
    |---|---|---|---|---|
    | `refat` | محمد رفعت | تسجيلات حفلات | `server14/refat/` | **31** |
    | `husr-warsh` | محمود خليل الحصري | ورش عن نافع | `server13/husr/Rewayat-Warsh-A-n-Nafi/` | 114 |
    | `mustafa` | مصطفى إسماعيل | حفص عن عاصم — مرتل | `server8/mustafa/` | 114 |
    | `bna` | محمود علي البنا | حفص عن عاصم — مرتل | `server8/bna/` | 114 |

    A surah auto-advances; at the end of a mushaf the **next reciter** starts from الفاتحة,
    wrapping past the last back to the first, indefinitely. Choice remembered per visitor.
    **محمد رفعت is a partial mushaf on purpose** — he died in 1950 having never recorded a
    complete one, and only 31 surahs survive. He is stored as *real surah numbers*, not list
    positions, so list position 5 requests `018.mp3` (الكهف) and his mushaf ends at العاديات.

20. **Morning Quran (2026-09-02).** At its scheduled moment it **pre-empts**, exactly like the
    athan, woduaa, duaa and azkar: whatever Quran tab was playing is paused — and **handed back
    when the window ends**. Pre-empting alone was not enough: `silenceOthers()` runs
    `stopForOther()`, which clears `_resumeWanted`, so the displaced radio never returned. The
    displaced players are captured *before* `play()` and re-armed in `stopMorningQuran()`, but
    only if the morning Quran was still the thing playing — otherwise a visitor who started
    المصحف المعلم at 08:00 would have the radio forced back over it. That is the
    `preempt` argument to `startMorningQuran`, passed only from the two Fajr paths.
    Every other caller — a page opened mid-window, the sound-gate tap, and any schedule
    rebuild (which happens on every settings save and location change) — is a *catch-up* and
    yields via `QuranPlayers.anyActive()`. Without that split, saving an unrelated setting at
    08:00 would cut off whatever the visitor had deliberately put on.
    Starts when the Fajr athan **and its duaa** finish — an
    outcome, not a clock time, so it hangs off the end of the chain rather than a schedule
    entry — and stops at a scheduled event, Morning Azkar + 60 min (configurable 0–240).
    Defaults to محمد رفعت. The Morning Azkar falls *inside* the window and still takes
    priority: the Quran pauses and resumes through the normal athan pipeline. A page opened
    mid-window resumes the surah it left on (`audio_settings.morning_quran_index`).

21. **The YouTube player was removed (2026-09-02).** With Al-Banna served as MP3s, `podcast.js`
    had no purpose left, and it was the app's largest trust concession — an iframe that can
    execute code, versus `<audio>` tags that cannot. The CSP shrank accordingly:
    `script-src` to `'self'`, `frame-src` to `'none'`, YouTube out of `connect-src` and
    `img-src`, and `https://*.mp3quran.net` into `media-src` (a wildcard: the files span
    server7–server16). This also ends the "YouTube requires its player stay visible"
    constraint, which mattered for hours of unattended morning playback.

22. **Spotify was re-evaluated and rejected again (2026-09-02).** Same conclusion as changelog
    item 2, now with evidence: both a linked show and album embed serve preview clips when
    logged out (`audioPreview` → `p.scdn.co/mp3-preview/…`, and a 42 s
    `podz-content…/clip_0_*.mp3`), the owner's Premium does not extend to visitors, and an
    iframe gives no dependable track-ended signal to drive auto-advance. Decisively, the
    محمد رفعت album is **verse-range excerpts** ("من 25 - 29 سورة البقرة"), not surahs, so
    an ordered الفاتحة→الناس sequence was never possible from it.

23. **Morning-window hardening (2026-09-02).** An adversarial review of item 20 found five
    real defects, all fixed the same day. Worth remembering as a class, because four of them
    share one root cause — *reading player state that is set asynchronously*:
    - The stop handler guarded on `playing`/`_shouldBePlaying`, both of which are false when
      something else has already paused the player, while `_resumeWanted` is still true. The
      stop was skipped and the next `resumeAll()` restarted the Quran after its window closed.
      **Stopping must be unconditional.** Reachable with UI-legal values: a 240-minute offset
      puts the window end exactly on Dhuhr.
    - `build()` rewrites `events` without rewinding `lastTick`, so any rebuild that places an
      event in the past means it can never fire. Disabling the feature mid-window therefore did
      not stop it. **Anything with a lifecycle needs a re-evaluation hook on rebuild**, not just
      a scheduled end event — hence `Scheduler.onRefresh` driving start/stop.
    - The "already running" guard tested `playing`, which is only set by the audio element's
      own event and cannot have fired by the next synchronous statement. Use
      `_shouldBePlaying`, which is set synchronously.
    - A fixed `setTimeout` after init raced geolocation (8s+) plus reverse-geocoding (6s) plus
      the Aladhan fetch (10s), and usually lost with no retry.
    - `select()` cleared the saved position before `startMorningQuran` read it, so the
      advertised resume had never once worked.
    Plus one data bug: رفعت's list rendered `i + 1`, showing "2" beside سورة يونس (surah 10).
    Invisible for full mushafs where position + 1 *is* the surah number — which is exactly why
    a happy-path harness could not catch it. **A partial mushaf must render real surah numbers.**

24. **Desktop app: the menu-bar icon opened nothing (2026-09-02).** The green crescent
    appeared and the app ran, but clicking it produced no window. Two faults, compounding:
    - `.venv` is built on **Homebrew python@3.14, which ships no tkinter** (it is the separate
      `python-tk` formula). `gui/main_window.py` imports tkinter at module level, so the helper
      process died on its first import.
    - `_show_rich_payload` launched that helper with `stderr=subprocess.DEVNULL`, and `Popen`
      itself succeeds — the process starts, *then* dies. So the tray returned success, no
      fallback dialog ran, and nothing anywhere recorded a reason.
    Underneath both: `_get_dialog_python()` returned the first candidate unconditionally (the
    `for` loop `return`ed on its first iteration), so the .venv was always chosen and the
    `python3` / `python` fallbacks below it were dead code.
    Fixed by probing each candidate with `python -c "import tkinter"` and taking the first that
    works, caching the result, appending `/usr/bin/python3` (macOS system Python always has Tk)
    as the last resort, keeping the helper's stderr in `~/.athan_app/helper-window.log`, and
    showing an actionable dialog when no interpreter can do Tk. The helper imports **only
    stdlib**, so system Python runs it fine — no venv packages are needed.

    **But the running menu-bar app is the FROZEN bundle**, not the source: the launchd agent
    points at `dist/AthanApp.app/Contents/MacOS/AthanApp`, so source fixes do nothing until
    the app is rebuilt. And the bundle has the same disease at its root — it was built from
    that same Tk-less venv, so `find dist/ -name '*tkinter*'` returns **zero** results. The
    spec *does* list tkinter in `hiddenimports`; PyInstaller can only bundle what it can
    import, so it warned and shipped a valid-looking .app with no Tk in it.

    `packaging/build_macos_app.sh` now fails fast when the build interpreter has no tkinter,
    so this cannot ship again. **Rebuilding requires `brew install python-tk@3.14` first.**

    **The lesson, and it recurs in this project:** `DEVNULL` on a subprocess you depend on is
    the same defect as `.catch(() => {})` on the service-worker registration (changelog 17) —
    a whole subsystem failing in total silence. A build warning nobody reads is the third form
    of it.

25. **Morning Quran on the desktop app (2026-09-02).** Full parity with the web version:
    four reciters, endless rotation, the morning window, athan priority, position remembered.

    **`docs/assets/reciters.json` is now the single source of truth** for the reciter table and
    the 114 surah names. `docs/js/reciters.js` fetches it; `core/quran_player.py` reads the same
    file off disk. Adding a reciter is one edit — plus its host in `media-src`, which only the
    web app needs. The JS fills `SURAH_NAMES`/`RECITERS` **in place** rather than reassigning,
    because `audio-players.js` captures `SURAH_NAMES` by reference at load time for
    المصحف المعلم; `app.js` loads the JSON once, then builds every player.

    Three things the desktop needed that the web did not:
    - **A second VLC player.** `AudioPlayer.media_player` is stopped and reused for every athan,
      duaa and azkar, so sharing it would destroy the Quran's position each time. `QuranPlayer`
      owns its own `vlc.Instance` and player, which can be paused and resumed while prayer audio
      holds the floor.
    - **URLs through the file layer.** `_resolve_audio_file_path` treated everything as a local
      path — a URL fell through to filename matching and hunted the audio folders for
      "001.mp3". Streams now short-circuit, in the resolver and in the playback queue.
    - **A "whole chain finished" signal.** "Right after Fajr" is an outcome, not a clock time.
      `AudioPlayer.on_chain_finished` fires when the queue drains — i.e. after the athan AND
      its duaa — and that is what opens the window and what resumes a suspended Quran.

    The window end is a scheduled event at Azkar + N; the start is the Fajr chain finishing.
    Verified to match the web app's computation exactly: Sep 02 05:35–10:14, Dec 21 06:05–09:13,
    Jun 21 04:31–10:17.

26. **محمد رفعت: 8 surahs served from the repo (2026-09-03).** The user had a downloaded
    رفعت collection. Only part of it was worth hosting, and the arithmetic decided it:
    of 14 complete surahs, **6 already stream from mp3quran** (58.5 MB of duplication) and
    **8 do not exist there at all** — البلد، القدر، القارعة، التكاثر، العصر، الهمزة، الفيل، قريش.
    Those 8 are 19.3 MB, so they now live in `docs/assets/audio/refat/` and رفعت goes from
    31 to **39 surahs**. The other 302 MB (17 verse-range excerpts, plus duplicates) stays
    off the site: GitHub Pages caps a published site at 1 GB and git keeps binaries forever.
    Site total is now 86 MB.

    `reciters.json` gained an optional **`local`** map (surah number -> filename under
    `assets/audio/<id>/`). A surah listed there is served from the repo instead of streamed;
    everything else still streams. Same-origin, so `media-src` needed no change.

    **Beware the folder's contents.** It is named for رفعت but has since acquired
    مصطفى إسماعيل recordings too, and one recital dated **Tanta 1961** — which cannot be
    رفعت, who died in 1950. Always check attribution before filing anything under a sheikh.

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
- **More reciters still**: adding one is a single entry in `RECITERS` (`docs/js/reciters.js`)
  plus its host in `media-src`. mp3quran.net lists 241 reciters; the API that enumerates them
  is `https://mp3quran.net/api/v3/reciters?language=ar`, and a moshaf entry's `server` field
  plus `NNN.mp3` is the whole URL. Verify a new one loads before shipping it.

---

## 9. The Safari wrong-city bug — resolved

**Symptom.** Safari showed `Location: Helsinki, 18` while Settings held the correct
Raleigh coordinates. Chrome on the same machine showed `Raleigh, NC`, which ruled out a
VPN. `18` is the tail of ISO 3166-2 `FI-18` (Uusimaa).

**Cause.** BigDataCloud answers from the caller's IP when it cannot use the coordinates
it was given, and Safari's egress was an iCloud Private Relay node in Finland.
CoreLocation was always correct; only the display label was wrong. **Prayer times were
never affected** — `prayer-times.js` uses latitude/longitude only.

**Why it took three sessions.** The fix was written once (commit `f93a95b`), never
pushed, and lost with the patch file. It also shipped with a known hole: the sandbox
blocked outbound HTTPS, so nobody could see the real response, and the guard depended on
the service echoing coordinates back.

**Settled by actually calling the API:**

```
reverse-geocode-client?latitude=35.78774&longitude=-78.68962
  -> latitude 35.78774, longitude -78.68962, city "Raleigh", code "US-NC"

reverse-geocode-client                       (no coordinates supplied)
  -> lookupSource "ip geolocation", plus the IP's own coordinates
```

Two independent signals, either sufficient. `location.js` now rejects any answer whose
`lookupSource` is `ip geolocation`, **and** any whose echoed coordinates are more than
0.5° (~55 km) from the request. A non-alphabetic ISO tail (`FI-18` → `18`) is no longer
rendered as a region abbreviation.

Five scenarios, old → new: IP-answered Helsinki `Helsinki, 18` → discarded; same with no
`lookupSource` → discarded; correct Raleigh answer → unchanged; a user genuinely in
Helsinki → `Helsinki, Uusimaa` (the guard rejects contradictions, not countries); a
degraded response with neither signal → unchanged.

---

## 10. Superseded session files

`ATHAN_SESSION_HANDOFF [Claude Code].md` and `SESSION-HANDOFF [Claude Design].md` sit at
the repo root, untracked and gitignored-by-omission. Everything still true in them has
been folded into this file. Their open items are all now closed: `f93a95b` rewritten
(§9), both Quran tabs tested end to end (§7 item 18), and the audio hosts verified. They
can be deleted.

**Two claims in them are wrong and should not be carried forward:**
- "all sources verified loading under the live policy" (Claude Design) was never tested —
  that session had no network. It happens to be true, but only as of 2026-09-02.
- The Claude Code handoff's `PROJECT_NOTES.md` line counts were already stale. Re-verify
  any number against `wc -l` before trusting it.
