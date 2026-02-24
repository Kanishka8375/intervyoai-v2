"""
Smoke Tests - Quick Sanity Checks
10% of tests (Pyramid Testing)
"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestSmoke:
    """Quick smoke tests to verify basic functionality"""

    def test_backend_imports(self):
        """Test backend modules can be imported"""
        from backend import config
        from backend.llm import llm_manager
        from backend.stt import stt_manager
        from backend.multilingual import multilingual_manager
        from backend.fast_response import fast_response

        assert True

    def test_config_loads(self):
        """Test configuration loads"""
        from backend.config import server_settings

        assert server_settings.host is not None
        assert server_settings.port > 0

    def test_roles_exist(self):
        """Test roles module loads"""
        from backend.nlp import roles

        assert roles is not None

    def test_llm_providers_available(self):
        """Test LLM providers are available"""
        from backend.llm import llm_manager

        assert "ollama" in llm_manager.providers

    def test_stt_providers_available(self):
        """Test STT providers are available"""
        from backend.stt import stt_manager

        assert "webspeech" in stt_manager.providers

    def test_languages_available(self):
        """Test languages are available"""
        from backend.multilingual import multilingual_manager

        languages = multilingual_manager.get_language_list()
        assert len(languages) > 40

    def test_stealth_config(self):
        """Test stealth configuration"""
        from backend.stealth.advanced import AdvancedStealthConfig

        config = AdvancedStealthConfig()
        assert config.exclude_from_capture is True
        assert config.click_through is True


class TestSanity:
    """Sanity tests for critical functionality"""

    def test_fast_response_caching(self):
        """Test fast response caching works"""
        from backend.fast_response import fast_response

        fast_response.set_cached("test", "role", "provider", "result")
        cached = fast_response.get_cached("test", "role", "provider")
        assert cached == "result"
        fast_response.clear_cache()

    def test_multilingual_detection(self):
        """Test language detection"""
        from backend.multilingual import multilingual_manager

        lang = multilingual_manager.get_language("en")
        assert lang is not None
        assert lang.code == "en"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
