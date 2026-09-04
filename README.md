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

## 🚀 Installation

One command. It works the first time and every time after — the same command
installs, updates, and repairs.

| Your system | What to do |
| --- | --- |
| **macOS** (Intel or Apple Silicon) | `./setup.sh` |
| **Linux** (Debian/Ubuntu) | `./setup.sh` |
| **Windows 10 / 11** | `powershell -ExecutionPolicy Bypass -File .\setup.ps1` |
| **iPhone / iPad** | Nothing to install — [open the website](https://aparsi0.github.io/athan_app/) and Share → Add to Home Screen |
| **Android** | Nothing to install — [open the website](https://aparsi0.github.io/athan_app/) and menu → Install app |
| **Anything else with a browser** | [Open the website](https://aparsi0.github.io/athan_app/) |

### macOS and Linux

```bash
cd ~/Desktop/athan_app
./setup.sh
```

That is the whole thing. It installs anything missing (Homebrew, Python,
Tkinter, VLC, ffmpeg), upgrades anything out of date, creates the Python
environment, runs the test suite, builds `AthanApp.app`, and copies it to
`/Applications`.

Starting from nothing, with no copy of the project yet:

```bash
git clone https://github.com/aparsi0/athan_app.git ~/Desktop/athan_app
cd ~/Desktop/athan_app && ./setup.sh
```

If Terminal says `permission denied`, run `chmod +x setup.sh` once and try again.

On Linux, `apt` needs your password once; everything else is the same. The
menu-bar app is macOS-only, so on Linux the script sets up Python and stops
there — run it with `python main.py`, or `main_headless.py` on a server.

### Windows 10 / 11

```powershell
cd $HOME\Desktop\athan_app
powershell -ExecutionPolicy Bypass -File .\setup.ps1
```

Same idea: Python and VLC through `winget`, then the environment, then the
tests. If PowerShell refuses to run the file, that is the execution policy —
the `-ExecutionPolicy Bypass` in the command above is what gets past it, so
copy the whole line rather than just `.\setup.ps1`.

Windows has no menu-bar equivalent; run the app with
`.\.venv\Scripts\python.exe main.py`.

### iPhone, iPad and Android

There is nothing to install and nothing to build. The web version is the
**full** app — prayer times, athan, azkar, the Quran tab with four mushafs,
the morning Quran window, and the day/night sky — and it runs in any browser:

**<https://aparsi0.github.io/athan_app/>**

Add it to your home screen and it behaves like a real app, with its own icon,
no browser chrome, and offline support:

- **iPhone / iPad (Safari):** Share button → **Add to Home Screen**
- **Android (Chrome):** ⋮ menu → **Install app** (or **Add to Home Screen**)

One caveat worth knowing on a phone: browsers suspend background tabs, so the
athan is reliable while the page is open — as an installed app in its own
window it is treated far better than a background tab. For a phone that must
sound the athan with the screen off, a native athan app is the right tool; this
is a web app and cannot outrank the operating system's power management.

### Options

| Command | What it does |
| --- | --- |
| `./setup.sh` | Install or update everything. Run it any time. |
| `./setup.sh --clean` | Delete this app's Python environment first, so every package is downloaded fresh at its newest version. Use this when something is broken and you want a clean slate. |
| `./setup.sh --autostart` | Also start the app automatically every time you log in. |
| `./setup.sh --no-app` | Set up Python only; skip building the `.app`. |
| `./setup.sh --help` | Print this list. |

On Windows the flags are `-Clean` and `-NoApp`.

### What it replaces, and what it leaves alone

This matters, because "reinstall everything" can mean two very different things.

**Upgraded, never removed:** Homebrew, Python, VLC, ffmpeg. These are shared
with the rest of your computer. Uninstalling VLC to reinstall it would take it
away from everything else that uses it, and an interrupted download would leave
you with no VLC at all. `brew upgrade` already gets you the current version,
which is the actual goal.

**Deleted and rebuilt every run:** `build/` and `dist/`, so a stale app bundle
can never be mistaken for the one you just built.

**Deleted and rebuilt with `--clean`:** `.venv`, this app's private Python
environment. That is the real "wipe it and start over" — every Python package
comes down fresh at its newest version. Nothing outside the project folder is
touched, and your settings in `~/.athan_app/` survive.

The script also rebuilds `.venv` on its own, without being asked, if it finds
the existing one broken — most often because the Python it was built from has
since been upgraded out from under it.

### If something goes wrong

The script checks its own work and says which part failed. Two checks are worth
knowing about:

- **tkinter** — without it the app runs and plays the athan, but its window
  never opens. Homebrew keeps Tkinter in a separate `python-tk` formula, and
  a Python missing it is the single most common cause of "the menu-bar icon
  does nothing". The script refuses to continue rather than build an app with
  no window in it.
- **VLC** — on Apple Silicon you need the arm64 build, not the Intel one. An
  Intel VLC on an M-series Mac loads but plays nothing.

Run the checks yourself at any time:

```bash
.venv/bin/python -c "import tkinter; print('tkinter OK', tkinter.TkVersion)"
.venv/bin/python -c "import vlc; vlc.Instance('--intf','dummy'); print('VLC OK')"
.venv/bin/python tests/test_quran_library.py
```


## 🌙 Running at login (macOS)

**Turn it on:**

```bash
./setup.sh --autostart
```

This installs a launchd agent that starts the menu-bar app every time you log
in. Look for the crescent in the menu bar, top-right.

**Verify it took:**

```bash
launchctl print "gui/$(id -u)/com.apa.athan-app" | head   # state should say: running
```

Restart the Mac once to confirm it comes back on its own.

### Keeping the Mac awake

A sleeping Mac plays no athan, so the agent does not run the app directly — it
runs it inside `caffeinate`, which holds the machine awake for exactly as long
as the app is alive and lets go the moment it exits:

```
caffeinate -ims /Applications/AthanApp.app/Contents/MacOS/AthanApp
```

| flag | effect |
| --- | --- |
| `-i` | no idle sleep |
| `-m` | no disk idle sleep |
| `-s` | no sleep while on AC power |
| `-d` | **also** keeps the display awake — not used, see below |

This was `-dims` until 2026-09-04. The extra `d` keeps the *screen* lit as well,
all night, every night, which does nothing for prayer times. If you do want the
display kept on, change `caffeinate -ims` back to `caffeinate -dims` in
`macos/com.apa.athan-menubar.plist` and run `./setup.sh --autostart` again.

To run it awake from a Terminal instead of through launchd:

```bash
caffeinate -ims /Applications/AthanApp.app/Contents/MacOS/AthanApp
```

That holds the window — closing it stops both. To detach it:

```bash
nohup caffeinate -ims /Applications/AthanApp.app/Contents/MacOS/AthanApp >/dev/null 2>&1 &
```

Headless, from a source checkout, same idea:

```bash
caffeinate -i .venv/bin/python main_headless.py
```

**Turn it off** — quits it now, and it stays off through reboots:

```bash
./setup.sh --no-autostart
```

That does nothing else: no rebuild, no package downloads. The equivalent by
hand, if you would rather see what it does:

```bash
launchctl bootout  gui/$(id -u)/com.apa.athan-app 2>/dev/null
launchctl disable  gui/$(id -u)/com.apa.athan-app
```

`bootout` alone is not enough — the agent file stays in `~/Library/LaunchAgents`
and would load again at the next login. `disable` is the half that persists.
To reverse it by hand, `enable` then `bootstrap`:

```bash
launchctl enable    gui/$(id -u)/com.apa.athan-app
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.apa.athan-app.plist
```

### Quit means quit

The agent used to set `KeepAlive` to `true`, which relaunches the app the
instant it exits **for any reason** — so Quit in the menu bar appeared to do
nothing at all. launchd simply put it straight back.

It is now `KeepAlive: { SuccessfulExit: false }`, which keeps the half that
matters: a crash is still restarted, because an athan that dies at 3 a.m. and
stays dead is worse than useless, while a deliberate Quit is respected until you
open the app again or log in again.

If you installed auto-start before 2026-09-03 you have the old behaviour, since
the agent in `~/Library/LaunchAgents` is a copy made at install time. Re-run
`./setup.sh --autostart` once to pick up the change.

### Everyday commands

```bash
# Restart it
launchctl kickstart -k "gui/$(id -u)/com.apa.athan-app"

# Is it running?
launchctl print "gui/$(id -u)/com.apa.athan-app" | head

# Watch the logs
tail -f ~/.athan_app/launchd.stdout.log
tail -f ~/.athan_app/launchd.stderr.log    # crashes and startup failures land here
tail -f ~/.athan_app/helper-window.log     # why the dashboard window would not open
```

For a headless machine with no menu bar, `macos/install_launch_agent.sh` runs
`main_headless.py` under the same agent label instead. Same label means
installing one **replaces** the other, so you can never end up with two athans
playing at once.

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
- **Python**: 3.8 or higher
- **RAM**: 50MB
- **Storage**: 100MB
- **Network**: Internet connection for prayer times

### Supported Platforms
- **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 7+
- **macOS**: 10.14+ (Mojave)
- **Windows**: 10/11 (with WSL or native Python)

### Dependencies
- `python3` and `pip3`
- `vlc` media player
- `tkinter` (the dashboard window). **On macOS Homebrew this is a separate formula**
  — `brew install python-tk` — and is not included by `brew install python`
- Python packages (auto-installed):
  - `schedule`, `python-vlc`, `pystray`, `requests`, `pytz`

## 🔍 Troubleshooting

### Common Issues

**1. Audio not playing**
```bash
# Test VLC installation
vlc --version

# Test audio file
python3 -c "from core.audio_player import AudioPlayer; player = AudioPlayer(); print('✅' if player.test_audio_file('assets/audio/Azansoundtrack.m4a') else '❌')"
```

**2. Prayer times not updating**
```bash
# Check internet connection
curl -s "https://api.aladhan.com/v1/status" | grep -q "OK" && echo "✅ API accessible" || echo "❌ API not accessible"

# Check logs
tail -f ~/.athan_app/athan_app.log
```

**3. Menu-bar icon appears but clicking it opens nothing**

This is almost always missing Tkinter. Check first:

```bash
.venv/bin/python -c "import tkinter"
```

`ModuleNotFoundError: No module named '_tkinter'` confirms it — Homebrew keeps
Tkinter in a separate formula. One command fixes the whole chain: it installs
`python-tk` for the right Python version, rebuilds the environment around it,
and rebuilds the app bundle, which also has to be redone because a bundle built
without Tk stays broken however you fix the environment.

```bash
./setup.sh --clean
launchctl kickstart -k gui/$(id -u)/com.apa.athan-app
```

The build script now refuses to run if Tkinter is missing, so it cannot silently
produce a window-less app again.

The helper window's errors are written to `~/.athan_app/helper-window.log`.

**4. System tray not appearing**
- Ensure you're running in a desktop environment
- Try the headless version: `athan-app-headless`
- Check if system tray is enabled in your desktop environment

**5. Permission errors**
```bash
# Fix permissions
chmod +x ~/.athan_app/main.py
chmod +x ~/.athan_app/main_headless.py
```

### Debug Mode

Enable verbose logging by editing the configuration or running:
```bash
cd ~/.athan_app
python3 main_headless.py 2>&1 | tee debug.log
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
