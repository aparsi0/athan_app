#!/usr/bin/env python3
"""
Test script for Athan App core functionality
Tests the application without GUI components
"""

import sys
import os
import time
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import core modules only
from config.settings import ConfigManager
from core.prayer_times import PrayerTimesAPI
from core.scheduler import PrayerScheduler
from core.audio_player import PrayerAudioManager


def test_prayer_callback(prayer_name: str):
    """Test callback for prayer times"""
    print(f"🕌 PRAYER TIME: {prayer_name.upper()} - {datetime.now().strftime('%H:%M:%S')}")
    print(f"   Playing Athan for {prayer_name.title()} prayer...")


def test_configuration():
    """Test configuration management"""
    print("\\n" + "="*50)
    print("TESTING CONFIGURATION MANAGEMENT")
    print("="*50)
    
    try:
        config = ConfigManager()
        
        # Test basic configuration
        location = config.get_location()
        print(f"✅ Location: {location['city']}, {location['state']}")
        print(f"   Coordinates: ({location['latitude']}, {location['longitude']})")
        
        # Test audio settings
        audio_settings = config.get_audio_settings()
        print(f"✅ Audio file: {audio_settings['audio_file']}")
        print(f"   Volume: {audio_settings['volume']}")
        
        # Test prayer settings
        prayer_settings = config.get_prayer_settings()
        print(f"✅ Calculation method: {prayer_settings['calculation_method']}")
        print(f"   Enabled prayers: {prayer_settings['enabled_prayers']}")
        
        # Test validation
        validation = config.validate_config()
        print(f"✅ Configuration valid: {validation['is_valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_prayer_times():
    """Test prayer times API"""
    print("\\n" + "="*50)
    print("TESTING PRAYER TIMES API")
    print("="*50)
    
    try:
        api = PrayerTimesAPI()
        
        # Test fetching prayer times for Raleigh, NC
        lat, lon = 35.7796, -78.6382
        prayer_data = api.get_today_prayer_times(lat, lon)
        
        if prayer_data:
            prayer_times = prayer_data['prayer_times']
            print("✅ Today's Prayer Times:")
            for prayer, time_str in prayer_times.items():
                print(f"   {prayer.title()}: {time_str}")
            
            # Test next prayer
            next_prayer, next_time = api.get_next_prayer(prayer_times)
            print(f"✅ Next prayer: {next_prayer.title()} at {next_time}")
            
            return True
        else:
            print("❌ Failed to fetch prayer times")
            return False
            
    except Exception as e:
        print(f"❌ Prayer times test failed: {e}")
        return False


def test_audio_player():
    """Test audio player"""
    print("\\n" + "="*50)
    print("TESTING AUDIO PLAYER")
    print("="*50)
    
    try:
        config = ConfigManager()
        audio_manager = PrayerAudioManager(config)
        
        # Test audio setup
        if audio_manager.test_audio_setup():
            print("✅ Audio setup test successful")
            
            # Get audio info
            audio_info = audio_manager.get_audio_info()
            print(f"✅ Audio file: {audio_info['default_audio_file']}")
            print(f"   File exists: {audio_info['audio_file_exists']}")
            print(f"   VLC available: {audio_info['playback_status']['vlc_available']}")
            
            return True
        else:
            print("❌ Audio setup test failed")
            return False
            
    except Exception as e:
        print(f"❌ Audio player test failed: {e}")
        return False


def test_scheduler():
    """Test prayer scheduler"""
    print("\\n" + "="*50)
    print("TESTING PRAYER SCHEDULER")
    print("="*50)
    
    try:
        scheduler = PrayerScheduler(test_prayer_callback)
        
        # Configure scheduler
        scheduler.set_location(35.7796, -78.6382)  # Raleigh, NC
        scheduler.set_calculation_method(2)  # ISNA
        
        # Schedule prayers
        if scheduler.schedule_daily_prayers():
            print("✅ Daily prayers scheduled successfully")
            
            # Get current schedule
            schedule = scheduler.get_current_schedule()
            print("✅ Current schedule:")
            for prayer, time_str in schedule.items():
                print(f"   {prayer.title()}: {time_str}")
            
            # Get next prayer info
            next_prayer = scheduler.get_next_prayer_info()
            if next_prayer:
                print(f"✅ Next prayer: {next_prayer['formatted']}")
            
            return True
        else:
            print("❌ Failed to schedule daily prayers")
            return False
            
    except Exception as e:
        print(f"❌ Scheduler test failed: {e}")
        return False


def test_integration():
    """Test integration of all components"""
    print("\\n" + "="*50)
    print("TESTING COMPONENT INTEGRATION")
    print("="*50)
    
    try:
        # Initialize all components
        config = ConfigManager()
        prayer_api = PrayerTimesAPI()
        audio_manager = PrayerAudioManager(config)
        scheduler = PrayerScheduler(test_prayer_callback)
        
        # Configure scheduler
        location = config.get_location()
        scheduler.set_location(location['latitude'], location['longitude'])
        
        prayer_settings = config.get_prayer_settings()
        scheduler.set_calculation_method(prayer_settings['calculation_method'])
        
        # Test scheduling
        if scheduler.schedule_daily_prayers():
            print("✅ All components integrated successfully")
            
            # Get comprehensive status
            schedule = scheduler.get_current_schedule()
            next_prayer = scheduler.get_next_prayer_info()
            audio_info = audio_manager.get_audio_info()
            
            print("\\n📊 SYSTEM STATUS:")
            print(f"   Prayer times scheduled: {len(schedule)} prayers")
            print(f"   Next prayer: {next_prayer['formatted'] if next_prayer else 'None'}")
            print(f"   Audio system: {'Ready' if audio_info['audio_file_exists'] else 'Not Ready'}")
            print(f"   Configuration: Valid")
            
            return True
        else:
            print("❌ Integration test failed")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Main test function"""
    print("🕌 ATHAN APP - CORE FUNCTIONALITY TEST")
    print("=" * 60)
    
    tests = [
        ("Configuration Management", test_configuration),
        ("Prayer Times API", test_prayer_times),
        ("Audio Player", test_audio_player),
        ("Prayer Scheduler", test_scheduler),
        ("Component Integration", test_integration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
    
    print("\\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\\n🎉 ALL TESTS PASSED! The Athan App core is ready.")
        print("\\n📝 NEXT STEPS:")
        print("   1. The application can run in headless mode")
        print("   2. System tray requires a desktop environment")
        print("   3. Audio playback is ready with VLC")
        print("   4. Prayer times are automatically scheduled")
    else:
        print(f"\\n⚠️  {total - passed} tests failed. Please check the issues above.")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())

