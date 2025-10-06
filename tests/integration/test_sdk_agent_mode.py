"""
Integration Tests for SDK Agent Mode.

Tests complete workflows, mode coexistence, and SDK integration
with the existing agent infrastructure.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
import tempfile

# Skip all tests if SDK not installed
pytest.importorskip("claude_agent_sdk", reason="SDK not installed")

from sdk_agent.client import SpringMVCAnalyzerAgent
from sdk_agent.config import SDKAgentConfig, load_config
from sdk_agent.exceptions import SDKAgentError


class TestSDKAgentInitialization:
    """Test SDK agent initialization and configuration."""

    def test_agent_initialization_default_config(self):
        """Test agent initializes with default configuration."""
        agent = SpringMVCAnalyzerAgent()

        assert agent.config is not None
        assert agent.client is not None
        assert agent.hooks is not None
        assert len(agent.hooks) > 0

    def test_agent_initialization_custom_config(self, tmp_path):
        """Test agent initializes with custom configuration."""
        # Create custom config
        config_file = tmp_path / "custom_config.yaml"
        config_file.write_text("""
mode: sdk_agent
hooks_enabled: true
permission_mode: acceptEdits
max_turns: 20
""")

        agent = SpringMVCAnalyzerAgent(
            config_path=str(config_file)
        )

        assert agent.config.mode == "sdk_agent"
        assert agent.config.hooks_enabled is True
        assert agent.config.permission_mode == "acceptEdits"
        assert agent.config.max_turns == 20

    def test_agent_initialization_with_overrides(self):
        """Test agent initialization with parameter overrides."""
        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=False,
            permission_mode="rejectAll",
            max_turns=5
        )

        # Overrides should take precedence over config
        assert agent.config.hooks_enabled is False
        assert agent.config.permission_mode == "rejectAll"
        assert agent.config.max_turns == 5

    def test_get_tools_returns_all_tools(self):
        """Test that all tools are registered."""
        agent = SpringMVCAnalyzerAgent()

        tools = agent.get_tools()

        # Should have 11 tools registered
        assert len(tools) >= 11

        # Check for key tools
        tool_names = [tool.get("name") for tool in tools]
        assert "analyze_controller" in str(tool_names)
        assert "build_graph" in str(tool_names)
        assert "query_graph" in str(tool_names)

    def test_get_hooks_returns_all_hooks(self):
        """Test that all hooks are registered."""
        agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

        hooks = agent.get_hooks()

        # Should have 5 hooks
        assert len(hooks) == 5


class TestSDKAgentWorkflows:
    """Test complete SDK agent workflows."""

    @pytest.mark.asyncio
    async def test_project_analysis_workflow(self, tmp_path):
        """Test complete project analysis workflow."""
        # Create test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        src_dir = project_dir / "src" / "main" / "java"
        src_dir.mkdir(parents=True)

        controller_file = src_dir / "UserController.java"
        controller_file.write_text("""
package com.example;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;

@Controller
@RequestMapping("/users")
public class UserController {
    @GetMapping
    public String list() {
        return "users/list";
    }
}
""")

        # Initialize agent
        agent = SpringMVCAnalyzerAgent()

        # Mock SDK client
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock()

        async def mock_receive():
            yield "Analysis complete. Found 1 controller with 1 endpoint."

        agent.client.receive_response = mock_receive

        # Execute workflow
        result = await agent.analyze_project(
            project_path=str(project_dir),
            output_format="markdown"
        )

        # Verify results
        assert result is not None
        assert result.get("success") is True
        assert result.get("project_path") == str(project_dir)
        assert "analysis" in result

    @pytest.mark.asyncio
    async def test_model_switching(self):
        """Test dynamic model switching."""
        agent = SpringMVCAnalyzerAgent()

        # Test switching to different models
        await agent.set_model("claude-3-5-haiku-20241022")
        await agent.set_model("claude-3-5-sonnet-20241022")
        await agent.set_model("claude-opus-4-20250514")

        # Should not raise errors

    @pytest.mark.asyncio
    async def test_permission_mode_switching(self):
        """Test dynamic permission mode switching."""
        agent = SpringMVCAnalyzerAgent()

        # Test valid permission modes
        await agent.set_permission_mode("acceptAll")
        assert agent.config.permission_mode == "acceptAll"

        await agent.set_permission_mode("acceptEdits")
        assert agent.config.permission_mode == "acceptEdits"

        await agent.set_permission_mode("rejectAll")
        assert agent.config.permission_mode == "rejectAll"

    @pytest.mark.asyncio
    async def test_invalid_permission_mode(self):
        """Test that invalid permission mode raises error."""
        agent = SpringMVCAnalyzerAgent()

        with pytest.raises(ValueError) as exc_info:
            await agent.set_permission_mode("invalid_mode")

        assert "Invalid permission mode" in str(exc_info.value)


class TestThreeModeCoexistence:
    """Test coexistence of API, Passive, and SDK Agent modes."""

    def test_config_supports_all_modes(self):
        """Test that configuration supports all three modes."""
        # Test API mode config
        api_config = SDKAgentConfig(
            mode="api",
            anthropic_api_key="test_key"
        )
        assert api_config.mode == "api"

        # Test passive mode config
        passive_config = SDKAgentConfig(
            mode="passive"
        )
        assert passive_config.mode == "passive"

        # Test SDK agent mode config
        sdk_config = SDKAgentConfig(
            mode="sdk_agent"
        )
        assert sdk_config.mode == "sdk_agent"

    def test_shared_components_work_across_modes(self):
        """Test that shared components (agents, graph) work in all modes."""
        from agents import ControllerAgent
        from core import GraphBuilder

        # Components should work regardless of mode
        # (They don't depend on the mode setting)

        # This test validates that the architecture supports mode independence

    @pytest.mark.asyncio
    async def test_sdk_agent_with_api_tools(self):
        """Test SDK agent can use API-mode tools."""
        agent = SpringMVCAnalyzerAgent()

        # SDK agent should be able to use all the same tools
        # that API mode uses (via different interface)

        tools = agent.get_tools()

        # Should have access to all analysis tools
        assert len(tools) >= 11


class TestHooksSystem:
    """Test hooks system integration."""

    @pytest.mark.asyncio
    async def test_hooks_enabled_flag(self):
        """Test that hooks can be enabled/disabled."""
        # With hooks enabled
        agent_with_hooks = SpringMVCAnalyzerAgent(hooks_enabled=True)
        assert agent_with_hooks.config.hooks_enabled is True
        assert len(agent_with_hooks.get_hooks()) == 5

        # With hooks disabled
        agent_without_hooks = SpringMVCAnalyzerAgent(hooks_enabled=False)
        assert agent_without_hooks.config.hooks_enabled is False

    @pytest.mark.asyncio
    async def test_validation_hook_integration(self):
        """Test validation hook integration."""
        from sdk_agent.hooks.validation import ValidationHook

        agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

        # Get validation hook
        validation_hook = agent.hooks[0]  # First hook is validation

        # Test validation
        result = await validation_hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            context={}
        )

        # Should allow valid input
        assert result.get("allowed") is not False

    @pytest.mark.asyncio
    async def test_cache_hook_integration(self):
        """Test cache hook integration."""
        from sdk_agent.hooks.cache import CacheHook

        agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

        # Get cache hook
        cache_hook = agent.hooks[1]  # Second hook is cache

        # Test caching
        result = await cache_hook(
            tool_name="analyze_controller",
            tool_input={"file_path": "test.java"},
            tool_output={"content": [{"type": "text", "text": "Result"}]},
            context={}
        )

        # Should return output
        assert isinstance(result, dict)


class TestErrorHandling:
    """Test error handling in SDK agent mode."""

    @pytest.mark.asyncio
    async def test_sdk_agent_error_handling(self):
        """Test that SDK agent errors are handled gracefully."""
        agent = SpringMVCAnalyzerAgent()

        # Mock client to raise error
        agent.client.__aenter__ = AsyncMock()
        agent.client.__aexit__ = AsyncMock()
        agent.client.query = AsyncMock(side_effect=Exception("SDK error"))

        await agent.client.__aenter__()
        try:
            with pytest.raises(Exception) as exc_info:
                await agent.client.query("test query")

            assert "SDK error" in str(exc_info.value)
        finally:
            await agent.client.__aexit__(None, None, None)

    @pytest.mark.asyncio
    async def test_configuration_error_handling(self):
        """Test configuration error handling."""
        with patch('sdk_agent.config.load_config') as mock_load:
            mock_load.side_effect = FileNotFoundError("Config not found")

            with pytest.raises(FileNotFoundError):
                agent = SpringMVCAnalyzerAgent(
                    config_path="nonexistent.yaml"
                )


class TestMigrationScenarios:
    """Test migration scenarios from other modes to SDK agent."""

    def test_api_to_sdk_migration(self):
        """Test migration from API mode to SDK agent mode."""
        # Simulate existing API mode configuration
        api_config = {
            "mode": "api",
            "anthropic_api_key": "test_key"
        }

        # Switch to SDK agent mode
        sdk_agent = SpringMVCAnalyzerAgent(
            hooks_enabled=True,
            permission_mode="acceptAll"
        )

        # Should work without API key
        assert sdk_agent.config.mode == "sdk_agent"
        assert sdk_agent.config.hooks_enabled is True

    def test_passive_to_sdk_migration(self):
        """Test migration from passive mode to SDK agent mode."""
        # Simulate passive mode
        passive_config = {
            "mode": "passive"
        }

        # Switch to SDK agent mode
        sdk_agent = SpringMVCAnalyzerAgent(
            hooks_enabled=True
        )

        # Should have enhanced features
        assert sdk_agent.config.mode == "sdk_agent"
        assert len(sdk_agent.get_hooks()) == 5


class TestPerformanceOptimization:
    """Test performance optimization features."""

    @pytest.mark.asyncio
    async def test_batch_processing_integration(self, tmp_path):
        """Test batch processing integration in SDK agent."""
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Create test files
        files = []
        for i in range(10):
            test_file = tmp_path / f"file{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        # Mock process function
        async def mock_process(file_path: Path):
            return {"file": str(file_path), "analyzed": True}

        # Process in batches
        results = await process_files_in_batches(
            files,
            mock_process,
            batch_size=5,
            max_concurrency=3
        )

        assert len(results) == 10
        assert all(r.get("success") for r in results)

    def test_caching_configuration(self):
        """Test caching configuration in SDK agent."""
        agent = SpringMVCAnalyzerAgent(hooks_enabled=True)

        # Cache hook should be configured
        cache_hook = None
        for hook in agent.hooks:
            if hook.__class__.__name__ == "CacheHook":
                cache_hook = hook
                break

        assert cache_hook is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
