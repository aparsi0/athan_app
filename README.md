# 🕌 Athan App - Islamic Prayer Time Application

An automated Islamic prayer time application that plays the Athan (call to prayer) at the correct times throughout the day. It detects the user's location at startup, schedules prayer-related audio events, and supports both development runs and packaged desktop use.

## ✨ Features

- **Automatic Prayer Times**: Fetches accurate prayer times daily from reliable Islamic APIs
- **Automatic Location Detection**: Detects your current location at startup and uses it for prayer times
- **5 Daily Prayers**: Fajr, Dhuhr, Asr, Maghrib, and Isha
- **Custom Athan Audio**: Uses your provided M4A audio file
- **Friday Pre-Dhuhr Reminder**: Plays `Surat_AlKahf` 3 hours before Dhuhr every Friday
- **Pre-Prayer Reminder**: Plays `Woduaa` 15 minutes before each prayer
- **After-Prayer Duaa**: Plays `Duaa` right after each prayer Athan finishes
- **Morning/Night Audio**: Plays additional configurable audio files every day
- **System Tray Integration**: Runs quietly in the background
- **Cross-Platform**: Works on Linux, macOS, and Windows
- **Headless Mode**: Can run on servers without GUI
- **Configurable**: Customizable settings and preferences
- **Reliable Scheduling**: Automatic daily refresh of prayer times

There is also a **browser version** at <https://aparsi0.github.io/athan_app/> (source in
`docs/`) with everything above plus a Quran tab — four complete mushafs behind a reciter
selector that rolls from one to the next indefinitely — a morning Quran window, a live
Cairo radio stream, and a 20-frame painted sky anchored to your real solar times.

## 🌍 Prefer the web version?

**<https://aparsi0.github.io/athan_app/>** — nothing to install. It runs in any browser,
uses your own location and timezone, plays the same athan and reminder audio, and adds a
Quran tab with four complete mushafs and a living day/night sky. Installable as a PWA.

Everything below is for the **desktop app**, which runs natively in the macOS menu bar and
keeps working whether or not a browser is open.

## 🚀 Getting the athan running

| Your device | What it takes |
| --- | --- |
| **[Phone or tablet](#phone-or-tablet)** | Nothing to install. Open a web page, add it to your home screen. |
| **[Mac or Linux](#mac-or-linux)** | Two lines you copy and paste. You get a menu-bar app. |
| **[Windows](#windows-10-and-11)** | Same app, set up through PowerShell. |

---

## Phone or tablet

There is nothing to download and no app store involved. The web version **is**
the full app — prayer times, the athan, azkar, the Quran tab and the living sky.

**<https://aparsi0.github.io/athan_app/>**

Open that link, then add it to your home screen so it gets its own icon and
opens without browser bars:

- **iPhone or iPad** — in Safari, tap the Share button (the square with an arrow
  coming out of it), scroll down, tap **Add to Home Screen**.
- **Android** — in Chrome, tap the **⋮** menu, tap **Install app** (sometimes
  called *Add to Home Screen*).

The first time you open it, allow **sound** and **location** when asked.
Location stays on your phone; it is only used to work out your prayer times.

### Keeping it awake: leave the Quran playing

Phones freeze web pages they think you have stopped using, and a frozen page
cannot sound the athan. A page that is **playing audio** is treated as active
and does not get frozen — so open the القرآن الكريم tab, start a reciter, and
turn the volume down as low as you like. The Quran keeps playing, the page stays
awake, and the athan interrupts it at prayer time and hands it back afterwards.

**The limits, honestly.** This is a web page and it cannot outrank your phone's
battery saver. With the app open — especially with audio playing — the athan is
dependable. Closed, or with the screen off for hours, it may not fire. It also
streams the Quran over the network, so use Wi-Fi if your data is limited. If you
need an athan that always sounds with the phone in your pocket, use a native
athan app for that and this for everything else.

---

## Mac or Linux

This installs a real app: a crescent in the menu bar, prayer times, the athan
through your speakers, and the Quran features.

**1. Open Terminal.** Terminal is an app already on your Mac that lets you type
instructions instead of clicking. Press **⌘ + Space**, type **Terminal**, press
**Return**. A window with a blinking cursor opens. That is all it is. On Linux,
open your Terminal the usual way for your desktop.

**2. Copy the files to your computer.** Paste this and press **Return**:

```bash
git clone https://github.com/aparsi0/athan_app.git ~/Desktop/athan_app
```

> The very first time, macOS may ask to install **developer tools**. Say yes,
> wait for it to finish, then paste the line again.

**3. Run the setup.** The first line moves into the folder you just downloaded;
the second does everything else.

```bash
cd ~/Desktop/athan_app
./setup.sh
```

It installs anything missing, upgrades anything old, runs its own tests, builds
the app and puts it in your Applications folder. Expect a few minutes and a lot
of scrolling text. It finishes by telling you what to do next.

> If it says `permission denied`, run `chmod +x setup.sh` once, then
> `./setup.sh` again.

**4. Open it.**

```bash
open /Applications/AthanApp.app
```

A crescent appears in the menu bar at the top right. Click it for the next
prayer, today's schedule, the تلاوات recitals, settings, and Quit.

> macOS may refuse the first time because the app is not signed by an Apple
> developer account. Go to **System Settings → Privacy & Security**, scroll
> down, click **Open Anyway**.

**5. Make it start by itself**, so the athan works every day without you opening
anything:

```bash
./setup.sh --autostart
```

Restart the Mac once to confirm the crescent comes back on its own.

**Linux differs in two ways:** `apt` asks for your password once, and there is
no menu-bar app — run it with `.venv/bin/python main.py`, or
`main_headless.py` on a machine with no screen.

---

## Windows 10 and 11

**1. Open PowerShell.** Press **Start**, type **PowerShell**, press **Enter**.

**2. Copy the files down.**

```powershell
git clone https://github.com/aparsi0/athan_app.git $HOME\Desktop\athan_app
```

> If Windows does not know `git`, install it with `winget install Git.Git`,
> then close and reopen PowerShell.

**3. Run the setup.**

```powershell
cd $HOME\Desktop\athan_app
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

`-ExecutionPolicy Bypass` is part of the command, not decoration — Windows
blocks scripts by default and that is what gets past it. Copy the whole line.

**4. Start it.**

```powershell
.\.venv\Scripts\python.exe main.py
```

Windows has no menu-bar equivalent, so leave that window open while you want the
athan running.

---

## Starting at login, and stopping it (macOS)

The everyday way is `./setup.sh --autostart` to turn it on and
`./setup.sh --no-autostart` to turn it off. Both run from the project folder.
Below is what those actually do, if you would rather drive it yourself.

**Turn it on:**

```bash
launchctl enable    gui/$(id -u)/com.apa.athan-app
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.apa.athan-app.plist
launchctl kickstart -k gui/$(id -u)/com.apa.athan-app
```

**Turn it off:**

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.apa.athan-app.plist
launchctl disable gui/$(id -u)/com.apa.athan-app
```

Both lines matter. `bootout` stops it now, but the agent file stays in your
`LaunchAgents` folder and would load again at your next login. `disable` is the
half that persists.

**Check what it is doing:**

```bash
launchctl print gui/$(id -u)/com.apa.athan-app | head   # state = running
launchctl list | grep com.apa.athan-app
launchctl print-disabled gui/$(id -u) | grep com.apa.athan-app
```

Logs live in `~/.athan_app/` — `launchd.stdout.log` for normal output,
`launchd.stderr.log` for crashes, `helper-window.log` if the dashboard window
will not open.

**Quit now means quit.** The agent used to be set to relaunch the app the
instant it exited, for any reason, so Quit in the menu bar appeared to do
nothing. It now restarts only after a crash — an athan that dies at 3 a.m. and
stays dead is worse than useless — and respects a deliberate Quit until your
next login.

---

## Keeping the Mac awake

A sleeping Mac plays no athan. So the login agent does not run the app directly
— it runs it inside `caffeinate`, which holds the machine awake for exactly as
long as the app is alive and lets go the moment it exits.

```bash
caffeinate -ims /Applications/AthanApp.app/Contents/MacOS/AthanApp
```

| Flag | What it holds off |
| --- | --- |
| `-i` | idle sleep |
| `-m` | disk idle sleep |
| `-s` | sleep while plugged into power |
| `-d` | display sleep — **not used**, see below |

This was `-dims` until September 2026. The extra `d` keeps the *screen* lit as
well, all night, every night, which does nothing for prayer times. If you do
want the display held on, change `caffeinate -ims` back to `caffeinate -dims` in
`macos/com.apa.athan-menubar.plist` and run `./setup.sh --autostart` again.

**Running it awake from Terminal instead.** This holds the window — closing it
stops both:

```bash
caffeinate -ims /Applications/AthanApp.app/Contents/MacOS/AthanApp
```

Or let it go on its own so you can close the window:

```bash
nohup caffeinate -ims /Applications/AthanApp.app/Contents/MacOS/AthanApp >/dev/null 2>&1 &
```

And headless — no menu-bar icon, straight from the project folder:

```bash
caffeinate -i .venv/bin/python main_headless.py
```

> The menu-bar agent and the headless agent share one name, so installing either
> replaces the other. You can never end up with two athans playing at once.

---

## Updating and repairing

The same command every time. There is no separate updater to remember and no
wrong one to pick.

```bash
cd ~/Desktop/athan_app
git pull
./setup.sh
```

| Add this | To |
| --- | --- |
| `--clean` | throw away the app's Python environment first, so every package comes down fresh. Use it when something is broken. |
| `--autostart` | start the app at every login |
| `--no-autostart` | stop that, and quit it now. Nothing else runs — no rebuild, no downloads. |
| `--no-app` | set up Python only, skip building the app |
| `--help` | print this list |

On Windows the flags are `-Clean` and `-NoApp`.

### What it replaces, and what it leaves alone

**Upgraded, never removed:** Homebrew, Python, VLC, ffmpeg. Your whole computer
shares those — uninstalling VLC to reinstall it would take it away from
everything else that uses it, and a download that failed halfway would leave you
with none.

**Rebuilt every run:** `build/` and `dist/`, so a stale app can never be
mistaken for a fresh one. With `--clean`, `.venv` as well.

**Never touched:** anything outside the project folder, including your settings
and custom sounds in `~/.athan_app/`.

The script also rebuilds `.venv` on its own, without being asked, if it finds
the existing one broken — most often because the Python it was built from has
since been upgraded out from under it.

---

## If something goes wrong

**The crescent is there, but clicking it opens nothing.** Almost always a Python
missing Tkinter, the part that draws windows. Homebrew keeps it in a separate
package, so a Python without it builds an app that runs and plays the athan but
has no window inside it. One command fixes the whole chain — it installs
`python-tk` for the right Python version, rebuilds the environment around it,
and rebuilds the app, which also has to be redone because a bundle built without
Tk stays broken however you fix the environment:

```bash
./setup.sh --clean
```

**No sound.** On Apple Silicon you need the **arm64** build of VLC, not the
Intel one. An Intel VLC on an M-series Mac loads without complaint and plays
nothing.

**Prayer times not updating.** Check the network, then the log:

```bash
curl -s "https://api.aladhan.com/v1/status" | grep -q "OK" && echo "API OK" || echo "API unreachable"
tail -f ~/.athan_app/athan_app.log
```

**Check it yourself.** Setup runs these itself and tells you which one failed,
so you rarely need them by hand:

```bash
.venv/bin/python -c "import tkinter; print('tkinter OK', tkinter.TkVersion)"
.venv/bin/python -c "import vlc; vlc.Instance('--intf','dummy'); print('VLC OK')"
.venv/bin/python tests/test_quran_library.py
```


## 📦 Packaging notes

`./setup.sh` builds the app for you; these are the details behind it.

- The build is `onedir`, not `onefile` — the VLC bindings and bundled assets
  are far more reliable that way.
- The build interpreter must have Tkinter. PyInstaller can only bundle what it
  can import, so a Python without it produces a valid-looking `.app` whose
  menu-bar icon opens nothing. Both `setup.sh` and
  `packaging/build_macos_app.sh` refuse to build in that state.
- Custom audio can be dropped into `~/.athan_app/assets/audio/` after install;
  it overrides the bundled files without a rebuild.
- To build without the rest of the setup: `./packaging/build_macos_app.sh`, or
  `.\packaging\build_windows_app.ps1` on Windows.


## 📱 Usage

### GUI Mode (Desktop)
- **System Tray**: Look for the green crescent moon icon in your system tray
- **Right-click** the tray icon to access:
  - View next prayer time
  - See today's prayer schedule
  - Test audio playback
  - Access settings
  - Exit application

### Headless Mode (Server/Background)
```bash
# Start in background
athan-app-headless

# Or run directly
python3 main_headless.py
```

### As a System Service (Linux)
```bash
# Start service
systemctl --user start athan-app

# Enable auto-start on boot
systemctl --user enable athan-app

# Check status
systemctl --user status athan-app

# View logs
journalctl --user -u athan-app -f
```

## ⚙️ Configuration

The application creates a configuration directory at `~/.athan_app/` with the following structure:

```
~/.athan_app/
├── config.json              # Main configuration file
├── assets/
│   └── audio/
│       └── Azansoundtrack.m4a # Your custom Athan audio
├── logs/
└── athan_app.log            # Application logs
```

### Default Settings

- **Location**: auto-detected at startup, with Raleigh, NC as the default fallback
- **Calculation Method**: ISNA (Islamic Society of North America)
- **All Prayers Enabled**: Fajr, Dhuhr, Asr, Maghrib, Isha
- **Volume**: 80%
- **Audio File**: Your custom Azansoundtrack.m4a

### Customizing Settings

Edit the configuration file at `~/.athan_app/config.json`:

```json
{
  "location": {
    "auto_detect": true,
    "latitude": 35.7796,
    "longitude": -78.6382,
    "city": "Raleigh",
    "state": "NC",
    "country": "USA",
    "timezone": "America/New_York"
  },
  "prayer_settings": {
    "calculation_method": 2,
    "enabled_prayers": {
      "fajr": true,
      "dhuhr": true,
      "asr": true,
      "maghrib": true,
      "isha": true
    }
  },
  "audio_settings": {
    "volume": 0.8,
    "athan_volume": 0.8,
    "audio_file": "assets/audio/Azansoundtrack.m4a",
    "athan_files": {
      "fajr": "assets/audio/fajr_athan.m4a",
      "dhuhr": "assets/audio/dhuhr_athan.m4a",
      "asr": "assets/audio/asr_athan.m4a",
      "maghrib": "assets/audio/maghrib_athan.m4a",
      "isha": "assets/audio/isha_athan.m4a"
    }
  },
  "special_audio_settings": {
    "friday_before_dhuhr": {
      "enabled": true,
      "reference_time": "dhuhr",
      "offset_minutes": -180,
      "weekday": 4,
      "audio_file": "assets/audio/Surat_AlKahf.m4a",
      "volume": 0.85
    },
    "after_prayer_duaa": {
      "enabled": true,
      "audio_file": "assets/audio/Duaa.m4a",
      "volume": 1.0
    },
    "pre_prayer_woduaa": {
      "enabled": true,
      "lead_minutes": 15,
      "audio_file": "assets/audio/Woduaa.m4a",
      "volume": 0.85
    },
    "morning_audio": {
      "enabled": true,
      "reference_time": "sunrise",
      "offset_minutes": -30,
      "audio_file": "assets/audio/morning_audio.m4a",
      "volume": 0.8
    },
    "night_audio": {
      "enabled": true,
      "reference_time": "asr",
      "offset_minutes": 30,
      "audio_file": "assets/audio/night_audio.m4a",
      "volume": 0.8
    }
  }
}
```

### Audio File Names

To replace any sound with your own, drop a file with the matching name into
`~/.athan_app/assets/audio/`. That folder is searched **first**, so your copy
wins over the bundled one without editing anything or rebuilding the app, and
it survives every update.

| Sound | File name |
| --- | --- |
| Default athan (fallback) | `Azansoundtrack.m4a` |
| Fajr | `fajr_athan.m4a` |
| Dhuhr | `dhuhr_athan.m4a` |
| Asr | `asr_athan.m4a` |
| Maghrib | `maghrib_athan.m4a` |
| Isha | `isha_athan.m4a` |
| Friday, 3 h before Dhuhr | `Surat_AlKahf.m4a` |
| After each prayer | `Duaa.m4a` |
| Pre-prayer reminder | `Woduaa.m4a` |
| Morning azkar | `morning_audio.m4a` |
| Night azkar | `night_audio.m4a` |

```bash
mkdir -p ~/.athan_app/assets/audio
cp ~/Downloads/my_athan.m4a ~/.athan_app/assets/audio/fajr_athan.m4a
```

The recordings that ship with the app live in `docs/assets/audio/`. That is one
folder, not two: the website has to serve from `docs/`, so rather than keep a
second identical copy for the desktop app, both read the same files. Editing
them there changes the website as well, which is why an override in
`~/.athan_app/` is the right way to change only your own athan.

For installed or packaged use, you can also place overrides in:

```text
~/.athan_app/assets/audio/
```

You can also change any of these paths in `config.json`. If a prayer-specific Athan file is missing, the app falls back to `Azansoundtrack.m4a`.

## 🔧 Testing

`./setup.sh` runs the last two automatically. Any of them can be run directly:

```bash
.venv/bin/python test_core.py               # config, API, audio, scheduler
.venv/bin/python tests/test_quran_library.py # local recordings and the player
.venv/bin/python tests/test_app_commands.py  # the dashboard -> daemon channel
```

This will test:
- ✅ Configuration management
- ✅ Prayer times API
- ✅ Audio player functionality
- ✅ Prayer scheduler
- ✅ Component integration

## 📋 Prayer Time Schedule

The application automatically:

1. **Fetches prayer times** daily at midnight
2. **Schedules alerts** for each prayer time
3. **Plays your Athan audio** at the correct time
4. **Shows notifications** (GUI mode only)
5. **Logs all activities** for debugging

### Today's Schedule Example
```
Fajr:    05:02 AM
Dhuhr:   01:21 PM
Asr:     05:08 PM
Maghrib: 08:19 PM
Isha:    09:39 PM
```

## 🎵 Audio System

- **Format Support**: M4A, MP3, WAV, OGG
- **Audio Engine**: VLC Media Player
- **Your File**: Custom Azansoundtrack.m4a is pre-configured
- **Volume Control**: Adjustable in configuration
- **Test Audio**: Use the system tray menu or `test_core.py`

## 🖥️ System Requirements

### Minimum Requirements
- **Python**: 3.10 or higher, with Tkinter
- **RAM**: 50MB
- **Storage**: 250MB for the built app
- **Network**: Internet connection for prayer times

### Supported Platforms
- **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 7+
- **macOS**: 10.14+ (Mojave)
- **Windows**: 10/11 (with WSL or native Python)

### Dependencies

`./setup.sh` installs and upgrades all of these; the list is here so you know
what is on your machine, not as something to do by hand.

- `python3` 3.10+ **with Tkinter** — on macOS, Homebrew keeps Tkinter in a
  separate `python-tk` formula that `brew install python` does not pull in
- `vlc` media player — arm64 build on Apple Silicon
- `ffmpeg`
- Python packages: `schedule`, `python-vlc`, `pystray`, `pillow`, `requests`,
  `pytz`, `pydub`, and `pyinstaller` for building the app

## 🔍 More troubleshooting

The common failures — no window, no sound, prayer times not updating — are
covered under [If something goes wrong](#if-something-goes-wrong). A few rarer
ones:

**The tray icon never appears at all.** You need a desktop session for it. On a
server or over SSH, run the headless version instead:
`.venv/bin/python main_headless.py`.

**Verbose logging**, when a log line is not enough:

```bash
.venv/bin/python main_headless.py 2>&1 | tee debug.log
```

**Test one audio file directly:**

```bash
.venv/bin/python -c "from core.audio_player import AudioPlayer; \
print('OK' if AudioPlayer().test_audio_file('assets/audio/Azansoundtrack.m4a') else 'FAILED')"
```


## 📚 API Information

**Prayer Times API**: [Aladhan.com](https://aladhan.com/prayer-times-api)
- **Calculation Method**: ISNA (Method 2) by default; 13 methods are selectable
- **Location**: detected at startup, or set manually in Settings — not fixed to any city
- **Timezone**: taken from your system
- **Update Frequency**: Daily at midnight

## 🤝 Support

### Log Files
- **Application logs**: `~/.athan_app/athan_app.log`
- **System service logs**: `journalctl --user -u athan-app`

### Configuration Reset
```bash
# Backup current config
cp ~/.athan_app/config/config.json ~/.athan_app/config/config.json.backup

# Reset to defaults
rm ~/.athan_app/config/config.json
python3 ~/.athan_app/main.py  # Will recreate with defaults
```

### Uninstallation
```bash
# Stop service
systemctl --user stop athan-app
systemctl --user disable athan-app

# Remove files
rm -rf ~/.athan_app
rm ~/.local/bin/athan-app*
rm ~/.local/share/applications/athan-app.desktop
rm ~/.config/systemd/user/athan-app.service
```

## 📄 License

This application is created for personal use. The prayer time data is provided by Aladhan.com API under their terms of service.

## 🤲 Islamic Information

**Prayer Times Calculation**: Based on the Islamic Society of North America (ISNA) method, which is widely accepted in North America.

**Fiqh Considerations**: 
- Prayer times are calculated astronomically
- Local adjustments may be needed based on your madhab
- The application provides reminders; actual prayer obligations remain with the individual

---

**May Allah accept your prayers and make this application beneficial for your worship. Ameen.** 🤲

---

*Built with Python, VLC, and Islamic prayer time APIs*
*Configured for Raleigh, NC with your custom Athan audio*
