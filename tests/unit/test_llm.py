"""
Unit Tests - LLM Module
70% of tests (Pyramid Testing)
"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.llm import OllamaLLM, DeepSeekLLM, GLMLLM, LLMManager


class TestOllamaLLM:
    """Test Ollama LLM provider"""

    def test_ollama_init(self):
        """Test Ollama initialization"""
        llm = OllamaLLM(base_url="http://localhost:11434")
        assert llm.base_url == "http://localhost:11434"
        assert "llama" in llm.model.lower()

    def test_ollama_models_list(self):
        """Test listing models"""
        import asyncio

        llm = OllamaLLM()

        async def test():
            models = await llm.list_models()
            return models

        # Should return at least default model
        result = asyncio.run(test())
        assert isinstance(result, list)


class TestDeepSeekLLM:
    """Test DeepSeek LLM provider"""

    def test_deepseek_init(self):
        """Test DeepSeek initialization"""
        llm = DeepSeekLLM(api_key="test-key")
        assert llm.api_key == "test-key"
        assert llm.base_url == "https://api.deepseek.com"


class TestGLMLLM:
    """Test GLM LLM provider"""

    def test_glm_init(self):
        """Test GLM initialization"""
        llm = GLMLLM(api_key="test-key")
        assert llm.api_key == "test-key"


class TestLLMManager:
    """Test LLM Manager"""

    def test_manager_init(self):
        """Test manager initialization"""
        manager = LLMManager()
        assert "ollama" in manager.providers

    def test_set_provider(self):
        """Test setting provider"""
        manager = LLMManager()
        manager.set_provider("ollama", {"url": "http://localhost:11434"})
        assert manager.current_provider == "ollama"

    def test_current_provider(self):
        """Test getting current provider"""
        manager = LLMManager()
        assert manager.current_provider is not None
        assert manager.current_provider == "ollama"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
