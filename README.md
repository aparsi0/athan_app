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

## 🚀 Installation

### Before You Start

You need these things on any computer:

- Python 3.10 or newer
- VLC Media Player
- The files from this project
- Internet access so the app can detect location and fetch prayer times

### iMac / MacBook Intel

1. Open `Terminal`.
2. Check whether Python 3 is already installed:
   ```bash
   python3 --version
   ```
3. If that says command not found, install Homebrew:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
4. Install Python:
   ```bash
   brew install python
   ```
5. Install VLC:
   ```bash
   brew install --cask vlc
   ```
6. Go to the project folder:
   ```bash
   cd /path/to/athan_app
   ```
7. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```
8. Activate it:
   ```bash
   source .venv/bin/activate
   ```
9. Install the Python packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
10. Start the app:
   ```bash
   python3 main_headless.py
   ```
11. To keep your Mac awake while it runs:
   ```bash
   caffeinate -i python3 main_headless.py
   ```

### MacBook M1 / M2 / M3

1. Open `Terminal`.
2. Install Homebrew if you do not already have it:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
3. Add Homebrew to your shell if the installer tells you to. On Apple Silicon this is usually:
   ```bash
   echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
   eval "$(/opt/homebrew/bin/brew shellenv)"
   ```
4. Install Python:
   ```bash
   brew install python
   ```
5. Install VLC:
   ```bash
   brew install --cask vlc
   ```
   > ⚠️ **Apple Silicon note:** VLC must be the **Apple Silicon (arm64)** build.
   > If VLC was previously downloaded manually, it may be the Intel version, and the
   > app will later fail with `OSError: dlopen ... libvlccore.dylib ... incompatible
   > architecture (have 'x86_64', need 'arm64')`. Fix it like this:
   > ```bash
   > sudo rm -rf /Applications/VLC.app
   > brew install --cask vlc
   > file /Applications/VLC.app/Contents/MacOS/lib/libvlccore.dylib   # must say arm64
   > ```
   > (If downloading from videolan.org instead, choose the "macOS — Apple Silicon" installer.)
6. Go to the project folder:
   ```bash
   cd /path/to/athan_app
   ```
7. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   ```
8. Activate it:
   ```bash
   source .venv/bin/activate
   ```
9. Install the Python packages:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
10. Start the app:
   ```bash
   python3 main_headless.py
   ```
11. To keep the Mac awake:
   ```bash
   caffeinate -i python3 main_headless.py
   ```

### Run Automatically on macOS with launchd

If you want the app to keep running without keeping Terminal open, use the included macOS launch agent.

1. Go to the project folder:
   ```bash
   cd /path/to/athan_app
   ```
2. Make the installer executable:
   ```bash
   chmod +x macos/install_launch_agent.sh
   ```
3. Install and start the launch agent:
   ```bash
   ./macos/install_launch_agent.sh
   ```
4. Verify it is loaded:
   ```bash
   launchctl print gui/$(id -u)/com.apa.athan-app
   ```
5. Check launch-agent logs if needed:
   ```bash
   tail -f ~/.athan_app/launchd.stdout.log
   tail -f ~/.athan_app/launchd.stderr.log
   ```

Restart the launch agent:

```bash
launchctl kickstart -k gui/$(id -u)/com.apa.athan-app
```

Stop and remove the launch agent:

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.apa.athan-app.plist
rm ~/Library/LaunchAgents/com.apa.athan-app.plist
```

### Windows 10 / 11

1. Install Python from `https://www.python.org/downloads/windows/`
2. During installation, check `Add Python to PATH`.
3. Install VLC from `https://www.videolan.org/vlc/`
4. Open `Command Prompt` or `PowerShell`.
5. Go to the project folder. Example:
   ```powershell
   cd C:\Users\YourName\Desktop\athan_app
   ```
6. Create a virtual environment:
   ```powershell
   py -3 -m venv .venv
   ```
7. Activate it:
   ```powershell
   .venv\Scripts\activate
   ```
8. Install the Python packages:
   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```
9. Start the app:
   ```powershell
   python main_headless.py
   ```
10. If Windows blocks VLC or Python the first time, allow them through the prompt.

### Verify Installation

Run this from the project folder after activating the virtual environment:

```bash
python3 test_core.py
```

On Windows:

```powershell
python test_core.py
```

## 📦 Package as a Desktop App

The repo now includes PyInstaller-based desktop packaging support.

### macOS App Bundle

1. Go to the project folder:
   ```bash
   cd /path/to/athan_app
   ```
2. Make the build script executable:
   ```bash
   chmod +x packaging/build_macos_app.sh
   ```
3. Build the app:
   ```bash
   ./packaging/build_macos_app.sh
   ```
4. The built app will be created at:
   ```text
   dist/AthanApp.app
   ```

### Windows Desktop App

1. Open PowerShell in the project folder.
2. Run:
   ```powershell
   .\packaging\build_windows_app.ps1
   ```
3. The packaged app folder will be created at:
   ```text
   dist\AthanApp
   ```

### Packaging Notes

- Packaging uses `onedir` mode because VLC bindings and bundled assets are more reliable that way.
- Custom audio files can be overridden after install by placing them in:
  ```text
  ~/.athan_app/assets/audio/
  ```
- Desktop packaging requires the extra dependency file:
  ```text
  requirements-desktop.txt
  ```

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

- Default Athan fallback: place your file at `assets/audio/Azansoundtrack.m4a`
- Fajr Athan: place your file at `assets/audio/fajr_athan.m4a`
- Dhuhr Athan: place your file at `assets/audio/dhuhr_athan.m4a`
- Asr Athan: place your file at `assets/audio/asr_athan.m4a`
- Maghrib Athan: place your file at `assets/audio/maghrib_athan.m4a`
- Isha Athan: place your file at `assets/audio/isha_athan.m4a`
- Friday 3 hours before Dhuhr: place your file at `assets/audio/Surat_AlKahf.m4a`
- After each prayer: place your file at `assets/audio/Duaa.m4a`
- Pre-prayer reminder: place your file at `assets/audio/Woduaa.m4a`
- Morning audio: place your file at `assets/audio/morning_audio.m4a` and it will play 30 minutes before sunrise
- Night audio: place your file at `assets/audio/night_audio.m4a` and it will play 30 minutes after Asr

During development, all of these go in:

```text
<project-folder>/assets/audio/
```

For installed or packaged use, you can also place overrides in:

```text
~/.athan_app/assets/audio/
```

You can also change any of these paths in `config.json`. If a prayer-specific Athan file is missing, the app falls back to `Azansoundtrack.m4a`.

## 🔧 Testing

Test the core functionality:

```bash
cd ~/.athan_app
python3 test_core.py
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
- `tkinter` (for GUI notifications)
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

**3. System tray not appearing**
- Ensure you're running in a desktop environment
- Try the headless version: `athan-app-headless`
- Check if system tray is enabled in your desktop environment

**4. Permission errors**
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
- **Calculation Method**: ISNA (Method 2)
- **Location**: Raleigh, NC coordinates
- **Timezone**: America/New_York
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
