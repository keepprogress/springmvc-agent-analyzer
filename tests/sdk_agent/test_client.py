"""Tests for SDK Agent client."""

import pytest
import tempfile
import os

from sdk_agent.client import SpringMVCAnalyzerAgent
from sdk_agent.exceptions import AgentNotInitializedError
from sdk_agent.constants import (
    SERVER_MODE_SDK_AGENT,
    PERMISSION_MODE_ACCEPT_EDITS,
    VALID_PERMISSION_MODES,
)


class TestSpringMVCAnalyzerAgent:
    """Test SpringMVCAnalyzerAgent class."""

    def test_initialization_default(self):
        """Test agent initialization with defaults."""
        agent = SpringMVCAnalyzerAgent()

        assert agent.config.mode == SERVER_MODE_SDK_AGENT
        assert agent.config.permission_mode == PERMISSION_MODE_ACCEPT_EDITS
        assert agent.config.hooks_enabled is True
        assert agent.system_prompt is not None

    def test_initialization_with_config(self):
        """Test agent initialization with config file."""
        config_data = """
server:
  mode: "sdk_agent"

sdk_agent:
  max_turns: 50
  permission_mode: "acceptAll"
  hooks_enabled: false
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(config_data)
            config_path = f.name

        try:
            agent = SpringMVCAnalyzerAgent(config_path=config_path)

            assert agent.config.max_turns == 50
            assert agent.config.permission_mode == "acceptAll"
            assert agent.config.hooks_enabled is False

        finally:
            os.unlink(config_path)

    def test_initialization_with_custom_prompt(self):
        """Test agent initialization with custom system prompt."""
        custom_prompt = "Custom analysis expert"

        agent = SpringMVCAnalyzerAgent(system_prompt=custom_prompt)

        assert agent.system_prompt == custom_prompt

    def test_initialization_override_params(self):
        """Test parameter overrides."""
        agent = SpringMVCAnalyzerAgent(
            hooks_enabled=False,
            permission_mode="acceptAll",
            max_turns=100
        )

        assert agent.config.hooks_enabled is False
        assert agent.config.permission_mode == "acceptAll"
        assert agent.config.max_turns == 100

    @pytest.mark.asyncio
    async def test_start_interactive_not_implemented(self):
        """Test start_interactive raises error (Phase 5)."""
        agent = SpringMVCAnalyzerAgent()

        with pytest.raises(
            AgentNotInitializedError,
            match="not yet implemented"
        ):
            await agent.start_interactive()

    @pytest.mark.asyncio
    async def test_analyze_project_not_implemented(self):
        """Test analyze_project raises error (Phase 5)."""
        agent = SpringMVCAnalyzerAgent()

        with pytest.raises(
            AgentNotInitializedError,
            match="not yet implemented"
        ):
            await agent.analyze_project("src/main/java")

    @pytest.mark.asyncio
    async def test_set_model_not_implemented(self):
        """Test set_model raises error (Phase 5)."""
        agent = SpringMVCAnalyzerAgent()

        with pytest.raises(
            AgentNotInitializedError,
            match="not yet implemented"
        ):
            await agent.set_model("claude-opus-4")

    @pytest.mark.asyncio
    async def test_set_permission_mode(self):
        """Test set_permission_mode."""
        agent = SpringMVCAnalyzerAgent()

        await agent.set_permission_mode("acceptAll")
        assert agent.config.permission_mode == "acceptAll"

        # Invalid mode
        with pytest.raises(ValueError, match="Invalid permission mode"):
            await agent.set_permission_mode("invalid")

    @pytest.mark.asyncio
    async def test_interrupt_not_implemented(self):
        """Test interrupt raises error (Phase 5)."""
        agent = SpringMVCAnalyzerAgent()

        with pytest.raises(
            AgentNotInitializedError,
            match="not yet implemented"
        ):
            await agent.interrupt()

    def test_get_config(self):
        """Test get_config."""
        agent = SpringMVCAnalyzerAgent()

        config = agent.get_config()
        assert config.mode == SERVER_MODE_SDK_AGENT

    def test_get_tools(self):
        """Test get_tools."""
        agent = SpringMVCAnalyzerAgent()

        tools = agent.get_tools()
        assert isinstance(tools, list)

    def test_get_hooks(self):
        """Test get_hooks."""
        agent = SpringMVCAnalyzerAgent()

        hooks = agent.get_hooks()
        assert isinstance(hooks, list)

    def test_system_prompt_caching(self):
        """Test system prompt is cached."""
        prompt_content = "Test prompt for caching"

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False
        ) as f:
            f.write(prompt_content)
            prompt_path = f.name

        try:
            # Create config with prompt path (use forward slashes for YAML compatibility)
            prompt_path_yaml = prompt_path.replace("\\", "/")
            config_data = f"""
server:
  mode: "sdk_agent"

sdk_agent:
  prompts:
    system_prompt_path: "{prompt_path_yaml}"
"""
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False
            ) as cf:
                cf.write(config_data)
                config_path = cf.name

            try:
                # First agent
                agent1 = SpringMVCAnalyzerAgent(config_path=config_path)
                assert agent1.system_prompt == prompt_content

                # Second agent - should use cached prompt
                agent2 = SpringMVCAnalyzerAgent(config_path=config_path)
                assert agent2.system_prompt == prompt_content

            finally:
                os.unlink(config_path)

        finally:
            os.unlink(prompt_path)
