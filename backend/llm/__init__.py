"""
LLM Integration Module
Supports Ollama, DeepSeek, HuggingFace, and GLM models
"""

import os
import json
import asyncio
from typing import Optional, Dict, List, AsyncGenerator
from dataclasses import dataclass
from abc import ABC, abstractmethod

import aiohttp
from loguru import logger


@dataclass
class LLMResponse:
    text: str
    model: str
    usage: Optional[Dict] = None
    finish_reason: Optional[str] = None


class BaseLLM(ABC):
    """Base class for LLM providers"""

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        pass

    @abstractmethod
    async def list_models(self) -> List[str]:
        pass


class OllamaLLM(BaseLLM):
    """Ollama local LLM provider"""

    def __init__(
        self, base_url: str = "http://localhost:11434", model: str = "llama3.1:latest"
    ):
        super().__init__(base_url=base_url)
        self.model = model

    def get_model(self) -> str:
        return self.model

    def set_model(self, model: str):
        self.model = model

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": False,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Ollama API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data.get("response", ""),
                        model=data.get("model", "llama3.2"),
                    )
        except asyncio.TimeoutError:
            raise Exception("Ollama request timed out")
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/api/generate"

        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "stream": True,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url, json=payload, timeout=aiohttp.ClientTimeout(total=120)
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Ollama API error: {error_text}")

                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Ollama stream error: {e}")
            raise

    async def list_models(self) -> List[str]:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags", timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list Ollama models: {e}")
        return ["llama3.2", "mistral", "codellama", "phi3"]


class DeepSeekLLM(BaseLLM):
    """DeepSeek cloud LLM provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.deepseek.com"):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("DeepSeek API key not configured")

        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"DeepSeek API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data["choices"][0]["message"]["content"],
                        model=data.get("model", "deepseek-chat"),
                        usage=data.get("usage"),
                        finish_reason=data["choices"][0].get("finish_reason"),
                    )
        except Exception as e:
            logger.error(f"DeepSeek error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise Exception("DeepSeek API key not configured")

        url = f"{self.base_url}/v1/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "deepseek-chat",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"DeepSeek API error: {error_text}")

                    async for line in resp.content:
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.error(f"DeepSeek stream error: {e}")
            raise

    async def list_models(self) -> List[str]:
        return ["deepseek-chat", "deepseek-coder"]


class HuggingFaceLLM(BaseLLM):
    """HuggingFace Inference API provider"""

    def __init__(
        self, api_key: str, base_url: str = "https://api-inference.huggingface.co"
    ):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("HuggingFace API key not configured")

        full_prompt = f"{system_prompt}\n\n" if system_prompt else ""
        full_prompt += prompt

        url = f"{self.base_url}/models/meta-llama/Llama-3.2-3B-Instruct"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "inputs": full_prompt,
            "parameters": {
                "temperature": temperature,
                "max_new_tokens": max_tokens,
                "return_full_text": False,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"HuggingFace API error: {error_text}")

                    data = await resp.json()
                    if isinstance(data, list) and len(data) > 0:
                        text = data[0].get("generated_text", "")
                    else:
                        text = str(data)

                    return LLMResponse(
                        text=text, model="meta-llama/Llama-3.2-3B-Instruct"
                    )
        except Exception as e:
            logger.error(f"HuggingFace error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        # HuggingFace doesn't support streaming for most models
        # Fall back to non-streaming
        response = await self.generate(prompt, system_prompt, temperature, max_tokens)
        yield response.text

    async def list_models(self) -> List[str]:
        return [
            "meta-llama/Llama-3.2-3B-Instruct",
            "meta-llama/Llama-3.1-8B-Instruct",
            "mistralai/Mistral-7B-Instruct-v0.2",
            "google/gemma-2-2b-it",
        ]


class GLMLLM(BaseLLM):
    """GLM (Zhipu AI) provider"""

    def __init__(
        self, api_key: str, base_url: str = "https://open.bigmodel.cn/api/paas/v4"
    ):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("GLM API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "glm-4-flash",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"GLM API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data["choices"][0]["message"]["content"],
                        model=data.get("model", "glm-4-flash"),
                        usage=data.get("usage"),
                        finish_reason=data["choices"][0].get("finish_reason"),
                    )
        except Exception as e:
            logger.error(f"GLM error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise Exception("GLM API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "glm-4-flash",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"GLM API error: {error_text}")

                    async for line in resp.content:
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.error(f"GLM stream error: {e}")
            raise

    async def list_models(self) -> List[str]:
        return ["glm-4-flash", "glm-4-plus", "glm-3-turbo"]


class ClaudeLLM(BaseLLM):
    """Anthropic Claude provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.anthropic.com"):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("Claude API key not configured")

        url = f"{self.base_url}/v1/messages"

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }

        messages = [{"role": "user", "content": prompt}]

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Claude API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data["content"][0]["text"],
                        model=data.get("model", "claude-3-5-sonnet"),
                    )
        except Exception as e:
            logger.error(f"Claude error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        response = await self.generate(prompt, system_prompt, temperature, max_tokens)
        yield response.text

    async def list_models(self) -> List[str]:
        return [
            "claude-3-5-sonnet-20241022",
            "claude-3-opus-20240229",
            "claude-3-haiku-20240307",
        ]


class GeminiLLM(BaseLLM):
    """Google Gemini provider"""

    def __init__(
        self, api_key: str, base_url: str = "https://generativelanguage.googleapis.com"
    ):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("Gemini API key not configured")

        url = f"{self.base_url}/v1beta/models/gemini-1.5-flash:generateContent"

        headers = {"Content-Type": "application/json"}

        full_prompt = f"{system_prompt}\n\n" if system_prompt else ""
        full_prompt += prompt

        payload = {
            "contents": [{"parts": [{"text": full_prompt}]}],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{url}?key={self.api_key}",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Gemini API error: {error_text}")

                    data = await resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    return LLMResponse(text=text, model="gemini-1.5-flash")
        except Exception as e:
            logger.error(f"Gemini error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        response = await self.generate(prompt, system_prompt, temperature, max_tokens)
        yield response.text

    async def list_models(self) -> List[str]:
        return ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-1.0-pro"]


class GrokLLM(BaseLLM):
    """xAI Grok provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.x.ai/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("Grok API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "grok-beta",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Grok API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data["choices"][0]["message"]["content"],
                        model=data.get("model", "grok-beta"),
                    )
        except Exception as e:
            logger.error(f"Grok error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "grok-beta",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Grok API error: {error_text}")

                    async for line in resp.content:
                        if line:
                            line = line.decode("utf-8")
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if "choices" in data and len(data["choices"]) > 0:
                                        delta = data["choices"][0].get("delta", {})
                                        if "content" in delta:
                                            yield delta["content"]
                                except json.JSONDecodeError:
                                    continue
        except Exception as e:
            logger.error(f"Grok stream error: {e}")
            raise

    async def list_models(self) -> List[str]:
        return ["grok-beta", "grok-2-1212"]


class OpenAILLM(BaseLLM):
    """OpenAI GPT provider"""

    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"OpenAI API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data["choices"][0]["message"]["content"],
                        model=data.get("model", "gpt-4o"),
                    )
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise Exception("OpenAI API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "gpt-4o",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"OpenAI API error: {error_text}")

                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"OpenAI stream error: {e}")
            raise

    async def list_models(self) -> List[str]:
        return ["gpt-4o", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]


class GroqLLM(BaseLLM):
    """Groq provider - fast inference"""

    def __init__(self, api_key: str, base_url: str = "https://api.groq.com/openai/v1"):
        super().__init__(api_key=api_key, base_url=base_url)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
    ) -> LLMResponse:
        if not self.api_key:
            raise Exception("Groq API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Groq API error: {error_text}")

                    data = await resp.json()
                    return LLMResponse(
                        text=data["choices"][0]["message"]["content"],
                        model=data.get("model", "llama-3.1-70b"),
                    )
        except Exception as e:
            logger.error(f"Groq error: {e}")
            raise

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise Exception("Groq API key not configured")

        url = f"{self.base_url}/chat/completions"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "llama-3.1-70b-versatile",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=120),
                ) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise Exception(f"Groq API error: {error_text}")

                    async for line in resp.content:
                        line = line.decode("utf-8").strip()
                        if line.startswith("data: "):
                            data_str = line[6:]
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                if "choices" in data and len(data["choices"]) > 0:
                                    delta = data["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        yield delta["content"]
                            except json.JSONDecodeError:
                                continue
        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            raise

    async def list_models(self) -> List[str]:
        return ["llama-3.1-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"]


class LLMManager:
    """Manager for multiple LLM providers"""

    def __init__(self):
        self.providers: Dict[str, BaseLLM] = {}
        self.current_provider: str = "ollama"
        self.ollama_url: str = "http://localhost:11434"
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize all LLM providers"""
        # Ollama - Local
        self.providers["ollama"] = OllamaLLM(base_url=self.ollama_url)

        # DeepSeek - Cloud
        deepseek_key = os.getenv("DEEPSEEK_API_KEY", "")
        if deepseek_key:
            self.providers["deepseek"] = DeepSeekLLM(api_key=deepseek_key)

        # HuggingFace - Cloud
        hf_key = os.getenv("HUGGINGFACE_API_KEY", "")
        if hf_key:
            self.providers["huggingface"] = HuggingFaceLLM(api_key=hf_key)

        # GLM - Cloud
        glm_key = os.getenv("GLM_API_KEY", "")
        if glm_key:
            self.providers["glm"] = GLMLLM(api_key=glm_key)

        # Claude - Cloud (Anthropic)
        claude_key = os.getenv("ANTHROPIC_API_KEY", "")
        if claude_key:
            self.providers["claude"] = ClaudeLLM(api_key=claude_key)

        # Gemini - Cloud (Google)
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key:
            self.providers["gemini"] = GeminiLLM(api_key=gemini_key)

        # Grok - Cloud (xAI)
        grok_key = os.getenv("GROK_API_KEY", "")
        if grok_key:
            self.providers["grok"] = GrokLLM(api_key=grok_key)

        # OpenAI - Cloud
        openai_key = os.getenv("OPENAI_API_KEY", "")
        if openai_key:
            self.providers["openai"] = OpenAILLM(api_key=openai_key)

        # Groq - Cloud (Fast inference)
        groq_key = os.getenv("GROQ_API_KEY", "")
        if groq_key:
            self.providers["groq"] = GroqLLM(api_key=groq_key)

        # Default to Ollama
        self.current_provider = "ollama"

    def set_provider(self, provider: str, config: Optional[Dict] = None):
        """Set the current LLM provider"""
        if provider not in self.providers:
            if provider == "ollama" and config:
                self.ollama_url = config.get("url", "http://localhost:11434")
                self.providers["ollama"] = OllamaLLM(base_url=self.ollama_url)
            elif provider == "deepseek" and config:
                self.providers["deepseek"] = DeepSeekLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get("base_url", "https://api.deepseek.com"),
                )
            elif provider == "huggingface" and config:
                self.providers["huggingface"] = HuggingFaceLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get(
                        "base_url", "https://api-inference.huggingface.co"
                    ),
                )
            elif provider == "glm" and config:
                self.providers["glm"] = GLMLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get(
                        "base_url", "https://open.bigmodel.cn/api/paas/v4"
                    ),
                )
            elif provider == "claude" and config:
                self.providers["claude"] = ClaudeLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get("base_url", "https://api.anthropic.com"),
                )
            elif provider == "gemini" and config:
                self.providers["gemini"] = GeminiLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get(
                        "base_url", "https://generativelanguage.googleapis.com"
                    ),
                )
            elif provider == "grok" and config:
                self.providers["grok"] = GrokLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get("base_url", "https://api.x.ai/v1"),
                )
            elif provider == "openai" and config:
                self.providers["openai"] = OpenAILLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get("base_url", "https://api.openai.com/v1"),
                )
            elif provider == "groq" and config:
                self.providers["groq"] = GroqLLM(
                    api_key=config.get("api_key", ""),
                    base_url=config.get("base_url", "https://api.groq.com/openai/v1"),
                )
            else:
                raise ValueError(f"Unknown provider: {provider}")

        self.current_provider = provider

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> LLMResponse:
        """Generate a response from the current provider"""
        provider = self.providers.get(self.current_provider)
        if not provider:
            raise Exception(f"Provider {self.current_provider} not configured")

        return await provider.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the current provider"""
        provider = self.providers.get(self.current_provider)
        if not provider:
            raise Exception(f"Provider {self.current_provider} not configured")

        async for token in provider.generate_stream(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        ):
            yield token

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


llm_manager = LLMManager()
