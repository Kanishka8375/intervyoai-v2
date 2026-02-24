"""
Unit Tests - Multilingual Module
70% of tests (Pyramid Testing)
"""

import pytest
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.multilingual import MultilingualManager, LANGUAGES


class TestMultilingualManager:
    """Test multilingual support"""

    def test_init(self):
        """Test multilingual manager initialization"""
        manager = MultilingualManager()
        assert manager.current_language is not None
        assert len(manager.supported_languages) > 0

    def test_get_language(self):
        """Test getting language config"""
        manager = MultilingualManager()
        lang = manager.get_language("en")
        assert lang is not None
        assert lang.code == "en"

    def test_set_language(self):
        """Test setting language"""
        manager = MultilingualManager()
        result = manager.set_language("es")
        assert result is True
        assert manager.current_language == "es"

    def test_set_invalid_language(self):
        """Test setting invalid language"""
        manager = MultilingualManager()
        result = manager.set_language("invalid_lang_xyz")
        assert result is False

    def test_get_language_list(self):
        """Test getting language list"""
        manager = MultilingualManager()
        languages = manager.get_language_list()
        assert isinstance(languages, list)
        assert len(languages) > 40  # At least 40 languages

    def test_get_stt_model(self):
        """Test getting STT model for language"""
        manager = MultilingualManager()
        model = manager.get_stt_model()
        assert model is not None
        assert isinstance(model, str)

    def test_system_language(self):
        """Test system language detection"""
        manager = MultilingualManager()
        sys_lang = manager.get_system_language()
        assert sys_lang is not None


class TestLanguages:
    """Test language configurations"""

    def test_english_support(self):
        """Test English is supported"""
        assert "en" in LANGUAGES
        assert LANGUAGES["en"].name == "English"

    def test_major_languages(self):
        """Test major languages are supported"""
        major_langs = ["en", "es", "fr", "de", "zh", "ja", "ko", "ru"]
        for lang in major_langs:
            assert lang in LANGUAGES, f"Missing language: {lang}"

    def test_language_codes(self):
        """Test all language codes are valid"""
        for code, config in LANGUAGES.items():
            assert config.code == code, f"Code mismatch for {code}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
