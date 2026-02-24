"""
Unit Tests - Fast Response Module
70% of tests (Pyramid Testing)
"""

import pytest
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.fast_response import FastResponseManager, FastResponseConfig


class TestFastResponseManager:
    """Test fast response manager"""

    def test_init(self):
        """Test initialization"""
        manager = FastResponseManager()
        assert manager.config.enable_caching is True
        assert manager._hit_count == 0
        assert manager._miss_count == 0

    def test_cache_key_generation(self):
        """Test cache key generation"""
        manager = FastResponseManager()
        key1 = manager._get_cache_key("test", "software_engineer", "ollama")
        key2 = manager._get_cache_key("test", "software_engineer", "ollama")
        assert key1 == key2  # Same inputs should generate same key

    def test_cache_key_different_inputs(self):
        """Test different inputs generate different keys"""
        manager = FastResponseManager()
        key1 = manager._get_cache_key("test1", "role1", "ollama")
        key2 = manager._get_cache_key("test2", "role2", "deepseek")
        assert key1 != key2

    def test_set_and_get_cached(self):
        """Test setting and getting cached response"""
        manager = FastResponseManager()
        manager.set_cached("test", "role", "ollama", "test response")
        result = manager.get_cached("test", "role", "ollama")
        assert result == "test response"

    def test_cache_miss(self):
        """Test cache miss returns None"""
        manager = FastResponseManager()
        result = manager.get_cached("nonexistent", "role", "ollama")
        assert result is None

    def test_cache_stats(self):
        """Test cache statistics"""
        manager = FastResponseManager()
        manager.set_cached("test", "role", "ollama", "response")
        manager.get_cached("test", "role", "ollama")
        stats = manager.get_stats()
        assert "hits" in stats
        assert "misses" in stats
        assert "cache_size" in stats

    def test_clear_cache(self):
        """Test clearing cache"""
        manager = FastResponseManager()
        manager.set_cached("test", "role", "ollama", "response")
        manager.clear_cache()
        result = manager.get_cached("test", "role", "ollama")
        assert result is None


class TestFastResponseConfig:
    """Test fast response configuration"""

    def test_default_config(self):
        """Test default configuration"""
        config = FastResponseConfig()
        assert config.enable_caching is True
        assert config.cache_ttl == 300
        assert config.max_cache_size == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
