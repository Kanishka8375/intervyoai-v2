# Configuration Module
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict


class InterviewMode(str, Enum):
    GENERAL = "general"
    CODING_COPILOT = "coding_copilot"
    PHONE_INTERVIEW = "phone_interview"
    HIREVUE = "hirevue"


class CareerLevel(str, Enum):
    ENTRY = "entry"
    MID_CAREER = "mid_career"
    SENIOR = "senior"
    EXECUTIVE = "executive"


class VerbosityLevel(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"


class ResponseFormat(str, Enum):
    BULLET = "bullet"
    PARAGRAPH = "paragraph"
    COMPACT = "compact"


INTERVIEW_MODE_PROMPTS = {
    InterviewMode.GENERAL: "You are a professional interview coach helping with general interview questions. Provide clear, structured answers that highlight the candidate's strengths and experiences. Use bullet points for clarity.",
    InterviewMode.CODING_COPILOT: "You are a coding assistant helping with technical interviews. Provide code examples in the answer when relevant. Explain algorithms and time complexity. Break down problems step by step.",
    InterviewMode.PHONE_INTERVIEW: "You are helping with phone screening interviews. Keep answers concise (30-90 seconds when spoken), verbal-friendly, and focused on key points. Avoid long lists.",
    InterviewMode.HIREVUE: "You are helping with recorded video interviews (HireVue). Provide brief, structured responses (60-90 seconds). Focus on STAR method for behavioral questions. Be concise and camera-friendly.",
}

CAREER_LEVEL_PROMPTS = {
    CareerLevel.ENTRY: "Focus on enthusiasm, learning ability, education, and transferable skills. Keep answers accessible.",
    CareerLevel.MID_CAREER: "Highlight achievements, growing responsibilities, and specific accomplishments. Show leadership potential.",
    CareerLevel.SENIOR: "Emphasize leadership, strategic thinking, cross-functional collaboration, and proven track record.",
    CareerLevel.EXECUTIVE: "Focus on vision, P&L responsibility, transformation stories, board-level communication, and executive presence.",
}

VERBOSITY_TOKENS = {
    VerbosityLevel.SHORT: 150,
    VerbosityLevel.MEDIUM: 300,
    VerbosityLevel.LONG: 600,
}


@dataclass
class AudioSettings:
    sample_rate: int = 16000
    channels: int = 1
    chunk_duration_ms: int = 100
    buffer_duration_ms: int = 500
    vad_mode: str = "silero"


@dataclass
class ASRSettings:
    model_type: str = "large-v3"
    device: str = "auto"
    compute_type: str = "default"
    language: str = "en"


@dataclass
class LLMSettings:
    model_name: str = "llama-3.1-8b"
    n_ctx: int = 4096
    n_gpu_layers: int = 0
    n_threads: int = 4
    temperature: float = 0.7
    top_p: float = 0.9
    max_tokens: int = 512


@dataclass
class ServerSettings:
    host: str = "0.0.0.0"
    port: int = 8080


@dataclass
class InterviewModeConfig:
    mode: InterviewMode = InterviewMode.GENERAL
    career_level: CareerLevel = CareerLevel.MID_CAREER
    verbosity: VerbosityLevel = VerbosityLevel.MEDIUM
    response_format: ResponseFormat = ResponseFormat.BULLET
    temperature: float = 0.7
    transcription_delay_ms: int = 500
    auto_scroll: bool = True
    smart_mode: bool = True  # Skip filler questions, only real questions


@dataclass
class ProviderConfig:
    provider: str = "ollama"
    model: str = "llama-3.1-8b"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    streaming: bool = True


@dataclass
class SessionState:
    is_paused: bool = False
    memory_enabled: bool = True
    is_active: bool = False
    start_time: Optional[str] = None
    questions_answered: int = 0
    current_mode: InterviewMode = InterviewMode.GENERAL


@dataclass
class AnswerScore:
    structure: float = 0.0
    clarity: float = 0.0
    tone: float = 0.0
    relevance: float = 0.0
    overall: float = 0.0


@dataclass
class ScheduledSession:
    id: Optional[int] = None
    scheduled_time: Optional[str] = None
    mode: InterviewMode = InterviewMode.GENERAL
    is_recurring: bool = False
    notes: str = ""


# Global settings instances
audio_settings = AudioSettings()
asr_settings = ASRSettings()
llm_settings = LLMSettings()
server_settings = ServerSettings()

# Feature settings instances
interview_mode_config = InterviewModeConfig()
provider_config = ProviderConfig()
session_state = SessionState()
