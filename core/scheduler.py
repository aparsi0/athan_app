"""
Prayer Time Scheduler Module
Handles background scheduling of prayer time alerts
"""

import schedule
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Callable, Optional
import logging
from .prayer_times import PrayerTimesAPI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrayerScheduler:
    """Handles scheduling and execution of prayer time alerts"""
    
    def __init__(
        self,
        prayer_callback: Callable[[str], None],
        custom_event_callback: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the prayer scheduler
        
        Args:
            prayer_callback: Function to call when prayer time arrives
                           Should accept prayer name as parameter
        """
        self.prayer_api = PrayerTimesAPI()
        self.prayer_callback = prayer_callback
        self.custom_event_callback = custom_event_callback
        self.is_running = False
        self.scheduler_thread = None
        self.current_schedule = {}
        self.custom_audio_schedule = {}
        self.prayer_reminder_schedule = {}
        
        # User location (Raleigh, NC)
        self.latitude = 35.7796
        self.longitude = -78.6382
        self.calculation_method = 2  # ISNA
        
        # Prayer names in order
        self.prayer_names = ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']
        
        # Settings
        self.enabled_prayers = {
            'fajr': True,
            'dhuhr': True,
            'asr': True,
            'maghrib': True,
            'isha': True
        }
        self.custom_audio_events = {
            'friday_before_dhuhr': {
                'enabled': False,
                'reference_time': 'dhuhr',
                'offset_minutes': -180,
                'weekday': 4,
            },
            'morning_audio': {
                'enabled': False,
                'reference_time': 'sunrise',
                'offset_minutes': -30,
            },
            'night_audio': {
                'enabled': False,
                'reference_time': 'asr',
                'offset_minutes': 30,
            }
        }
    
    def set_location(self, latitude: float, longitude: float):
        """
        Set user location coordinates
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """
        self.latitude = latitude
        self.longitude = longitude
        logger.info(f"Location updated to ({latitude}, {longitude})")
    
    def set_calculation_method(self, method: int):
        """
        Set prayer calculation method
        
        Args:
            method: Calculation method ID
        """
        self.calculation_method = method
        logger.info(f"Calculation method updated to {method}")
    
    def enable_prayer(self, prayer_name: str, enabled: bool = True):
        """
        Enable or disable a specific prayer alert
        
        Args:
            prayer_name: Name of the prayer
            enabled: Whether to enable the prayer alert
        """
        if prayer_name in self.enabled_prayers:
            self.enabled_prayers[prayer_name] = enabled
            logger.info(f"Prayer {prayer_name} {'enabled' if enabled else 'disabled'}")

    def set_custom_audio_schedule(self, event_name: str, time_str: str, enabled: bool = True):
        """Configure a custom daily audio event."""
        if event_name not in self.custom_audio_events:
            self.custom_audio_events[event_name] = {}

        self.custom_audio_events[event_name]['time'] = time_str
        self.custom_audio_events[event_name]['enabled'] = enabled
        logger.info(
            "Custom audio event %s configured at %s (%s)",
            event_name,
            time_str,
            "enabled" if enabled else "disabled",
        )

    def set_custom_audio_relative_schedule(
        self,
        event_name: str,
        reference_time: str,
        offset_minutes: int,
        enabled: bool = True,
    ):
        """Configure a custom daily audio event relative to a prayer-related time."""
        if event_name not in self.custom_audio_events:
            self.custom_audio_events[event_name] = {}

        self.custom_audio_events[event_name]['reference_time'] = reference_time
        self.custom_audio_events[event_name]['offset_minutes'] = offset_minutes
        self.custom_audio_events[event_name]['enabled'] = enabled
        logger.info(
            "Custom audio event %s configured relative to %s (%+d min, %s)",
            event_name,
            reference_time,
            offset_minutes,
            "enabled" if enabled else "disabled",
        )
    
    def schedule_daily_prayers(self) -> bool:
        """
        Schedule today's prayer times
        
        Returns:
            True if successful (even if 0 prayers left today), False on error
        """
        try:
            # Fetch today's prayer times
            prayer_data = self.prayer_api.get_today_prayer_times(
                self.latitude, self.longitude, self.calculation_method
            )
            
            if not prayer_data:
                logger.error("Failed to fetch prayer times for scheduling")
                return False
            
            prayer_times = prayer_data['prayer_times']
            
            # Clear existing schedule
            schedule.clear()
            self.current_schedule = {}
            self.prayer_reminder_schedule = {}

            # Keep all prayer times for the day, even if some have already passed.
            for prayer_name in self.prayer_names:
                if prayer_name in prayer_times and self.enabled_prayers.get(prayer_name, True):
                    self.current_schedule[prayer_name] = prayer_times[prayer_name]

            # Make non-prayer reference times (e.g. sunrise) available for relative events.
            sunrise_time = prayer_times.get('sunrise')
            if sunrise_time:
                self.current_schedule['sunrise'] = sunrise_time
            
            # Schedule each prayer
            scheduled_count = 0
            for prayer_name in self.prayer_names:
                if prayer_name in prayer_times and self.enabled_prayers.get(prayer_name, True):
                    prayer_time = prayer_times[prayer_name]
                    
                    if self._schedule_prayer(prayer_name, prayer_time):
                        scheduled_count += 1

            # Schedule custom non-prayer audio events.
            self._schedule_custom_audio_events()
            
            # ALWAYS schedule daily refresh at midnight (00:01)
            # This ensures the script continues running for tomorrow
            schedule.every().day.at("00:01").do(self._daily_refresh)
            
            if scheduled_count == 0:
                logger.info("All prayers for today have passed. Waiting for midnight refresh.")
            else:
                logger.info(f"Successfully scheduled {scheduled_count} prayers for today")
                logger.info(f"Current schedule: {self.current_schedule}")
            
            # FIX: Return True even if count is 0, so the scheduler thread starts successfully
            return True
            
        except Exception as e:
            logger.error(f"Error scheduling daily prayers: {e}")
            return False
    
    def _schedule_prayer(self, prayer_name: str, prayer_time: str) -> bool:
        """
        Schedule a single prayer time
        
        Args:
            prayer_name: Name of the prayer
            prayer_time: Time string in HH:MM format
            
        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Parse time
            time_parts = prayer_time.split(':')
            if len(time_parts) != 2:
                logger.error(f"Invalid time format for {prayer_name}: {prayer_time}")
                return False
            
            hour = int(time_parts[0])
            minute = int(time_parts[1])
            
            # Check if time has already passed today
            now = datetime.now()
            prayer_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if prayer_datetime <= now:
                logger.info(f"Prayer time {prayer_name} at {prayer_time} has already passed today")
                return False
            
            # Schedule the prayer
            schedule.every().day.at(prayer_time).do(self._execute_prayer_alert, prayer_name)
            
            logger.info(f"Scheduled {prayer_name} at {prayer_time}")
            return True
            
        except (ValueError, IndexError) as e:
            logger.error(f"Error scheduling {prayer_name} at {prayer_time}: {e}")
            return False
    
    def _execute_prayer_alert(self, prayer_name: str):
        """
        Execute prayer alert callback
        
        Args:
            prayer_name: Name of the prayer
        """
        try:
            logger.info(f"Executing prayer alert for {prayer_name}")
            self.prayer_callback(prayer_name)
        except Exception as e:
            logger.error(f"Error executing prayer alert for {prayer_name}: {e}")

    def _schedule_custom_audio_events(self):
        """Schedule fixed-time and relative custom audio events.

        Always records the computed time-of-day in ``custom_audio_schedule`` so
        the UI can display passed events too. Only the actual runtime job is
        skipped when the time has already elapsed today.
        """
        self.custom_audio_schedule = {}

        for event_name, config in self.custom_audio_events.items():
            if not config.get('enabled', False):
                continue

            if event_name == 'pre_prayer_woduaa':
                continue

            if 'reference_time' in config:
                computed_time = self._schedule_relative_custom_audio_event(event_name, config)
                if computed_time:
                    self.custom_audio_schedule[event_name] = computed_time
                continue

            time_str = config.get('time', '')
            if time_str:
                # Try to register the runtime job; record the time regardless.
                self._schedule_custom_audio_event(event_name, time_str)
                self.custom_audio_schedule[event_name] = time_str

        self._schedule_prayer_relative_events()

    def _schedule_relative_custom_audio_event(self, event_name: str, config: Dict[str, object]) -> Optional[str]:
        """Compute and (when still in the future) schedule a relative event.

        Returns the computed HH:MM time string when the event applies to today,
        regardless of whether the time has already passed. The runtime job is
        registered only if the time is still upcoming. Returns ``None`` when
        the event does not apply today (e.g. wrong weekday) or when its
        reference time isn't known yet.
        """
        reference_time_name = str(config.get('reference_time', ''))
        offset_minutes = int(config.get('offset_minutes', 0))
        target_weekday = config.get('weekday')
        reference_time = self.current_schedule.get(reference_time_name)

        if target_weekday is not None and datetime.now().weekday() != int(target_weekday):
            logger.info(
                "Skipping %s because today is not target weekday %s",
                event_name,
                target_weekday,
            )
            return None

        if not reference_time:
            logger.warning(
                "Could not schedule %s because reference time %s is unavailable",
                event_name,
                reference_time_name,
            )
            return None

        scheduled_time = self._calculate_relative_time(reference_time, offset_minutes)
        if not scheduled_time:
            return None

        # Always return the computed time so the UI can show it. The job
        # registration (which fails for already-passed times) is best-effort.
        self._schedule_custom_audio_event(event_name, scheduled_time)
        return scheduled_time

    def _schedule_prayer_relative_events(self):
        """Schedule events that occur relative to prayer times."""
        reminder_config = self.custom_audio_events.get('pre_prayer_woduaa', {})
        if not reminder_config.get('enabled', False):
            return

        lead_minutes = int(reminder_config.get('lead_minutes', 15))
        for prayer_name in self.prayer_names:
            prayer_time = self.current_schedule.get(prayer_name)
            if not prayer_time:
                continue
            reminder_time = self._calculate_relative_time(prayer_time, -lead_minutes)
            if not reminder_time:
                continue

            event_name = f"pre_prayer_woduaa:{prayer_name}"
            # Record the time regardless so the UI can display it for the day;
            # job registration is best-effort (skipped for already-passed times).
            self._schedule_custom_audio_event(event_name, reminder_time)
            self.prayer_reminder_schedule[event_name] = reminder_time

    def _calculate_relative_time(self, time_str: str, minute_offset: int) -> Optional[str]:
        """Return HH:MM after applying a minute offset to a HH:MM input."""
        try:
            hour_str, minute_str = time_str.split(':')
            base = datetime.now().replace(
                hour=int(hour_str),
                minute=int(minute_str),
                second=0,
                microsecond=0,
            )
            adjusted = base + timedelta(minutes=minute_offset)
            return adjusted.strftime("%H:%M")
        except (ValueError, IndexError) as exc:
            logger.error("Error calculating relative time from %s: %s", time_str, exc)
            return None

    def _schedule_custom_audio_event(self, event_name: str, time_str: str) -> bool:
        """Schedule a non-prayer daily event at a fixed time."""
        try:
            time_parts = time_str.split(':')
            if len(time_parts) != 2:
                logger.error("Invalid custom event time format for %s: %s", event_name, time_str)
                return False

            hour = int(time_parts[0])
            minute = int(time_parts[1])
            now = datetime.now()
            event_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

            if event_datetime <= now:
                logger.info("Custom event %s at %s has already passed today", event_name, time_str)
                return False

            schedule.every().day.at(time_str).do(self._execute_custom_event, event_name)
            logger.info("Scheduled custom event %s at %s", event_name, time_str)
            return True
        except (ValueError, IndexError) as exc:
            logger.error("Error scheduling custom event %s at %s: %s", event_name, time_str, exc)
            return False

    def _execute_custom_event(self, event_name: str):
        """Execute a custom scheduled event."""
        try:
            logger.info("Executing custom audio event %s", event_name)
            if self.custom_event_callback:
                self.custom_event_callback(event_name)
        except Exception as exc:
            logger.error("Error executing custom event %s: %s", event_name, exc)
    
    def _daily_refresh(self):
        """
        Daily refresh of prayer times (called at midnight)
        """
        logger.info("Performing daily prayer times refresh")
        
        # Clear old cache
        self.prayer_api.clear_cache()
        
        # Schedule new day's prayers
        if not self.schedule_daily_prayers():
            logger.error("Failed to refresh daily prayer schedule")
        else:
            logger.info("Daily prayer schedule refreshed successfully")
    
    def start_scheduler(self):
        """
        Start the background scheduler thread
        """
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Schedule today's prayers first
        if not self.schedule_daily_prayers():
            logger.error("Failed to schedule initial prayers")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("Prayer scheduler started")
    
    def stop_scheduler(self):
        """
        Stop the background scheduler
        """
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=2)
        
        logger.info("Prayer scheduler stopped")
    
    def _run_scheduler(self):
        """
        Background scheduler loop
        """
        logger.info("Scheduler thread started")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(5)  # Wait before retrying
        
        logger.info("Scheduler thread stopped")
    
    def get_current_schedule(self) -> Dict[str, str]:
        """
        Get the current prayer schedule
        
        Returns:
            Dictionary of scheduled prayers and their times
        """
        return self.current_schedule.copy()

    def get_custom_audio_schedule(self) -> Dict[str, str]:
        """Get the fixed-time custom audio schedule."""
        return self.custom_audio_schedule.copy()

    def get_prayer_reminder_schedule(self) -> Dict[str, str]:
        """Get the prayer-relative reminder schedule."""
        return self.prayer_reminder_schedule.copy()
    
    def get_next_prayer_info(self) -> Optional[Dict]:
        """
        Get information about the next upcoming prayer
        
        Returns:
            Dictionary with next prayer information or None
        """
        if not self.current_schedule:
            return None
        
        try:
            now = datetime.now()
            next_prayer = None
            next_time = None
            
            for prayer_name in self.prayer_names:
                if prayer_name in self.current_schedule:
                    prayer_time_str = self.current_schedule[prayer_name]
                    time_parts = prayer_time_str.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1])
                    
                    prayer_datetime = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    
                    if prayer_datetime > now:
                        next_prayer = prayer_name
                        next_time = prayer_time_str
                        break
            
            if next_prayer:
                return {
                    'prayer': next_prayer,
                    'time': next_time,
                    'formatted': f"{next_prayer.title()} at {next_time}"
                }
            else:
                return {
                    'prayer': 'fajr',
                    'time': 'Tomorrow',
                    'formatted': 'Fajr tomorrow'
                }
                
        except Exception as e:
            logger.error(f"Error getting next prayer info: {e}")
            return None
    
    def force_refresh(self):
        """
        Force refresh of prayer times schedule
        """
        logger.info("Force refreshing prayer schedule")
        self._daily_refresh()
    
    def is_scheduler_running(self) -> bool:
        """
        Check if scheduler is currently running
        
        Returns:
            True if running, False otherwise
        """
        return self.is_running and self.scheduler_thread and self.scheduler_thread.is_alive()


# Example usage and testing
if __name__ == "__main__":
    def test_prayer_callback(prayer_name: str):
        """Test callback function"""
        print(f"🕌 PRAYER TIME: {prayer_name.upper()} - {datetime.now().strftime('%H:%M:%S')}")
    
    # Create scheduler
    scheduler = PrayerScheduler(test_prayer_callback)
    
    # Test scheduling
    print("Testing prayer scheduler...")
    
    if scheduler.schedule_daily_prayers():
        print("✅ Daily prayers scheduled successfully")
        print(f"Current schedule: {scheduler.get_current_schedule()}")
        
        next_prayer = scheduler.get_next_prayer_info()
        if next_prayer:
            print(f"Next prayer: {next_prayer['formatted']}")
    else:
        print("❌ Failed to schedule daily prayers")
    
    # Start scheduler for testing (uncomment to test)
    # scheduler.start_scheduler()
    # 
    # try:
    #     print("Scheduler running... Press Ctrl+C to stop")
    #     while True:
    #         time.sleep(1)
    # except KeyboardInterrupt:
    #     print("\nStopping scheduler...")
    #     scheduler.stop_scheduler()
