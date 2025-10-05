"""
SDK Agent Module for SpringMVC Analyzer.

This module provides an interactive, dialogue-driven analysis mode using
Claude Agent SDK. It enables bidirectional conversation with autonomous
agent decision-making.

Main Components:
- SpringMVCAnalyzerAgent: Main client class for SDK Agent mode
- Tools: @tool decorated functions for code analysis
- Hooks: Pre/Post processing hooks for validation, caching, etc.
- Permissions: Fine-grained tool usage control

Usage:
    from sdk_agent.client import SpringMVCAnalyzerAgent

    agent = SpringMVCAnalyzerAgent(
        config_path="config/sdk_agent_config.yaml",
        hooks_enabled=True
    )

    await agent.start_interactive()
"""

__version__ = "0.1.0"

from sdk_agent.client import SpringMVCAnalyzerAgent

__all__ = ["SpringMVCAnalyzerAgent"]
