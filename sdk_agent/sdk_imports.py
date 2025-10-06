"""
Defensive imports for Claude Agent SDK.

Provides clear error messages if SDK is not installed.
"""

def check_sdk_installed():
    """Check if Claude Agent SDK is installed and provide helpful error message."""
    try:
        import claude_agent_sdk
        return True
    except ImportError:
        error_msg = """
╔════════════════════════════════════════════════════════════════╗
║  Claude Agent SDK Not Installed                                 ║
╚════════════════════════════════════════════════════════════════╝

The SDK Agent mode requires the Claude Agent SDK to be installed.

Installation:
  pip install claude-agent-sdk>=0.1.0

Requirements:
  • Python 3.10 or higher
  • Node.js (latest LTS version)
  • Claude Code 2.0.0 or higher

For more information, see:
  https://docs.claude.com/en/api/agent-sdk/python
  https://github.com/anthropics/claude-agent-sdk-python

After installation, restart the application.
"""
        raise ImportError(error_msg)


def import_sdk():
    """
    Import Claude Agent SDK components with error handling.

    Returns:
        Tuple of (tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient)

    Raises:
        ImportError: If SDK is not installed
    """
    check_sdk_installed()

    try:
        from claude_agent_sdk import (
            tool,
            create_sdk_mcp_server,
            ClaudeAgentOptions,
            ClaudeSDKClient
        )
        return tool, create_sdk_mcp_server, ClaudeAgentOptions, ClaudeSDKClient
    except ImportError as e:
        raise ImportError(f"Failed to import Claude Agent SDK components: {e}")
