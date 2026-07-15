"""
System Tray Interface Module
Handles system tray icon and menu for the Athan application
"""

import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import base64
import json
import logging
import os
import shutil
import subprocess
import sys
import threading
from utils.app_paths import get_bundle_root, get_project_root

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SystemTrayManager:
    """Manages system tray icon and menu"""
    
    def __init__(self, app_controller=None):
        """
        Initialize system tray manager
        
        Args:
            app_controller: Main application controller
        """
        self.app_controller = app_controller
        self.icon = None
        self.is_running = False
        self._ready_callback = None
        
        # Create tray icon
        self.tray_icon = self._create_icon()
        
        # Menu items
        self.menu_items = self._create_menu()

    def _run_async(self, callback):
        """Run menu actions off the tray event loop."""
        threading.Thread(target=callback, daemon=True).start()

    def _encode_payload(self, payload: dict) -> str:
        """Encode dialog payloads for the helper window process."""
        raw = json.dumps(payload).encode("utf-8")
        return base64.urlsafe_b64encode(raw).decode("utf-8")

    def _get_dialog_python(self) -> str | None:
        """Return a usable Python executable for the detached dialog helper."""
        candidates = []
        project_python = get_project_root() / ".venv" / "bin" / "python"
        if project_python.exists():
            candidates.append(str(project_python))
        if sys.executable and os.path.basename(sys.executable).startswith("python"):
            candidates.append(sys.executable)
        python3_path = shutil.which("python3")
        if python3_path:
            candidates.append(python3_path)
        python_path = shutil.which("python")
        if python_path:
            candidates.append(python_path)

        seen = set()
        for candidate in candidates:
            if candidate and candidate not in seen:
                seen.add(candidate)
                return candidate
        return None

    def _show_rich_payload(self, payload: dict) -> bool:
        """Show the styled helper window.

        - When running as a frozen .app bundle, run the Tk window in-process
          on a daemon thread (no external interpreter is available).
        - When running from source, prefer spawning a detached helper process
          so the tray loop is fully isolated from Tk.
        """
        # Frozen .app: relaunch our own binary in helper-window mode.
        # Tk on macOS must run on the main thread, so we use a child process.
        if getattr(sys, "frozen", False):
            try:
                env = os.environ.copy()
                # Help the child find Tcl/Tk frameworks bundled inside the .app
                env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
                subprocess.Popen(
                    [sys.executable, "--show-window", self._encode_payload(payload)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    env=env,
                )
                return True
            except Exception as e:
                logger.error(f"Error launching helper window subprocess: {e}")
                self._show_simple_info(
                    payload.get("title", "Athan App"),
                    payload.get("message", ""),
                )
                return False

        # Source/dev path: detached subprocess
        helper_path = get_project_root() / "gui" / "main_window.py"
        python_executable = self._get_dialog_python()

        if not helper_path.exists() or not python_executable:
            # Fall back to in-process if helper layout is missing
            try:
                from gui import main_window as _mw  # type: ignore
                threading.Thread(
                    target=_mw.show_payload,
                    args=(payload,),
                    daemon=True,
                ).start()
                return True
            except Exception as e:
                logger.warning(
                    f"Helper window unavailable, falling back to simple dialog: {e}"
                )
                self._show_simple_info(
                    payload.get("title", "Athan App"),
                    payload.get("message", ""),
                )
                return False

        try:
            subprocess.Popen(
                [python_executable, str(helper_path), self._encode_payload(payload)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            return True
        except Exception as e:
            logger.error(f"Error launching rich dialog: {e}")
            self._show_simple_info(payload.get("title", "Athan App"), payload.get("message", ""))
            return False
    
    def _create_icon(self) -> Image.Image:
        """
        Create system tray icon
        
        Returns:
            PIL Image for the tray icon
        """
        try:
            # Try to load custom icon if available
            icon_path = get_bundle_root() / 'assets' / 'icons' / 'tray_icon.png'
            
            if icon_path.exists():
                return Image.open(icon_path)
            else:
                # Create a simple mosque/crescent icon programmatically
                return self._create_default_icon()
                
        except Exception as e:
            logger.warning(f"Could not load icon, creating default: {e}")
            return self._create_default_icon()
    
    def _create_default_icon(self) -> Image.Image:
        """
        Create a default icon programmatically
        
        Returns:
            PIL Image with a simple mosque/crescent design
        """
        # Create a 64x64 image with transparent background
        image = Image.new('RGBA', (64, 64), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw a simple crescent moon (Islamic symbol)
        # Outer circle (larger)
        draw.ellipse([10, 10, 54, 54], fill=(34, 139, 34, 255))  # Green circle
        
        # Inner circle (smaller, to create crescent)
        draw.ellipse([20, 8, 56, 44], fill=(0, 0, 0, 0))  # Transparent circle
        
        # Add a small star
        star_points = [
            (45, 20), (47, 25), (52, 25), (48, 28),
            (50, 33), (45, 30), (40, 33), (42, 28),
            (38, 25), (43, 25)
        ]
        draw.polygon(star_points, fill=(255, 255, 255, 255))  # White star
        
        return image
    
    def _create_menu(self) -> tuple:
        """
        Create system tray menu
        
        Returns:
            Tuple of menu items
        """
        return (
            item('Athan App', self._show_main_window, default=True),
            item('Next Prayer', self._show_next_prayer),
            pystray.Menu.SEPARATOR,
            item('Prayer Times', self._show_prayer_times),
            item('Settings', self._show_settings),
            pystray.Menu.SEPARATOR,
            item('Test Audio', self._test_audio),
            item('Test Audio File…', self._test_audio_file),
            item('Stop Audio', self._stop_audio),
            pystray.Menu.SEPARATOR,
            item('About', self._show_about),
            item('Exit', self._quit_application)
        )
    
    def _show_main_window(self, icon, item):
        """Show main application window"""
        self._run_async(self._handle_show_main_window)

    def _handle_show_main_window(self):
        try:
            if self.app_controller:
                payload = self.app_controller.get_dialog_payload('dashboard')
                self._show_rich_payload(payload)
            else:
                self._show_simple_info("Athan App", "Main window not available")
        except Exception as e:
            logger.error(f"Error showing main window: {e}")
    
    def _show_next_prayer(self, icon, item):
        """Show next prayer information"""
        self._run_async(self._handle_show_next_prayer)

    def _handle_show_next_prayer(self):
        try:
            if self.app_controller:
                payload = self.app_controller.get_dialog_payload('next_prayer')
                self._show_rich_payload(payload)
            else:
                self._show_simple_info("Next Prayer", "Prayer information not available")
            
        except Exception as e:
            logger.error(f"Error showing next prayer: {e}")
            self._show_simple_info("Error", "Could not get prayer information")
    
    def _show_prayer_times(self, icon, item):
        """Show today's prayer times"""
        self._run_async(self._handle_show_prayer_times)

    def _handle_show_prayer_times(self):
        try:
            if self.app_controller:
                payload = self.app_controller.get_dialog_payload('prayer_times')
                self._show_rich_payload(payload)
            else:
                self._show_simple_info("Prayer Times", "Prayer times not available")
            
        except Exception as e:
            logger.error(f"Error showing prayer times: {e}")
            self._show_simple_info("Error", "Could not get prayer times")
    
    def _show_settings(self, icon, item):
        """Show settings window"""
        self._run_async(self._handle_show_settings)

    def _handle_show_settings(self):
        try:
            if self.app_controller:
                payload = self.app_controller.get_dialog_payload('settings')
                self._show_rich_payload(payload)
            else:
                self._show_simple_info("Settings", "Settings window not available")
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
    
    def _test_audio(self, icon, item):
        """Test audio playback"""
        self._run_async(self._handle_test_audio)

    def _handle_test_audio(self):
        try:
            if self.app_controller:
                success = self.app_controller.test_audio()
                if success:
                    payload = self.app_controller.get_dialog_payload('audio_test_success')
                    self._show_rich_payload(payload)
                else:
                    payload = self.app_controller.get_dialog_payload('audio_test_failure')
                    self._show_rich_payload(payload)
            else:
                self._show_simple_info("Audio Test", "Audio test not available")
        except Exception as e:
            logger.error(f"Error testing audio: {e}")
            self._show_simple_info("Error", "Could not test audio")
    
    def _test_audio_file(self, icon, item):
        """Prompt user for an audio file and play it via afplay."""
        self._run_async(self._handle_test_audio_file)

    # Track the most recent test-file process so we can stop it.
    _test_file_proc = None

    def _handle_test_audio_file(self):
        try:
            # macOS-native file picker via AppleScript. Returns POSIX path on OK.
            ok, path = self._pick_audio_file_via_applescript()
            if not ok or not path:
                return  # user cancelled
            if not os.path.exists(path):
                self._show_simple_info("Test Audio File", f"File not found:\n{path}")
                return

            # Stop any prior test-file playback
            prior = SystemTrayManager._test_file_proc
            if prior and prior.poll() is None:
                try:
                    prior.terminate()
                except Exception:
                    pass

            SystemTrayManager._test_file_proc = subprocess.Popen(
                ["/usr/bin/afplay", path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("Test-playing audio file via afplay: %s", path)
        except Exception as e:
            logger.error(f"Error in test audio file: {e}")
            self._show_simple_info("Test Audio File", f"Failed:\n{e}")

    def _pick_audio_file_via_applescript(self) -> tuple[bool, str]:
        """Show a native file picker using osascript. Returns (ok, posix_path)."""
        script = (
            'try\n'
            '  set f to choose file with prompt "Pick an audio file to test"'
            ' of type {"public.audio","m4a","mp3","wav","aac","ogg"}\n'
            '  return POSIX path of f\n'
            'on error number -128\n'  # user cancelled
            '  return ""\n'
            'end try'
        )
        try:
            result = subprocess.run(
                ["osascript", "-e", script],
                capture_output=True,
                text=True,
                timeout=120,
            )
            path = (result.stdout or "").strip()
            return (True, path) if path else (False, "")
        except Exception as e:
            logger.error(f"File picker failed: {e}")
            return (False, "")

    def _stop_audio(self, icon, item):
        """Stop current audio playback"""
        self._run_async(self._handle_stop_audio)

    def _handle_stop_audio(self):
        try:
            # Stop any test-file playback first.
            prior = SystemTrayManager._test_file_proc
            if prior and prior.poll() is None:
                try:
                    prior.terminate()
                except Exception:
                    pass
                SystemTrayManager._test_file_proc = None

            if self.app_controller:
                self.app_controller.stop_audio()
                if self.app_controller:
                    payload = self.app_controller.get_dialog_payload('audio_stopped')
                    self._show_rich_payload(payload)
            else:
                self._show_simple_info("Audio", "Audio control not available")
        except Exception as e:
            logger.error(f"Error stopping audio: {e}")
    
    def _show_about(self, icon, item):
        """Show about dialog"""
        self._run_async(self._handle_show_about)

    def _handle_show_about(self):
        if self.app_controller:
            payload = self.app_controller.get_dialog_payload('about')
            self._show_rich_payload(payload)
        else:
            self._show_simple_info("About Athan App", "Islamic Prayer Time Application")
    
    def _quit_application(self, icon, item):
        """Quit the application"""
        self._run_async(self._handle_quit_application)

    def _handle_quit_application(self):
        try:
            if self.app_controller:
                self.app_controller.quit_application()
            else:
                self.stop()
        except Exception as e:
            logger.error(f"Error quitting application: {e}")
            self.stop()
    
    def _show_simple_info(self, title: str, message: str):
        """
        Show a simple info dialog.
        
        Args:
            title: Dialog title
            message: Dialog message
        """
        try:
            if sys.platform == 'darwin':
                apple_title = self._escape_applescript(title)
                apple_message = self._escape_applescript(message)
                subprocess.run(
                    [
                        'osascript',
                        '-e',
                        f'display dialog "{apple_message}" with title "{apple_title}" buttons {{"OK"}} default button "OK"',
                    ],
                    check=False,
                )
            else:
                logger.info("%s: %s", title, message)
        except Exception as e:
            logger.error(f"Error showing info dialog: {e}")

    @staticmethod
    def _escape_applescript(value: str) -> str:
        """Escape strings for AppleScript dialog commands."""
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    
    def _on_tray_ready(self, icon):
        """Mark the tray as ready once pystray has initialized."""
        try:
            icon.visible = True
            self.is_running = True
            logger.info("System tray started")
            if self._ready_callback:
                self._ready_callback()
        except Exception as e:
            logger.error(f"Error during tray setup: {e}")

    def start(self, on_ready=None):
        """Start the system tray on the main thread."""
        try:
            if self.is_running:
                logger.warning("System tray is already running")
                return
            
            # Create pystray icon
            self.icon = pystray.Icon(
                "athan_app",
                self.tray_icon,
                "Athan App - Islamic Prayer Times",
                self.menu_items
            )
            self._ready_callback = on_ready
            self.icon.run(setup=self._on_tray_ready)
            
        except Exception as e:
            logger.error(f"Error starting system tray: {e}")
            self.is_running = False
    
    def stop(self):
        """Stop the system tray"""
        try:
            if self.icon:
                self.icon.stop()
            self.is_running = False
            logger.info("System tray stopped")
        except Exception as e:
            logger.error(f"Error stopping system tray: {e}")
    
    def update_tooltip(self, text: str):
        """
        Update system tray tooltip
        
        Args:
            text: New tooltip text
        """
        try:
            if self.icon:
                self.icon.title = text
        except Exception as e:
            logger.error(f"Error updating tooltip: {e}")
    
    def show_notification(self, title: str, message: str):
        """
        Show system notification
        
        Args:
            title: Notification title
            message: Notification message
        """
        try:
            if self.icon:
                self.icon.notify(message, title)
        except Exception as e:
            logger.error(f"Error showing notification: {e}")
    
    def is_tray_running(self) -> bool:
        """
        Check if system tray is running
        
        Returns:
            True if running, False otherwise
        """
        return self.is_running


# Example usage and testing
if __name__ == "__main__":
    import time
    
    print("Testing System Tray...")
    
    # Mock app controller for testing
    class MockAppController:
        def show_main_window(self):
            print("Mock: Show main window")
        
        def show_settings_window(self):
            print("Mock: Show settings window")
        
        def get_next_prayer_info(self):
            return {'formatted': 'Dhuhr at 13:21'}
        
        def get_today_prayer_times(self):
            return {
                'fajr': '05:02',
                'dhuhr': '13:21',
                'asr': '17:08',
                'maghrib': '20:19',
                'isha': '21:39'
            }
        
        def test_audio(self):
            print("Mock: Test audio")
            return True
        
        def stop_audio(self):
            print("Mock: Stop audio")
        
        def quit_application(self):
            print("Mock: Quit application")
    
    # Test system tray
    mock_controller = MockAppController()
    tray_manager = SystemTrayManager(mock_controller)
    
    print("Starting system tray (will run for 10 seconds)...")
    tray_manager.start()
    
    # Wait a bit to let it start
    time.sleep(2)
    
    if tray_manager.is_tray_running():
        print("✅ System tray started successfully")
        
        # Test notification
        tray_manager.show_notification("Test", "System tray is working!")
        
        # Update tooltip
        tray_manager.update_tooltip("Athan App - Next: Dhuhr at 13:21")
        
        # Wait and then stop
        time.sleep(8)
        tray_manager.stop()
        print("✅ System tray test completed")
    else:
        print("❌ System tray failed to start")
