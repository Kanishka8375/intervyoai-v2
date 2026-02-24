"""
Cross-platform Stealth Module
Provides unified API for screen capture exclusion across Windows, Linux, and macOS
"""

import os
import sys
import platform
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class StealthConfig:
    """Stealth mode configuration"""

    exclude_from_capture: bool = True
    click_through: bool = False
    hide_from_taskbar: bool = True
    always_on_top: bool = True
    rename_process: bool = True


class StealthManager:
    """
    Unified stealth manager for all platforms
    Detects platform and uses appropriate backend
    """

    def __init__(self):
        self.platform = platform.system().lower()
        self.stealth = None
        self.config = StealthConfig()
        self._init_platform()

    def _init_platform(self):
        """Initialize platform-specific stealth implementation"""
        if self.platform == "linux":
            try:
                from backend.stealth.linux import linux_stealth

                self.stealth = linux_stealth
                logger.info("Linux stealth module initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Linux stealth: {e}")

        elif self.platform == "windows":
            try:
                from backend.stealth.windows import windows_stealth

                self.stealth = windows_stealth
                logger.info("Windows stealth module initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Windows stealth: {e}")

        elif self.platform == "darwin":
            # macOS - would use pyobjc for native APIs
            logger.info("macOS stealth - limited implementation")
            self.stealth = None

        else:
            logger.warning(f"Unknown platform: {self.platform}")
            self.stealth = None

    def set_stealth_mode(self, window_id: int, enable: bool = True) -> bool:
        """
        Enable or disable stealth mode for a window
        window_id: X11 window ID (Linux) or HWND (Windows)
        """
        if not self.stealth:
            logger.warning("Stealth not available on this platform")
            return False

        try:
            if enable:
                # Enable stealth mode
                if hasattr(self.stealth, "set_window_exclude_from_capture"):
                    self.stealth.set_window_exclude_from_capture(window_id)

                if self.config.hide_from_taskbar:
                    if hasattr(self.stealth, "hide_from_taskbar"):
                        self.stealth.hide_from_taskbar(window_id)

                if self.config.click_through:
                    if hasattr(self.stealth, "set_click_through"):
                        self.stealth.set_click_through(window_id, True)

                if self.config.always_on_top:
                    if hasattr(self.stealth, "set_always_on_top"):
                        self.stealth.set_always_on_top(window_id, True)

                logger.info(f"Stealth mode enabled for window {window_id}")
                return True

            else:
                # Disable stealth mode
                if hasattr(self.stealth, "set_window_exclude_from_capture"):
                    # Try to remove capture exclusion
                    pass  # Some platforms don't support removing

                if hasattr(self.stealth, "show_in_taskbar"):
                    self.stealth.show_in_taskbar(window_id)

                if hasattr(self.stealth, "set_click_through"):
                    self.stealth.set_click_through(window_id, False)

                logger.info(f"Stealth mode disabled for window {window_id}")
                return True

        except Exception as e:
            logger.error(f"Failed to set stealth mode: {e}")
            return False

    def set_click_through(self, window_id: int, enable: bool = True) -> bool:
        """Enable or disable click-through mode"""
        if not self.stealth or not hasattr(self.stealth, "set_click_through"):
            return False

        try:
            return self.stealth.set_click_through(window_id, enable)
        except Exception as e:
            logger.error(f"Failed to set click-through: {e}")
            return False

    def hide_from_capture(self, window_id: int) -> bool:
        """Hide window from screen capture"""
        if not self.stealth or not hasattr(
            self.stealth, "set_window_exclude_from_capture"
        ):
            return False

        try:
            return self.stealth.set_window_exclude_from_capture(window_id)
        except Exception as e:
            logger.error(f"Failed to hide from capture: {e}")
            return False

    def hide_from_taskbar(self, window_id: int) -> bool:
        """Hide window from taskbar"""
        if not self.stealth or not hasattr(self.stealth, "hide_from_taskbar"):
            return False

        try:
            return self.stealth.hide_from_taskbar(window_id)
        except Exception as e:
            logger.error(f"Failed to hide from taskbar: {e}")
            return False

    def get_active_window(self):
        """Get the currently active window info"""
        if not self.stealth or not hasattr(self.stealth, "get_active_window"):
            return None

        try:
            return self.stealth.get_active_window()
        except Exception as e:
            logger.debug(f"Failed to get active window: {e}")
            return None

    def set_always_on_top(self, window_id: int, enable: bool = True) -> bool:
        """Set window always on top"""
        if not self.stealth or not hasattr(self.stealth, "set_always_on_top"):
            return False

        try:
            return self.stealth.set_always_on_top(window_id, enable)
        except Exception as e:
            logger.error(f"Failed to set always on top: {e}")
            return False


# Global instance
stealth_manager = StealthManager()
