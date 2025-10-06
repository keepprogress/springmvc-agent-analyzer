"""Tests for SDK Agent configuration."""

import pytest
import tempfile
import os
from pathlib import Path

from sdk_agent.config import SDKAgentConfig, load_config, validate_config_file
from sdk_agent.exceptions import ConfigurationError
from sdk_agent.constants import (
    SERVER_MODE_SDK_AGENT,
    PERMISSION_MODE_ACCEPT_EDITS,
    MIN_CONFIDENCE_THRESHOLD,
    DEFAULT_MAX_TURNS,
)


class TestSDKAgentConfig:
    """Test SDKAgentConfig model."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SDKAgentConfig()

        assert config.mode == SERVER_MODE_SDK_AGENT
        assert config.default_model == "claude-sonnet-4-5"
        assert config.min_confidence == MIN_CONFIDENCE_THRESHOLD
        assert config.max_turns == DEFAULT_MAX_TURNS
        assert config.permission_mode == PERMISSION_MODE_ACCEPT_EDITS
        assert config.hooks_enabled is True

    def test_invalid_permission_mode(self):
        """Test invalid permission mode raises error."""
        with pytest.raises(ValueError, match="Invalid permission_mode"):
            SDKAgentConfig(permission_mode="invalid")

    def test_invalid_server_mode(self):
        """Test invalid server mode raises error."""
        with pytest.raises(ValueError, match="Invalid mode"):
            SDKAgentConfig(mode="invalid")

    def test_confidence_bounds(self):
        """Test confidence threshold bounds."""
        # Valid
        config = SDKAgentConfig(min_confidence=0.8)
        assert config.min_confidence == 0.8

        # Invalid - too low
        with pytest.raises(ValueError):
            SDKAgentConfig(min_confidence=-0.1)

        # Invalid - too high
        with pytest.raises(ValueError):
            SDKAgentConfig(min_confidence=1.1)

    def test_max_turns_bounds(self):
        """Test max turns bounds."""
        # Valid
        config = SDKAgentConfig(max_turns=50)
        assert config.max_turns == 50

        # Invalid - too low
        with pytest.raises(ValueError):
            SDKAgentConfig(max_turns=0)

        # Invalid - too high
        with pytest.raises(ValueError):
            SDKAgentConfig(max_turns=101)


class TestLoadConfig:
    """Test configuration loading."""

    def test_load_valid_config(self):
        """Test loading valid configuration."""
        config_data = """
server:
  mode: "sdk_agent"

models:
  default: "claude-sonnet-4-5"

agents:
  min_confidence: 0.8

sdk_agent:
  max_turns: 30
  permission_mode: "acceptAll"
  hooks_enabled: false

cache:
  cache_dir: ".test_cache"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(config_data)
            config_path = f.name

        try:
            config = load_config(config_path)

            assert config.mode == "sdk_agent"
            assert config.min_confidence == 0.8
            assert config.max_turns == 30
            assert config.permission_mode == "acceptAll"
            assert config.hooks_enabled is False
            assert config.cache_dir == ".test_cache"

        finally:
            os.unlink(config_path)

    def test_load_nonexistent_config(self):
        """Test loading non-existent config raises error."""
        with pytest.raises(ConfigurationError, match="not found"):
            load_config("/nonexistent/config.yaml")

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error."""
        config_data = """
        invalid: yaml: content:
        - broken
        """
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(config_data)
            config_path = f.name

        try:
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                load_config(config_path)
        finally:
            os.unlink(config_path)

    def test_validate_config_file(self):
        """Test config validation."""
        config_data = """
server:
  mode: "sdk_agent"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(config_data)
            config_path = f.name

        try:
            assert validate_config_file(config_path) is True
        finally:
            os.unlink(config_path)
