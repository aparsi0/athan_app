# Athan Web — Session Handoff (Claude Design → next project)

**Session scope:** two new Quran tabs added to the Athan Web PWA, plus a CSP fix that
made the live radio work. Packaged for manual deployment; **not yet pushed.**

- **Repo:** `aparsi0/athan_app`, branch `main`, site root `docs/`
- **Live URL:** https://aparsi0.github.io/athan_app/
- **State of `main` at time of packaging:** cache version `athan-web-v21`, unchanged since
  the 2026-08-03 sync. Verified by reading `docs/sw.js` on `main` before packaging.
- **Session date:** 2026-08-18. Handoff written 2026-09-02.
- **Repo's own notes file:** `PROJECT_NOTES.md` at the repo root (not `PROJECT_STATE.md` —
  that name exists only inside the Claude Design project and is not a repo file).

> This session did **not** touch the sky/day-night theme. `docs/js/scene.js` and the 20 sky
> images are untouched and are deliberately absent from the deployment package. Everything
> below is additive to the audio side of the app.

---

## 1. What was built

### Tab 2 — المصحف المعلم (Al-Mos'ahaf Al-Moa'alem)

Sheikh Mahmoud Khalil Al-Hosary's teaching mushaf, all 114 surahs in Quran order.

- Source: `https://www.el-hosary.com/Elmoalem/001.mp3` … `114.mp3`
  (surah number, **zero-padded to 3 digits**). Derived from https://el-hosary.com/el-moalem/
- Plain HTML5 `<audio>`, not a YouTube iframe — so there is no visible-player requirement
  and no thumbnail to keep on screen (unlike the original Quran tab).
- Full seek bar, prev/next, auto-advance, loops An-Nas → Al-Fatiha.
- Surah names reuse `PODCAST.surahs` from `docs/js/podcast.js` — the list is not duplicated.

### Tab 3 — إذاعة القرآن الكريم من القاهرة (Quran Radio Cairo 98.2)

The live 24/7 Cairo station, from the Radio Garden channel the user linked:
https://radio.garden/listen/quran-fm-98-2-idhaet-alqran-alkrym/GQxvGBNK

- Being live, there is **no seek bar** and no resume-at-position. After an athan it
  **rejoins at the live edge** rather than resuming.
- Source fallback chain, tried in order, with a `?ts=` cache-buster on every attempt
  (a live stream must never be served from a stale buffer):
  1. `https://n12.radiojar.com/8s5u5tpdtwzuv`
  2. `https://n0b.radiojar.com/8s5u5tpdtwzuv`
  3. `https://stream.radiojar.com/8s5u5tpdtwzuv`
  4. `https://radio.garden/api/ara/content/listen/GQxvGBNK/channel.mp3`
- Direct Radiojar edges come **first** (one hop, no redirect); the Radio Garden resolver is
  the fallback since it 302s to whichever edge is currently healthy.

### Shared machinery

Both live in the new `docs/js/audio-players.js`:

- **`makeAudioPlayer(opts)`** — one engine for both. A player with `opts.tracks` gets a
  list + seek + auto-advance; a player without one is treated as a single live stream.
- **`QuranPlayers` registry** — every Quran-ish player registers itself, so only one Quran
  source can sound at a time across all three tabs. Starting any one silences the others,
  including the original YouTube podcast player.
- **Athan priority preserved**: `pause()` / `maybeResume()` / `cancelResume()` on every
  player, fanned out from `docs/js/app.js`. Prayer audio always wins; a player that was
  playing resumes (or rejoins) after the whole athan chain finishes. A user pressing Stop
  cancels any pending auto-resume.
- **Per-player persisted volume**, independent of the athan volume:
  `audio_settings.moalem_volume`, `audio_settings.radio_volume`.
- **Stall watchdog** per player (6 s interval + a `visibilitychange` check), same shape as
  the existing YouTube player's: compares what *should* be playing against what actually is,
  nudges `play()`, and after repeated failures re-fetches the source — at the same position
  for tracks, at the live edge for the radio. Track players skip a persistently failing
  surah; the radio reconnects through the next source in the chain.

---

## 2. The bug worth remembering: CSP validates redirect targets

The radio appeared completely broken on first attempt. Cause was **not** the stream.

`radio.garden` does not serve the audio itself — it **302-redirects** to a rotating Radiojar
edge (`n12`, `n0b`, `n0e`…). CSP checks the *redirect target*, so pinning individual hosts in
`media-src` silently blocked whichever edge happened to be served that minute.

**Fix:** use a wildcard.

```
media-src 'self' https://www.el-hosary.com https://el-hosary.com
          https://radio.garden https://*.radiojar.com;
```

Verified by probing all four radio addresses and the el-hosary MP3s under the exact live CSP —
all loaded. **Rule going forward:** adding any new audio source means adding its host to
`media-src` in `docs/index.html`, and using a wildcard for anything that might redirect.

---

## 3. Files changed — deployment manifest

Six files, staged in the delivered zip under `docs/` so the paths already match the repo.
They are the repo's current files plus only these edits (diffed against `main` before
packaging), so they should be **copied over wholesale, not hand-merged**.

| Path | Change |
|---|---|
| `docs/js/audio-players.js` | **New file.** Both players + the `QuranPlayers` registry + `makeAudioPlayer` + `fmtClock`. |
| `docs/index.html` | 2 new tab buttons (`data-tab="moalem"`, `data-tab="radio"`, both `lang="ar"`); 2 new `<section class="panel">` panels; CSP `media-src` hosts; `<script src="js/audio-players.js">` after `podcast.js`. |
| `docs/js/app.js` | `Moalem.init()` + `QuranRadio.init()`; pause / resume / cancel now fan out via `QuranPlayers.pauseAll()` / `resumeAll()` / `cancelAll()` at each existing `Podcast.*` call site. |
| `docs/js/podcast.js` | One line in `play()` — `QuranPlayers.silenceOthers('podcast')`. |
| `docs/css/style.css` | One rule — `nav.tabs button[lang="ar"] { letter-spacing: 0; text-transform: none; font-size: 13px; }` (Arabic labels must not be letter-spaced or uppercased). |
| `docs/sw.js` | `CACHE_VERSION` → `athan-web-v22`; `'js/audio-players.js'` added to the app-shell list. |

Also in the zip root: `PROJECT_NOTES-edits.md` — six find-and-replace edits against the
repo's `PROJECT_NOTES.md`, written in that file's own format (header date, v21→v22 note,
folder map now 8 tabs, a "Two more Quran tabs" block in §4, the CSP lesson in §6, changelog
item 15, and the pending items for §8).

**Deploy:** copy the zip's `docs/` over `athan_app/docs/` (replacing five files, adding one),
apply the notes edits, commit, push. GitHub Pages picks it up in a minute or two. The `sw.js`
version bump is required or returning visitors keep the cached v21 shell.

**Caveat carried forward:** if anything under `docs/` was edited after 2026-08-18 (the user
also works on this from an iMac session), re-diff those files before overwriting.

---

## 4. Pending — asked for, not built

### 4.1 Multiple reciters with a selector

Additional full-mushaf sheikhs, 114 surahs each in order, with a reciter selector in the UI
that remembers the visitor's choice (same `Config` persistence pattern as the volumes).

Cheapest next sources: el-hosary.com already hosts several more complete mushafs in the same
predictable URL shape — المجود، المفسر، حفص الإذاعة المصرية، ورش، قالون. That means the
existing `makeAudioPlayer` needs only a swappable `srcFor` + a `<select>`, not a new engine.
Awaiting the user's pick of which sheikhs/mushafs to include.

### 4.2 Morning Quran auto-play

Auto-play a chosen Quran source between **sunrise and the morning Azkar (~9:06 AM)**,
toggleable in Settings. Belongs in `docs/js/scheduler.js` (which already owns the
solar/prayer-anchored windows) driving one of the players.

**Still unanswered — needed before building:**
- Which source plays in the morning window (YouTube playlist / المصحف المعلم / the radio)?
- Does it **pause or stop** when the Azkar begin?
- Should a mid-window page load **auto-play immediately**, or only trigger at sunrise?

---

## 5. Architecture context (for the next session)

Audio-relevant files under `docs/js/`:

| File | Role |
|---|---|
| `app.js` | Wires location, prayer times, scheduler, audio and UI. Owns athan playback and the pause/resume fan-out to every Quran player. |
| `config.js` | Persisted settings (`Config.get` / `Config.set`), incl. per-player volumes. |
| `scheduler.js` | Background clock (Web Worker) + the solar/prayer-anchored windows. Home for the pending morning auto-play. |
| `audio.js` | `AudioManager` — athan/prayer audio. `AudioManager.isPlaying()` is the priority gate every Quran player checks before starting. |
| `podcast.js` | Quran tab 1 — YouTube playlist `PL8475A8813886C6A5` (Sheikh Mahmoud Ali Al-Banna), seek bar, resume logic. Exports `PODCAST.surahs`, the 114 surah names. Its iframe **must stay visible** (YouTube requirement) — the two new tabs have no such constraint. |
| `audio-players.js` | Quran tabs 2 & 3 (this session). |
| `scene.js` | Day-night sky: 20 frames cross-faded, anchored to prayer/solar times, plus clouds, stars, shooting stars, bird flocks, water shimmer. **Out of scope — do not revisit.** |

Conventions to keep: athan always has priority; one Quran source at a time; every new audio
host goes in `media-src`; bump `CACHE_VERSION` on every deploy; Arabic UI strings get
`lang="ar"` so the tab CSS rule applies.
