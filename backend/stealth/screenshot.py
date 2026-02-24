"""
Screenshot Module
Provides full-screen and region screenshot capabilities with stealth features
Supports Linux (X11), Windows, and macOS
"""

import os
import sys
import time
import logging
import base64
import io
from typing import Optional, Tuple, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Try to import platform-specific libraries
try:
    import mss

    MSS_AVAILABLE = True
except ImportError:
    MSS_AVAILABLE = False
    logger.warning("mss not available, using fallback")

try:
    from PIL import Image, ImageGrab

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logger.warning("PIL not available")


@dataclass
class ScreenshotResult:
    """Result of a screenshot operation"""

    success: bool
    image_data: Optional[str] = None  # Base64 encoded
    error: Optional[str] = None
    region: Optional[Tuple[int, int, int, int]] = None  # x, y, width, height


class Screenshot:
    """Cross-platform screenshot capture"""

    def __init__(self):
        self.sct = None
        self.platform = sys.platform
        self._init_screenshot()

    def _init_screenshot(self):
        """Initialize screenshot backend"""
        if self.platform == "win32":
            self._init_windows()
        elif self.platform == "linux":
            self._init_linux()
        elif self.platform == "darwin":
            self._init_macos()

    def _init_windows(self):
        """Initialize Windows screenshot"""
        if PIL_AVAILABLE:
            logger.info("Windows screenshot initialized with PIL")

    def _init_linux(self):
        """Initialize Linux screenshot"""
        if MSS_AVAILABLE:
            try:
                self.sct = mss.mss()
                logger.info("Linux screenshot initialized with mss")
            except Exception as e:
                logger.warning(f"Failed to init mss: {e}")
        elif PIL_AVAILABLE:
            logger.info("Linux screenshot initialized with PIL (fallback)")

    def _init_macos(self):
        """Initialize macOS screenshot"""
        if PIL_AVAILABLE:
            logger.info("macOS screenshot initialized with PIL")

    def capture_fullscreen(self, monitor: int = 0) -> ScreenshotResult:
        """Capture full screen"""
        try:
            if self.platform == "win32" and PIL_AVAILABLE:
                # Windows with PIL
                img = ImageGrab.grab()
                return self._pil_to_result(img)

            elif self.platform == "linux" and self.sct:
                # Linux with mss
                monitors = self.sct.monitors
                if monitor >= len(monitors):
                    monitor = 0

                monitor_info = monitors[monitor]
                screenshot = self.sct.grab(monitor_info)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                return self._pil_to_result(img)

            elif self.platform == "linux" and PIL_AVAILABLE:
                # Linux fallback with PIL
                img = ImageGrab.grab()
                return self._pil_to_result(img)

            elif self.platform == "darwin" and PIL_AVAILABLE:
                # macOS with PIL
                img = ImageGrab.grab()
                return self._pil_to_result(img)

            else:
                return ScreenshotResult(
                    success=False, error="Screenshot not available on this platform"
                )

        except Exception as e:
            logger.error(f"Fullscreen capture failed: {e}")
            return ScreenshotResult(success=False, error=str(e))

    def capture_region(
        self, x: int, y: int, width: int, height: int
    ) -> ScreenshotResult:
        """Capture a specific region of the screen"""
        try:
            if self.platform == "win32" and PIL_AVAILABLE:
                # Windows with PIL
                img = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                return self._pil_to_result(img, region=(x, y, width, height))

            elif self.platform == "linux" and self.sct:
                # Linux with mss
                region = {"top": y, "left": x, "width": width, "height": height}
                screenshot = self.sct.grab(region)
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                return self._pil_to_result(img, region=(x, y, width, height))

            elif self.platform == "darwin" and PIL_AVAILABLE:
                # macOS
                img = ImageGrab.grab(bbox=(x, y, x + width, y + height))
                return self._pil_to_result(img, region=(x, y, width, height))

            else:
                return ScreenshotResult(
                    success=False, error="Region capture not available"
                )

        except Exception as e:
            logger.error(f"Region capture failed: {e}")
            return ScreenshotResult(success=False, error=str(e))

    def capture_window(self, window_title: str = None) -> ScreenshotResult:
        """Capture a specific window by title"""
        # This would require platform-specific code
        # For now, fall back to fullscreen
        logger.warning("Window capture not implemented, using fullscreen")
        return self.capture_fullscreen()

    def _pil_to_result(
        self, img: Image.Image, region: Tuple[int, int, int, int] = None
    ) -> ScreenshotResult:
        """Convert PIL Image to ScreenshotResult"""
        try:
            # Convert to base64
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

            return ScreenshotResult(success=True, image_data=img_str, region=region)

        except Exception as e:
            logger.error(f"Failed to encode image: {e}")
            return ScreenshotResult(success=False, error=str(e))

    def get_monitors(self) -> List[dict]:
        """Get list of available monitors"""
        try:
            if self.platform == "linux" and self.sct:
                monitors = []
                for i, m in enumerate(self.sct.monitors):
                    if i > 0:  # Skip the "all monitors" entry
                        monitors.append(
                            {
                                "id": i,
                                "x": m["left"],
                                "y": m["top"],
                                "width": m["width"],
                                "height": m["height"],
                            }
                        )
                return monitors
            else:
                # Return default monitor
                return [{"id": 0, "x": 0, "y": 0, "width": 1920, "height": 1080}]
        except Exception as e:
            logger.error(f"Failed to get monitors: {e}")
            return [{"id": 0, "x": 0, "y": 0, "width": 1920, "height": 1080}]

    def close(self):
        """Clean up resources"""
        if self.sct:
            try:
                self.sct.close()
            except:
                pass


# Global instance
screenshot = Screenshot()
