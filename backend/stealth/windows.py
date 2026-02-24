"""
Windows Stealth Module
Provides screen capture exclusion and process hiding for Windows
Uses SetWindowDisplayAffinity and other Windows APIs
"""

import os
import sys
import ctypes
import logging
from typing import Optional
from dataclasses import dataclass
from ctypes import wintypes

logger = logging.getLogger(__name__)


# Windows constants
WDA_EXCLUDEFROMCAPTURE = 0x00000011
WDA_NONE = 0x00000000
WS_EX_TRANSPARENT = 0x00000020
WS_EX_LAYERED = 0x00080000
GWL_EXSTYLE = -20


@dataclass
class WindowInfo:
    hwnd: int
    title: str
    process_id: int


class WindowsStealth:
    """Windows stealth operations"""

    def __init__(self):
        self.user32 = None
        self.kernel32 = None
        self._init_windows()

    def _init_windows(self):
        """Initialize Windows API"""
        try:
            if sys.platform != "win32":
                logger.debug("Not on Windows, skipping Windows API init")
                return

            self.user32 = ctypes.windll.user32
            self.kernel32 = ctypes.windll.kernel32

            # Set up function signatures
            self.user32.SetWindowDisplayAffinity.argtypes = [
                wintypes.HWND,
                wintypes.DWORD,
            ]
            self.user32.SetWindowDisplayAffinity.restype = wintypes.BOOL

            self.user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
            self.user32.GetWindowLongW.restype = wintypes.LONG

            self.user32.SetWindowLongW.argtypes = [
                wintypes.HWND,
                ctypes.c_int,
                wintypes.LONG,
            ]
            self.user32.SetWindowLongW.restype = wintypes.LONG

            self.user32.SetLayeredWindowAttributes.argtypes = [
                wintypes.HWND,
                wintypes.COLORREF,
                wintypes.BYTE,
                wintypes.DWORD,
            ]
            self.user32.SetLayeredWindowAttributes.restype = wintypes.BOOL

            self.user32.SetWindowPos.argtypes = [
                wintypes.HWND,
                wintypes.HWND,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_int,
                wintypes.UINT,
            ]
            self.user32.SetWindowPos.restype = wintypes.BOOL

            # Get current process ID
            self.kernel32.GetCurrentProcessId.argtypes = []
            self.kernel32.GetCurrentProcessId.restype = wintypes.DWORD

            logger.info("Windows API initialized successfully")

        except Exception as e:
            logger.warning(f"Windows API initialization failed: {e}")
            self.user32 = None

    def set_window_exclude_from_capture(self, hwnd: int) -> bool:
        """
        Set window to be excluded from screen capture on Windows
        Uses SetWindowDisplayAffinity with WDA_EXCLUDEFROMCAPTURE
        This is the KEY stealth feature!
        """
        if not self.user32:
            logger.warning("Windows API not available")
            return False

        try:
            result = self.user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)

            if result:
                logger.info(f"Window {hwnd} excluded from screen capture")
                return True
            else:
                error = ctypes.get_last_error()
                logger.error(f"Failed to set capture exclusion. Error code: {error}")
                return False

        except Exception as e:
            logger.error(f"Exception setting capture exclusion: {e}")
            return False

    def remove_window_exclude_from_capture(self, hwnd: int) -> bool:
        """Remove screen capture exclusion"""
        if not self.user32:
            return False

        try:
            result = self.user32.SetWindowDisplayAffinity(hwnd, WDA_NONE)
            if result:
                logger.info(f"Window {hwnd} capture exclusion removed")
            return bool(result)
        except Exception as e:
            logger.error(f"Failed to remove capture exclusion: {e}")
            return False

    def set_click_through(self, hwnd: int, ignore: bool = True) -> bool:
        """Set window to ignore mouse events (click-through)"""
        if not self.user32:
            return False

        try:
            # Get current extended style
            extended_style = self.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)

            if ignore:
                # Add WS_EX_TRANSPARENT for click-through
                new_style = extended_style | WS_EX_TRANSPARENT
            else:
                # Remove WS_EX_TRANSPARENT
                new_style = extended_style & ~WS_EX_TRANSPARENT

            self.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, new_style)

            logger.info(f"Click-through set for window {hwnd}: {ignore}")
            return True

        except Exception as e:
            logger.error(f"Failed to set click-through: {e}")
            return False

    def hide_from_taskbar(self, hwnd: int) -> bool:
        """Hide window from taskbar"""
        if not self.user32:
            return False

        try:
            # Use SetWindowPos to hide from taskbar
            # SWP_HIDE = 0x0001
            result = self.user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                0x0001 | 0x0004,  # SWP_HIDE | SWP_NOACTIVATE
            )

            if result:
                logger.info(f"Window {hwnd} hidden from taskbar")
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to hide from taskbar: {e}")
            return False

    def show_in_taskbar(self, hwnd: int) -> bool:
        """Show window in taskbar"""
        if not self.user32:
            return False

        try:
            # SWP_SHOWWINDOW = 0x0040
            result = self.user32.SetWindowPos(
                hwnd,
                0,
                0,
                0,
                0,
                0,
                0x0040 | 0x0004,  # SWP_SHOWWINDOW | SWP_NOACTIVATE
            )

            if result:
                logger.info(f"Window {hwnd} shown in taskbar")
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to show in taskbar: {e}")
            return False

    def get_foreground_window(self) -> Optional[WindowInfo]:
        """Get the currently active window"""
        if not self.user32:
            return None

        try:
            hwnd = self.user32.GetForegroundWindow()
            if not hwnd:
                return None

            # Get window title
            length = self.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(hwnd, buffer, length + 1)
                title = buffer.value
            else:
                title = ""

            # Get process ID
            process_id = wintypes.DWORD()
            self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))

            return WindowInfo(hwnd=hwnd, title=title, process_id=process_id.value)

        except Exception as e:
            logger.debug(f"Failed to get foreground window: {e}")
            return None

    def set_always_on_top(self, hwnd: int, top: bool = True) -> bool:
        """Set window always on top"""
        if not self.user32:
            return False

        try:
            # HWND_TOPMOST = -1
            # HWND_NOTOPMOST = -2
            # SWP_NOMOVE = 0x0002
            # SWP_NOSIZE = 0x0001

            hwnd_insert = -1 if top else -2
            result = self.user32.SetWindowPos(
                hwnd,
                hwnd_insert,
                0,
                0,
                0,
                0,
                0x0001 | 0x0002 | 0x0004,  # SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE
            )

            logger.info(f"Always on top set for window {hwnd}: {top}")
            return bool(result)

        except Exception as e:
            logger.error(f"Failed to set always on top: {e}")
            return False

    def get_window_handle_from_pid(self, pid: int) -> Optional[int]:
        """Get window handle from process ID"""
        if not self.user32:
            return None

        try:
            # Callback for EnumWindows
            @ctypes.WINFUNCTYPE(
                ctypes.c_bool, wintypes.HWND, ctypes.POINTER(ctypes.c_int)
            )
            def enum_callback(hwnd, lParam):
                process_id = wintypes.DWORD()
                self.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
                if process_id.value == pid:
                    # Found the window
                    lParam[0] = hwnd
                    return False  # Stop enumeration
                return True  # Continue

            pid_ref = ctypes.c_int(0)
            self.user32.EnumWindows(enum_callback, ctypes.byref(pid_ref))

            if pid_ref.value:
                return pid_ref.value

        except Exception as e:
            logger.debug(f"Failed to get window from PID: {e}")

        return None


# Global instance
windows_stealth = WindowsStealth()
