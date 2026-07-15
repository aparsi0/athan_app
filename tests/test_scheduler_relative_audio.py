from datetime import datetime

from core.scheduler import PrayerScheduler


class FixedPrayerTimesAPI:
    def get_today_prayer_times(self, latitude, longitude, method):
        return {
            "prayer_times": {
                "fajr": "05:15",
                "sunrise": "06:42",
                "dhuhr": "13:08",
                "asr": "16:47",
                "maghrib": "19:51",
                "isha": "21:04",
            }
        }

    def clear_cache(self):
        pass


def _callback(_name: str):
    pass


def test_schedule_daily_prayers_keeps_sunrise_for_relative_events(monkeypatch):
    scheduler = PrayerScheduler(_callback)
    scheduler.prayer_api = FixedPrayerTimesAPI()
    scheduler.set_custom_audio_relative_schedule("morning_audio", "sunrise", -30, True)

    class MorningTime(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 4, 30, 5, 0, 0)

    monkeypatch.setattr("core.scheduler.datetime", MorningTime)

    assert scheduler.schedule_daily_prayers() is True
    assert scheduler.get_current_schedule()["sunrise"] == "06:42"
    assert scheduler.get_custom_audio_schedule()["morning_audio"] == "06:12"


def test_schedule_daily_prayers_skips_past_sunrise_relative_event(monkeypatch):
    scheduler = PrayerScheduler(_callback)
    scheduler.prayer_api = FixedPrayerTimesAPI()
    scheduler.set_custom_audio_relative_schedule("morning_audio", "sunrise", -30, True)

    class LateMorning(datetime):
        @classmethod
        def now(cls):
            return cls(2026, 4, 30, 6, 30, 0)

    monkeypatch.setattr("core.scheduler.datetime", LateMorning)

    assert scheduler.schedule_daily_prayers() is True
    assert scheduler.get_current_schedule()["sunrise"] == "06:42"
    assert "morning_audio" not in scheduler.get_custom_audio_schedule()
