"""
Audio Player Module
Handles audio playback for Athan/Azan calls
"""

import vlc
import os
import threading
import time
from typing import Optional, Callable
import logging
from pathlib import Path
from utils.app_paths import get_audio_search_dirs, get_bundle_root, get_config_dir

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioPlayer:
    """Handles audio playback for prayer calls"""
    
    def __init__(self):
        """Initialize the audio player"""
        self.vlc_instance = None
        self.media_player = None
        self.current_audio_file = None
        self.volume = 0.8  # Default volume (0.0 to 1.0)
        self.is_playing = False
        self.playback_thread = None
        
        # Callbacks
        self.on_playback_finished = None
        
        # Initialize VLC
        self._initialize_vlc()
    
    def _initialize_vlc(self):
        """Initialize VLC media player"""
        try:
            # Create VLC instance with minimal options for headless operation
            vlc_args = [
                '--intf', 'dummy',  # No interface
                '--no-video',       # Audio only
                '--quiet',          # Reduce verbosity
                '--no-osd'          # No on-screen display
            ]
            
            self.vlc_instance = vlc.Instance(vlc_args)
            self.media_player = self.vlc_instance.media_player_new()
            
            # Set up event callbacks
            event_manager = self.media_player.event_manager()
            event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._on_end_reached)
            event_manager.event_attach(vlc.EventType.MediaPlayerEncounteredError, self._on_error)
            
            logger.info("VLC audio player initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize VLC: {e}")
            self.vlc_instance = None
            self.media_player = None
    
    def _on_end_reached(self, event):
        """Callback when playback ends"""
        logger.info("Audio playback finished")
        self.is_playing = False
        
        if self.on_playback_finished:
            try:
                self.on_playback_finished()
            except Exception as e:
                logger.error(f"Error in playback finished callback: {e}")
    
    def _on_error(self, event):
        """Callback when playback error occurs"""
        logger.error("Audio playback error occurred")
        self.is_playing = False
    
    def set_audio_file(self, file_path: str) -> bool:
        """
        Set the audio file to be played
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Audio file not found: {file_path}")
                return False
            
            self.current_audio_file = file_path
            logger.info(f"Audio file set to: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting audio file: {e}")
            return False
    
    def set_volume(self, volume: float) -> bool:
        """
        Set playback volume
        
        Args:
            volume: Volume level (0.0 to 1.0)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Clamp volume between 0 and 1
            volume = max(0.0, min(1.0, volume))
            self.volume = volume
            
            if self.media_player:
                # VLC volume is 0-100
                vlc_volume = int(volume * 100)
                self.media_player.audio_set_volume(vlc_volume)
                logger.info(f"Volume set to {volume:.1f} ({vlc_volume}%)")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
            return False
    
    def play_audio(self, file_path: Optional[str] = None, volume: Optional[float] = None) -> bool:
        """
        Play audio file
        
        Args:
            file_path: Optional path to audio file (uses current if not provided)
            
        Returns:
            True if playback started successfully, False otherwise
        """
        try:
            if not self.vlc_instance or not self.media_player:
                logger.error("VLC not initialized")
                return False
            
            # Use provided file or current file
            audio_file = file_path or self.current_audio_file
            
            if not audio_file or not os.path.exists(audio_file):
                logger.error(f"Audio file not found: {audio_file}")
                return False
            
            # Stop any current playback
            if self.is_playing:
                self.stop_audio()
            
            # Create media and set to player
            media = self.vlc_instance.media_new(audio_file)
            self.media_player.set_media(media)
            
            # Set volume
            playback_volume = self.volume if volume is None else volume
            self.set_volume(playback_volume)
            
            # Start playback
            result = self.media_player.play()
            
            if result == 0:  # Success
                self.is_playing = True
                logger.info(f"Started playing: {os.path.basename(audio_file)}")
                return True
            else:
                logger.error(f"Failed to start playback: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Error playing audio: {e}")
            return False
    
    def stop_audio(self) -> bool:
        """
        Stop audio playback
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.media_player and self.is_playing:
                self.media_player.stop()
                self.is_playing = False
                logger.info("Audio playback stopped")
                return True
            
            return True  # Already stopped
            
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
            return False
    
    def pause_audio(self) -> bool:
        """
        Pause audio playback
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.media_player and self.is_playing:
                self.media_player.pause()
                logger.info("Audio playback paused")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error pausing audio: {e}")
            return False
    
    def resume_audio(self) -> bool:
        """
        Resume audio playback
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.media_player:
                self.media_player.play()
                self.is_playing = True
                logger.info("Audio playback resumed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error resuming audio: {e}")
            return False
    
    def get_playback_status(self) -> dict:
        """
        Get current playback status
        
        Returns:
            Dictionary with playback information
        """
        try:
            status = {
                'is_playing': self.is_playing,
                'current_file': self.current_audio_file,
                'volume': self.volume,
                'vlc_available': self.vlc_instance is not None
            }
            
            if self.media_player and self.is_playing:
                status['position'] = self.media_player.get_position()
                status['time'] = self.media_player.get_time()
                status['length'] = self.media_player.get_length()
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting playback status: {e}")
            return {'error': str(e)}
    
    def set_playback_finished_callback(self, callback: Callable):
        """
        Set callback function to be called when playback finishes
        
        Args:
            callback: Function to call when playback ends
        """
        self.on_playback_finished = callback
    
    def test_audio_file(self, file_path: str) -> bool:
        """
        Test if an audio file can be played
        
        Args:
            file_path: Path to audio file to test
            
        Returns:
            True if file can be played, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                logger.error(f"Test file not found: {file_path}")
                return False
            
            if not self.vlc_instance:
                logger.error("VLC not available for testing")
                return False
            
            # Try to create media object
            media = self.vlc_instance.media_new(file_path)
            if media:
                logger.info(f"Audio file test successful: {file_path}")
                return True
            else:
                logger.error(f"Failed to create media for: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Error testing audio file: {e}")
            return False
    
    def cleanup(self):
        """Clean up resources"""
        try:
            if self.is_playing:
                self.stop_audio()
            
            if self.media_player:
                self.media_player.release()
            
            if self.vlc_instance:
                self.vlc_instance.release()
            
            logger.info("Audio player cleaned up")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


class PrayerAudioManager:
    """High-level manager for prayer audio playback"""
    
    def __init__(self, config_manager=None):
        """
        Initialize prayer audio manager
        
        Args:
            config_manager: Configuration manager instance
        """
        self.audio_player = AudioPlayer()
        self.config_manager = config_manager
        self.default_audio_file = None
        self.prayer_audio_files = {}
        self.special_audio_files = {}
        self.special_audio_settings = {}
        self.pending_audio_queue = []
        self.queue_lock = threading.Lock()
        self.queue_monitor_thread = None
        self.queue_monitor_generation = 0

        self.audio_player.set_playback_finished_callback(self._on_playback_finished)
        
        # Load audio settings from config
        if config_manager:
            self._load_audio_settings()
    
    def _load_audio_settings(self):
        """Load audio settings from configuration"""
        try:
            audio_settings = self.config_manager.get_audio_settings()
            self.special_audio_settings = self.config_manager.get_special_audio_settings()
            
            # Set volume
            volume = audio_settings.get('volume', 0.8)
            self.audio_player.set_volume(volume)
            
            # Set default audio file
            audio_file = audio_settings.get('audio_file')
            if audio_file:
                audio_file = self._resolve_audio_file_path(audio_file)
                if os.path.exists(audio_file):
                    self.default_audio_file = audio_file
                    self.audio_player.set_audio_file(audio_file)
                    logger.info(f"Loaded default audio file: {audio_file}")
                else:
                    logger.warning(f"Configured audio file not found: {audio_file}")

            configured_prayer_audio = audio_settings.get('athan_files', {})
            for prayer_name, prayer_audio_path in configured_prayer_audio.items():
                resolved_path = self._resolve_audio_file_path(prayer_audio_path) if prayer_audio_path else ''
                if resolved_path and os.path.exists(resolved_path):
                    self.prayer_audio_files[prayer_name] = resolved_path
                    logger.info("Loaded prayer-specific Athan for %s: %s", prayer_name, resolved_path)
                elif prayer_audio_path:
                    logger.warning(
                        "Configured prayer-specific Athan file not found for %s: %s",
                        prayer_name,
                        prayer_audio_path,
                    )

            for event_name, event_settings in self.special_audio_settings.items():
                configured_path = event_settings.get('audio_file', '')
                resolved_path = self._resolve_audio_file_path(configured_path) if configured_path else ''
                if resolved_path and os.path.exists(resolved_path):
                    self.special_audio_files[event_name] = resolved_path
                    logger.info("Loaded special audio for %s: %s", event_name, resolved_path)
                elif configured_path:
                    logger.warning(
                        "Configured special audio file not found for %s: %s",
                        event_name,
                        configured_path,
                    )
            
        except Exception as e:
            logger.error(f"Error loading audio settings: {e}")

    def _resolve_audio_file_path(self, file_path: str) -> str:
        """Resolve configured file paths and stem-only names into repository audio files."""
        if not file_path:
            return ''

        if os.path.isabs(file_path):
            return file_path

        filename = os.path.basename(file_path)
        stem, ext = os.path.splitext(filename)
        relative_path = Path(file_path)

        # First try the configured relative path against supported roots.
        candidate_roots = [get_config_dir(), get_bundle_root()]
        for root in candidate_roots:
            candidate = root / relative_path
            if candidate.exists():
                return str(candidate)

        # Then try matching by filename or filename stem inside known audio dirs.
        for audio_dir in get_audio_search_dirs():
            if audio_dir.is_dir():
                for entry in audio_dir.iterdir():
                    if not entry.is_file():
                        continue
                    entry_stem, _ = os.path.splitext(entry.name)
                    if entry.name == filename or entry_stem == filename or entry_stem == stem:
                        return str(entry)

        # Fall back to the primary user-config path for future writes or clearer logging.
        return str(get_config_dir() / relative_path)

    def _on_playback_finished(self):
        """Continue any queued audio after the current track finishes."""
        with self.queue_lock:
            if not self.pending_audio_queue:
                return

            next_item = self.pending_audio_queue.pop(0)

        next_file = next_item['file_path']
        next_volume = next_item.get('volume')

        if os.path.exists(next_file):
            logger.info("Queueing next audio start: %s", os.path.basename(next_file))
            threading.Thread(
                target=self._play_queued_audio,
                args=(next_file, next_volume),
                daemon=True,
            ).start()
        else:
            logger.warning("Queued audio file no longer exists: %s", next_file)
            self._on_playback_finished()

    def _play_queued_audio(self, next_file: str, volume: Optional[float]):
        """Start the next queued audio with a short delay after VLC end callbacks."""
        time.sleep(0.5)
        logger.info("Starting queued audio: %s", os.path.basename(next_file))
        started = self.audio_player.play_audio(next_file, volume=volume)
        if started:
            logger.info("Queued audio started successfully: %s", os.path.basename(next_file))
        else:
            logger.error("Queued audio failed to start: %s", os.path.basename(next_file))

    def _queue_audio_files(self, file_specs):
        """Append existing files to the playback queue."""
        with self.queue_lock:
            for file_spec in file_specs:
                if isinstance(file_spec, dict):
                    file_path = file_spec.get('file_path')
                    volume = file_spec.get('volume')
                else:
                    file_path = file_spec
                    volume = None

                if file_path and os.path.exists(file_path):
                    self.pending_audio_queue.append({
                        'file_path': file_path,
                        'volume': volume,
                    })

    def _start_queue_monitor(self):
        """Start a fallback monitor in case VLC end callbacks are missed."""
        with self.queue_lock:
            self.queue_monitor_generation += 1
            generation = self.queue_monitor_generation

        def monitor():
            # Give VLC a brief moment to transition into active playback.
            time.sleep(1)
            idle_polls = 0

            while True:
                with self.queue_lock:
                    if generation != self.queue_monitor_generation:
                        return
                    has_pending = bool(self.pending_audio_queue)

                if not has_pending:
                    return

                if self.audio_player.is_playing:
                    idle_polls = 0
                else:
                    idle_polls += 1
                    # Require a few consecutive idle polls before advancing.
                    if idle_polls >= 3:
                        logger.info("Queue monitor advancing to next queued audio")
                        self._on_playback_finished()
                        return

                time.sleep(1)

        self.queue_monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.queue_monitor_thread.start()

    def _get_special_audio_file(self, event_name: str) -> Optional[str]:
        """Return a special audio file if configured and available."""
        file_path = self.special_audio_files.get(event_name)
        if file_path and os.path.exists(file_path):
            return file_path
        return None

    def _get_prayer_audio_file(self, prayer_name: str) -> Optional[str]:
        """Return a prayer-specific Athan file, falling back to the default Athan."""
        prayer_specific = self.prayer_audio_files.get(prayer_name)
        if prayer_specific and os.path.exists(prayer_specific):
            return prayer_specific
        return self.default_audio_file

    def _get_special_audio_volume(self, event_name: str, default: float) -> float:
        """Return the configured volume for a named special audio event."""
        event_settings = self.special_audio_settings.get(event_name, {})
        volume = event_settings.get('volume', default)
        try:
            return max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            return default

    def _get_athan_volume(self) -> float:
        """Return the configured Athan volume."""
        audio_settings = self.config_manager.get_audio_settings() if self.config_manager else {}
        volume = audio_settings.get('athan_volume', audio_settings.get('volume', 0.8))
        try:
            return max(0.0, min(1.0, float(volume)))
        except (TypeError, ValueError):
            return 0.8
    
    def play_prayer_call(self, prayer_name: str, follow_up_keys=None) -> bool:
        """
        Play prayer call audio
        
        Args:
            prayer_name: Name of the prayer
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"🕌 Playing {prayer_name.title()} call")
            
            audio_file = self._get_prayer_audio_file(prayer_name)
            if not audio_file:
                logger.error("No audio file configured")
                return False

            with self.queue_lock:
                self.pending_audio_queue = []
            after_prayer_settings = self.special_audio_settings.get('after_prayer_duaa', {})
            if after_prayer_settings.get('enabled', False):
                queued_after_prayer = self._get_special_audio_file('after_prayer_duaa')
                self._queue_audio_files([{
                    'file_path': queued_after_prayer,
                    'volume': self._get_special_audio_volume('after_prayer_duaa', 1.0),
                }])
            if follow_up_keys:
                queued_files = [{
                    'file_path': self._get_special_audio_file(key),
                    'volume': self._get_special_audio_volume(key, 0.8),
                } for key in follow_up_keys]
                self._queue_audio_files(queued_files)

            started = self.audio_player.play_audio(audio_file, volume=self._get_athan_volume())
            if started:
                with self.queue_lock:
                    has_pending = bool(self.pending_audio_queue)
                if has_pending:
                    self._start_queue_monitor()
            return started
            
        except Exception as e:
            logger.error(f"Error playing prayer call: {e}")
            return False
    
    def stop_prayer_call(self) -> bool:
        """Stop current prayer call"""
        return self.audio_player.stop_audio()
    
    def test_audio_setup(self) -> bool:
        """
        Test the audio setup
        
        Returns:
            True if audio setup is working, False otherwise
        """
        try:
            if not self.default_audio_file:
                logger.error("No audio file configured for testing")
                return False
            
            return self.audio_player.test_audio_file(self.default_audio_file)
            
        except Exception as e:
            logger.error(f"Error testing audio setup: {e}")
            return False

    def play_test_audio(self, prayer_name: str = 'dhuhr') -> bool:
        """Play a short manual preview using a prayer Athan file without follow-up audio."""
        try:
            audio_file = self._get_prayer_audio_file(prayer_name)
            if not audio_file:
                logger.error("No audio file configured for test playback")
                return False

            with self.queue_lock:
                self.pending_audio_queue = []

            logger.info("Playing test audio using %s", os.path.basename(audio_file))
            return self.audio_player.play_audio(audio_file, volume=self._get_athan_volume())
        except Exception as e:
            logger.error(f"Error playing test audio: {e}")
            return False
    
    def get_audio_info(self) -> dict:
        """Get information about current audio setup"""
        return {
            'default_audio_file': self.default_audio_file,
            'prayer_audio_files': self.prayer_audio_files.copy(),
            'special_audio_files': self.special_audio_files.copy(),
            'playback_status': self.audio_player.get_playback_status(),
            'audio_file_exists': os.path.exists(self.default_audio_file) if self.default_audio_file else False
        }

    def play_named_audio(self, event_name: str) -> bool:
        """Play a configured non-prayer audio file immediately."""
        try:
            file_path = self._get_special_audio_file(event_name)
            if not file_path:
                logger.error("No configured audio file found for %s", event_name)
                return False

            with self.queue_lock:
                self.pending_audio_queue = []
            logger.info("Playing named audio event %s", event_name)
            return self.audio_player.play_audio(
                file_path,
                volume=self._get_special_audio_volume(event_name, 0.8),
            )
        except Exception as exc:
            logger.error("Error playing named audio %s: %s", event_name, exc)
            return False


# Example usage and testing
if __name__ == "__main__":
    # Test the audio player
    print("Testing Audio Player...")
    
    # Test with user's audio file
    audio_file = str(get_bundle_root() / "assets" / "audio" / "Azansoundtrack.m4a")
    
    if os.path.exists(audio_file):
        player = AudioPlayer()
        
        # Test file
        if player.test_audio_file(audio_file):
            print("✅ Audio file test successful")
            
            # Set volume
            player.set_volume(0.5)
            
            # Play audio (uncomment to test actual playback)
            # print("Playing audio for 5 seconds...")
            # if player.play_audio(audio_file):
            #     time.sleep(5)
            #     player.stop_audio()
            #     print("✅ Audio playback test completed")
            # else:
            #     print("❌ Failed to play audio")
            
        else:
            print("❌ Audio file test failed")
        
        # Cleanup
        player.cleanup()
    else:
        print(f"❌ Audio file not found: {audio_file}")
    
    # Test prayer audio manager
    print("\nTesting Prayer Audio Manager...")
    from config.settings import ConfigManager
    
    config = ConfigManager()
    prayer_audio = PrayerAudioManager(config)
    
    audio_info = prayer_audio.get_audio_info()
    print(f"Audio info: {audio_info}")
    
    if prayer_audio.test_audio_setup():
        print("✅ Prayer audio setup test successful")
    else:
        print("❌ Prayer audio setup test failed")
