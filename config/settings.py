"""
Configuration Management Module
Handles application settings and user preferences
"""

import json
import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path
from utils.app_paths import ensure_runtime_dirs, get_config_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration and user settings"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Custom configuration directory path
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = get_config_dir()
        
        self.config_file = self.config_dir / 'config.json'
        ensure_runtime_dirs()
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configuration
        self.default_config = {
            'location': {
                'auto_detect': True,
                'latitude': 35.7796,
                'longitude': -78.6382,
                'city': 'Raleigh',
                'state': 'NC',
                'country': 'USA',
                'timezone': 'America/New_York',
                'location_source': 'default',
                'location_provider': '',
                'last_detected_at': ''
            },
            'prayer_settings': {
                'calculation_method': 2,  # ISNA
                'enabled_prayers': {
                    'fajr': True,
                    'dhuhr': True,
                    'asr': True,
                    'maghrib': True,
                    'isha': True
                }
            },
            'audio_settings': {
                'volume': 0.8,
                'athan_volume': 0.8,
                'audio_file': 'assets/audio/Azansoundtrack.m4a',
                'athan_files': {
                    'fajr': 'assets/audio/fajr_athan.m4a',
                    'dhuhr': 'assets/audio/dhuhr_athan.m4a',
                    'asr': 'assets/audio/asr_athan.m4a',
                    'maghrib': 'assets/audio/maghrib_athan.m4a',
                    'isha': 'assets/audio/isha_athan.m4a'
                },
                'use_custom_audio': True,
                'audio_format': 'm4a'
            },
            'special_audio_settings': {
                'friday_before_dhuhr': {
                    'enabled': True,
                    'reference_time': 'dhuhr',
                    'offset_minutes': -60,
                    'weekday': 4,
                    'audio_file': 'assets/audio/Surat_AlKahf.m4a',
                    'volume': 0.8
                },
                'after_prayer_duaa': {
                    'enabled': True,
                    'audio_file': 'assets/audio/Duaa.m4a',
                    'volume': 0.7
                },
                'pre_prayer_woduaa': {
                    'enabled': True,
                    'lead_minutes': 15,
                    'audio_file': 'assets/audio/Woduaa.m4a',
                    'volume': 1.0
                },
                'morning_audio': {
                    'enabled': True,
                    'reference_time': 'dhuhr',
                    'offset_minutes': -180,
                    'audio_file': 'assets/audio/morning_audio.m4a',
                    'volume': 0.8
                },
                'night_audio': {
                    'enabled': True,
                    'reference_time': 'asr',
                    'offset_minutes': 30,
                    'audio_file': 'assets/audio/night_audio.m4a',
                    'volume': 0.8
                }
            },
            'ui_settings': {
                'show_notifications': True,
                'minimize_to_tray': True,
                'start_with_system': False,
                'show_prayer_names_in_english': True
            },
            'advanced_settings': {
                'api_timeout': 10,
                'cache_duration_hours': 24,
                'retry_attempts': 3,
                'log_level': 'INFO'
            }
        }
        
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file
        
        Returns:
            Configuration dictionary
        """
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                config = self._merge_configs(self.default_config, loaded_config)
                logger.info("Configuration loaded successfully")
                return config
            else:
                logger.info("No existing config found, using defaults")
                return self.default_config.copy()
                
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error loading config: {e}")
            logger.info("Using default configuration")
            return self.default_config.copy()
    
    def save_config(self) -> bool:
        """
        Save current configuration to file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info("Configuration saved successfully")
            return True
            
        except IOError as e:
            logger.error(f"Error saving config: {e}")
            return False
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """
        Merge loaded config with defaults to ensure all keys exist
        
        Args:
            default: Default configuration
            loaded: Loaded configuration
            
        Returns:
            Merged configuration
        """
        merged = default.copy()
        
        for key, value in loaded.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        
        Args:
            key_path: Dot-separated key path (e.g., 'location.latitude')
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            keys = key_path.split('.')
            value = self.config
            
            for key in keys:
                value = value[key]
            
            return value
            
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any) -> bool:
        """
        Set configuration value using dot notation
        
        Args:
            key_path: Dot-separated key path
            value: Value to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            keys = key_path.split('.')
            target = self.config
            
            # Navigate to parent of target key
            for key in keys[:-1]:
                if key not in target:
                    target[key] = {}
                target = target[key]
            
            # Set the value
            target[keys[-1]] = value
            
            logger.info(f"Config updated: {key_path} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting config {key_path}: {e}")
            return False
    
    def get_location(self) -> Dict[str, Any]:
        """Get location settings"""
        return self.config.get('location', {})
    
    def set_location(self, latitude: float, longitude: float,
                    city: str = '', state: str = '', country: str = '',
                    timezone: str = '', auto_detect: Optional[bool] = None,
                    location_source: str = '', location_provider: str = '',
                    last_detected_at: str = '') -> bool:
        """
        Set location settings
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            city: City name
            state: State/province
            country: Country name
            
        Returns:
            True if successful
        """
        location_data = {
            'latitude': latitude,
            'longitude': longitude,
            'city': city,
            'state': state,
            'country': country
        }

        if timezone:
            location_data['timezone'] = timezone
        if auto_detect is not None:
            location_data['auto_detect'] = auto_detect
        if location_source:
            location_data['location_source'] = location_source
        if location_provider:
            location_data['location_provider'] = location_provider
        if last_detected_at:
            location_data['last_detected_at'] = last_detected_at
        
        for key, value in location_data.items():
            if not self.set(f'location.{key}', value):
                return False
        
        return True
    
    def get_prayer_settings(self) -> Dict[str, Any]:
        """Get prayer settings"""
        return self.config.get('prayer_settings', {})
    
    def set_calculation_method(self, method: int) -> bool:
        """Set prayer calculation method"""
        return self.set('prayer_settings.calculation_method', method)
    
    def enable_prayer(self, prayer_name: str, enabled: bool = True) -> bool:
        """Enable or disable a prayer"""
        return self.set(f'prayer_settings.enabled_prayers.{prayer_name}', enabled)
    
    def get_audio_settings(self) -> Dict[str, Any]:
        """Get audio settings"""
        return self.config.get('audio_settings', {})

    def get_special_audio_settings(self) -> Dict[str, Any]:
        """Get special audio scheduling settings"""
        return self.config.get('special_audio_settings', {})
    
    def set_audio_file(self, file_path: str) -> bool:
        """Set custom audio file path"""
        return self.set('audio_settings.audio_file', file_path)
    
    def set_volume(self, volume: float) -> bool:
        """Set audio volume (0.0 to 1.0)"""
        volume = max(0.0, min(1.0, volume))  # Clamp between 0 and 1
        return self.set('audio_settings.volume', volume)
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI settings"""
        return self.config.get('ui_settings', {})

    def should_auto_detect_location(self) -> bool:
        """Return whether location auto-detection is enabled."""
        return bool(self.get('location.auto_detect', True))
    
    def set_start_with_system(self, enabled: bool) -> bool:
        """Set whether to start with system"""
        return self.set('ui_settings.start_with_system', enabled)
    
    def set_minimize_to_tray(self, enabled: bool) -> bool:
        """Set whether to minimize to system tray"""
        return self.set('ui_settings.minimize_to_tray', enabled)
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults
        
        Returns:
            True if successful
        """
        try:
            self.config = self.default_config.copy()
            logger.info("Configuration reset to defaults")
            return True
        except Exception as e:
            logger.error(f"Error resetting config: {e}")
            return False
    
    def export_config(self, file_path: str) -> bool:
        """
        Export configuration to a file
        
        Args:
            file_path: Path to export file
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {file_path}")
            return True
            
        except IOError as e:
            logger.error(f"Error exporting config: {e}")
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        Import configuration from a file
        
        Args:
            file_path: Path to import file
            
        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
            
            self.config = self._merge_configs(self.default_config, imported_config)
            logger.info(f"Configuration imported from {file_path}")
            return True
            
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"Error importing config: {e}")
            return False
    
    def get_config_file_path(self) -> str:
        """Get the configuration file path"""
        return str(self.config_file)
    
    def validate_config(self) -> Dict[str, list]:
        """
        Validate current configuration
        
        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []
        
        # Validate location
        location = self.get_location()
        lat = location.get('latitude')
        lon = location.get('longitude')
        
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            errors.append("Invalid latitude value")
        
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            errors.append("Invalid longitude value")
        
        # Validate prayer settings
        method = self.get('prayer_settings.calculation_method')
        if not isinstance(method, int) or not (0 <= method <= 23):
            errors.append("Invalid calculation method")
        
        # Validate audio settings
        volume = self.get('audio_settings.volume')
        if not isinstance(volume, (int, float)) or not (0.0 <= volume <= 1.0):
            warnings.append("Volume should be between 0.0 and 1.0")
        
        audio_file = self.get('audio_settings.audio_file')
        if audio_file and not os.path.exists(audio_file):
            warnings.append(f"Audio file not found: {audio_file}")
        
        return {
            'errors': errors,
            'warnings': warnings,
            'is_valid': len(errors) == 0
        }


# Example usage and testing
if __name__ == "__main__":
    # Test configuration manager
    config = ConfigManager()
    
    print("Testing Configuration Manager...")
    
    # Test getting values
    print(f"Location: {config.get_location()}")
    print(f"Prayer method: {config.get('prayer_settings.calculation_method')}")
    print(f"Volume: {config.get('audio_settings.volume')}")
    
    # Test setting values
    config.set_volume(0.9)
    config.set_calculation_method(3)
    config.enable_prayer('fajr', False)
    
    # Test validation
    validation = config.validate_config()
    print(f"Config validation: {validation}")
    
    # Test save/load
    if config.save_config():
        print("✅ Configuration saved successfully")
    else:
        print("❌ Failed to save configuration")
    
    print(f"Config file location: {config.get_config_file_path()}")
