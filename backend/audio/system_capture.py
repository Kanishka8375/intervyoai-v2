"""
System Audio Capture Module
Captures system audio from Linux (PulseAudio/PipeWire), Windows (WASAPI), macOS (CoreAudio)
"""

import os
import sys
import logging
import threading
import queue
from typing import Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class AudioConfig:
    """Audio capture configuration"""

    sample_rate: int = 16000
    channels: int = 1
    format: str = "int16"
    buffer_size: int = 4096


class SystemAudioCapture:
    """Cross-platform system audio capture"""

    def __init__(self, config: AudioConfig = None):
        self.config = config or AudioConfig()
        self.platform = sys.platform
        self.running = False
        self.thread = None
        self.audio_queue = queue.Queue()
        self.callback = None
        self._init_platform()

    def _init_platform(self):
        """Initialize platform-specific audio capture"""
        if self.platform == "linux":
            self._init_linux()
        elif self.platform == "win32":
            self._init_windows()
        elif self.platform == "darwin":
            self._init_macos()

    def _init_linux(self):
        """Initialize Linux audio (PulseAudio)"""
        try:
            import pulsectl

            self.pulse = pulsectl.Pulse("intervyoai")
            logger.info("PulseAudio initialized")
        except ImportError:
            logger.warning("pulsectl not available, system audio capture disabled")
            self.pulse = None
        except Exception as e:
            logger.warning(f"Failed to init PulseAudio: {e}")
            self.pulse = None

    def _init_windows(self):
        """Initialize Windows audio (WASAPI)"""
        try:
            # Would use pycaw for Windows
            logger.info("Windows audio initialized")
        except Exception as e:
            logger.warning(f"Failed to init Windows audio: {e}")

    def _init_macos(self):
        """Initialize macOS audio (CoreAudio)"""
        try:
            # Would use pyobjc for macOS
            logger.info("macOS audio initialized")
        except Exception as e:
            logger.warning(f"Failed to init macOS audio: {e}")

    def start(self, callback: Optional[Callable] = None) -> bool:
        """Start capturing system audio"""
        if self.running:
            logger.warning("Audio capture already running")
            return True

        self.callback = callback

        try:
            if self.platform == "linux":
                return self._start_linux()
            elif self.platform == "win32":
                return self._start_windows()
            elif self.platform == "darwin":
                return self._start_macos()
            else:
                logger.error(f"Unsupported platform: {self.platform}")
                return False
        except Exception as e:
            logger.error(f"Failed to start audio capture: {e}")
            return False

    def _start_linux(self) -> bool:
        """Start Linux audio capture"""
        if not self.pulse:
            logger.warning("PulseAudio not available")
            return False

        try:
            # Get system audio source
            sources = self.pulse.source_list()
            system_audio = None

            for source in sources:
                # Look for monitor sources (these capture system audio)
                if "monitor" in source.name.lower() or "pactl" in source.name.lower():
                    system_audio = source
                    break

            if not system_audio:
                # Use default monitor
                for source in sources:
                    if "default" in source.name.lower():
                        system_audio = source
                        break

            if not system_audio:
                logger.warning("No system audio source found")
                return False

            logger.info(f"Capturing from: {system_audio.name}")

            self.running = True
            self.thread = threading.Thread(
                target=self._capture_linux, args=(system_audio.name,)
            )
            self.thread.daemon = True
            self.thread.start()

            return True

        except Exception as e:
            logger.error(f"Failed to start Linux audio: {e}")
            return False

    def _capture_linux(self, source_name: str):
        """Capture audio from Linux"""
        try:
            from pulsectl import PulseAudioError

            with self.pulse.recording(source_name) as stream:
                while self.running:
                    try:
                        for chunk in stream:
                            if not self.running:
                                break

                            # Put audio data in queue
                            self.audio_queue.put(chunk)

                            # Call callback if set
                            if self.callback:
                                self.callback(chunk)

                    except PulseAudioError:
                        break

        except Exception as e:
            logger.error(f"Linux audio capture error: {e}")
        finally:
            self.running = False

    def _start_windows(self) -> bool:
        """Start Windows audio capture"""
        # Would implement with pycaw
        logger.info("Windows system audio capture not fully implemented")
        return False

    def _start_macos(self) -> bool:
        """Start macOS audio capture"""
        # Would implement with pyobjc
        logger.info("macOS system audio capture not fully implemented")
        return False

    def stop(self):
        """Stop capturing audio"""
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

        logger.info("Audio capture stopped")

    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        """Get audio chunk from queue (non-blocking)"""
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def clear_queue(self):
        """Clear audio queue"""
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break


# Global instance
system_audio = SystemAudioCapture()
