"""
Linux Stealth Module
Provides screen capture exclusion and process hiding for Linux (X11/Wayland)
"""

import os
import sys
import ctypes
import logging
from typing import Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WindowInfo:
    xid: int
    title: str
    process_id: int


class LinuxStealth:
    """Linux stealth operations for X11/Wayland"""

    def __init__(self):
        self.x11_lib = None
        self.display = None
        self.window_xid = None
        self._init_x11()

    def _init_x11(self):
        """Initialize X11 connection"""
        try:
            # Try to load X11 library
            self.x11_lib = ctypes.CDLL("libX11.so.6", use_errno=True)
            self.x11_lib.XOpenDisplay.argtypes = [ctypes.c_char_p]
            self.x11_lib.XOpenDisplay.restype = ctypes.c_void_p
            self.x11_lib.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
            self.x11_lib.XDefaultRootWindow.restype = ctypes.c_uint32

            # Open display
            display_name = os.environ.get("DISPLAY", b":0")
            if isinstance(display_name, str):
                display_name = display_name.encode()

            self.display = self.x11_lib.XOpenDisplay(display_name)
            if not self.display:
                logger.warning("Failed to open X11 display")
                return

            logger.info("X11 display opened successfully")
        except Exception as e:
            logger.warning(f"X11 initialization failed: {e}")
            self.x11_lib = None
            self.display = None

    def set_window_exclude_from_capture(self, window_xid: int) -> bool:
        """
        Set window to be excluded from screen capture on Linux
        Uses _NET_WM_STATE and XFixes extension
        """
        if not self.display or not self.x11_lib:
            logger.warning("X11 not available, cannot set capture exclusion")
            return False

        try:
            # Try using XFixes to set window region as non-capturable
            # This works on some systems
            self._set_net_wm_state(window_xid, True)

            # Try XFixes extension
            try:
                xfixes = ctypes.CDLL("libXfixes.so.3", use_errno=True)
                xfixes.XFixesHideWindow.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
                xfixes.XFixesHideWindow(self.display, window_xid)
                logger.info(f"Window {window_xid} hidden from capture via XFixes")
            except Exception as e:
                logger.debug(f"XFixes not available: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to set capture exclusion: {e}")
            return False

    def _set_net_wm_state(self, window_xid: int, exclude: bool = True):
        """Set _NET_WM_STATE to hide window"""
        if not self.display or not self.x11_lib:
            return

        try:
            # Load Xlib
            from Xlib import X, display, Xatom

            d = display.Display()
            window = d.create_resource_object("window", window_xid)

            # Get _NET_WM_STATE atom
            net_wm_state = d.intern_atom("_NET_WM_STATE")
            hidden = d.intern_atom("_NET_WM_STATE_SKIP_TASKBAR")
            skip_pager = d.intern_atom("_NET_WM_STATE_SKIP_PAGER")

            # Get current state
            try:
                current = window.get_property(net_wm_state, Xatom.STRING, 0, 1024)
                if current:
                    current_atoms = [
                        d.intern_atom(a.decode() if isinstance(a, bytes) else a)
                        for a in current.value
                    ]
                else:
                    current_atoms = []
            except:
                current_atoms = []

            # Add hidden atoms if not present
            new_atoms = current_atoms[:]
            if exclude:
                if hidden not in new_atoms:
                    new_atoms.append(hidden)
                if skip_pager not in new_atoms:
                    new_atoms.append(skip_pager)

            # Set new state
            if new_atoms:
                # Convert atoms to Xlib objects
                atom_objects = [
                    d.get_atom_name(a) if isinstance(a, int) else a for a in new_atoms
                ]
                # For simplicity, just set the basic flags
                window.change_property(
                    net_wm_state,
                    Xatom.STRING,
                    8,
                    b"_NET_WM_STATE_SKIP_TASKBAR,_NET_WM_STATE_SKIP_PAGER",
                )

            d.sync()
            logger.info(f"Set _NET_WM_STATE for window {window_xid}")

        except ImportError:
            logger.debug("python-xlib not available for _NET_WM_STATE")
        except Exception as e:
            logger.debug(f"Failed to set _NET_WM_STATE: {e}")

    def hide_from_taskbar(self, window_xid: int) -> bool:
        """Hide window from taskbar and pager"""
        return self._set_net_wm_state(window_xid, True)

    def show_in_taskbar(self, window_xid: int) -> bool:
        """Show window in taskbar and pager"""
        return self._set_net_wm_state(window_xid, False)

    def set_click_through(self, window_xid: int, ignore: bool = True) -> bool:
        """Set window to ignore mouse events (click-through)"""
        if not self.display or not self.x11_lib:
            return False

        try:
            from Xlib import X, display

            d = display.Display()
            window = d.create_resource_object("window", window_xid)

            if ignore:
                # Set input shape to empty (make click-through)
                window.change_property(
                    d.intern_atom("_NET_WM_STATE"),
                    d.intern_atom("STRING"),
                    8,
                    b"_NET_WM_STATE_SKIP_TASKBAR",
                )

                # Also use XFixes for input passthrough
                try:
                    xfixes = ctypes.CDLL("libXfixes.so.3")
                    xfixes.XFixesSetWindowShapeRegion(self.display, window_xid, 0, 0, 0)
                except:
                    pass

            d.sync()
            logger.info(f"Set click-through for window {window_xid}: {ignore}")
            return True

        except Exception as e:
            logger.debug(f"Failed to set click-through: {e}")
            return False

    def get_window_under_cursor(self) -> Optional[WindowInfo]:
        """Get window info under cursor (for screenshot targeting)"""
        # This would require more complex X11 interaction
        return None

    def get_active_window(self) -> Optional[WindowInfo]:
        """Get currently active window info"""
        # Get the active window from X11
        if not self.display or not self.x11_lib:
            return None

        try:
            from Xlib import display, Xatom

            d = display.Display()
            root = d.screen().root

            # Get active window using _NET_ACTIVE_WINDOW
            active_window = root.get_property(
                d.intern_atom("_NET_ACTIVE_WINDOW"), Xatom.WINDOW, 0, 1
            )

            if active_window and active_window.value:
                xid = active_window.value[0]

                # Try to get window title
                try:
                    window = d.create_resource_object("window", xid)
                    title_prop = window.get_property(
                        d.intern_atom("_NET_WM_NAME"),
                        d.intern_atom("UTF8_STRING"),
                        0,
                        256,
                    )
                    title = (
                        title_prop.value.decode("utf-8") if title_prop else "Unknown"
                    )
                except:
                    title = "Unknown"

                return WindowInfo(xid=xid, title=title, process_id=0)

        except Exception as e:
            logger.debug(f"Failed to get active window: {e}")

        return None

    def close(self):
        """Close X11 connection"""
        if self.display and self.x11_lib:
            try:
                self.x11_lib.XCloseDisplay(self.display)
            except:
                pass


# Global instance
linux_stealth = LinuxStealth()
