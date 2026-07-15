#!/usr/bin/env python3
"""
Athan App - Islamic Prayer Time Application
Main application entry point and controller
"""

import sys
import os
import signal
import time
import threading
import logging
from utils.app_paths import ensure_runtime_dirs, get_log_file_path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules
from config.settings import ConfigManager
from core.prayer_times import PrayerTimesAPI
from core.scheduler import PrayerScheduler
from core.audio_player import PrayerAudioManager
from core.location_service import LocationService
from gui.system_tray import SystemTrayManager

# Configure logging
ensure_runtime_dirs()
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(get_log_file_path()),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class AthanApp:
    """Main Athan Application Controller"""
    
    def __init__(self):
        """Initialize the Athan application"""
        logger.info("Initializing Athan App...")
        
        # Core components
        self.config_manager = None
        self.prayer_api = None
        self.scheduler = None
        self.audio_manager = None
        self.tray_manager = None
        self.location_service = None
        
        # State
        self.is_running = False
        self.current_prayer_times = {}
        self.status_thread = None
        
        # Initialize components
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all application components"""
        try:
            # Configuration manager
            self.config_manager = ConfigManager()
            logger.info("Configuration manager initialized")
            
            # Prayer times API
            self.prayer_api = PrayerTimesAPI()
            logger.info("Prayer times API initialized")

            # Location service
            self.location_service = LocationService()
            logger.info("Location service initialized")
            
            # Audio manager
            self.audio_manager = PrayerAudioManager(self.config_manager)
            logger.info("Audio manager initialized")
            
            # Prayer scheduler
            self.scheduler = PrayerScheduler(
                self._on_prayer_time,
                self._on_custom_audio_event,
            )
            
            self._configure_scheduler()
            
            logger.info("Prayer scheduler initialized")
            
            # System tray manager
            self.tray_manager = SystemTrayManager(self)
            logger.info("System tray manager initialized")
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise

    def _configure_scheduler(self):
        """Apply config-driven location, prayer, and custom audio settings."""
        self._refresh_location_from_detection()

        location = self.config_manager.get_location()
        self.scheduler.set_location(
            location['latitude'],
            location['longitude']
        )

        prayer_settings = self.config_manager.get_prayer_settings()
        self.scheduler.set_calculation_method(
            prayer_settings.get('calculation_method', 2)
        )

        enabled_prayers = prayer_settings.get('enabled_prayers', {})
        for prayer, enabled in enabled_prayers.items():
            self.scheduler.enable_prayer(prayer, enabled)

        special_audio_settings = self.config_manager.get_special_audio_settings()
        for event_name in ('friday_before_dhuhr', 'morning_audio', 'night_audio'):
            event_config = special_audio_settings.get(event_name, {})
            self.scheduler.set_custom_audio_relative_schedule(
                event_name,
                event_config.get(
                    'reference_time',
                    'dhuhr' if event_name == 'friday_before_dhuhr' else ('sunrise' if event_name == 'morning_audio' else 'asr')
                ),
                int(event_config.get(
                    'offset_minutes',
                    -180 if event_name == 'friday_before_dhuhr' else (-30 if event_name == 'morning_audio' else 30)
                )),
                event_config.get('enabled', False),
            )
            if 'weekday' in event_config:
                self.scheduler.custom_audio_events[event_name]['weekday'] = int(event_config['weekday'])
        woduaa_config = special_audio_settings.get('pre_prayer_woduaa', {})
        self.scheduler.set_custom_audio_schedule(
            'pre_prayer_woduaa',
            '',
            woduaa_config.get('enabled', False),
        )
        self.scheduler.custom_audio_events['pre_prayer_woduaa']['lead_minutes'] = woduaa_config.get('lead_minutes', 15)

    def _refresh_location_from_detection(self):
        """Update the configured location from network geolocation when enabled."""
        if not self.config_manager or not self.location_service:
            return

        if not self.config_manager.should_auto_detect_location():
            return

        detected_location = self.location_service.detect_current_location()
        if not detected_location:
            logger.warning("Using configured fallback location because auto-detection failed")
            return

        self.config_manager.set_location(
            detected_location['latitude'],
            detected_location['longitude'],
            city=detected_location.get('city', ''),
            state=detected_location.get('state', ''),
            country=detected_location.get('country', ''),
            timezone=detected_location.get('timezone', ''),
            auto_detect=True,
            location_source=detected_location.get('location_source', 'ip_geolocation'),
            location_provider=detected_location.get('location_provider', ''),
            last_detected_at=detected_location.get('last_detected_at', ''),
        )
        self.config_manager.save_config()

    def _get_woduaa_lead_minutes(self) -> int:
        """Return the configured pre-prayer reminder lead time."""
        settings = self.config_manager.get_special_audio_settings()
        woduaa_config = settings.get('pre_prayer_woduaa', {})
        return int(woduaa_config.get('lead_minutes', 15))
    
    def _on_prayer_time(self, prayer_name: str):
        """
        Callback function called when it's time for prayer
        
        Args:
            prayer_name: Name of the prayer
        """
        try:
            logger.info(f"🕌 Prayer time: {prayer_name.title()}")
            
            # Show notification
            if self.tray_manager:
                self.tray_manager.show_notification(
                    "Prayer Time",
                    f"It's time for {prayer_name.title()} prayer"
                )
            
            # Play audio
            if self.audio_manager:
                success = self.audio_manager.play_prayer_call(prayer_name)
                if success:
                    logger.info(f"Playing {prayer_name} call")
                else:
                    logger.error(f"Failed to play {prayer_name} call")
            
            # Update tray tooltip with next prayer
            self._update_tray_tooltip()
            
        except Exception as e:
            logger.error(f"Error handling prayer time {prayer_name}: {e}")

    def _on_custom_audio_event(self, event_name: str):
        """Handle scheduled custom audio events."""
        try:
            logger.info("Scheduled custom audio event fired: %s", event_name)
            if self.audio_manager:
                audio_key = event_name.split(':', 1)[0]
                success = self.audio_manager.play_named_audio(audio_key)
                if not success:
                    logger.error("Failed to play custom audio event %s", event_name)
                elif self.tray_manager and audio_key == 'pre_prayer_woduaa' and ':' in event_name:
                    prayer_name = event_name.split(':', 1)[1]
                    lead_minutes = self._get_woduaa_lead_minutes()
                    self.tray_manager.show_notification(
                        "Prayer Reminder",
                        f"Woduaa reminder: {prayer_name.title()} in {lead_minutes} minutes"
                    )
                elif self.tray_manager and audio_key == 'friday_before_dhuhr':
                    self.tray_manager.show_notification(
                        "Friday Reminder",
                        "Now playing Surat Al-Kahf, 1 hour before Dhuhr"
                    )
        except Exception as exc:
            logger.error("Error handling custom audio event %s: %s", event_name, exc)
    
    def _update_tray_tooltip(self):
        """Update system tray tooltip with next prayer info"""
        try:
            if self.tray_manager and self.scheduler:
                next_prayer = self.scheduler.get_next_prayer_info()
                if next_prayer:
                    tooltip = f"Athan App - Next: {next_prayer['formatted']}"
                else:
                    tooltip = "Athan App - Islamic Prayer Times"
                
                self.tray_manager.update_tooltip(tooltip)
                
        except Exception as e:
            logger.error(f"Error updating tray tooltip: {e}")
    
    def start(self):
        """Start the application"""
        try:
            if self.is_running:
                logger.warning("Application is already running")
                return
            
            logger.info("Starting Athan App...")
            
            # Test audio setup
            if self.audio_manager:
                if self.audio_manager.test_audio_setup():
                    logger.info("Audio setup test successful")
                else:
                    logger.warning("Audio setup test failed - audio may not work")
            
            # Start prayer scheduler
            if self.scheduler:
                self.scheduler.start_scheduler()
                
                # Get current schedule
                schedule = self.scheduler.get_current_schedule()
                if schedule:
                    logger.info(f"Prayer schedule: {schedule}")
                    self.current_prayer_times = schedule
                else:
                    logger.warning("No prayer times scheduled")

            self.is_running = True
            logger.info("Athan App started successfully")

            self.status_thread = threading.Thread(
                target=self._status_loop,
                name="athan-status-loop",
                daemon=True,
            )
            self.status_thread.start()

            self.reload_watcher_thread = threading.Thread(
                target=self._config_reload_watcher,
                name="athan-reload-watcher",
                daemon=True,
            )
            self.reload_watcher_thread.start()

            if self.tray_manager:
                self.tray_manager.start(on_ready=self._on_tray_ready)
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            self.stop()
            raise

    def _on_tray_ready(self):
        """Finalize UI work after the tray is visible."""
        self._update_tray_tooltip()
        if self.tray_manager:
            self.tray_manager.show_notification(
                "Athan App Started",
                "Islamic prayer times are now active"
            )

    def _status_loop(self):
        """Periodic background maintenance while the GUI app is running."""
        while self.is_running:
            time.sleep(1)
            if int(time.time()) % 300 == 0:
                status = self.get_app_status()
                logger.info(
                    "Status check - Scheduler: %s, Tray: %s",
                    status['scheduler_running'],
                    status['tray_running'],
                )
                self._update_tray_tooltip()
    
    def stop(self):
        """Stop the application"""
        try:
            if not self.is_running:
                return
            
            logger.info("Stopping Athan App...")
            
            # Stop scheduler
            if self.scheduler:
                self.scheduler.stop_scheduler()
            
            # Stop audio
            if self.audio_manager:
                self.audio_manager.stop_prayer_call()
            
            # Stop system tray
            if self.tray_manager:
                self.tray_manager.stop()
            
            self.is_running = False
            logger.info("Athan App stopped")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
    
    def restart(self):
        """Restart the application"""
        logger.info("Restarting Athan App...")
        self.stop()
        time.sleep(1)
        self.start()
    
    # Interface methods for system tray
    
    def show_main_window(self):
        """Legacy tray hook kept for compatibility."""
        logger.info("Status window requested")
    
    def show_settings_window(self):
        """Legacy settings hook kept for compatibility."""
        logger.info("Settings window requested (not implemented yet)")
    
    def get_next_prayer_info(self):
        """Get next prayer information"""
        if self.scheduler:
            return self.scheduler.get_next_prayer_info()
        return None
    
    def get_today_prayer_times(self):
        """Get today's prayer times"""
        return self.current_prayer_times
    
    def test_audio(self) -> bool:
        """Test audio playback"""
        if self.audio_manager:
            return self.audio_manager.play_test_audio('dhuhr')
        return False
    
    def stop_audio(self):
        """Stop current audio playback"""
        if self.audio_manager:
            self.audio_manager.stop_prayer_call()
    
    def quit_application(self):
        """Quit the application"""
        logger.info("Application quit requested")
        self.stop()
    
    def refresh_prayer_times(self):
        """Manually refresh prayer times"""
        if self.scheduler:
            self.scheduler.force_refresh()
            schedule = self.scheduler.get_current_schedule()
            if schedule:
                self.current_prayer_times = schedule
                logger.info("Prayer times refreshed")
                return True
        return False
    
    def get_app_status(self) -> dict:
        """Get application status information"""
        return {
            'is_running': self.is_running,
            'scheduler_running': self.scheduler.is_scheduler_running() if self.scheduler else False,
            'tray_running': self.tray_manager.is_tray_running() if self.tray_manager else False,
            'current_prayer_times': self.current_prayer_times,
            'next_prayer': self.get_next_prayer_info(),
            'audio_info': self.audio_manager.get_audio_info() if self.audio_manager else {},
            'location': self.config_manager.get_location() if self.config_manager else {},
        }

    def get_status_summary_text(self) -> str:
        """Return a human-readable status summary for the tray UI."""
        status = self.get_app_status()
        location = status.get('location', {})
        location_parts = [location.get('city', ''), location.get('state', ''), location.get('country', '')]
        location_name = ", ".join(part for part in location_parts if part) or "Unknown"
        next_prayer = status.get('next_prayer')
        next_prayer_text = next_prayer['formatted'] if next_prayer else "Not available"

        prayer_lines = []
        for prayer_name, time_value in status.get('current_prayer_times', {}).items():
            prayer_lines.append(f"{prayer_name.title()}: {time_value}")

        audio_info = status.get('audio_info', {})
        audio_lines = []
        default_audio = audio_info.get('default_audio_file')
        if default_audio:
            audio_lines.append(f"Default Athan: {os.path.basename(default_audio)}")

        for prayer_name, file_path in audio_info.get('prayer_audio_files', {}).items():
            audio_lines.append(f"{prayer_name.title()} Athan: {os.path.basename(file_path)}")

        special_audio_labels = {
            'after_prayer_duaa': 'After-prayer Duaa',
            'pre_prayer_woduaa': 'Pre-prayer Woduaa',
            'friday_before_dhuhr': 'Friday Surat Al-Kahf',
            'morning_audio': 'Morning audio',
            'night_audio': 'Night audio',
        }
        for key, label in special_audio_labels.items():
            file_path = audio_info.get('special_audio_files', {}).get(key)
            if file_path:
                audio_lines.append(f"{label}: {os.path.basename(file_path)}")

        sections = [
            f"Running: {'Yes' if status['is_running'] else 'No'}",
            f"Scheduler: {'Active' if status['scheduler_running'] else 'Stopped'}",
            f"Tray: {'Active' if status['tray_running'] else 'Stopped'}",
            "",
            f"Location: {location_name}",
            f"Coordinates: {location.get('latitude', 'Unknown')}, {location.get('longitude', 'Unknown')}",
            f"Timezone: {location.get('timezone', 'Unknown')}",
            "",
            f"Next Prayer: {next_prayer_text}",
            "",
            "Today's Prayer Times:",
            "\n".join(prayer_lines) if prayer_lines else "Not available",
            "",
            "Loaded Audio:",
            "\n".join(audio_lines) if audio_lines else "No audio files loaded",
        ]
        return "\n".join(sections)

    def get_dialog_payload(self, view: str) -> dict:
        """Build structured payloads for the styled tray dialogs."""
        status = self.get_app_status()
        location = status.get('location', {})
        location_parts = [location.get('city', ''), location.get('state', ''), location.get('country', '')]
        location_name = ", ".join(part for part in location_parts if part) or "Unknown"
        next_prayer = status.get('next_prayer')

        prayer_times = []
        for prayer_name, time_value in status.get('current_prayer_times', {}).items():
            prayer_times.append({
                'label': prayer_name.title(),
                'time': time_value,
                'highlight': bool(next_prayer and prayer_name == next_prayer.get('prayer')),
                'note': 'Up next' if next_prayer and prayer_name == next_prayer.get('prayer') else '',
            })

        audio_info = status.get('audio_info', {})
        audio_lines = []
        default_audio = audio_info.get('default_audio_file')
        if default_audio:
            audio_lines.append(f"Default Athan: {os.path.basename(default_audio)}")
        for prayer_name, file_path in audio_info.get('prayer_audio_files', {}).items():
            audio_lines.append(f"{prayer_name.title()} Athan: {os.path.basename(file_path)}")
        special_audio_labels = {
            'after_prayer_duaa': 'After-prayer Duaa',
            'pre_prayer_woduaa': 'Pre-prayer Woduaa',
            'friday_before_dhuhr': 'Friday Surat Al-Kahf',
            'morning_audio': 'Morning audio',
            'night_audio': 'Night audio',
        }
        for key, label in special_audio_labels.items():
            file_path = audio_info.get('special_audio_files', {}).get(key)
            if file_path:
                audio_lines.append(f"{label}: {os.path.basename(file_path)}")

        base_payload = {
            'subtitle': f"{location_name}  |  {location.get('timezone', 'Unknown')}",
            'next_prayer': {
                'name': next_prayer.get('prayer', '').title() if next_prayer else '',
                'formatted': next_prayer.get('formatted', 'Not available') if next_prayer else 'Not available',
            } if next_prayer else None,
            'prayer_times': prayer_times,
        }

        if view == 'status':
            return {
                **base_payload,
                'title': 'Athan App',
                'message_title': 'Live Status',
                'message': "Prayer scheduling is active and the app is ready to play your configured reminders.",
                'facts': [
                    f"Running: {'Yes' if status['is_running'] else 'No'}",
                    f"Scheduler: {'Active' if status['scheduler_running'] else 'Stopped'}",
                    f"Tray: {'Active' if status['tray_running'] else 'Stopped'}",
                    f"Coordinates: {location.get('latitude', 'Unknown')}, {location.get('longitude', 'Unknown')}",
                    *audio_lines,
                ],
            }

        if view == 'prayer_times':
            # Use the live dashboard so users see countdowns next to each prayer.
            return self._build_dashboard_payload(initial_tab='today', title="Today's Prayer Times")

        if view == 'next_prayer':
            # Use the live dashboard for the same reason.
            return self._build_dashboard_payload(initial_tab='today', title='Next Prayer')

        if view == 'settings':
            return self._build_dashboard_payload(initial_tab='settings', title='Settings')

        if view == 'dashboard':
            return self._build_dashboard_payload(initial_tab='today', title='Athan App')

        if view == 'about':
            return {
                'title': 'About Athan App',
                'subtitle': 'Islamic Prayer Time Companion',
                'message_title': 'About',
                'message': "Athan App calculates prayer times from your location and plays your configured Athan and reminder audio automatically.",
                'facts': [
                    "Built with Python, VLC, and a macOS menu-bar launcher.",
                    "Supports per-prayer Athan, Woduaa, Duaa, Friday Surat Al-Kahf, and morning/night reminders.",
                ],
            }

        if view == 'audio_test_success':
            return {
                'title': 'Audio Test',
                'subtitle': 'Preview Started',
                'message_title': 'Audio Test',
                'message': "A live Athan preview is now playing. Use Stop Audio from the menu if you want to stop it early.",
                'facts': audio_lines[:6] if audio_lines else ["No audio files are currently loaded."],
            }

        if view == 'audio_test_failure':
            return {
                'title': 'Audio Test',
                'subtitle': 'Preview Failed',
                'message_title': 'Audio Test',
                'message': "The app could not start audio playback. Check that your Athan files exist and VLC audio playback is available.",
                'facts': [
                    "Verify files in ~/.athan_app/assets/audio/ or the bundled assets folder.",
                    "Check that your Mac audio output is available and not muted.",
                ],
            }

        if view == 'audio_stopped':
            return {
                'title': 'Audio',
                'subtitle': 'Playback Stopped',
                'message_title': 'Audio Control',
                'message': "Current playback has been stopped.",
                'facts': ["You can start a preview again from Test Audio."],
            }

        return {
            'title': 'Athan App',
            'subtitle': 'Information',
            'message_title': 'Info',
            'message': 'No data available.',
        }

    def _build_dashboard_payload(self, initial_tab: str = 'today', title: str = 'Athan App') -> dict:
        """Build a rich payload consumed by the tabbed DashboardWindow."""
        status = self.get_app_status()
        location = status.get('location', {})
        location_parts = [location.get('city', ''), location.get('state', ''), location.get('country', '')]
        location_name = ", ".join(part for part in location_parts if part) or "Unknown"
        next_prayer = status.get('next_prayer')

        prayer_times_map = dict(status.get('current_prayer_times', {}) or {})

        reminder_schedule = {}
        custom_audio_schedule = {}
        if self.scheduler:
            try:
                reminder_schedule = self.scheduler.get_prayer_reminder_schedule()
            except Exception:
                reminder_schedule = {}
            try:
                custom_audio_schedule = self.scheduler.get_custom_audio_schedule()
            except Exception:
                custom_audio_schedule = {}

        return {
            'kind': 'dashboard',
            'title': title,
            'subtitle': f"{location_name}  |  {location.get('timezone', 'Unknown')}",
            'initial_tab': initial_tab,
            'config': self.config_manager.config if self.config_manager else {},
            'prayer_times_map': prayer_times_map,
            'reminder_schedule': reminder_schedule,
            'custom_audio_schedule': custom_audio_schedule,
            'next_prayer': next_prayer,
            'audio_info': status.get('audio_info', {}),
        }

    def _reload_config_from_disk(self):
        """Re-read config.json and re-apply scheduler + audio settings."""
        try:
            logger.info("Reload requested — re-reading config.json")
            if self.config_manager:
                self.config_manager.config = self.config_manager.load_config()
            if self.scheduler:
                self._configure_scheduler()
                self.scheduler.force_refresh()
                schedule = self.scheduler.get_current_schedule()
                if schedule:
                    self.current_prayer_times = schedule
            if self.audio_manager:
                # Reload volumes and audio file paths from the new config.
                self.audio_manager._load_audio_settings()
            self._update_tray_tooltip()
            logger.info("Config reloaded successfully")
        except Exception as exc:
            logger.error("Error reloading config: %s", exc)

    def _config_reload_watcher(self):
        """Background thread: poll for the settings-saved sentinel file."""
        from utils.app_paths import get_config_dir
        sentinel = get_config_dir() / ".reload_request"
        while self.is_running:
            try:
                if sentinel.exists():
                    sentinel.unlink(missing_ok=True)
                    self._reload_config_from_disk()
            except Exception as exc:
                logger.error("Reload watcher error: %s", exc)
            time.sleep(2)


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down...")
    if hasattr(signal_handler, 'app') and signal_handler.app:
        signal_handler.app.stop()
    sys.exit(0)


def main():
    """Main application entry point"""
    # Helper-window mode: when invoked with --show-window <base64-payload>,
    # just display the requested Tk window on the main thread and exit.
    # This is used by the system tray (in frozen .app bundles) to open
    # menu dialogs in a child process, since Tk on macOS requires the
    # main thread.
    if len(sys.argv) >= 3 and sys.argv[1] == "--show-window":
        try:
            from gui.main_window import _decode_payload, show_payload
            payload = _decode_payload(sys.argv[2])
            show_payload(payload)
        except Exception as e:
            logger.error(f"Helper window failed: {e}")
            return 1
        return 0

    try:
        logger.info("=" * 50)
        logger.info("Starting Athan App - Islamic Prayer Times")
        logger.info("=" * 50)
        
        # Create application instance
        app = AthanApp()
        
        # Set up signal handlers for graceful shutdown
        signal_handler.app = app
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the application
        app.start()

    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        return 1
    
    finally:
        if 'app' in locals():
            app.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
