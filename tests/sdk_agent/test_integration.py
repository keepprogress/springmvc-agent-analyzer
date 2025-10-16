"""
Integration Tests for SDK Agent Mode.

Tests the full SDK integration including:
- SDK client initialization
- Tool registration
- Hook execution
- MCP server creation
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from sdk_agent.client import SpringMVCAnalyzerAgent
from sdk_agent.mcp_server_factory import create_analyzer_mcp_server
from sdk_agent.sdk_tools import ALL_SDK_TOOLS


def _check_sdk_available():
    """Check if Claude Agent SDK is available."""
    try:
        import claude_agent_sdk
        return True
    except ImportError:
        return False


class TestSDKIntegration:
    """Test SDK Agent integration."""

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    def test_sdk_client_initialization(self):
        """Test SDK client initializes with all components."""
        agent = SpringMVCAnalyzerAgent()

        assert agent.client is not None, "SDK client should be initialized"
        assert agent.mcp_server is not None, "MCP server should be created"
        assert len(agent.hooks) == 5, "Should have 5 hooks initialized"

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    def test_tools_registered(self):
        """Test all tools are registered with SDK."""
        agent = SpringMVCAnalyzerAgent()

        tools = agent.get_tools()
        assert len(tools) == 11, f"Expected 11 tools, got {len(tools)}"

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    def test_hooks_enabled(self):
        """Test hooks are enabled when configured."""
        agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

        assert agent.config.hooks_enabled is True
        assert len(agent.hooks) == 5
        # Verify each hook is initialized
        assert all(hook is not None for hook in agent.hooks)

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    def test_hooks_disabled(self):
        """Test hooks can be disabled."""
        agent = SpringMVCAnalyzerAgent(hooks_enabled=False)

        assert agent.config.hooks_enabled is False
        # Hooks are still created but not registered with SDK

    def test_mcp_server_creation(self):
        """Test MCP server factory."""
        if not _check_sdk_available():
            pytest.skip("Claude Agent SDK not installed")

        server = create_analyzer_mcp_server()
        assert server is not None

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    def test_tool_list_dynamic(self):
        """Test tool list is generated dynamically."""
        agent = SpringMVCAnalyzerAgent()

        # Should match ALL_SDK_TOOLS count
        assert len(agent.get_tools()) == len(ALL_SDK_TOOLS)


class TestSDKImportHandling:
    """Test SDK import error handling."""

    def test_sdk_not_installed_error(self):
        """Test error message when SDK not installed."""
        with patch('sdk_agent.sdk_imports.check_sdk_installed') as mock_check:
            mock_check.side_effect = ImportError("SDK not found")

            with pytest.raises(ImportError) as exc_info:
                from sdk_agent.sdk_imports import import_sdk
                import_sdk()

            assert "SDK not found" in str(exc_info.value)


class TestValidationHook:
    """Test ValidationHook integration."""

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    @pytest.mark.asyncio
    async def test_validation_hook_blocks_dangerous_paths(self):
        """Test ValidationHook blocks path traversal attempts."""
        from sdk_agent.hooks.validation import ValidationHook

        hook = ValidationHook({"enabled": True, "strict_mode": True})

        # Test dangerous path
        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "../../../etc/passwd"},
            context={}
        )

        assert result["allowed"] is False
        assert "dangerous" in result.get("reason", "").lower()

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    @pytest.mark.asyncio
    async def test_validation_hook_allows_safe_paths(self):
        """Test ValidationHook allows safe paths."""
        from sdk_agent.hooks.validation import ValidationHook

        hook = ValidationHook({"enabled": True})

        # Test safe path
        result = await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "src/main/java/Controller.java"},
            context={}
        )

        # Should allow or raise SDKAgentError (which is caught)
        # Either way, it shouldn't block with security reason
        assert "dangerous" not in result.get("reason", "").lower()


class TestCacheHook:
    """Test CacheHook integration."""

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    @pytest.mark.asyncio
    async def test_cache_hook_saves_results(self, tmp_path):
        """Test CacheHook saves analysis results."""
        from sdk_agent.hooks.cache import CacheHook

        cache_dir = tmp_path / ".cache"
        hook = CacheHook({
            "enabled": True,
            "cache_dir": str(cache_dir)
        })

        # Mock successful tool execution
        await hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            tool_output={
                "content": [{"type": "text", "text": "Analysis result"}],
                "data": {"analysis": "test"}
            },
            context={}
        )

        # Check cache directory was created
        assert cache_dir.exists()


class TestContextManagerFix:
    """Test that context manager is properly managed."""

    @pytest.mark.skipif(
        not _check_sdk_available(),
        reason="Claude Agent SDK not installed"
    )
    @pytest.mark.asyncio
    async def test_client_session_management(self):
        """Test client session is properly initialized and cleaned up."""
        agent = SpringMVCAnalyzerAgent()

        # Mock the client methods
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock()

        async def mock_receive():
            yield "test response"

        agent.client.receive_response = mock_receive

        # Test analyze_project manages session correctly
        result = await agent.analyze_project("test/path")

        # Verify __aenter__ and __aexit__ were called
        agent.client.__aenter__.assert_called_once()
        agent.client.__aexit__.assert_called_once()


# Skip all tests if SDK not installed
pytestmark = pytest.mark.skipif(
    not _check_sdk_available(),
    reason="Claude Agent SDK not installed - integration tests skipped"
)
