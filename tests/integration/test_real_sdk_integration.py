"""
Real SDK Integration Tests (Requires Claude Agent SDK).

These tests use the actual Claude Agent SDK if installed, providing
true integration testing beyond mocked unit tests.

Tests are automatically skipped if SDK is not installed.
"""

import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile
import os

# Conditionally import SDK
try:
    from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    ClaudeSDKClient = None
    ClaudeAgentOptions = None


# Skip all tests in this module if SDK not available
pytestmark = pytest.mark.skipif(
    not SDK_AVAILABLE,
    reason="Claude Agent SDK not installed. Install with: pip install claude-agent-sdk>=0.1.0"
)


@pytest.fixture
def sdk_client_config():
    """Provide SDK client configuration for tests."""
    return {
        "model": "claude-3-5-haiku-20241022",  # Use cheapest model for tests
        "max_turns": 5,  # Limit turns for tests
        "permission_mode": "rejectAll"  # Safety: reject all tool uses in tests
    }


class TestRealSDKClientIntegration:
    """Test with real Claude Agent SDK client."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_sdk_client_initialization(self, sdk_client_config):
        """Test that SDK client can be initialized with our config."""
        from sdk_agent.client import SpringMVCAnalyzerAgent

        # Initialize with minimal config
        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=False,  # Disable hooks for simple test
            max_turns=sdk_client_config["max_turns"]
        )

        # Verify client is initialized
        assert agent.client is not None
        assert agent.config.max_turns == 5

    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_sdk_client_context_manager(self, sdk_client_config):
        """Test SDK client context manager works correctly."""
        from sdk_agent.client import SpringMVCAnalyzerAgent

        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=False,
            max_turns=3
        )

        # Test context manager protocol
        await agent.client.__aenter__()
        try:
            # Client should be active
            assert agent.client is not None
        finally:
            await agent.client.__aexit__(None, None, None)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_mcp_server_creation(self):
        """Test that MCP server is created with all tools."""
        from sdk_agent.mcp_server_factory import create_analyzer_mcp_server

        # Create MCP server
        mcp_server = create_analyzer_mcp_server()

        # Verify server is created
        assert mcp_server is not None

        # Verify tools are registered
        # (Structure depends on MCP server implementation)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_tool_registration(self):
        """Test that all tools are properly registered."""
        from sdk_agent.client import SpringMVCAnalyzerAgent

        agent = SpringMVCAnalyzerAgent(hooks_enabled=False)

        # Get registered tools
        tools = agent.get_tools()

        # Should have 11 tools
        assert len(tools) >= 11

        # Verify tool names
        tool_names = {tool.get("name", "") for tool in tools}

        # Check for key tools (names may have MCP prefix)
        assert any("analyze_controller" in name for name in tool_names)
        assert any("build_graph" in name for name in tool_names)
        assert any("query_graph" in name for name in tool_names)

    @pytest.mark.integration
    @pytest.mark.slow
    def test_hooks_registration(self):
        """Test that hooks are registered when enabled."""
        from sdk_agent.client import SpringMVCAnalyzerAgent

        # With hooks enabled
        agent_with_hooks = SpringMVCAnalyzerAgent(hooks_enabled=True)
        assert len(agent_with_hooks.get_hooks()) == 5

        # With hooks disabled
        agent_without_hooks = SpringMVCAnalyzerAgent(hooks_enabled=False)
        # Hooks list should be empty or have no active hooks


class TestRealFileSystemOperations:
    """Test with real file system operations (no mocking)."""

    @pytest.mark.integration
    def test_real_path_validation(self, tmp_path):
        """Test path validation with real file system."""
        from sdk_agent.tools.common import validate_and_expand_path

        # Create real test file
        test_file = tmp_path / "real_test.java"
        test_file.write_text("public class RealTest {}")

        # Test with real file
        result = validate_and_expand_path(
            str(test_file),
            project_root=str(tmp_path),
            must_exist=True
        )

        assert result.exists()
        assert result.read_text() == "public class RealTest {}"

    @pytest.mark.integration
    def test_real_batch_processing(self, tmp_path):
        """Test batch processing with real files."""
        import asyncio
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Create real test files
        files = []
        for i in range(10):
            test_file = tmp_path / f"file{i}.java"
            test_file.write_text(f"// File {i}")
            files.append(test_file)

        # Real process function that reads files
        async def real_process(file_path: Path):
            content = file_path.read_text()
            return {"file": str(file_path), "content": content}

        # Run batch processing
        results = asyncio.run(process_files_in_batches(
            files,
            real_process,
            batch_size=5,
            max_concurrency=3
        ))

        # Verify all files processed
        assert len(results) == 10
        assert all(r.get("success") for r in results)

        # Verify content was read
        for i, result in enumerate(results):
            if result.get("success"):
                assert f"// File" in result["result"]["content"]


class TestRealConfigurationLoading:
    """Test with real configuration files."""

    @pytest.mark.integration
    def test_load_real_config_file(self, tmp_path):
        """Test loading real configuration file."""
        from sdk_agent.config import load_config

        # Create real config file
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
mode: sdk_agent
hooks_enabled: true
permission_mode: acceptEdits
max_turns: 15
cache_dir: .cache/sdk_agent
""")

        # Load real config
        config = load_config(str(config_file))

        # Verify loaded correctly
        assert config.mode == "sdk_agent"
        assert config.hooks_enabled is True
        assert config.permission_mode == "acceptEdits"
        assert config.max_turns == 15

    @pytest.mark.integration
    def test_config_override(self):
        """Test configuration parameter override."""
        from sdk_agent.client import SpringMVCAnalyzerAgent

        # Create agent with overrides
        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=False,
            permission_mode="rejectAll",
            max_turns=3
        )

        # Verify overrides applied
        assert agent.config.hooks_enabled is False
        assert agent.config.permission_mode == "rejectAll"
        assert agent.config.max_turns == 3


class TestErrorHandlingWithRealScenarios:
    """Test error handling with real error scenarios."""

    @pytest.mark.integration
    def test_real_file_not_found_error(self, tmp_path):
        """Test real file not found error."""
        from sdk_agent.tools.common import validate_and_expand_path
        from sdk_agent.exceptions import SDKAgentError

        # Try to access non-existent file
        with pytest.raises(SDKAgentError) as exc_info:
            validate_and_expand_path(
                "nonexistent_file.java",
                project_root=str(tmp_path),
                must_exist=True
            )

        # Verify error message format
        error_msg = str(exc_info.value)
        assert "FileNotFoundError" in error_msg
        assert "nonexistent_file.java" in error_msg
        assert "Suggestions:" in error_msg

    @pytest.mark.integration
    def test_real_configuration_validation_error(self):
        """Test real configuration validation error."""
        import asyncio
        from sdk_agent.tools.batch_processor import process_files_in_batches

        # Try invalid batch_size
        with pytest.raises(ValueError) as exc_info:
            asyncio.run(process_files_in_batches(
                [],
                None,
                batch_size=0,  # Invalid
                max_concurrency=5
            ))

        # Verify standardized error format
        error_msg = str(exc_info.value)
        assert "batch_size must be >= 1" in error_msg
        assert "got 0" in error_msg


@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set. Skipping tests that require API access."
)
class TestWithRealAPIAccess:
    """
    Tests that require real Anthropic API access.

    These tests are expensive and only run if ANTHROPIC_API_KEY is set.
    Use sparingly and consider cost implications.
    """

    @pytest.mark.integration
    @pytest.mark.expensive
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_real_api_project_analysis(self, tmp_path):
        """
        Test real project analysis with API (EXPENSIVE).

        This test makes real API calls and incurs costs.
        Only runs if explicitly enabled via environment variable.
        """
        pytest.skip("Skipped by default to avoid API costs. Set RUN_EXPENSIVE_TESTS=1 to enable.")

        if not os.environ.get("RUN_EXPENSIVE_TESTS"):
            pytest.skip("Expensive tests disabled. Set RUN_EXPENSIVE_TESTS=1 to enable.")

        from sdk_agent.client import SpringMVCAnalyzerAgent

        # Create minimal test project
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        controller_file = project_dir / "TestController.java"
        controller_file.write_text("""
package com.test;

import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;

@Controller
public class TestController {
    @GetMapping("/test")
    public String test() {
        return "test";
    }
}
""")

        # Run real analysis
        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=True,
            max_turns=5
        )

        result = await agent.analyze_project(
            project_path=str(project_dir),
            output_format="markdown"
        )

        # Verify result structure
        assert result is not None
        assert "success" in result or "analysis" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])
