"""
Prayer Times API Integration Module
Handles fetching prayer times from Aladhan.com API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrayerTimesAPI:
    """Handles prayer time calculations and API integration"""
    
    def __init__(self):
        self.base_url = "https://api.aladhan.com/v1"
        self.default_method = 2  # ISNA - Islamic Society of North America
        self.cache = {}
        
    def get_coordinates_for_location(self, city: str, state: str, country: str) -> Tuple[float, float]:
        """
        Get coordinates for a given location
        For now, returns hardcoded coordinates for Raleigh, NC
        In a full implementation, this could use a geocoding service
        """
        # Hardcoded for user's location: Raleigh, NC
        if "raleigh" in city.lower() and "nc" in state.lower():
            return 35.7796, -78.6382
        
        # Default fallback coordinates (Raleigh, NC)
        return 35.7796, -78.6382
    
    def fetch_prayer_times(self, 
                          latitude: float, 
                          longitude: float, 
                          date: Optional[str] = None,
                          method: int = 2,
                          timezone: str = "America/New_York") -> Optional[Dict]:
        """
        Fetch prayer times from Aladhan API
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            date: Date in DD-MM-YYYY format (default: today)
            method: Calculation method (default: 2 - ISNA)
            timezone: Timezone string (default: America/New_York)
            
        Returns:
            Dictionary containing prayer times or None if failed
        """
        if date is None:
            date = datetime.now().strftime("%d-%m-%Y")
            
        # Check cache first
        cache_key = f"{latitude}_{longitude}_{date}_{method}"
        if cache_key in self.cache:
            logger.info(f"Returning cached prayer times for {date}")
            return self.cache[cache_key]
        
        url = f"{self.base_url}/timings/{date}"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'method': method,
            'timezone': timezone
        }
        
        try:
            logger.info(f"Fetching prayer times for {date} at coordinates ({latitude}, {longitude})")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('code') == 200 and 'data' in data:
                prayer_data = self._process_prayer_times(data['data'])
                
                # Cache the result
                self.cache[cache_key] = prayer_data
                
                logger.info("Successfully fetched and cached prayer times")
                return prayer_data
            else:
                logger.error(f"API returned error: {data}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching prayer times: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def _process_prayer_times(self, data: Dict) -> Dict:
        """
        Process raw API data into a clean format
        
        Args:
            data: Raw API response data
            
        Returns:
            Processed prayer times dictionary
        """
        timings = data.get('timings', {})
        date_info = data.get('date', {})
        
        # Extract the 5 main prayer times
        prayer_times = {
            'fajr': timings.get('Fajr', ''),
            'sunrise': timings.get('Sunrise', ''),
            'dhuhr': timings.get('Dhuhr', ''),
            'asr': timings.get('Asr', ''),
            'maghrib': timings.get('Maghrib', ''),
            'isha': timings.get('Isha', '')
        }
        
        # Clean up times (remove timezone info if present)
        for prayer, time_str in prayer_times.items():
            if '(' in time_str:
                prayer_times[prayer] = time_str.split('(')[0].strip()
        
        processed_data = {
            'prayer_times': prayer_times,
            'date': {
                'readable': date_info.get('readable', ''),
                'gregorian': date_info.get('gregorian', {}),
                'hijri': date_info.get('hijri', {})
            },
            'meta': data.get('meta', {}),
            'fetched_at': datetime.now().isoformat()
        }
        
        return processed_data
    
    def get_today_prayer_times(self, 
                              latitude: float, 
                              longitude: float, 
                              method: int = 2) -> Optional[Dict]:
        """
        Get today's prayer times
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            method: Calculation method
            
        Returns:
            Today's prayer times or None if failed
        """
        return self.fetch_prayer_times(latitude, longitude, method=method)
    
    def get_tomorrow_prayer_times(self, 
                                 latitude: float, 
                                 longitude: float, 
                                 method: int = 2) -> Optional[Dict]:
        """
        Get tomorrow's prayer times
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            method: Calculation method
            
        Returns:
            Tomorrow's prayer times or None if failed
        """
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%d-%m-%Y")
        return self.fetch_prayer_times(latitude, longitude, date=tomorrow, method=method)
    
    def get_prayer_times_range(self, 
                              latitude: float, 
                              longitude: float, 
                              days: int = 7,
                              method: int = 2) -> Dict[str, Dict]:
        """
        Get prayer times for multiple days
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            days: Number of days to fetch (default: 7)
            method: Calculation method
            
        Returns:
            Dictionary with dates as keys and prayer times as values
        """
        prayer_times_range = {}
        
        for i in range(days):
            target_date = datetime.now() + timedelta(days=i)
            date_str = target_date.strftime("%d-%m-%Y")
            
            prayer_data = self.fetch_prayer_times(
                latitude, longitude, date=date_str, method=method
            )
            
            if prayer_data:
                prayer_times_range[date_str] = prayer_data
            
        return prayer_times_range
    
    def convert_to_datetime_objects(self, 
                                   prayer_times: Dict[str, str], 
                                   date: Optional[datetime] = None) -> Dict[str, datetime]:
        """
        Convert prayer time strings to datetime objects
        
        Args:
            prayer_times: Dictionary of prayer names and time strings
            date: Base date (default: today)
            
        Returns:
            Dictionary of prayer names and datetime objects
        """
        if date is None:
            date = datetime.now().date()
        
        timezone = pytz.timezone("America/New_York")
        datetime_objects = {}
        
        for prayer, time_str in prayer_times.items():
            try:
                # Parse time string (format: HH:MM)
                time_parts = time_str.split(':')
                hour = int(time_parts[0])
                minute = int(time_parts[1])
                
                # Create datetime object
                prayer_datetime = datetime.combine(date, datetime.min.time().replace(hour=hour, minute=minute))
                
                # Apply timezone
                prayer_datetime = timezone.localize(prayer_datetime)
                
                datetime_objects[prayer] = prayer_datetime
                
            except (ValueError, IndexError) as e:
                logger.error(f"Error parsing time for {prayer}: {time_str} - {e}")
                continue
        
        return datetime_objects
    
    def get_next_prayer(self, prayer_times: Dict[str, str]) -> Tuple[str, str]:
        """
        Get the next upcoming prayer time
        
        Args:
            prayer_times: Dictionary of prayer times
            
        Returns:
            Tuple of (prayer_name, prayer_time)
        """
        now = datetime.now()
        today_prayers = self.convert_to_datetime_objects(prayer_times)
        
        # Find next prayer
        for prayer in ['fajr', 'dhuhr', 'asr', 'maghrib', 'isha']:
            if prayer in today_prayers:
                prayer_datetime = today_prayers[prayer]
                # Convert to naive datetime for comparison
                if prayer_datetime.tzinfo is not None:
                    prayer_datetime = prayer_datetime.replace(tzinfo=None)
                
                if prayer_datetime > now:
                    return prayer, prayer_times[prayer]
        
        # If no more prayers today, return tomorrow's Fajr
        return 'fajr', 'Tomorrow'
    
    def clear_cache(self):
        """Clear the prayer times cache"""
        self.cache.clear()
        logger.info("Prayer times cache cleared")


# Example usage and testing
if __name__ == "__main__":
    # Test the prayer times API
    api = PrayerTimesAPI()
    
    # Test coordinates for Raleigh, NC
    lat, lon = 35.7796, -78.6382
    
    # Fetch today's prayer times
    today_times = api.get_today_prayer_times(lat, lon)
    
    if today_times:
        print("Today's Prayer Times:")
        print(json.dumps(today_times, indent=2))
        
        # Get next prayer
        prayer_times = today_times['prayer_times']
        next_prayer, next_time = api.get_next_prayer(prayer_times)
        print(f"\nNext Prayer: {next_prayer.title()} at {next_time}")
    else:
        print("Failed to fetch prayer times")
