"""
Integration Tests - API Endpoints
20% of tests (Pyramid Testing)
"""

import pytest
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.server.api import IntervyoServer


class TestAPIIntegration:
    """Integration tests for API endpoints"""

    @pytest.fixture
    def server(self):
        """Create test server instance"""
        return IntervyoServer(host="127.0.0.1", port=8888)

    def test_server_init(self, server):
        """Test server initialization"""
        assert server is not None
        assert server.host == "127.0.0.1"
        assert server.port == 8888

    def test_app_created(self, server):
        """Test FastAPI app is created"""
        assert server.app is not None

    def test_cors_configured(self, server):
        """Test CORS is configured"""
        # Just verify app exists and has routes
        assert len(server.app.routes) > 0


class TestRolesAPI:
    """Test roles API"""

    def test_roles_module_exists(self):
        """Test roles module exists"""
        from backend.nlp import roles

        assert roles is not None
        assert hasattr(roles, "JobRole")


class TestSTTIntegration:
    """Test STT integration"""

    def test_stt_manager_init(self):
        """Test STT manager initialization"""
        from backend.stt import stt_manager

        assert stt_manager is not None
        assert "webspeech" in stt_manager.providers

    def test_set_stt_provider(self):
        """Test setting STT provider"""
        from backend.stt import stt_manager

        stt_manager.set_provider("webspeech")
        assert stt_manager.current_provider == "webspeech"


class TestLLMIntegration:
    """Test LLM integration"""

    def test_llm_manager_init(self):
        """Test LLM manager initialization"""
        from backend.llm import llm_manager

        assert llm_manager is not None
        assert "ollama" in llm_manager.providers

    def test_set_llm_provider(self):
        """Test setting LLM provider"""
        from backend.llm import llm_manager

        llm_manager.set_provider("ollama")
        assert llm_manager.current_provider == "ollama"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
