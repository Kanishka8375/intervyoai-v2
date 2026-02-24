"""
Speech-to-Text (STT) Module
Supports NVIDIA NeMo Parakeet, Whisper, and Web Speech API
"""

import os
import asyncio
import base64
import json
from typing import Optional, List, Dict, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod

import aiohttp
from loguru import logger


@dataclass
class TranscriptionResult:
    text: str
    confidence: float = 1.0
    language: str = "en"
    duration: Optional[float] = None


class BaseSTT(ABC):
    """Base class for STT providers"""

    def __init__(self):
        pass

    @abstractmethod
    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        pass

    @abstractmethod
    async def transcribe_stream(self, audio_chunk: bytes) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        pass


class WhisperSTT(BaseSTT):
    """OpenAI Whisper STT (local or cloud)"""

    def __init__(
        self,
        model: str = "base",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        super().__init__()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or "http://localhost:11434"

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio using Whisper"""
        try:
            url = f"{self.base_url}/v1/audio/transcriptions"

            form = aiohttp.FormData()
            form.add_field(
                "file", audio_data, filename="audio.wav", content_type="audio/wav"
            )
            form.add_field("model", self.model)

            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=form,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        raise Exception(f"Whisper API error: {error}")

                    result = await resp.json()
                    return TranscriptionResult(
                        text=result.get("text", ""),
                        language=result.get("language", "en"),
                    )
        except Exception as e:
            logger.error(f"Whisper transcription error: {e}")
            raise

    async def transcribe_stream(self, audio_chunk: bytes) -> AsyncGenerator[str, None]:
        # Streaming not supported for Whisper
        result = await self.transcribe(audio_chunk)
        yield result.text

    async def list_models(self) -> List[str]:
        return ["tiny", "base", "small", "medium", "large"]


class NvidiaParakeetSTT(BaseSTT):
    """NVIDIA NeMo Parakeet STT"""

    def __init__(self, model: str = "parakeet-tdt-1.1b", api_key: Optional[str] = None):
        super().__init__()
        self.model = model
        self.api_key = api_key or os.getenv("NVIDIA_API_KEY", "")

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio using NVIDIA NeMo Parakeet"""
        if not self.api_key:
            raise Exception(
                "NVIDIA API key required. Set NVIDIA_API_KEY environment variable."
            )

        try:
            url = "https://api.nvidia.com/v1/nlp/parakeet-tdt/transcribe"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "audio/wav",
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    data=audio_data,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        raise Exception(f"NVIDIA Parakeet API error: {error}")

                    result = await resp.json()
                    return TranscriptionResult(
                        text=result.get("text", ""),
                        confidence=result.get("confidence", 1.0),
                        language=result.get("language", "en"),
                    )
        except Exception as e:
            logger.error(f"NVIDIA Parakeet transcription error: {e}")
            raise

    async def transcribe_stream(self, audio_chunk: bytes) -> AsyncGenerator[str, None]:
        result = await self.transcribe(audio_chunk)
        yield result.text

    async def list_models(self) -> List[str]:
        return ["parakeet-tdt-600m", "parakeet-tdt-1.1b", "parakeet-ctc-1.1b"]


class WebSpeechSTT(BaseSTT):
    """Browser Web Speech API (fallback)"""

    def __init__(self, language: str = "en-US"):
        super().__init__()
        self.language = language

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Web Speech API requires browser - return placeholder"""
        return TranscriptionResult(
            text="[Use browser Web Speech API for transcription]",
            language=self.language,
        )

    async def transcribe_stream(self, audio_chunk: bytes) -> AsyncGenerator[str, None]:
        yield "[Use browser Web Speech API]"

    async def list_models(self) -> List[str]:
        return ["Web Speech API"]


class FasterWhisperSTT(BaseSTT):
    """Faster Whisper (local, CPU/GPU optimized)"""

    def __init__(self, model: str = "base", device: str = "auto"):
        super().__init__()
        self.model = model
        self.device = device
        self._client = None

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe using Faster Whisper"""
        try:
            # Try using faster-whisper package
            from faster_whisper import WhisperModel

            model_size = self.model

            if self._client is None:
                self._client = WhisperModel(
                    model_size,
                    device=self.device if self.device != "auto" else "cpu",
                    compute_type="int8",
                )

            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(audio_data)
                temp_path = f.name

            try:
                segments, info = self._client.transcribe(temp_path)
                text = " ".join([seg.text for seg in segments])

                return TranscriptionResult(
                    text=text,
                    confidence=info.language_probability,
                    language=info.language,
                )
            finally:
                os.unlink(temp_path)

        except ImportError:
            return TranscriptionResult(
                text="[faster-whisper not installed]", language="en"
            )
        except Exception as e:
            logger.error(f"Faster Whisper error: {e}")
            raise

    async def transcribe_stream(self, audio_chunk: bytes) -> AsyncGenerator[str, None]:
        result = await self.transcribe(audio_chunk)
        yield result.text

    async def list_models(self) -> List[str]:
        return ["tiny", "base", "small", "medium", "large-v2", "large-v3"]


class STTManager:
    """Manager for multiple STT providers"""

    def __init__(self):
        self.providers: Dict[str, BaseSTT] = {}
        self.current_provider: str = "webspeech"
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all STT providers"""
        # Web Speech API (browser fallback)
        self.providers["webspeech"] = WebSpeechSTT()

        # Faster Whisper (local)
        try:
            self.providers["faster-whisper"] = FasterWhisperSTT()
        except Exception as e:
            logger.warning(f"Failed to initialize Faster Whisper: {e}")

        # Whisper (local or cloud)
        self.providers["whisper"] = WhisperSTT()

        # NVIDIA Parakeet (cloud)
        if os.getenv("NVIDIA_API_KEY"):
            try:
                self.providers["nvidia-parakeet"] = NvidiaParakeetSTT()
            except Exception as e:
                logger.warning(f"Failed to initialize NVIDIA Parakeet: {e}")

        # Default to Web Speech
        self.current_provider = "webspeech"

    def set_provider(self, provider: str, config: Optional[Dict] = None):
        """Set the current STT provider"""
        if provider not in self.providers:
            if provider == "whisper" and config:
                self.providers["whisper"] = WhisperSTT(
                    model=config.get("model", "base"),
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url"),
                )
            elif provider == "nvidia-parakeet" and config:
                self.providers["nvidia-parakeet"] = NvidiaParakeetSTT(
                    model=config.get("model", "parakeet-tdt-1.1b"),
                    api_key=config.get("api_key"),
                )
            elif provider == "faster-whisper" and config:
                self.providers["faster-whisper"] = FasterWhisperSTT(
                    model=config.get("model", "base"),
                    device=config.get("device", "auto"),
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")

        self.current_provider = provider

    async def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio from the current provider"""
        provider = self.providers.get(self.current_provider)
        if not provider:
            raise Exception(f"Provider {self.current_provider} not configured")

        return await provider.transcribe(audio_data)

    async def transcribe_base64(self, audio_base64: str) -> TranscriptionResult:
        """Transcribe base64 encoded audio"""
        audio_data = base64.b64decode(audio_base64)
        return await self.transcribe(audio_data)

    async def list_models(self) -> Dict[str, List[str]]:
        """List available models for all providers"""
        models = {}
        for name, provider in self.providers.items():
            try:
                models[name] = await provider.list_models()
            except Exception as e:
                logger.warning(f"Failed to list models for {name}: {e}")
                models[name] = []
        return models

    def set_language(self, language: str):
        """Set language for STT"""
        for provider in self.providers.values():
            if hasattr(provider, "set_language"):
                provider.set_language(language)
        logger.info(f"STT language set to: {language}")


stt_manager = STTManager()
