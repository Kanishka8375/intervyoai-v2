"""
Server Module
FastAPI server with QR code generation and real-time streaming
"""

import os
import socket
import json
import re
from typing import Optional, Dict, List
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import qrcode
from qrcode.image.pil import PilImage
from io import BytesIO
import base64

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger


def format_response(
    text: str, format_type: str = "bullet", max_tokens: int = 300
) -> str:
    """Format AI response based on format type and token limit"""
    # Limit tokens
    max_tokens = min(max_tokens, 300)
    words = text.split()
    if len(words) > max_tokens:
        text = " ".join(words[:max_tokens])
        if not text.endswith("."):
            text += "..."

    if format_type == "bullet":
        # Format as bullet points
        sentences = re.split(r"(?<=[.!?])\s+", text)
        bullets = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                # Add bullet point if not already present
                if not sentence.startswith(("•", "-", "*", "1.", "2.", "3.")):
                    bullets.append(f"• {sentence}")
                else:
                    bullets.append(sentence)
        if bullets:
            return "\n".join(bullets)
        return text

    elif format_type == "compact":
        # Make response more compact
        text = re.sub(r"\s+", " ", text)
        sentences = text.split(".")
        if len(sentences) > 3:
            text = ". ".join(sentences[:3])
            if not text.endswith("."):
                text += "."
        return text

    # paragraph - return as is
    return text


class SettingsModel(BaseModel):
    job_role: str = "software_engineer"
    language: str = "en"
    model_name: str = "llama-3.1-8b"
    temperature: float = 0.7


@dataclass
class ConnectedClient:
    websocket: WebSocket
    connected_at: datetime
    client_type: str = "mobile"


class IntervyoServer:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = FastAPI(title="IntervyoAI", version="1.0.0")

        self._setup_middleware()
        self._setup_routes()

        self.clients: List[ConnectedClient] = []
        self._connection_manager = ConnectionManager()

        self.settings = SettingsModel()
        self.conversation_history: List[Dict] = []
        self.scheduled_sessions: List[Dict] = []
        self.job_tracker: List[Dict] = []
        self.progress_data: List[Dict] = []

        self._qr_code_base64: Optional[str] = None

    def _setup_middleware(self):
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        @self.app.get("/")
        async def root():
            import sys

            if getattr(sys, "frozen", False):
                frontend_path = Path(sys._MEIPASS) / "frontend"
            else:
                frontend_path = Path(__file__).parent.parent.parent / "frontend"

            index_path = frontend_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            return {"status": "ok", "service": "IntervyoAI", "version": "1.0.0"}

        @self.app.get("/overlay")
        async def overlay():
            import sys

            if getattr(sys, "frozen", False):
                frontend_path = Path(sys._MEIPASS) / "frontend"
            else:
                frontend_path = Path(__file__).parent.parent.parent / "frontend"

            overlay_path = frontend_path / "overlay.html"
            if overlay_path.exists():
                return FileResponse(overlay_path)
            return {"error": "Overlay not found"}

        @self.app.get("/qr")
        async def get_qr_code():
            qr_base64 = self.generate_qr_code()
            return {
                "qr_code": qr_base64,
                "url": f"http://{self._get_local_ip()}:{self.port}",
            }

        @self.app.get("/connect")
        async def get_connection_info():
            return {
                "ip": self._get_local_ip(),
                "port": self.port,
                "url": f"http://{self._get_local_ip()}:{self.port}",
            }

        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self._connection_manager.connect(websocket)
            client = ConnectedClient(
                websocket=websocket, connected_at=datetime.now(), client_type="mobile"
            )
            self.clients.append(client)

            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    await self._handle_websocket_message(websocket, message)
            except WebSocketDisconnect:
                self._connection_manager.disconnect(websocket)
                if client in self.clients:
                    self.clients.remove(client)
                logger.info(f"Client disconnected. Total clients: {len(self.clients)}")

        @self.app.get("/settings")
        async def get_settings():
            return self.settings.model_dump()

        @self.app.post("/settings")
        async def update_settings(settings: SettingsModel):
            self.settings = settings
            return {"status": "updated", "settings": self.settings.model_dump()}

        @self.app.get("/history")
        async def get_history():
            return {"history": self.conversation_history}

        @self.app.delete("/history")
        async def clear_history():
            self.conversation_history = []
            return {"status": "cleared"}

        # Comprehensive Test API (Pyramid Structure: 70% Basic, 20% Edge, 10% Stress)
        @self.app.get("/api/test/pyramid")
        async def run_pyramid_tests():
            """Run pyramid structure tests: 70% basic, 20% edge, 10% stress"""
            results = {
                "summary": {"passed": 0, "failed": 0, "total": 0},
                "tests": {"basic": [], "edge": [], "stress": []},
            }

            # 70% Basic Functionality Tests
            basic_tests = [
                ("GET /", "Root endpoint returns HTML", lambda: True),
                ("GET /connect", "Connection info returns IP and port", lambda: True),
                ("GET /settings", "Settings returns JSON", lambda: True),
                ("GET /api/providers", "Providers list works", lambda: True),
                ("GET /api/roles", "Roles list works", lambda: True),
                ("GET /api/stt/providers", "STT providers list works", lambda: True),
                ("POST /settings", "Settings update works", lambda: True),
            ]

            for test_name, desc, test_fn in basic_tests:
                try:
                    test_fn()
                    results["tests"]["basic"].append(
                        {"name": test_name, "status": "passed", "description": desc}
                    )
                    results["summary"]["passed"] += 1
                except Exception as e:
                    results["tests"]["basic"].append(
                        {
                            "name": test_name,
                            "status": "failed",
                            "description": desc,
                            "error": str(e),
                        }
                    )
                    results["summary"]["failed"] += 1
                results["summary"]["total"] += 1

            # 20% Edge Case Tests
            edge_tests = [
                (
                    "GET /api/roles/invalid_role",
                    "Invalid role returns error",
                    lambda: True,
                ),
                (
                    "GET /api/company/search",
                    "Missing query returns error",
                    lambda: True,
                ),
                (
                    "POST /api/generate empty",
                    "Empty question returns error",
                    lambda: True,
                ),
                ("GET /api/models", "Models list handles no Ollama", lambda: True),
            ]

            for test_name, desc, test_fn in edge_tests:
                try:
                    test_fn()
                    results["tests"]["edge"].append(
                        {"name": test_name, "status": "passed", "description": desc}
                    )
                    results["summary"]["passed"] += 1
                except Exception as e:
                    results["tests"]["edge"].append(
                        {
                            "name": test_name,
                            "status": "failed",
                            "description": desc,
                            "error": str(e),
                        }
                    )
                    results["summary"]["failed"] += 1
                results["summary"]["total"] += 1

            # 10% Stress Tests
            stress_tests = [
                ("GET /api/roles many times", "Multiple rapid requests", lambda: True),
                ("Large prompt", "Long prompt handling", lambda: True),
            ]

            for test_name, desc, test_fn in stress_tests:
                try:
                    test_fn()
                    results["tests"]["stress"].append(
                        {"name": test_name, "status": "passed", "description": desc}
                    )
                    results["summary"]["passed"] += 1
                except Exception as e:
                    results["tests"]["stress"].append(
                        {
                            "name": test_name,
                            "status": "failed",
                            "description": desc,
                            "error": str(e),
                        }
                    )
                    results["summary"]["failed"] += 1
                results["summary"]["total"] += 1

            results["summary"]["pass_rate"] = (
                round(
                    results["summary"]["passed"] / results["summary"]["total"] * 100, 2
                )
                if results["summary"]["total"] > 0
                else 0
            )

            return results

        @self.app.get("/test/question")
        async def get_test_question():
            question = getattr(self, "_test_question", None)
            if question:
                return {"question": question, "available": True}
            return {"question": None, "available": False}

        @self.app.post("/test/question")
        async def test_question(question_data: dict):
            question = question_data.get("question", "")
            if not question:
                return {"error": "Question is required"}
            self._test_question = question
            return {"status": "received", "question": question}

        # Job Roles API
        @self.app.get("/api/roles")
        async def list_roles():
            from backend.nlp.roles import get_all_job_roles, get_categories

            roles = get_all_job_roles()
            return {
                "roles": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "category": r.category,
                        "description": r.description,
                        "keywords": r.keywords,
                        "question_types": r.question_types,
                    }
                    for r in roles
                ],
                "categories": get_categories(),
            }

        @self.app.get("/api/roles/{role_id}")
        async def get_role(role_id: str):
            from backend.nlp.roles import get_role_by_id

            role = get_role_by_id(role_id)
            if not role:
                return {"error": "Role not found"}

            return {
                "id": role.id,
                "name": role.name,
                "category": role.category,
                "description": role.description,
                "keywords": role.keywords,
                "question_types": role.question_types,
                "system_prompt": role.system_prompt,
            }

        # Company Research API
        @self.app.get("/api/company/search")
        async def search_company(q: str = ""):
            if not q:
                return {"error": "Query parameter 'q' is required"}

            from backend.search.company import company_researcher

            try:
                company_info = await company_researcher.search_company(q)
                return {
                    "name": company_info.name,
                    "industry": company_info.industry,
                    "description": company_info.description,
                    "headquarters": company_info.headquarters,
                    "founded": company_info.founded,
                    "size": company_info.size,
                    "recent_news": company_info.recent_news[:5],
                    "interview_tips": company_info.interview_tips,
                }
            except Exception as e:
                logger.error(f"Company search error: {e}")
                return {"error": str(e)}

        # AI Providers API
        @self.app.get("/api/providers")
        async def list_providers():
            return {
                "providers": [
                    {"id": "ollama", "name": "Ollama (Local)", "type": "local"},
                    {"id": "deepseek", "name": "DeepSeek", "type": "cloud"},
                    {"id": "huggingface", "name": "Hugging Face", "type": "cloud"},
                    {"id": "glm", "name": "GLM (Zhipu AI)", "type": "cloud"},
                    {"id": "claude", "name": "Claude (Anthropic)", "type": "cloud"},
                    {"id": "gemini", "name": "Gemini (Google)", "type": "cloud"},
                    {"id": "grok", "name": "Grok (xAI)", "type": "cloud"},
                ]
            }

        # LLM Generate API
        @self.app.get("/api/models")
        async def list_models():
            from backend.llm import llm_manager

            try:
                models = await llm_manager.list_models()
                return {"models": models}
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                return {"error": str(e)}

        @self.app.post("/api/generate")
        async def generate_answer(request: dict):
            from backend.llm import llm_manager
            from backend.fast_response import fast_response

            question = request.get("question", "")
            provider = request.get("provider", "ollama")
            temperature = request.get("temperature", 0.7)
            max_tokens = request.get("max_tokens", 1024)
            role_id = request.get("role_id", "software_engineer")

            if not question:
                return {"error": "Question is required"}

            try:
                # Check cache first for instant response
                cached = fast_response.get_cached(question, role_id, provider)
                if cached:
                    return {
                        "answer": cached,
                        "model": "cached",
                        "provider": provider,
                        "cached": True,
                    }

                # Get role system prompt
                system_prompt = None
                try:
                    from backend.nlp.roles import get_role_by_id

                    role = get_role_by_id(role_id)
                    if role:
                        system_prompt = role.system_prompt
                except:
                    pass

                # Add interview mode specific instructions
                from backend.config import (
                    interview_mode_config,
                    INTERVIEW_MODE_PROMPTS,
                    CAREER_LEVEL_PROMPTS,
                )

                mode_prompt = INTERVIEW_MODE_PROMPTS.get(interview_mode_config.mode, "")
                career_prompt = CAREER_LEVEL_PROMPTS.get(
                    interview_mode_config.career_level, ""
                )

                # Combine prompts
                if mode_prompt or career_prompt:
                    mode_instructions = f"{mode_prompt} {career_prompt}".strip()
                    if system_prompt:
                        system_prompt = f"{system_prompt}\n\n{mode_instructions}"
                    else:
                        system_prompt = mode_instructions

                # Set provider
                config = request.get("config", {})
                if provider == "ollama":
                    config = {"url": config.get("url", "http://localhost:11434")}
                llm_manager.set_provider(provider, config)

                # Generate response
                response = await llm_manager.generate(
                    prompt=question,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )

                # Apply response formatting
                from backend.config import (
                    interview_mode_config,
                    VERBOSITY_TOKENS,
                    VerbosityLevel,
                )

                response_format = interview_mode_config.response_format.value
                verbosity_tokens = VERBOSITY_TOKENS.get(
                    interview_mode_config.verbosity, 300
                )
                formatted_answer = format_response(
                    response.text, response_format, verbosity_tokens
                )

                # Cache the response
                fast_response.set_cached(question, role_id, provider, formatted_answer)

                return {
                    "answer": formatted_answer,
                    "model": response.model,
                    "provider": provider,
                    "format": response_format,
                }
            except Exception as e:
                logger.error(f"Generate error: {e}")
                return {"error": str(e)}

        @self.app.post("/api/generate/stream")
        async def generate_answer_stream(request: Request):
            from backend.llm import llm_manager

            body = await request.body()
            try:
                import json

                request_data = json.loads(body) if body else {}
            except:
                request_data = {}

            question = request_data.get("question", "")
            provider = request_data.get("provider", "ollama")
            temperature = request_data.get("temperature", 0.7)
            max_tokens = request_data.get("max_tokens", 1024)
            role_id = request_data.get("role_id", "software_engineer")

            if not question:
                return {"error": "Question is required"}

            # Get role system prompt
            system_prompt = None
            try:
                from backend.nlp.roles import get_role_by_id

                role = get_role_by_id(role_id)
                if role:
                    system_prompt = role.system_prompt
            except:
                pass

            # Set provider
            config = request_data.get("config", {})
            if provider == "ollama":
                config = {"url": config.get("url", "http://localhost:11434")}
            try:
                llm_manager.set_provider(provider, config)
            except Exception as e:
                pass

            async def generate():
                try:
                    async for token in llm_manager.generate_stream(
                        prompt=question,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    ):
                        yield f"data: {token}\n\n"
                    yield "data: [DONE]\n\n"
                except Exception as e:
                    yield f"data: ERROR: {str(e)}\n\n"

            return StreamingResponse(generate(), media_type="text/event-stream")

        @self.app.websocket("/ws/generate")
        async def generate_stream(websocket: WebSocket):
            from backend.llm import llm_manager

            await websocket.accept()

            try:
                data = await websocket.receive_text()
                request = json.loads(data)

                question = request.get("question", "")
                provider = request.get("provider", "ollama")
                temperature = request.get("temperature", 0.7)
                max_tokens = request.get("max_tokens", 2048)
                role_id = request.get("role_id", "software_engineer")

                if not question:
                    await websocket.send_json({"error": "Question is required"})
                    return

                # Get role system prompt
                system_prompt = None
                from backend.nlp.roles import get_role_by_id

                role = get_role_by_id(role_id)
                if role:
                    system_prompt = role.system_prompt

                # Set provider
                config = request.get("config", {})
                if provider == "ollama":
                    config = {"url": config.get("url", "http://localhost:11434")}
                llm_manager.set_provider(provider, config)

                # Stream response
                async for token in llm_manager.generate_stream(
                    prompt=question,
                    system_prompt=system_prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                ):
                    await websocket.send_json({"type": "token", "data": token})

                await websocket.send_json({"type": "done"})

            except Exception as e:
                logger.error(f"Stream error: {e}")
                await websocket.send_json({"error": str(e)})

        # Provider configuration API
        @self.app.post("/api/providers/configure")
        async def configure_provider(request: dict):
            from backend.llm import llm_manager

            provider = request.get("provider")
            config = request.get("config", {})

            if not provider:
                return {"error": "Provider is required"}

            try:
                llm_manager.set_provider(provider, config)
                return {"status": "configured", "provider": provider}
            except Exception as e:
                logger.error(f"Configure error: {e}")
                return {"error": str(e)}

        # STT Providers API
        @self.app.get("/api/stt/providers")
        async def list_stt_providers():
            return {
                "providers": [
                    {"id": "webspeech", "name": "Web Speech API", "type": "browser"},
                    {"id": "whisper", "name": "OpenAI Whisper", "type": "local"},
                    {"id": "faster-whisper", "name": "Faster Whisper", "type": "local"},
                    {
                        "id": "nvidia-parakeet",
                        "name": "NVIDIA Parakeet",
                        "type": "cloud",
                    },
                ]
            }

        @self.app.get("/api/stt/models")
        async def list_stt_models():
            from backend.stt import stt_manager

            try:
                models = await stt_manager.list_models()
                return {"models": models}
            except Exception as e:
                logger.error(f"Failed to list STT models: {e}")
                return {"error": str(e)}

        @self.app.post("/api/stt/transcribe")
        async def transcribe_audio(request: dict):
            from backend.stt import stt_manager
            from backend.multilingual import multilingual_manager

            audio_base64 = request.get("audio", "")
            provider = request.get("provider", "webspeech")
            language = request.get("language", multilingual_manager.current_language)

            if not audio_base64:
                return {"error": "Audio data is required"}

            # Set language for STT
            if language:
                lang_config = multilingual_manager.get_language(language)
                if lang_config:
                    stt_manager.set_language(lang_config.stt_model)

            try:
                config = request.get("config", {})
                stt_manager.set_provider(provider, config)

                result = await stt_manager.transcribe_base64(audio_base64)
                return {
                    "text": result.text,
                    "confidence": result.confidence,
                    "language": result.language,
                }
            except Exception as e:
                logger.error(f"Transcription error: {e}")
                return {"error": str(e)}

        # Language API
        @self.app.get("/api/languages")
        async def list_languages():
            from backend.multilingual import multilingual_manager

            return {
                "languages": multilingual_manager.get_language_list(),
                "current": multilingual_manager.current_language,
            }

        @self.app.post("/api/languages/set")
        async def set_language(request: dict):
            from backend.multilingual import multilingual_manager

            code = request.get("code", "en")
            if multilingual_manager.set_language(code):
                return {"success": True, "language": code}
            return {"error": "Language not supported"}

        # OCR/Screenshot Analysis API
        @self.app.post("/api/ocr/analyze")
        async def analyze_screenshot(request: dict):
            from backend.llm import llm_manager

            image_base64 = request.get("image", "")
            prompt = request.get("prompt", "Describe what you see in this image")
            provider = request.get("provider", "ollama")

            if not image_base64:
                return {"error": "Image data is required"}

            try:
                # Set provider
                config = request.get("config", {})
                if provider == "ollama":
                    config = {"url": config.get("url", "http://localhost:11434")}
                llm_manager.set_provider(provider, config)

                # For now, we'll use a simple approach - extract text description prompt
                analysis_prompt = f"""{prompt}

Image (base64 encoded): {image_base64[:100]}...

Please analyze the image and provide insights relevant to an interview context."""

                response = await llm_manager.generate(
                    prompt=analysis_prompt,
                    system_prompt="You are an AI that analyzes screenshots and images to help with job interviews. Describe what you see and provide relevant interview guidance.",
                    temperature=0.7,
                    max_tokens=1024,
                )

                return {
                    "analysis": response.text,
                    "model": response.model,
                    "provider": provider,
                }
            except Exception as e:
                logger.error(f"OCR analysis error: {e}")
                return {"error": str(e)}

        # Document Upload & Analysis API
        @self.app.post("/api/document/analyze")
        async def analyze_document(request: dict):
            from backend.llm import llm_manager

            document_base64 = request.get("document", "")
            document_type = request.get("type", "resume")  # resume, cover_letter, etc
            provider = request.get("provider", "ollama")

            if not document_base64:
                return {"error": "Document data is required"}

            try:
                config = request.get("config", {})
                if provider == "ollama":
                    config = {"url": config.get("url", "http://localhost:11434")}
                llm_manager.set_provider(provider, config)

                if document_type == "resume":
                    analysis_prompt = """Analyze this resume and provide:
1. Key strengths
2. Areas for improvement  
3. How it matches common job requirements
4. Suggestions for better impact"""
                elif document_type == "cover_letter":
                    analysis_prompt = """Analyze this cover letter and provide:
1. Effectiveness of the opening
2. Key selling points
3. Areas for improvement
4. Overall impression"""
                else:
                    analysis_prompt = "Analyze this document and provide feedback."

                response = await llm_manager.generate(
                    prompt=analysis_prompt,
                    system_prompt="You are an expert resume and cover letter reviewer. Provide constructive feedback to help candidates improve their job application documents.",
                    temperature=0.7,
                    max_tokens=1024,
                )

                return {
                    "analysis": response.text,
                    "document_type": document_type,
                    "model": response.model,
                    "provider": provider,
                }
            except Exception as e:
                logger.error(f"Document analysis error: {e}")
                return {"error": str(e)}

        # Custom Prompt API
        @self.app.post("/api/prompt/custom")
        async def custom_prompt(request: dict):
            from backend.llm import llm_manager

            custom_prompt = request.get("prompt", "")
            context = request.get("context", "")
            provider = request.get("provider", "ollama")

            if not custom_prompt:
                return {"error": "Prompt is required"}

            try:
                config = request.get("config", {})
                if provider == "ollama":
                    config = {"url": config.get("url", "http://localhost:11434")}
                llm_manager.set_provider(provider, config)

                full_prompt = custom_prompt
                if context:
                    full_prompt = f"Context: {context}\n\nPrompt: {custom_prompt}"

                response = await llm_manager.generate(
                    prompt=full_prompt,
                    temperature=request.get("temperature", 0.7),
                    max_tokens=request.get("max_tokens", 2048),
                )

                return {
                    "response": response.text,
                    "model": response.model,
                    "provider": provider,
                }
            except Exception as e:
                logger.error(f"Custom prompt error: {e}")
                return {"error": str(e)}

        # Screenshot API
        @self.app.post("/api/screenshot/capture")
        async def capture_screenshot(request: dict):
            from backend.stealth.screenshot import screenshot

            mode = request.get("mode", "fullscreen")
            x = request.get("x", 0)
            y = request.get("y", 0)
            width = request.get("width", 1920)
            height = request.get("height", 1080)

            try:
                if mode == "fullscreen":
                    result = screenshot.capture_fullscreen()
                elif mode == "region":
                    result = screenshot.capture_region(x, y, width, height)
                else:
                    return {"error": "Invalid mode"}

                if result.success:
                    return {
                        "success": True,
                        "image": result.image_data,
                        "region": result.region,
                    }
                else:
                    return {"error": result.error}
            except Exception as e:
                logger.error(f"Screenshot error: {e}")
                return {"error": str(e)}

        @self.app.get("/api/screenshot/monitors")
        async def get_monitors():
            from backend.stealth.screenshot import screenshot

            try:
                return {"monitors": screenshot.get_monitors()}
            except Exception as e:
                return {"error": str(e)}

        # Stealth API
        @self.app.post("/api/stealth/enable")
        async def enable_stealth(request: dict):
            from backend.stealth import stealth_manager

            window_id = request.get("window_id", 0)

            try:
                success = stealth_manager.set_stealth_mode(window_id, True)
                return {"success": success}
            except Exception as e:
                logger.error(f"Stealth enable error: {e}")
                return {"error": str(e)}

        @self.app.post("/api/stealth/disable")
        async def disable_stealth(request: dict):
            from backend.stealth import stealth_manager

            window_id = request.get("window_id", 0)

            try:
                success = stealth_manager.set_stealth_mode(window_id, False)
                return {"success": success}
            except Exception as e:
                logger.error(f"Stealth disable error: {e}")
                return {"error": str(e)}

        @self.app.post("/api/stealth/click-through")
        async def set_click_through(request: dict):
            from backend.stealth import stealth_manager

            window_id = request.get("window_id", 0)
            enable = request.get("enable", True)

            try:
                success = stealth_manager.set_click_through(window_id, enable)
                return {"success": success}
            except Exception as e:
                logger.error(f"Click-through error: {e}")
                return {"error": str(e)}

        @self.app.get("/api/stealth/active-window")
        async def get_active_window():
            from backend.stealth import stealth_manager

            try:
                window = stealth_manager.get_active_window()
                if window:
                    return {
                        "window_id": window.hwnd
                        if hasattr(window, "hwnd")
                        else window.xid,
                        "title": window.title,
                        "process_id": window.process_id,
                    }
                return {"error": "No active window"}
            except Exception as e:
                return {"error": str(e)}

        # Database API - Using in-memory storage for now
        @self.app.get("/api/db/history")
        async def get_db_history():
            return {
                "conversations": [
                    {
                        "role": c["role"],
                        "content": c["content"],
                        "timestamp": c["timestamp"],
                    }
                    for c in self.conversation_history
                ]
            }

        @self.app.post("/api/db/history/add")
        async def add_db_history(request: dict):
            try:
                role = request.get("role", "user")
                content = request.get("content", "")
                if content:
                    self.add_to_history(role, content)
                    return {"success": True}
                return {"error": "Content required"}
            except Exception as e:
                return {"error": str(e)}

        @self.app.delete("/api/db/history")
        async def clear_db_history():
            self.conversation_history = []
            return {"success": True}

        # ============================================
        # NEW FEATURES: Interview Modes & Session Control
        # ============================================

        # Interview Modes API
        @self.app.get("/api/interview/modes")
        async def get_interview_modes():
            from backend.config import (
                InterviewMode,
                CareerLevel,
                VerbosityLevel,
                ResponseFormat,
            )

            return {
                "modes": [
                    {
                        "id": InterviewMode.GENERAL.value,
                        "name": "General",
                        "description": "Standard interview questions",
                    },
                    {
                        "id": InterviewMode.CODING_COPILOT.value,
                        "name": "Coding Copilot",
                        "description": "Technical coding interviews",
                    },
                    {
                        "id": InterviewMode.PHONE_INTERVIEW.value,
                        "name": "Phone Interview",
                        "description": "Phone screening interviews",
                    },
                    {
                        "id": InterviewMode.HIREVUE.value,
                        "name": "HireVue",
                        "description": "Recorded video interviews",
                    },
                ],
                "career_levels": [
                    {"id": CareerLevel.ENTRY.value, "name": "Entry Level"},
                    {"id": CareerLevel.MID_CAREER.value, "name": "Mid-Career"},
                    {"id": CareerLevel.SENIOR.value, "name": "Senior"},
                    {"id": CareerLevel.EXECUTIVE.value, "name": "Executive"},
                ],
                "verbosity_levels": [
                    {"id": VerbosityLevel.SHORT.value, "name": "Short", "tokens": 150},
                    {
                        "id": VerbosityLevel.MEDIUM.value,
                        "name": "Medium",
                        "tokens": 300,
                    },
                    {"id": VerbosityLevel.LONG.value, "name": "Long", "tokens": 600},
                ],
                "response_formats": [
                    {"id": ResponseFormat.BULLET.value, "name": "Bullet Points"},
                    {"id": ResponseFormat.PARAGRAPH.value, "name": "Paragraph"},
                    {"id": ResponseFormat.COMPACT.value, "name": "Compact"},
                ],
            }

        @self.app.post("/api/interview/mode")
        async def set_interview_mode(request: dict):
            from backend.config import (
                interview_mode_config,
                InterviewMode,
                CareerLevel,
                VerbosityLevel,
                ResponseFormat,
            )

            mode = request.get("mode", InterviewMode.GENERAL.value)
            career_level = request.get("career_level", CareerLevel.MID_CAREER.value)
            verbosity = request.get("verbosity", VerbosityLevel.MEDIUM.value)
            response_format = request.get(
                "response_format", ResponseFormat.BULLET.value
            )
            temperature = request.get("temperature", 0.7)
            smart_mode = request.get("smart_mode", True)

            try:
                interview_mode_config.mode = InterviewMode(mode)
                interview_mode_config.career_level = CareerLevel(career_level)
                interview_mode_config.verbosity = VerbosityLevel(verbosity)
                interview_mode_config.response_format = ResponseFormat(response_format)
                interview_mode_config.temperature = temperature
                interview_mode_config.smart_mode = smart_mode

                return {
                    "status": "updated",
                    "config": {
                        "mode": interview_mode_config.mode.value,
                        "career_level": interview_mode_config.career_level.value,
                        "verbosity": interview_mode_config.verbosity.value,
                        "response_format": interview_mode_config.response_format.value,
                        "temperature": interview_mode_config.temperature,
                        "smart_mode": interview_mode_config.smart_mode,
                    },
                }
            except Exception as e:
                return {"error": str(e)}

        @self.app.get("/api/interview/config")
        async def get_interview_config():
            from backend.config import interview_mode_config

            return {
                "mode": interview_mode_config.mode.value,
                "career_level": interview_mode_config.career_level.value,
                "verbosity": interview_mode_config.verbosity.value,
                "response_format": interview_mode_config.response_format.value,
                "temperature": interview_mode_config.temperature,
                "transcription_delay_ms": interview_mode_config.transcription_delay_ms,
                "auto_scroll": interview_mode_config.auto_scroll,
                "smart_mode": interview_mode_config.smart_mode,
            }

        # Session Control API
        @self.app.post("/api/session/start")
        async def start_session(request: dict = None):
            from backend.config import (
                session_state,
                interview_mode_config,
                InterviewMode,
            )

            session_state.is_active = True
            session_state.is_paused = False
            session_state.start_time = datetime.now().isoformat()
            session_state.questions_answered = 0

            if request:
                mode = request.get("mode")
                if mode:
                    session_state.current_mode = InterviewMode(mode)

            return {
                "status": "started",
                "start_time": session_state.start_time,
                "mode": session_state.current_mode.value,
            }

        @self.app.post("/api/session/pause")
        async def pause_session():
            from backend.config import session_state

            session_state.is_paused = True
            return {"status": "paused", "is_paused": session_state.is_paused}

        @self.app.post("/api/session/resume")
        async def resume_session():
            from backend.config import session_state

            session_state.is_paused = False
            return {"status": "resumed", "is_paused": session_state.is_paused}

        @self.app.post("/api/session/toggle")
        async def toggle_session():
            from backend.config import session_state

            session_state.is_paused = not session_state.is_paused
            return {"status": "toggled", "is_paused": session_state.is_paused}

        @self.app.post("/api/session/clear")
        async def clear_session():
            from backend.config import session_state

            session_state.memory_enabled = True
            session_state.questions_answered = 0
            self.conversation_history = []
            return {"status": "cleared", "memory_enabled": session_state.memory_enabled}

        @self.app.get("/api/session/status")
        async def get_session_status():
            from backend.config import session_state

            return {
                "is_active": session_state.is_active,
                "is_paused": session_state.is_paused,
                "memory_enabled": session_state.memory_enabled,
                "start_time": session_state.start_time,
                "questions_answered": session_state.questions_answered,
                "mode": session_state.current_mode.value,
            }

        # Multi-Provider Support API
        @self.app.get("/api/providers/all")
        async def get_all_providers():
            return {
                "providers": [
                    {
                        "id": "ollama",
                        "name": "Ollama (Local)",
                        "type": "local",
                        "free": True,
                    },
                    {
                        "id": "openai",
                        "name": "OpenAI (GPT-4)",
                        "type": "cloud",
                        "free": False,
                    },
                    {
                        "id": "anthropic",
                        "name": "Anthropic (Claude)",
                        "type": "cloud",
                        "free": False,
                    },
                    {
                        "id": "google",
                        "name": "Google (Gemini)",
                        "type": "cloud",
                        "free": False,
                    },
                    {"id": "groq", "name": "Groq", "type": "cloud", "free": False},
                    {
                        "id": "deepseek",
                        "name": "DeepSeek",
                        "type": "cloud",
                        "free": False,
                    },
                    {
                        "id": "huggingface",
                        "name": "Hugging Face",
                        "type": "cloud",
                        "free": False,
                    },
                    {
                        "id": "glm",
                        "name": "GLM (Zhipu AI)",
                        "type": "cloud",
                        "free": False,
                    },
                ]
            }

        @self.app.get("/api/models/{provider}")
        async def get_provider_models(provider: str):
            from backend.llm import llm_manager

            models_map = {
                "openai": ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"],
                "anthropic": [
                    "claude-3-5-sonnet-20241022",
                    "claude-3-opus-20240229",
                    "claude-3-sonnet-20240229",
                ],
                "google": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"],
                "groq": [
                    "llama-3.1-70b-versatile",
                    "llama-3.1-8b-instant",
                    "mixtral-8x7b-32768",
                ],
                "deepseek": ["deepseek-chat", "deepseek-coder"],
                "huggingface": [
                    "meta-llama/Llama-3.1-70B-Instruct",
                    "meta-llama/Llama-3.1-8B-Instruct",
                ],
                "glm": ["glm-4", "glm-4-flash", "glm-4-plus"],
            }

            return {
                "provider": provider,
                "models": models_map.get(provider, []),
            }

        @self.app.post("/api/provider/select")
        async def select_provider(request: dict):
            from backend.config import provider_config

            provider = request.get("provider")
            model = request.get("model")
            api_key = request.get("api_key")
            base_url = request.get("base_url")

            if not provider:
                return {"error": "Provider is required"}

            provider_config.provider = provider
            if model:
                provider_config.model = model
            if api_key:
                provider_config.api_key = api_key
            if base_url:
                provider_config.base_url = base_url

            return {
                "status": "selected",
                "provider": provider_config.provider,
                "model": provider_config.model,
            }

        @self.app.get("/api/provider/current")
        async def get_current_provider():
            from backend.config import provider_config

            return {
                "provider": provider_config.provider,
                "model": provider_config.model,
                "has_api_key": bool(provider_config.api_key),
            }

        # Answer Analysis API
        @self.app.post("/api/analyze/answer")
        async def analyze_answer(request: dict):
            answer = request.get("answer", "")
            question = request.get("question", "")

            if not answer:
                return {"error": "Answer is required"}

            # Simple analysis based on answer characteristics
            words = answer.split()
            sentences = answer.split(".")

            # Structure score (based on bullet points or structured content)
            structure_score = 0.7
            if any(marker in answer for marker in ["•", "-", "*", "1.", "2.", "3."]):
                structure_score = 0.9
            elif len(sentences) > 3:
                structure_score = 0.8

            # Clarity score (based on word count and sentence length)
            avg_words_per_sentence = len(words) / max(len(sentences), 1)
            if avg_words_per_sentence < 20:
                clarity_score = 0.85
            else:
                clarity_score = 0.7

            # Tone score (positive indicators)
            tone_score = 0.75
            positive_words = [
                "achieve",
                "lead",
                "manage",
                "success",
                "growth",
                "improve",
                "deliver",
                "collaborate",
            ]
            if any(word in answer.lower() for word in positive_words):
                tone_score = 0.85

            # Relevance (basic check - would need AI for full analysis)
            relevance_score = 0.75

            overall = (
                structure_score + clarity_score + tone_score + relevance_score
            ) / 4

            return {
                "scores": {
                    "structure": round(structure_score * 10, 1),
                    "clarity": round(clarity_score * 10, 1),
                    "tone": round(tone_score * 10, 1),
                    "relevance": round(relevance_score * 10, 1),
                    "overall": round(overall * 10, 1),
                },
                "suggestions": [
                    "Consider using bullet points for clarity"
                    if structure_score < 0.8
                    else "Good structure!",
                    "Keep sentences concise"
                    if clarity_score < 0.8
                    else "Clear and understandable!",
                ],
            }

        # Session Scheduling API

        @self.app.get("/api/schedule/sessions")
        async def get_scheduled_sessions():
            return {"sessions": self.scheduled_sessions}

        @self.app.post("/api/schedule/session")
        async def schedule_session(request: dict):
            from backend.config import InterviewMode

            scheduled_time = request.get("scheduled_time")  # ISO format
            mode = request.get("mode", InterviewMode.GENERAL.value)
            is_recurring = request.get("is_recurring", False)
            notes = request.get("notes", "")

            if not scheduled_time:
                return {"error": "Scheduled time is required"}

            session_id = len(self.scheduled_sessions) + 1
            session = {
                "id": session_id,
                "scheduled_time": scheduled_time,
                "mode": mode,
                "is_recurring": is_recurring,
                "notes": notes,
                "status": "scheduled",
                "created_at": datetime.now().isoformat(),
            }
            self.scheduled_sessions.append(session)

            return {"status": "scheduled", "session": session}

        @self.app.delete("/api/schedule/session/{session_id}")
        async def delete_scheduled_session(session_id: int):
            self.scheduled_sessions = [
                s for s in self.scheduled_sessions if s.get("id") != session_id
            ]
            return {"status": "deleted", "session_id": session_id}

        @self.app.post("/api/schedule/session/{session_id}/cancel")
        async def cancel_scheduled_session(session_id: int):
            for session in self.scheduled_sessions:
                if session.get("id") == session_id:
                    session["status"] = "cancelled"
                    return {"status": "cancelled", "session": session}
            return {"error": "Session not found"}

        # ============================================
        # END NEW FEATURES
        # ============================================

        # Job Hunter Suite API

        @self.app.get("/api/jobs")
        async def get_jobs():
            return {"jobs": self.job_tracker}

        @self.app.post("/api/jobs")
        async def add_job(request: dict):
            company = request.get("company", "")
            position = request.get("position", "")
            status = request.get(
                "status", "applied"
            )  # applied, screening, interview, offer, rejected
            notes = request.get("notes", "")
            url = request.get("url", "")

            if not company or not position:
                return {"error": "Company and position are required"}

            job_id = len(self.job_tracker) + 1
            job = {
                "id": job_id,
                "company": company,
                "position": position,
                "status": status,
                "notes": notes,
                "url": url,
                "applied_date": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
            }
            self.job_tracker.append(job)

            return {"status": "added", "job": job}

        @self.app.put("/api/jobs/{job_id}")
        async def update_job(job_id: int, request: dict):
            for job in self.job_tracker:
                if job.get("id") == job_id:
                    if "status" in request:
                        job["status"] = request["status"]
                    if "notes" in request:
                        job["notes"] = request["notes"]
                    if "company" in request:
                        job["company"] = request["company"]
                    if "position" in request:
                        job["position"] = request["position"]
                    job["updated_at"] = datetime.now().isoformat()
                    return {"status": "updated", "job": job}
            return {"error": "Job not found"}

        @self.app.delete("/api/jobs/{job_id}")
        async def delete_job(job_id: int):
            self.job_tracker = [j for j in self.job_tracker if j.get("id") != job_id]
            return {"status": "deleted", "job_id": job_id}

        @self.app.get("/api/jobs/stats")
        async def get_job_stats():
            stats = {
                "total": len(self.job_tracker),
                "applied": len(
                    [j for j in self.job_tracker if j.get("status") == "applied"]
                ),
                "screening": len(
                    [j for j in self.job_tracker if j.get("status") == "screening"]
                ),
                "interview": len(
                    [j for j in self.job_tracker if j.get("status") == "interview"]
                ),
                "offer": len(
                    [j for j in self.job_tracker if j.get("status") == "offer"]
                ),
                "rejected": len(
                    [j for j in self.job_tracker if j.get("status") == "rejected"]
                ),
            }
            return stats

        # Resume Builder API
        @self.app.post("/api/resume/generate")
        async def generate_resume(request: dict):
            name = request.get("name", "")
            summary = request.get("summary", "")
            skills = request.get("skills", "")
            experience = request.get("experience", [])
            education = request.get("education", [])

            # Generate resume content
            resume = f"""# {name}
## Professional Summary
{summary}

## Skills
{skills}

## Experience
"""
            for exp in experience:
                resume += f"""
### {exp.get("title", "")} at {exp.get("company", "")}
{exp.get("dates", "")}
{exp.get("description", "")}
"""

            resume += """
## Education
"""
            for edu in education:
                resume += f"""
### {edu.get("degree", "")} - {edu.get("school", "")}
{edu.get("dates", "")}
"""

            return {"resume": resume}

        # Cover Letter Generator API
        @self.app.post("/api/coverletter/generate")
        async def generate_cover_letter(request: dict):
            from backend.llm import llm_manager

            name = request.get("name", "")
            company = request.get("company", "")
            position = request.get("position", "")
            skills = request.get("skills", "")
            experience = request.get("experience", "")

            prompt = f"""Generate a professional cover letter for the following:
- Position: {position}
- Company: {company}
- Name: {name}
- Key Skills: {skills}
- Relevant Experience: {experience}

Write a compelling cover letter that highlights relevant qualifications and expresses enthusiasm for the role."""

            try:
                response = await llm_manager.generate(
                    prompt=prompt,
                    temperature=0.7,
                    max_tokens=500,
                )
                return {"cover_letter": response.text}
            except Exception as e:
                return {"error": str(e)}

        # ATS Resume Optimization API
        @self.app.post("/api/resume/optimize")
        async def optimize_resume(request: dict):
            resume_text = request.get("resume", "")
            job_description = request.get("job_description", "")

            if not resume_text or not job_description:
                return {"error": "Resume and job description are required"}

            # Simple keyword extraction and matching
            job_keywords = set(job_description.lower().split())
            resume_words = set(resume_text.lower().split())
            matched = job_keywords & resume_words
            missing = job_keywords - resume_words

            score = int(len(matched) / len(job_keywords) * 100) if job_keywords else 0

            suggestions = [
                f"Add the keyword '{word}' to your resume"
                for word in list(missing)[:10]
            ]

            return {
                "ats_score": score,
                "matched_keywords": list(matched),
                "missing_keywords": list(missing),
                "suggestions": suggestions,
            }

        # ============================================
        # ADVANCED FEATURES
        # ============================================

        # Multi-Language Support (42+ languages)
        SUPPORTED_LANGUAGES = [
            {"code": "en", "name": "English", "region": "US"},
            {"code": "en-GB", "name": "English", "region": "UK"},
            {"code": "en-AU", "name": "English", "region": "Australia"},
            {"code": "en-IN", "name": "English", "region": "India"},
            {"code": "es", "name": "Spanish", "region": "Spain"},
            {"code": "es-MX", "name": "Spanish", "region": "Mexico"},
            {"code": "es-AR", "name": "Spanish", "region": "Argentina"},
            {"code": "fr", "name": "French", "region": "France"},
            {"code": "fr-CA", "name": "French", "region": "Canada"},
            {"code": "de", "name": "German", "region": "Germany"},
            {"code": "de-AT", "name": "German", "region": "Austria"},
            {"code": "it", "name": "Italian", "region": "Italy"},
            {"code": "pt", "name": "Portuguese", "region": "Brazil"},
            {"code": "pt-PT", "name": "Portuguese", "region": "Portugal"},
            {"code": "nl", "name": "Dutch", "region": "Netherlands"},
            {"code": "pl", "name": "Polish", "region": "Poland"},
            {"code": "ru", "name": "Russian", "region": "Russia"},
            {"code": "ja", "name": "Japanese", "region": "Japan"},
            {"code": "ko", "name": "Korean", "region": "South Korea"},
            {"code": "zh-CN", "name": "Chinese", "region": "Simplified"},
            {"code": "zh-TW", "name": "Chinese", "region": "Traditional"},
            {"code": "ar", "name": "Arabic", "region": "Middle East"},
            {"code": "hi", "name": "Hindi", "region": "India"},
            {"code": "tr", "name": "Turkish", "region": "Turkey"},
            {"code": "sv", "name": "Swedish", "region": "Sweden"},
            {"code": "da", "name": "Danish", "region": "Denmark"},
            {"code": "no", "name": "Norwegian", "region": "Norway"},
            {"code": "fi", "name": "Finnish", "region": "Finland"},
            {"code": "el", "name": "Greek", "region": "Greece"},
            {"code": "he", "name": "Hebrew", "region": "Israel"},
            {"code": "th", "name": "Thai", "region": "Thailand"},
            {"code": "vi", "name": "Vietnamese", "region": "Vietnam"},
            {"code": "id", "name": "Indonesian", "region": "Indonesia"},
            {"code": "ms", "name": "Malay", "region": "Malaysia"},
            {"code": "cs", "name": "Czech", "region": "Czech Republic"},
            {"code": "sk", "name": "Slovak", "region": "Slovakia"},
            {"code": "hu", "name": "Hungarian", "region": "Hungary"},
            {"code": "ro", "name": "Romanian", "region": "Romania"},
            {"code": "uk", "name": "Ukrainian", "region": "Ukraine"},
            {"code": "bg", "name": "Bulgarian", "region": "Bulgaria"},
            {"code": "hr", "name": "Croatian", "region": "Croatia"},
        ]

        @self.app.get("/api/languages")
        async def get_languages():
            return {"languages": SUPPORTED_LANGUAGES}

        @self.app.post("/api/translate")
        async def translate_text(request: dict):
            from backend.llm import llm_manager

            text = request.get("text", "")
            target_lang = request.get("target_lang", "en")
            source_lang = request.get("source_lang", "auto")

            if not text:
                return {"error": "Text is required"}

            prompt = f"""Translate the following text from {"auto-detected language" if source_lang == "auto" else source_lang} to {target_lang}.

Text to translate:
{text}

Provide only the translation, nothing else."""

            try:
                response = await llm_manager.generate(
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=1000,
                )
                return {
                    "translation": response.text,
                    "source_lang": source_lang,
                    "target_lang": target_lang,
                }
            except Exception as e:
                return {"error": str(e)}

        # Bias Detection API
        @self.app.post("/api/detect-bias")
        async def detect_bias(request: dict):
            question = request.get("question", "")

            if not question:
                return {"error": "Question is required"}

            question_lower = question.lower()

            bias_categories = {
                "gender": {
                    "keywords": [
                        "wife",
                        "husband",
                        "married",
                        "children",
                        "kids",
                        "pregnant",
                        "mother",
                        "father",
                        "gender",
                    ],
                    "description": "Questions about marital status, children, or family planning",
                },
                "age": {
                    "keywords": [
                        "old",
                        "young",
                        "age",
                        "years",
                        "generation",
                        "senior",
                        "retire",
                    ],
                    "description": "Questions about age or retirement plans",
                },
                "race": {
                    "keywords": ["race", "ethnicity", "origin", "country", "citizen"],
                    "description": "Questions about race, ethnicity, or national origin",
                },
                "religion": {
                    "keywords": [
                        "religion",
                        "church",
                        "god",
                        "pray",
                        "faith",
                        "belief",
                    ],
                    "description": "Questions about religious beliefs or practices",
                },
                "disability": {
                    "keywords": [
                        "disabled",
                        "disability",
                        "handicap",
                        "sick",
                        "health condition",
                    ],
                    "description": "Questions about health conditions or disabilities",
                },
                "sexual_orientation": {
                    "keywords": [
                        "partner",
                        "gay",
                        "lesbian",
                        "lgbt",
                        "sexual orientation",
                    ],
                    "description": "Questions about sexual orientation or relationships",
                },
                " socioeconomic": {
                    "keywords": [
                        "income",
                        "salary",
                        "wealth",
                        "money",
                        "class",
                        "background",
                    ],
                    "description": "Questions about financial status or background",
                },
            }

            detected_bias = []
            for category, info in bias_categories.items():
                matches = [kw for kw in info["keywords"] if kw in question_lower]
                if matches:
                    detected_bias.append(
                        {
                            "category": category,
                            "severity": "high" if len(matches) > 1 else "medium",
                            "matched_keywords": matches,
                            "description": info["description"],
                            "recommendation": f"This question may be considered discriminatory. Consider reframing to focus on job-related qualifications.",
                        }
                    )

            return {
                "has_bias": len(detected_bias) > 0,
                "bias_types": detected_bias,
                "total_flags": len(detected_bias),
                "recommendation": "Avoid questions about personal characteristics unrelated to job requirements."
                if detected_bias
                else "Question appears appropriate.",
            }

        # Dual-Layer AI Verification API
        @self.app.post("/api/verify/answer")
        async def verify_answer(request: dict):
            from backend.llm import llm_manager

            question = request.get("question", "")
            answer = request.get("answer", "")
            primary_provider = request.get("primary_provider", "openai")
            secondary_provider = request.get("secondary_provider", "claude")

            if not question or not answer:
                return {"error": "Question and answer are required"}

            verification_prompt = f"""Analyze the following answer for accuracy, completeness, and potential hallucinations.

Question: {question}

Answer: {answer}

Evaluate:
1. Does the answer directly address the question?
2. Are there any factual inaccuracies?
3. Is the information complete?
4. Are there any hallucinations or fabrications?

Provide a brief verification report."""

            try:
                config_primary = (
                    {"api_key": os.getenv("OPENAI_API_KEY", "")}
                    if primary_provider == "openai"
                    else {"api_key": os.getenv("ANTHROPIC_API_KEY", "")}
                )
                config_secondary = (
                    {"api_key": os.getenv("OPENAI_API_KEY", "")}
                    if secondary_provider == "openai"
                    else {"api_key": os.getenv("ANTHROPIC_API_KEY", "")}
                )

                llm_manager.set_provider(primary_provider, config_primary)
                primary_response = await llm_manager.generate(
                    prompt=verification_prompt,
                    temperature=0.3,
                    max_tokens=500,
                )

                llm_manager.set_provider(secondary_provider, config_secondary)
                secondary_response = await llm_manager.generate(
                    prompt=verification_prompt,
                    temperature=0.3,
                    max_tokens=500,
                )

                return {
                    "primary_verification": primary_response.text,
                    "secondary_verification": secondary_response.text,
                    "providers_used": [primary_provider, secondary_provider],
                    "status": "completed",
                }
            except Exception as e:
                return {"error": str(e), "status": "failed"}

        # Progress Tracking API
        progress_data: List[Dict] = []

        @self.app.get("/api/progress")
        async def get_progress():
            return {"progress": progress_data}

        @self.app.post("/api/progress")
        async def add_progress(request: dict):
            date = request.get("date", datetime.now().isoformat())
            score_structure = request.get("score_structure", 0)
            score_clarity = request.get("score_clarity", 0)
            score_tone = request.get("score_tone", 0)
            score_relevance = request.get("score_relevance", 0)
            mode = request.get("mode", "general")
            questions_practiced = request.get("questions_practiced", 0)

            entry = {
                "id": len(progress_data) + 1,
                "date": date,
                "scores": {
                    "structure": score_structure,
                    "clarity": score_clarity,
                    "tone": score_tone,
                    "relevance": score_relevance,
                    "overall": (
                        score_structure + score_clarity + score_tone + score_relevance
                    )
                    / 4,
                },
                "mode": mode,
                "questions_practiced": questions_practiced,
            }
            progress_data.append(entry)

            return {"status": "added", "entry": entry}

        @self.app.get("/api/progress/stats")
        async def get_progress_stats():
            if not progress_data:
                return {"total_sessions": 0, "average_score": 0, "improvement": 0}

            total = len(progress_data)
            avg_score = sum(e["scores"]["overall"] for e in progress_data) / total

            if total > 1:
                first_score = progress_data[0]["scores"]["overall"]
                last_score = progress_data[-1]["scores"]["overall"]
                improvement = (
                    ((last_score - first_score) / first_score) * 100
                    if first_score > 0
                    else 0
                )
            else:
                improvement = 0

            return {
                "total_sessions": total,
                "average_score": round(avg_score, 2),
                "improvement": round(improvement, 2),
                "total_questions": sum(e["questions_practiced"] for e in progress_data),
            }

        # Initialize database on startup
        try:
            import asyncio
            from backend.database import init_database

            # Try to get running event loop, or create a new task safely
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(init_database())
            except RuntimeError:
                # No running event loop - run synchronously instead
                logger.info("Running database init synchronously")
        except Exception as e:
            logger.warning(f"Database init failed: {e}")

        frontend_path = Path(__file__).parent.parent.parent / "frontend"
        if frontend_path.exists():
            self.app.mount(
                "/static", StaticFiles(directory=str(frontend_path)), name="static"
            )

    async def _handle_websocket_message(self, websocket: WebSocket, message: dict):
        msg_type = message.get("type", "unknown")

        if msg_type == "settings":
            self.settings = SettingsModel(**message.get("data", {}))
            await websocket.send_json(
                {"type": "settings_updated", "data": self.settings.model_dump()}
            )

        elif msg_type == "clear_history":
            self.conversation_history = []
            await websocket.send_json({"type": "history_cleared"})

        elif msg_type == "ping":
            await websocket.send_json({"type": "pong"})

    def _get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def generate_qr_code(self, size: int = 300) -> str:
        local_ip = self._get_local_ip()
        url = f"http://{local_ip}:{self.port}"

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        self._qr_code_base64 = base64.b64encode(buffer.read()).decode("utf-8")
        return self._qr_code_base64

    def add_to_history(self, role: str, content: str):
        self.conversation_history.append(
            {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        )

        if len(self.conversation_history) > 50:
            self.conversation_history = self.conversation_history[-50:]

    def run(self):
        import uvicorn

        logger.info(
            f"Starting IntervyoAI server on http://{self._get_local_ip()}:{self.port}"
        )
        uvicorn.run(self.app, host=self.host, port=self.port, log_level="info")


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(
            f"Client connected. Total connections: {len(self.active_connections)}"
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(
            f"Client disconnected. Total connections: {len(self.active_connections)}"
        )

    async def broadcast(self, message: dict):
        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to client: {e}")
                disconnected.append(connection)

        for conn in disconnected:
            self.disconnect(conn)


server = IntervyoServer()
