"""
Voice Activity Detection (VAD) Module
Detects when user is speaking and triggers audio capture automatically
"""

import os
import logging
from typing import Optional, Callable
from dataclasses import dataclass

logger = logging.getLogger(__name__)

try:
    import webrtcvad

    WEBRTC_VAD_AVAILABLE = True
except ImportError:
    WEBRTC_VAD_AVAILABLE = False
    logger.warning("webrtcvad not available")


@dataclass
class VADConfig:
    """Voice Activity Detection configuration"""

    sample_rate: int = 16000
    frame_duration: int = 30  # ms (10, 20, or 30)
    padding_duration: int = 300  # ms of silence before stopping
    aggressiveness: int = 2  # 0-3 (most aggressive)


class VoiceActivityDetector:
    """
    Voice Activity Detection using WebRTC VAD
    Automatically detects when user starts/stops speaking
    """

    def __init__(self, config: VADConfig = None):
        self.config = config or VADConfig()
        self.vad = None
        self.is_speaking = False
        self.callback_start = None
        self.callback_stop = None
        self._init_vad()

    def _init_vad(self):
        """Initialize WebRTC VAD"""
        if not WEBRTC_VAD_AVAILABLE:
            logger.warning("WebRTC VAD not available, using fallback")
            return

        try:
            self.vad = webrtcvad.Vad(self.config.aggressiveness)
            self.vad.set_mode(self.config.aggressiveness)
            logger.info(f"VAD initialized with mode {self.config.aggressiveness}")
        except Exception as e:
            logger.error(f"Failed to initialize VAD: {e}")
            self.vad = None

    def is_speech(self, audio_chunk: bytes) -> bool:
        """Check if audio chunk contains speech"""
        if not self.vad:
            # Fallback: use energy-based detection
            return self._energy_based_detection(audio_chunk)

        try:
            return self.vad.is_speech(audio_chunk, self.config.sample_rate)
        except Exception as e:
            logger.debug(f"VAD error: {e}")
            return False

    def _energy_based_detection(self, audio_chunk: bytes) -> bool:
        """Fallback energy-based voice detection"""
        import struct

        # Calculate RMS energy
        if len(audio_chunk) < 2:
            return False

        try:
            # Assume 16-bit PCM
            samples = struct.unpack(f"{len(audio_chunk) // 2}h", audio_chunk)
            energy = sum(abs(s) for s in samples) / len(samples)

            # Threshold for speech detection
            return energy > 500
        except:
            return False

    def process_audio(self, audio_chunk: bytes) -> bool:
        """
        Process audio chunk and detect speech
        Returns True if speech detected, False otherwise
        """
        was_speaking = self.is_speaking
        self.is_speaking = self.is_speech(audio_chunk)

        # Trigger callbacks
        if self.is_speaking and not was_speaking:
            if self.callback_start:
                self.callback_start()
            logger.debug("Speech started")

        if not self.is_speaking and was_speaking:
            if self.callback_stop:
                self.callback_stop()
            logger.debug("Speech stopped")

        return self.is_speaking

    def on_speech_start(self, callback: Callable):
        """Set callback for speech start"""
        self.callback_start = callback

    def on_speech_stop(self, callback: Callable):
        """Set callback for speech stop"""
        self.callback_stop = callback

    def reset(self):
        """Reset VAD state"""
        self.is_speaking = False


class AudioProcessor:
    """
    Audio processor with VAD and real-time processing
    Used for voice input with automatic detection
    """

    def __init__(self):
        self.vad = VoiceActivityDetector()
        self.is_recording = False
        self.audio_buffer = []
        self.on_audio_ready = None

    async def process_chunk(self, audio_chunk: bytes):
        """Process incoming audio chunk"""
        # Detect voice activity
        is_speech = self.vad.process_audio(audio_chunk)

        if is_speech:
            # Add to buffer
            self.audio_buffer.append(audio_chunk)

        return is_speech

    def get_audio_buffer(self) -> bytes:
        """Get all buffered audio"""
        return b"".join(self.audio_buffer)

    def clear_buffer(self):
        """Clear audio buffer"""
        self.audio_buffer = []


# Global instance
vad = VoiceActivityDetector()
audio_processor = AudioProcessor()
