#!/usr/bin/env python3
"""
Athan App - Headless Version
Islamic Prayer Time Application without GUI
Suitable for servers and headless systems
"""

import sys
import os
import signal
import time
import threading
from datetime import datetime
import logging
from utils.app_paths import ensure_runtime_dirs, get_log_file_path

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import application modules (excluding GUI)
from config.settings import ConfigManager
from core.prayer_times import PrayerTimesAPI
from core.scheduler import PrayerScheduler
from core.audio_player import PrayerAudioManager
from core.location_service import LocationService

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


class AthanAppHeadless:
    """Headless Athan Application Controller"""
    
    def __init__(self):
        """Initialize the headless Athan application"""
        logger.info("Initializing Athan App (Headless Mode)...")
        
        # Core components
        self.config_manager = None
        self.prayer_api = None
        self.scheduler = None
        self.audio_manager = None
        self.location_service = None
        
        # State
        self.is_running = False
        self.current_prayer_times = {}
        
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
            
            # Print to console (since no GUI notifications)
            print(f"\\n{'='*50}")
            print(f"🕌 PRAYER TIME: {prayer_name.upper()}")
            print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*50}\\n")
            
            # Play audio
            if self.audio_manager:
                success = self.audio_manager.play_prayer_call(prayer_name)
                if success:
                    logger.info(f"Playing {prayer_name} call")
                    after_prayer_duaa = self.config_manager.get_special_audio_settings().get('after_prayer_duaa', {})
                    if after_prayer_duaa.get('enabled', False):
                        print("📿 Duaa will play automatically after the prayer Athan finishes\n")
                else:
                    logger.error(f"Failed to play {prayer_name} call")
            
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
                elif audio_key == 'pre_prayer_woduaa' and ':' in event_name:
                    prayer_name = event_name.split(':', 1)[1]
                    lead_minutes = self._get_woduaa_lead_minutes()
                    print(f"\n🔔 Woduaa reminder: {prayer_name.title()} in {lead_minutes} minutes\n")
                elif audio_key == 'friday_before_dhuhr':
                    print("\n📖 Surat Al-Kahf reminder: now playing 1 hour before Dhuhr\n")
        except Exception as exc:
            logger.error("Error handling custom audio event %s: %s", event_name, exc)
    
    def start(self):
        """Start the application"""
        try:
            if self.is_running:
                logger.warning("Application is already running")
                return
            
            logger.info("Starting Athan App (Headless Mode)...")
            
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
                    self._print_daily_summary()
                else:
                    logger.warning("No prayer times scheduled")
            
            self.is_running = True
            logger.info("Athan App started successfully")
            
        except Exception as e:
            logger.error(f"Error starting application: {e}")
            self.stop()
            raise
    
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
            
            self.is_running = False
            logger.info("Athan App stopped")
            
        except Exception as e:
            logger.error(f"Error stopping application: {e}")
    
    def get_status(self) -> dict:
        """Get application status information"""
        return {
            'is_running': self.is_running,
            'scheduler_running': self.scheduler.is_scheduler_running() if self.scheduler else False,
            'current_prayer_times': self.current_prayer_times,
            'next_prayer': self.scheduler.get_next_prayer_info() if self.scheduler else None,
            'location': self.config_manager.get_location() if self.config_manager else {},
            'audio_info': self.audio_manager.get_audio_info() if self.audio_manager else {}
        }

    def _print_daily_summary(self):
        """Print the detected location and today's full prayer schedule."""
        location = self.config_manager.get_location() if self.config_manager else {}
        next_prayer = self.scheduler.get_next_prayer_info() if self.scheduler else None

        print("\n📍 CURRENT LOCATION")
        print("=" * 60)
        city_parts = [location.get('city', ''), location.get('state', ''), location.get('country', '')]
        location_label = ", ".join([part for part in city_parts if part])
        if location_label:
            print(f"  {location_label}")
        print(f"  Coordinates: {location.get('latitude', 'N/A')}, {location.get('longitude', 'N/A')}")
        print(f"  Timezone: {location.get('timezone', 'N/A')}")
        source = location.get('location_source', 'unknown')
        provider = location.get('location_provider', '')
        provider_suffix = f" via {provider}" if provider else ""
        print(f"  Source: {source}{provider_suffix}")

        print("\n📅 TODAY'S PRAYER TIMES")
        print("=" * 60)
        for prayer in ('fajr', 'dhuhr', 'asr', 'maghrib', 'isha'):
            time_str = self.current_prayer_times.get(prayer, '--:--')
            marker = '  '
            if next_prayer and next_prayer.get('prayer') == prayer:
                marker = '→ '
            print(f"{marker}{prayer.title():8} {time_str}")

        if next_prayer:
            print(f"\n⏰ Next prayer: {next_prayer['formatted']}")

        reminder_schedule = self.scheduler.get_prayer_reminder_schedule() if self.scheduler else {}
        if reminder_schedule:
            print("\n🔔 Woduaa reminders")
            print("=" * 60)
            for prayer in ('fajr', 'dhuhr', 'asr', 'maghrib', 'isha'):
                event_name = f'pre_prayer_woduaa:{prayer}'
                if event_name in reminder_schedule:
                    print(f"  {prayer.title():8} {reminder_schedule[event_name]}")

        print()
    
    def print_status(self):
        """Print current status to console"""
        status = self.get_status()
        
        print(f"\\n📊 ATHAN APP STATUS")
        print(f"{'='*30}")
        print(f"Running: {'Yes' if status['is_running'] else 'No'}")
        print(f"Scheduler: {'Active' if status['scheduler_running'] else 'Inactive'}")
        
        if status['current_prayer_times']:
            print(f"\\nToday's Prayers:")
            for prayer in ('fajr', 'dhuhr', 'asr', 'maghrib', 'isha'):
                if prayer in status['current_prayer_times']:
                    prefix = '-> ' if status['next_prayer'] and status['next_prayer'].get('prayer') == prayer else '   '
                    print(f"{prefix}{prayer.title()}: {status['current_prayer_times'][prayer]}")

        if status['next_prayer']:
            print(f"\\nNext Prayer: {status['next_prayer']['formatted']}")

        location = status.get('location', {})
        if location:
            print(f"\nLocation: {location.get('city', '')}, {location.get('state', '')} ({location.get('latitude', 'N/A')}, {location.get('longitude', 'N/A')})")
        
        audio_info = status['audio_info']
        if audio_info:
            print(f"\\nAudio Status:")
            print(f"  Default fallback: {os.path.basename(audio_info.get('default_audio_file', 'None'))}")
            print(f"  Ready: {'Yes' if audio_info.get('audio_file_exists', False) else 'No'}")

            prayer_audio_files = audio_info.get('prayer_audio_files', {})
            if prayer_audio_files:
                print(f"\\nPrayer-specific Athan files:")
                for prayer in ('fajr', 'dhuhr', 'asr', 'maghrib', 'isha'):
                    if prayer in prayer_audio_files:
                        print(f"  {prayer.title()}: {os.path.basename(prayer_audio_files[prayer])}")
        
        print()


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, shutting down...")
    if hasattr(signal_handler, 'app') and signal_handler.app:
        signal_handler.app.stop()
    sys.exit(0)


def main():
    """Main application entry point"""
    try:
        print("🕌 ATHAN APP - ISLAMIC PRAYER TIMES (Headless Mode)")
        print("=" * 60)
        
        # Create application instance
        app = AthanAppHeadless()
        
        # Set up signal handlers for graceful shutdown
        signal_handler.app = app
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the application
        app.start()
        
        # Print initial status
        app.print_status()
        
        print("Application is running. Press Ctrl+C to stop.")
        print("Logs are being written to 'athan_app.log'")
        print("-" * 60)
        
        # Keep the main thread alive
        try:
            status_check_counter = 0
            while app.is_running:
                time.sleep(1)
                status_check_counter += 1
                
                # Periodic status check (every 5 minutes)
                if status_check_counter >= 300:
                    status = app.get_status()
                    logger.info(f"Status check - Scheduler: {status['scheduler_running']}")
                    status_check_counter = 0
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        return 1
    
    finally:
        if 'app' in locals():
            app.stop()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
