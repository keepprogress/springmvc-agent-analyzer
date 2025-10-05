"""
SDK Agent Configuration Module.

Handles loading and validation of SDK Agent configuration.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from sdk_agent.exceptions import ConfigurationError


class SDKAgentConfig(BaseModel):
    """SDK Agent configuration model."""

    # Server mode
    mode: str = Field(default="sdk_agent", description="Operating mode")

    # Model configuration
    default_model: str = Field(
        default="claude-sonnet-4-5",
        description="Default model"
    )

    # Agent configuration
    min_confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold"
    )

    # SDK Agent specific
    max_turns: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum conversation turns"
    )

    permission_mode: str = Field(
        default="acceptEdits",
        description="Permission mode: acceptAll, acceptEdits, rejectAll"
    )

    hooks_enabled: bool = Field(
        default=True,
        description="Enable hooks system"
    )

    # Hooks configuration
    hooks: Dict[str, Any] = Field(
        default_factory=lambda: {
            "validation": {"enabled": True, "min_confidence": 0.7},
            "cache": {"enabled": True, "similarity_threshold": 0.85},
            "context_manager": {"enabled": True, "compact_threshold": 50},
            "input_enhancement": {"enabled": True},
            "cleanup": {"enabled": True}
        },
        description="Hooks configuration"
    )

    # Prompts
    system_prompt_path: Optional[str] = Field(
        default="prompts/sdk_agent/system_prompt.md",
        description="Path to system prompt"
    )

    include_examples: bool = Field(
        default=True,
        description="Include few-shot examples in prompts"
    )

    # Graph
    auto_build_graph: bool = Field(
        default=True,
        description="Automatically build graph after analysis"
    )

    export_format: str = Field(
        default="d3",
        description="Default graph export format"
    )

    # Cache
    cache_dir: str = Field(
        default=".cache",
        description="Cache directory"
    )

    max_cache_size_mb: int = Field(
        default=1000,
        ge=0,
        description="Max cache size in MB"
    )

    ttl_seconds: int = Field(
        default=86400,
        ge=0,
        description="Cache TTL in seconds"
    )

    @validator("permission_mode")
    def validate_permission_mode(cls, v):
        """Validate permission mode."""
        valid_modes = ["acceptAll", "acceptEdits", "rejectAll", "custom"]
        if v not in valid_modes:
            raise ValueError(
                f"Invalid permission_mode: {v}. "
                f"Must be one of {valid_modes}"
            )
        return v

    @validator("mode")
    def validate_mode(cls, v):
        """Validate server mode."""
        if v not in ["api", "passive", "sdk_agent"]:
            raise ValueError(
                f"Invalid mode: {v}. "
                f"Must be one of: api, passive, sdk_agent"
            )
        return v


def load_config(config_path: Optional[str] = None) -> SDKAgentConfig:
    """
    Load SDK Agent configuration from file.

    Args:
        config_path: Path to config file (YAML)

    Returns:
        SDKAgentConfig instance

    Raises:
        ConfigurationError: If config is invalid
    """
    if config_path is None:
        config_path = "config/sdk_agent_config.yaml"

    config_file = Path(config_path)

    if not config_file.exists():
        raise ConfigurationError(
            f"Configuration file not found: {config_path}"
        )

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        # Extract relevant sections
        server_config = config_data.get("server", {})
        models_config = config_data.get("models", {})
        agents_config = config_data.get("agents", {})
        sdk_agent_config = config_data.get("sdk_agent", {})
        graph_config = config_data.get("graph", {})
        cache_config = config_data.get("cache", {})

        # Merge into flat config
        merged_config = {
            "mode": server_config.get("mode", "sdk_agent"),
            "default_model": models_config.get("default", "claude-sonnet-4-5"),
            "min_confidence": agents_config.get("min_confidence", 0.7),
            "max_turns": sdk_agent_config.get("max_turns", 20),
            "permission_mode": sdk_agent_config.get("permission_mode", "acceptEdits"),
            "hooks_enabled": sdk_agent_config.get("hooks_enabled", True),
            "hooks": sdk_agent_config.get("hooks", {}),
            "system_prompt_path": sdk_agent_config.get("prompts", {}).get(
                "system_prompt_path",
                "prompts/sdk_agent/system_prompt.md"
            ),
            "include_examples": sdk_agent_config.get("prompts", {}).get(
                "include_examples",
                True
            ),
            "auto_build_graph": graph_config.get("auto_build", True),
            "export_format": graph_config.get("export_format", "d3"),
            "cache_dir": cache_config.get("cache_dir", ".cache"),
            "max_cache_size_mb": cache_config.get("max_size_mb", 1000),
            "ttl_seconds": cache_config.get("ttl_seconds", 86400),
        }

        return SDKAgentConfig(**merged_config)

    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load config: {e}")


def validate_config_file(config_path: str) -> bool:
    """
    Validate configuration file.

    Args:
        config_path: Path to config file

    Returns:
        True if valid

    Raises:
        ConfigurationError: If invalid
    """
    try:
        load_config(config_path)
        return True
    except ConfigurationError:
        raise
